"""Song Project Orchestrator - Coordinates services for song project operations

IMPORTANT: This orchestrator coordinates services but contains NO business logic.
Business logic is in song_project_transformer.py (100% testable).
This orchestrator is NOT unit-tested (orchestration only).
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any
from uuid import UUID

from config.settings import S3_SONG_PROJECTS_BUCKET
from infrastructure.storage import get_storage


if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from business.song_project_transformer import (
    calculate_file_hash,
    calculate_pagination_meta,
    detect_file_type,
    generate_s3_prefix,
    get_default_folder_structure,
    get_display_cover_info,
    get_mime_type,
    normalize_project_name,
    transform_image_to_assigned_response,
    transform_project_detail_to_response,
    transform_project_to_response,
    transform_release_to_assigned_response,
    transform_sketch_to_assigned_response,
    transform_song_to_assigned_response,
)
from db.song_project_service import song_project_service
from utils.logger import logger


class SongProjectOrchestrator:
    """Orchestrator for song project operations (coordinates services, NO business logic)"""

    def __init__(self):
        """Initialize orchestrator with services"""
        self.db_service = song_project_service
        self._storage = None  # Lazy init to allow server startup when MinIO is down

    @property
    def storage(self):
        """Lazy-load S3 storage (only when first accessed)"""
        if self._storage is None:
            self._storage = get_storage(bucket=S3_SONG_PROJECTS_BUCKET)
        return self._storage

    def create_project_with_structure(
        self,
        db: Session,
        user_id: UUID,
        project_name: str,
        tags: list[str] | None = None,
        description: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Create project with default folder structure and S3 setup

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_name: Project name
            tags: Optional tags list
            description: Optional description

        Returns:
            Project data dictionary or None if failed
        """
        try:
            # 1. Normalize project name (business logic in transformer)
            normalized_name = normalize_project_name(project_name)
            if not normalized_name:
                logger.warning("Project name is empty after normalization")
                return None

            # 2. Generate S3 prefix (business logic in transformer)
            s3_prefix = generate_s3_prefix(normalized_name, str(user_id))

            # 3. Create project in DB (CRUD in db_service)
            project = self.db_service.create_project(
                db=db,
                user_id=user_id,
                project_name=normalized_name,
                s3_prefix=s3_prefix,
                tags=tags,
                description=description,
            )

            if not project:
                logger.error("Failed to create project in DB")
                return None

            # 4. Get default folder structure (business logic in transformer)
            folder_defs = get_default_folder_structure()

            # 5. Create folders in DB and S3 (coordination)
            created_folders = []
            for folder_def in folder_defs:
                # Generate S3 prefix for folder
                folder_s3_prefix = f"{s3_prefix}{folder_def['folder_name']}/"

                # Create folder in DB
                folder = self.db_service.create_folder(
                    db=db,
                    project_id=project.id,
                    folder_name=folder_def["folder_name"],
                    folder_type=folder_def["folder_type"],
                    s3_prefix=folder_s3_prefix,
                    custom_icon=folder_def.get("custom_icon"),
                )

                if folder:
                    created_folders.append(folder)

                    # Create placeholder file in S3 (to ensure folder exists)
                    try:
                        placeholder_key = f"{folder_s3_prefix}.gitkeep"
                        self.storage.upload(b"", placeholder_key, content_type="text/plain")
                    except Exception as e:
                        logger.warning(
                            "Failed to create S3 placeholder", folder=folder_def["folder_name"], error=str(e)
                        )

            logger.info(
                "Project created with structure",
                project_id=str(project.id),
                project_name=normalized_name,
                folders_created=len(created_folders),
            )

            # 6. Transform to response (business logic in transformer)
            return transform_project_to_response(project)

        except Exception as e:
            logger.error("Project creation orchestration failed", error=str(e), error_type=type(e).__name__)
            return None

    def get_project_by_id(self, db: Session, project_id: UUID, user_id: UUID) -> dict[str, Any] | None:
        """
        Get project by ID (without details)

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User ID (for ownership check)

        Returns:
            Project data dictionary or None if not found/unauthorized
        """
        try:
            # Get project from DB
            project = self.db_service.get_project_by_id(db, project_id)

            if not project:
                logger.debug("Project not found", project_id=str(project_id))
                return None

            # Check ownership
            if project.user_id != user_id:
                logger.warning("Unauthorized project access", project_id=str(project_id), user_id=str(user_id))
                return None

            # Transform to response
            return transform_project_to_response(project)

        except Exception as e:
            logger.error(
                "Get project by ID failed", project_id=str(project_id), error=str(e), error_type=type(e).__name__
            )
            return None

    def _load_assigned_assets_for_folders(
        self, db: Session, project_id: UUID, folders_data: list[dict[str, Any]]
    ) -> None:
        """
        Load assigned assets (songs, sketches, images) for all folders (coordination only)

        Args:
            db: Database session
            project_id: Project UUID
            folders_data: List of folder dictionaries (will be modified in-place)

        Note:
            This method modifies folders_data in-place by adding assigned_songs,
            assigned_sketches, and assigned_images lists to each folder.
        """
        try:
            for folder_data in folders_data:
                folder_id = UUID(folder_data["id"])

                # Load assigned songs from DB
                songs = self.db_service.get_assigned_songs_for_folder(db, project_id, folder_id)
                folder_data["assigned_songs"] = [transform_song_to_assigned_response(song) for song in songs]

                # Load assigned sketches from DB
                sketches = self.db_service.get_assigned_sketches_for_folder(db, project_id, folder_id)
                folder_data["assigned_sketches"] = [
                    transform_sketch_to_assigned_response(sketch) for sketch in sketches
                ]

                # Load assigned images from DB
                images = self.db_service.get_assigned_images_for_folder(db, project_id, folder_id)
                folder_data["assigned_images"] = [transform_image_to_assigned_response(image) for image in images]

                logger.debug(
                    "Assigned assets loaded for folder",
                    folder_id=str(folder_id),
                    songs_count=len(songs),
                    sketches_count=len(sketches),
                    images_count=len(images),
                )

        except Exception as e:
            logger.error(
                "Failed to load assigned assets",
                project_id=str(project_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            # Don't fail the entire request, just log the error

    def _load_assigned_releases(self, db: Session, project_id: UUID, response_data: dict[str, Any]) -> None:
        """
        Load assigned releases for project (coordination only)

        Args:
            db: Database session
            project_id: Project UUID
            response_data: Response dictionary (will be modified in-place)

        Note:
            This method modifies response_data in-place by adding assigned_releases list
        """
        try:
            # Load assigned releases from DB
            releases = self.db_service.get_assigned_releases_for_project(db, project_id)
            response_data["assigned_releases"] = [
                transform_release_to_assigned_response(release) for release in releases
            ]

            logger.debug(
                "Assigned releases loaded for project", project_id=str(project_id), releases_count=len(releases)
            )

        except Exception as e:
            logger.error(
                "Failed to load assigned releases",
                project_id=str(project_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            # Don't fail the entire request, just log the error
            response_data["assigned_releases"] = []

    def _load_all_assigned_assets(self, db: Session, project_id: UUID, response_data: dict[str, Any]) -> None:
        """
        Load ALL assigned assets for project (for Metadata tab, regardless of folder assignment)

        Args:
            db: Database session
            project_id: Project UUID
            response_data: Response dictionary (will be modified in-place)

        Note:
            This method modifies response_data in-place by adding all_assigned_songs,
            all_assigned_sketches, and all_assigned_images lists.
        """
        try:
            # Load ALL assigned songs from DB
            songs = self.db_service.get_all_assigned_songs_for_project(db, project_id)
            response_data["all_assigned_songs"] = [transform_song_to_assigned_response(song) for song in songs]

            # Load ALL assigned sketches from DB
            sketches = self.db_service.get_all_assigned_sketches_for_project(db, project_id)
            response_data["all_assigned_sketches"] = [
                transform_sketch_to_assigned_response(sketch) for sketch in sketches
            ]

            # Load ALL assigned images from DB
            images = self.db_service.get_all_assigned_images_for_project(db, project_id)
            response_data["all_assigned_images"] = [transform_image_to_assigned_response(image) for image in images]

            logger.debug(
                "All assigned assets loaded for project",
                project_id=str(project_id),
                songs_count=len(songs),
                sketches_count=len(sketches),
                images_count=len(images),
            )

        except Exception as e:
            logger.error(
                "Failed to load all assigned assets",
                project_id=str(project_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            # Don't fail the entire request, just log the error
            response_data["all_assigned_songs"] = []
            response_data["all_assigned_sketches"] = []
            response_data["all_assigned_images"] = []

    def get_project_with_details(self, db: Session, project_id: UUID, user_id: UUID) -> dict[str, Any] | None:
        """
        Get project with all folders, files, and assigned assets

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User ID (for ownership check)

        Returns:
            Project data with folders, files, and assigned assets, or None if not found/unauthorized
        """
        try:
            # Get project with details from DB
            project = self.db_service.get_project_with_details(db, project_id)

            if not project:
                logger.debug("Project not found", project_id=str(project_id))
                return None

            # Check ownership
            if project.user_id != user_id:
                logger.warning("Unauthorized project access", project_id=str(project_id), user_id=str(user_id))
                return None

            # Transform to response (includes folders and files)
            response = transform_project_detail_to_response(project)

            # Load assigned assets for all folders (coordination)
            self._load_assigned_assets_for_folders(db, project_id, response["folders"])

            # Load assigned releases for project (coordination)
            self._load_assigned_releases(db, project_id, response)

            # Load ALL assigned assets for project (for Metadata tab)
            self._load_all_assigned_assets(db, project_id, response)

            # Add cover_info based on assigned releases (business logic in transformer)
            releases = self.db_service.get_assigned_releases_for_project(db, project_id)
            cover_info = get_display_cover_info(releases)
            response["cover_info"] = cover_info

            return response

        except Exception as e:
            logger.error(
                "Get project details failed", project_id=str(project_id), error=str(e), error_type=type(e).__name__
            )
            return None

    def list_projects(
        self,
        db: Session,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
        tags: str | None = None,
        project_status: str | None = None,
    ) -> dict[str, Any]:
        """
        List projects for user (paginated)

        Args:
            db: Database session
            user_id: User ID (from JWT)
            limit: Items per page
            offset: Offset for pagination
            search: Search term
            tags: Comma-separated tags
            project_status: Status filter ('new', 'progress', 'archived', or None for all non-archived)

        Returns:
            Dictionary with projects and pagination meta
        """
        try:
            # Get paginated projects from DB
            result = self.db_service.get_projects_paginated(
                db=db,
                user_id=user_id,
                limit=limit,
                offset=offset,
                search=search,
                tags=tags,
                project_status=project_status,
            )

            # Transform projects to response
            projects_data = [transform_project_to_response(p) for p in result["items"]]

            # Add cover_info for each project (based on assigned releases)
            for project_data in projects_data:
                project_id = UUID(project_data["id"])
                # Load assigned releases
                releases = self.db_service.get_assigned_releases_for_project(db, project_id)
                # Determine cover display logic (business logic in transformer)
                cover_info = get_display_cover_info(releases)
                project_data["cover_info"] = cover_info

            # Calculate pagination metadata (business logic in transformer)
            pagination = calculate_pagination_meta(result["total"], limit, offset)

            return {
                "projects": projects_data,
                "pagination": pagination,
            }

        except Exception as e:
            logger.error("List projects failed", user_id=str(user_id), error=str(e), error_type=type(e).__name__)
            return {
                "projects": [],
                "pagination": {"total": 0, "limit": limit, "offset": offset, "has_more": False},
            }

    def update_project(
        self,
        db: Session,
        project_id: UUID,
        user_id: UUID,
        update_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Update project

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User ID (for ownership check)
            update_data: Data to update

        Returns:
            Updated project data or None if failed
        """
        try:
            # Get project for ownership check
            project = self.db_service.get_project_by_id(db, project_id)
            if not project:
                logger.debug("Project not found", project_id=str(project_id))
                return None

            # Check ownership
            if project.user_id != user_id:
                logger.warning("Unauthorized project update", project_id=str(project_id), user_id=str(user_id))
                return None

            # Normalize project name if provided (business logic in transformer)
            if "project_name" in update_data:
                update_data["project_name"] = normalize_project_name(update_data["project_name"])

            # Update project in DB
            updated_project = self.db_service.update_project(db, project_id, user_id, update_data)

            if not updated_project:
                logger.error("Failed to update project in DB", project_id=str(project_id))
                return None

            # Transform to response
            return transform_project_to_response(updated_project)

        except Exception as e:
            logger.error("Update project failed", project_id=str(project_id), error=str(e), error_type=type(e).__name__)
            return None

    def delete_project_with_cleanup(self, db: Session, project_id: UUID, user_id: UUID) -> bool:
        """
        Delete project with S3 cleanup

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User ID (for ownership check)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get project for ownership check
            project = self.db_service.get_project_by_id(db, project_id)
            if not project:
                logger.debug("Project not found", project_id=str(project_id))
                return False

            # Check ownership
            if project.user_id != user_id:
                logger.warning("Unauthorized project deletion", project_id=str(project_id), user_id=str(user_id))
                return False

            # Prevent deletion of archived projects
            if project.project_status == "archived":
                logger.warning(
                    "Cannot delete archived project",
                    project_id=str(project_id),
                    project_status=project.project_status,
                )
                return False

            # Prevent deletion of projects assigned to releases
            assigned_releases = self.db_service.get_assigned_releases_for_project(db, project_id)
            if assigned_releases:
                logger.warning(
                    "Cannot delete project assigned to releases",
                    project_id=str(project_id),
                    release_count=len(assigned_releases),
                )
                return False

            # Delete S3 files if s3_prefix exists
            if project.s3_prefix:
                try:
                    # List all files with this prefix
                    files = self.storage.list_files(project.s3_prefix)
                    for file_key in files:
                        self.storage.delete(file_key)
                    logger.info("S3 files deleted", project_id=str(project_id), files_deleted=len(files))
                except Exception as e:
                    logger.warning("S3 cleanup failed", project_id=str(project_id), error=str(e))
                    # Continue with DB deletion even if S3 fails

            # Delete project from DB (cascade deletes folders and files)
            success = self.db_service.delete_project(db, project_id)

            if success:
                logger.info("Project deleted with cleanup", project_id=str(project_id))
            else:
                logger.error("Failed to delete project from DB", project_id=str(project_id))

            return success

        except Exception as e:
            logger.error(
                "Delete project with cleanup failed",
                project_id=str(project_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def upload_file_to_project(
        self,
        db: Session,
        project_id: UUID,
        user_id: UUID,
        folder_name: str,
        filename: str,
        file_data: bytes,
    ) -> dict[str, Any] | None:
        """
        Upload file to project folder (S3 + DB)

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User ID (for ownership check)
            folder_name: Target folder name
            filename: File name
            file_data: File bytes

        Returns:
            File data dictionary or None if failed
        """
        try:
            # Get project for ownership check
            project = self.db_service.get_project_by_id(db, project_id)
            if not project or project.user_id != user_id:
                logger.warning("Unauthorized file upload", project_id=str(project_id), user_id=str(user_id))
                return None

            # Get project with details to find folder
            project_details = self.db_service.get_project_with_details(db, project_id)
            if not project_details:
                return None

            # Find folder by name
            folder = next((f for f in project_details.folders if f.folder_name == folder_name), None)
            if not folder:
                logger.warning("Folder not found", folder_name=folder_name, project_id=str(project_id))
                return None

            # Extract actual filename from path (if filename contains subdirectories)
            # Example: "Drums/Kick.wav" → filename="Kick.wav", subdir="Drums/"
            from pathlib import Path as PathLib

            file_path_obj = PathLib(filename)
            actual_filename = file_path_obj.name  # Just the filename
            subdir = str(file_path_obj.parent) if file_path_obj.parent != PathLib(".") else ""

            # Detect file type and MIME type (business logic in transformer)
            file_type = detect_file_type(actual_filename)
            mime_type = get_mime_type(actual_filename)

            # Generate S3 key with subdirectories preserved
            # Example: folder.s3_prefix = "user_123/project_456/Audio Files/"
            # filename = "Drums/Kick.wav" → s3_key = "user_123/project_456/Audio Files/Drums/Kick.wav"
            if subdir:
                # Normalize subdirectory path (forward slashes)
                subdir_normalized = subdir.replace("\\", "/")
                if not subdir_normalized.endswith("/"):
                    subdir_normalized += "/"
                s3_key = f"{folder.s3_prefix}{subdir_normalized}{actual_filename}"
                relative_path = f"{folder_name}/{subdir_normalized}{actual_filename}"
            else:
                s3_key = f"{folder.s3_prefix}{actual_filename}"
                relative_path = f"{folder_name}/{actual_filename}"

            # Calculate file hash (for Mirror sync comparison)
            file_hash = calculate_file_hash(file_data)
            logger.debug(
                "File hash calculated",
                filename=actual_filename,
                hash_length=len(file_hash) if file_hash else 0,
                hash_preview=file_hash[:16] if file_hash else "None",
            )

            # Check if file already exists (Mirror update scenario)
            existing_file = self.db_service.get_file_by_path(db, project_id, relative_path)

            if existing_file:
                logger.info(
                    "File exists, updating (Mirror scenario)",
                    file_id=str(existing_file.id),
                    relative_path=relative_path,
                    old_hash=existing_file.file_hash,
                    new_hash=file_hash,
                )

                # Upload to S3 (overwrite existing)
                try:
                    self.storage.upload(file_data, s3_key, content_type=mime_type)
                except Exception as e:
                    logger.error("S3 upload failed", s3_key=s3_key, error=str(e))
                    return None

                # Update existing file record
                file_record = self.db_service.update_file(
                    db=db,
                    file_id=existing_file.id,
                    s3_key=s3_key,
                    file_size_bytes=len(file_data),
                    file_hash=file_hash,
                    mime_type=mime_type,
                )

                if not file_record:
                    logger.error("Failed to update file record in DB", file_id=str(existing_file.id))
                    return None

            else:
                # New file - upload to S3 and create DB record
                logger.debug("New file, creating", relative_path=relative_path)

                # Upload to S3
                try:
                    self.storage.upload(file_data, s3_key, content_type=mime_type)
                except Exception as e:
                    logger.error("S3 upload failed", s3_key=s3_key, error=str(e))
                    return None

                # Create file record in DB
                # filename = just the filename (no subdirs)
                # relative_path = full path including subdirs (e.g., "Audio Files/Drums/Kick.wav")
                file_record = self.db_service.create_file(
                    db=db,
                    project_id=project_id,
                    folder_id=folder.id,
                    filename=actual_filename,  # Just the filename
                    relative_path=relative_path,  # Full path with subdirs
                    s3_key=s3_key,
                    file_type=file_type,
                    mime_type=mime_type,
                    file_size_bytes=len(file_data),
                    file_hash=file_hash,  # SHA256 for Mirror comparison
                    storage_backend="s3",
                )

                if not file_record:
                    logger.error("Failed to create file record in DB", s3_key=s3_key)
                    # Try to cleanup S3
                    with contextlib.suppress(Exception):
                        self.storage.delete(s3_key)
                    return None

            logger.info(
                "File uploaded to project",
                project_id=str(project_id),
                filename=actual_filename,
                relative_path=relative_path,
                folder=folder_name,
            )

            # Auto-update project status: 'new' → 'progress' after first file upload
            if project.project_status == "new":
                updated_project = self.db_service.update_project(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    update_data={"project_status": "progress"},
                )
                if updated_project:
                    logger.info(
                        "Project status auto-updated after file upload",
                        project_id=str(project_id),
                        old_status="new",
                        new_status="progress",
                    )
                else:
                    logger.warning("Failed to auto-update project status", project_id=str(project_id))

            # Note: Project stats (total_files, total_size_bytes) are calculated LIVE
            # in transform_project_detail_to_response() from actual files (Single Source of Truth)

            # Generate download URL
            download_url = self.storage.get_url(s3_key, expires_in=3600)

            # Transform to response (business logic in transformer)
            from business.song_project_transformer import transform_file_to_response

            return transform_file_to_response(file_record, download_url=download_url)

        except Exception as e:
            logger.error(
                "Upload file to project failed", project_id=str(project_id), error=str(e), error_type=type(e).__name__
            )
            return None

    def batch_upload_files_to_project(
        self,
        db: Session,
        project_id: UUID,
        user_id: UUID,
        folder_name: str,
        files: list,
    ) -> dict[str, Any]:
        """
        Upload multiple files to project folder

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User ID (for ownership check)
            folder_name: Target folder name
            files: List of FileStorage objects from request.files.getlist()

        Returns:
            Dictionary with upload results:
            {
                'uploaded': int,
                'failed': int,
                'errors': [{'filename': str, 'error': str}, ...]
            }
        """
        uploaded = 0
        failed = 0
        errors = []

        for file in files:
            try:
                filename = file.filename
                file_data = file.read()

                # Reuse existing single-file upload logic
                result = self.upload_file_to_project(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    folder_name=folder_name,
                    filename=filename,
                    file_data=file_data,
                )

                if result:
                    uploaded += 1
                    logger.debug("File uploaded", filename=filename, project_id=str(project_id))
                else:
                    failed += 1
                    errors.append({"filename": filename, "error": "Upload failed"})
                    logger.warning("File upload failed", filename=filename, project_id=str(project_id))

            except Exception as e:
                failed += 1
                errors.append({"filename": file.filename, "error": str(e)})
                logger.error(
                    "File upload error in batch",
                    filename=file.filename,
                    project_id=str(project_id),
                    error=str(e),
                    error_type=type(e).__name__,
                )

        logger.info(
            "Batch upload completed",
            project_id=str(project_id),
            uploaded=uploaded,
            failed=failed,
            total=len(files),
        )

        return {"uploaded": uploaded, "failed": failed, "errors": errors}

    def mirror_compare_files(
        self,
        db: Session,
        project_id: UUID,
        user_id: UUID,
        folder_id: UUID,
        local_files: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Compare local files vs remote files (for Mirror sync)

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User ID (for ownership check)
            folder_id: Folder UUID
            local_files: List of dicts with keys: relative_path, file_hash, file_size_bytes

        Returns:
            Dictionary with diff:
            {
                'to_upload': [relative_path, ...],  # New files
                'to_update': [relative_path, ...],  # Changed files (hash mismatch)
                'to_delete': [{'file_id': uuid, 'relative_path': str}, ...],  # Remote only
                'unchanged': [relative_path, ...]  # Hash match
            }
        """
        try:
            # Get project for ownership check
            project = self.db_service.get_project_by_id(db, project_id)
            if not project or project.user_id != user_id:
                logger.warning("Unauthorized mirror compare", project_id=str(project_id), user_id=str(user_id))
                return None

            # Get folder to extract folder_name (needed for path normalization)
            folder = self.db_service.get_folder_by_id(db, folder_id)
            if not folder:
                logger.warning("Folder not found", folder_id=str(folder_id))
                return None

            folder_name = folder.folder_name

            # Get all remote files for this folder
            remote_files = self.db_service.get_files_by_folder(db, folder_id)

            # Build lookup maps
            # IMPORTANT: Remote files have relative_path like "01 Arrangement/Bounces/file.wav"
            # but CLI sends "Bounces/file.wav" (without folder_name prefix).
            # We need to strip the folder_name prefix from remote paths for comparison!
            # CRITICAL: Normalize the relative_path IN the dictionary itself, not just the key!
            local_map = {}
            for f in local_files:
                normalized_path = f["relative_path"].lstrip("/")
                # Create new dict with normalized path
                normalized_file = {**f, "relative_path": normalized_path}
                local_map[normalized_path] = normalized_file

            remote_map = {}
            for f in remote_files:
                # Strip folder_name prefix (e.g., "01 Arrangement/" → "")
                normalized_path = f.relative_path
                if normalized_path.startswith(f"{folder_name}/"):
                    normalized_path = normalized_path[len(folder_name) + 1 :]  # +1 for trailing slash
                # Also strip leading slash if present
                normalized_path = normalized_path.lstrip("/")
                remote_map[normalized_path] = f

            # Calculate diff
            to_upload = []
            to_update = []
            to_delete = []
            unchanged = []

            # Check local files vs remote
            for rel_path, local_file in local_map.items():
                if rel_path not in remote_map:
                    # File exists locally but not remotely → upload
                    to_upload.append(rel_path)
                else:
                    remote_file = remote_map[rel_path]
                    # Compare hashes
                    if local_file["file_hash"] != remote_file.file_hash:
                        # Hash mismatch → update
                        to_update.append(rel_path)
                    else:
                        # Hash match → unchanged
                        unchanged.append(rel_path)

            # Check remote files not in local (leichen!)
            for rel_path, remote_file in remote_map.items():
                if rel_path not in local_map:
                    # File exists remotely but not locally → delete
                    to_delete.append(
                        {
                            "file_id": str(remote_file.id),
                            "relative_path": rel_path,
                            "file_size_bytes": remote_file.file_size_bytes,
                        }
                    )

            # MOVE DETECTION: Detect files with same hash but different path
            # Build hash-to-files maps for move detection
            local_hash_map: dict[str, list[str]] = {}
            remote_hash_map: dict[str, list[dict]] = {}

            for rel_path, local_file in local_map.items():
                hash_val = local_file["file_hash"]
                local_hash_map.setdefault(hash_val, []).append(rel_path)

            for rel_path, remote_file in remote_map.items():
                hash_val = remote_file.file_hash
                remote_hash_map.setdefault(hash_val, []).append({"path": rel_path, "file": remote_file})

            # Detect moves (same hash, different path)
            to_move = []
            moved_upload_paths = set()  # Track paths to remove from to_upload
            moved_delete_items = []  # Track items to remove from to_delete

            for hash_val in local_hash_map.keys() & remote_hash_map.keys():
                local_paths = set(local_hash_map[hash_val])
                remote_items = remote_hash_map[hash_val]
                remote_paths = {item["path"] for item in remote_items}

                # Files that disappeared from old location
                disappeared = remote_paths - local_paths
                # Files that appeared at new location
                appeared = local_paths - remote_paths

                # Only handle clear 1:1 moves to avoid ambiguity
                if len(disappeared) == 1 and len(appeared) == 1:
                    old_path = list(disappeared)[0]
                    new_path = list(appeared)[0]
                    remote_file = next(item["file"] for item in remote_items if item["path"] == old_path)

                    # Construct new S3 key (must include folder_name prefix)
                    # Strip leading slash from new_path to avoid double slashes
                    new_s3_key = f"{project.s3_prefix.rstrip('/')}/{folder_name}/{new_path.lstrip('/')}"

                    to_move.append(
                        {
                            "file_id": str(remote_file.id),
                            "old_path": old_path,
                            "new_path": new_path,
                            "file_hash": hash_val,
                            "file_size_bytes": remote_file.file_size_bytes,
                            "s3_key_old": remote_file.s3_key,
                            "s3_key_new": new_s3_key,
                        }
                    )

                    # Mark for removal from to_upload/to_delete
                    moved_upload_paths.add(new_path)
                    moved_delete_items.append(str(remote_file.id))

            # Remove moved files from to_upload and to_delete
            to_upload = [p for p in to_upload if p not in moved_upload_paths]
            to_delete = [d for d in to_delete if d["file_id"] not in moved_delete_items]

            logger.info(
                "Mirror compare completed",
                project_id=str(project_id),
                folder_id=str(folder_id),
                to_upload=len(to_upload),
                to_update=len(to_update),
                to_move=len(to_move),
                to_delete=len(to_delete),
                unchanged=len(unchanged),
            )

            return {
                "to_upload": to_upload,
                "to_update": to_update,
                "to_move": to_move,
                "to_delete": to_delete,
                "unchanged": unchanged,
            }

        except Exception as e:
            logger.error(
                "Mirror compare failed",
                project_id=str(project_id),
                folder_id=str(folder_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def batch_delete_files(
        self,
        db: Session,
        project_id: UUID,
        user_id: UUID,
        file_ids: list[str],
    ) -> dict[str, Any]:
        """
        Delete multiple files from project (S3 + DB)

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User ID (for ownership check)
            file_ids: List of file UUID strings

        Returns:
            Dictionary with deletion results:
            {
                'deleted': int,
                'failed': int,
                'errors': [{'file_id': str, 'error': str}, ...]
            }
        """
        deleted = 0
        failed = 0
        errors = []

        try:
            # Get project for ownership check
            project = self.db_service.get_project_by_id(db, project_id)
            if not project or project.user_id != user_id:
                logger.warning("Unauthorized batch delete", project_id=str(project_id), user_id=str(user_id))
                return {
                    "deleted": 0,
                    "failed": len(file_ids),
                    "errors": [{"file_id": fid, "error": "Unauthorized"} for fid in file_ids],
                }

            # Delete each file
            for file_id_str in file_ids:
                try:
                    file_id = UUID(file_id_str)

                    # Get file record for S3 key
                    file_record = self.db_service.get_file_by_id(db, file_id)

                    if not file_record:
                        failed += 1
                        errors.append({"file_id": file_id_str, "error": "File not found"})
                        logger.warning("File not found for deletion", file_id=file_id_str)
                        continue

                    # Check ownership (file belongs to this project)
                    if file_record.project_id != project_id:
                        failed += 1
                        errors.append({"file_id": file_id_str, "error": "File does not belong to this project"})
                        logger.warning("File ownership mismatch", file_id=file_id_str, project_id=str(project_id))
                        continue

                    # Delete from S3
                    try:
                        if file_record.s3_key:
                            self.storage.delete(file_record.s3_key)
                    except Exception as e:
                        logger.warning("S3 delete failed", file_id=file_id_str, s3_key=file_record.s3_key, error=str(e))
                        # Continue with DB deletion even if S3 fails

                    # Delete from DB
                    if self.db_service.delete_file(db, file_id):
                        deleted += 1
                        logger.debug("File deleted", file_id=file_id_str, filename=file_record.filename)
                    else:
                        failed += 1
                        errors.append({"file_id": file_id_str, "error": "Database deletion failed"})

                except ValueError:
                    failed += 1
                    errors.append({"file_id": file_id_str, "error": "Invalid UUID"})
                    logger.warning("Invalid file UUID", file_id=file_id_str)
                except Exception as e:
                    failed += 1
                    errors.append({"file_id": file_id_str, "error": str(e)})
                    logger.error("File deletion error", file_id=file_id_str, error=str(e), error_type=type(e).__name__)

            logger.info(
                "Batch delete completed",
                project_id=str(project_id),
                deleted=deleted,
                failed=failed,
                total=len(file_ids),
            )

            return {"deleted": deleted, "failed": failed, "errors": errors}

        except Exception as e:
            logger.error(
                "Batch delete failed",
                project_id=str(project_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "deleted": deleted,
                "failed": len(file_ids) - deleted,
                "errors": [{"file_id": "unknown", "error": f"Batch delete orchestration failed: {str(e)}"}],
            }

    def batch_move_files(
        self,
        db: Session,
        project_id: UUID,
        user_id: UUID,
        move_actions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Move multiple files in S3 and update DB (for Mirror sync)

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User ID (for ownership check)
            move_actions: List with keys: file_id, old_path, new_path,
                          s3_key_old, s3_key_new, file_hash

        Returns:
            Dictionary with move results:
            {
                'moved': int,
                'failed': int,
                'errors': [{'file_id': str, 'error': str}, ...]
            }
        """
        moved = 0
        failed = 0
        errors = []

        try:
            # Get project for ownership check
            project = self.db_service.get_project_by_id(db, project_id)
            if not project or project.user_id != user_id:
                logger.warning("Unauthorized batch move", project_id=str(project_id), user_id=str(user_id))
                return {
                    "moved": 0,
                    "failed": len(move_actions),
                    "errors": [{"error": "Unauthorized"}],
                }

            # Process each move action
            for action in move_actions:
                try:
                    file_id = UUID(action["file_id"])
                    s3_key_old = action["s3_key_old"]
                    s3_key_new = action["s3_key_new"]
                    new_path = action["new_path"]

                    # Step 1: S3 move (server-side copy + delete)
                    move_success = self.storage.move(s3_key_old, s3_key_new)

                    if not move_success:
                        failed += 1
                        errors.append(
                            {
                                "file_id": str(file_id),
                                "error": f"S3 move failed: {s3_key_old} → {s3_key_new}",
                            }
                        )
                        logger.warning(
                            "S3 move failed", file_id=str(file_id), s3_key_old=s3_key_old, s3_key_new=s3_key_new
                        )
                        continue

                    # Step 2: Update DB record
                    updated_file = self.db_service.move_file(
                        db=db,
                        file_id=file_id,
                        new_relative_path=new_path,
                        new_s3_key=s3_key_new,
                    )

                    if not updated_file:
                        failed += 1
                        errors.append(
                            {
                                "file_id": str(file_id),
                                "error": "DB update failed after S3 move (inconsistent state!)",
                            }
                        )
                        logger.error(
                            "DB update failed after S3 move",
                            file_id=str(file_id),
                            old_path=action.get("old_path"),
                            new_path=new_path,
                        )
                        continue

                    moved += 1
                    logger.debug(
                        "File moved successfully",
                        file_id=str(file_id),
                        old_path=action.get("old_path"),
                        new_path=new_path,
                    )

                except Exception as e:
                    failed += 1
                    errors.append(
                        {
                            "file_id": action.get("file_id", "unknown"),
                            "error": str(e),
                        }
                    )
                    logger.error(
                        "Move action failed",
                        file_id=action.get("file_id"),
                        error=str(e),
                        error_type=type(e).__name__,
                    )

            logger.info(
                "Batch move completed",
                project_id=str(project_id),
                moved=moved,
                failed=failed,
                total=len(move_actions),
            )

            return {"moved": moved, "failed": failed, "errors": errors}

        except Exception as e:
            logger.error(
                "Batch move orchestration failed",
                project_id=str(project_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "moved": 0,
                "failed": len(move_actions),
                "errors": [{"error": f"Batch move failed: {str(e)}"}],
            }

    def get_all_project_files_with_urls(self, db: Session, project_id: UUID, user_id: UUID) -> dict[str, Any] | None:
        """
        Get all files from all folders for complete project download

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User ID (for ownership check)

        Returns:
            Dictionary with project_name and folders (with download URLs) or None if failed
            Structure:
            {
                'project_name': str,
                'folders': [
                    {
                        'folder_name': str,
                        'files': [
                            {
                                'filename': str,
                                'relative_path': str,
                                'download_url': str,
                                'size': int
                            }
                        ]
                    }
                ]
            }
        """
        try:
            # Get project with details from DB
            project = self.db_service.get_project_with_details(db, project_id)

            if not project:
                logger.debug("Project not found", project_id=str(project_id))
                return None

            # Check ownership
            if project.user_id != user_id:
                logger.warning(
                    "Unauthorized complete download access", project_id=str(project_id), user_id=str(user_id)
                )
                return None

            # Build response structure
            folders_data = []

            # Iterate over all folders (including empty ones)
            for folder in project.folders:
                files_data = []

                # Get files for this folder
                for file in folder.files:
                    # Generate backend proxy URL (instead of presigned S3 URL)
                    # CLI will combine with api_url: {api_url}/api/v1/song-projects/{project_id}/files/{file_id}/download
                    download_url = f"/api/v1/song-projects/{project_id}/files/{file.id}/download"

                    files_data.append(
                        {
                            "filename": file.filename,
                            "relative_path": file.relative_path,
                            "download_url": download_url,
                            "size": file.file_size_bytes or 0,
                        }
                    )

                # Add folder to response (even if files list is empty)
                folders_data.append({"folder_name": folder.folder_name, "files": files_data})

            logger.info(
                "Complete download data prepared",
                project_id=str(project_id),
                folders_count=len(folders_data),
                total_files=sum(len(f["files"]) for f in folders_data),
            )

            return {"project_name": project.project_name, "folders": folders_data}

        except Exception as e:
            logger.error(
                "Get all project files failed", project_id=str(project_id), error=str(e), error_type=type(e).__name__
            )
            return None

    def clear_folder_files(
        self,
        db: Session,
        project_id: UUID,
        folder_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any]:
        """
        Clear all files in a folder (MinIO + DB)

        Args:
            db: Database session
            project_id: Project UUID
            folder_id: Folder UUID
            user_id: User ID (from JWT, for ownership check)

        Returns:
            {"deleted": int, "errors": list}
        """
        try:
            # Load project (ownership check via user_id)
            project = self.db_service.get_project_by_id(db, project_id)
            if not project or project.user_id != user_id:
                raise ValueError("Project not found or unauthorized")

            # Check if project is archived
            if project.project_status == "archived":
                raise ValueError("Cannot clear folder in archived project")

            # Load folder
            folder = self.db_service.get_folder_by_id(db, folder_id)
            if not folder or folder.project_id != project.id:
                raise ValueError("Folder not found")

            # Get all files in folder
            files = self.db_service.get_files_by_folder(db, folder_id)

            if not files:
                logger.info("Folder is already empty", folder_id=str(folder_id))
                return {"deleted": 0, "errors": []}

            # Delete from S3 (batch) and DB
            deleted_count = 0
            errors = []

            for file in files:
                try:
                    # Delete from S3
                    if file.s3_key:
                        self.storage.delete(file.s3_key)

                    # Delete from DB
                    self.db_service.delete_file(db, file.id)
                    deleted_count += 1

                except Exception as e:
                    logger.error(
                        "Failed to delete file",
                        file_id=str(file.id),
                        filename=file.filename,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    errors.append({"file_id": str(file.id), "filename": file.filename, "error": str(e)})

            db.commit()

            logger.info(
                "Folder cleared",
                folder_id=str(folder_id),
                folder_name=folder.folder_name,
                deleted=deleted_count,
                errors_count=len(errors),
            )

            return {"deleted": deleted_count, "errors": errors}

        except ValueError as e:
            logger.warning("Clear folder validation failed", error=str(e))
            raise
        except Exception as e:
            logger.error("Clear folder failed", folder_id=str(folder_id), error=str(e), error_type=type(e).__name__)
            raise


# Global orchestrator instance
song_project_orchestrator = SongProjectOrchestrator()
