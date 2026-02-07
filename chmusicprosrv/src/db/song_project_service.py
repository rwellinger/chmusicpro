"""Song Project Service - Database operations for song project management"""

import traceback
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import case, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from db.models import ProjectFile, ProjectFolder, SongProject
from utils.logger import logger


class SongProjectService:
    """Service for song project database operations (CRUD only, NO business logic)"""

    def create_project(
        self,
        db: Session,
        user_id: UUID,
        project_name: str,
        s3_prefix: str | None = None,
        tags: list[str] | None = None,
        description: str | None = None,
        project_status: str = "new",
    ) -> SongProject | None:
        """
        Create a new song project record

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_name: Project name
            s3_prefix: S3 prefix for storage
            tags: List of tags
            description: Project description
            project_status: Project status ('new', 'progress', 'archived')

        Returns:
            SongProject instance if successful, None otherwise
        """
        try:
            project = SongProject(
                user_id=user_id,
                project_name=project_name,
                s3_prefix=s3_prefix,
                tags=tags or [],
                description=description,
                project_status=project_status,
            )

            db.add(project)
            db.commit()
            db.refresh(project)

            logger.info(
                "Song project created",
                project_id=str(project.id),
                project_name=project_name,
                user_id=str(user_id),
                status=project_status,
            )
            return project

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Project creation DB error", error=str(e), error_type=type(e).__name__)
            return None
        except Exception as e:
            logger.error("Project creation failed", error=str(e), error_type=type(e).__name__)
            return None

    def get_project_by_id(self, db: Session, project_id: UUID) -> SongProject | None:
        """
        Get project by ID (without relationships)

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            SongProject instance if found, None otherwise
        """
        try:
            project = db.query(SongProject).filter(SongProject.id == project_id).first()
            if project:
                logger.debug("Project retrieved", project_id=str(project_id))
            else:
                logger.debug("Project not found", project_id=str(project_id))
            return project
        except Exception as e:
            logger.error(
                "Error getting project by ID", project_id=str(project_id), error=str(e), error_type=type(e).__name__
            )
            return None

    def get_project_with_details(self, db: Session, project_id: UUID) -> SongProject | None:
        """
        Get project with all folders and files (eager loading)

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            SongProject instance with folders and files, None if not found
        """
        try:
            project = (
                db.query(SongProject)
                .options(
                    joinedload(SongProject.folders).joinedload(ProjectFolder.files),
                    joinedload(SongProject.files),
                )
                .filter(SongProject.id == project_id)
                .first()
            )
            if project:
                logger.debug(
                    "Project with details retrieved", project_id=str(project_id), folder_count=len(project.folders)
                )
            else:
                logger.debug("Project not found", project_id=str(project_id))
            return project
        except Exception as e:
            logger.error(
                "Error getting project with details",
                project_id=str(project_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def get_projects_paginated(
        self,
        db: Session,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
        tags: str | None = None,
        project_status: str | None = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> dict[str, Any]:
        """
        Get paginated list of projects for a user

        Args:
            db: Database session
            user_id: User ID (from JWT)
            limit: Number of projects to return
            offset: Number of projects to skip
            search: Search term (project_name, description)
            tags: Comma-separated tags for filtering
            project_status: Status filter ('new', 'progress', 'archived', or None for all non-archived)
            sort_by: Field to sort by (created_at, updated_at, project_name)
            sort_direction: Sort direction (asc, desc)

        Returns:
            Dictionary with 'items' (list of projects) and 'total' (count)
        """
        try:
            query = db.query(SongProject).filter(SongProject.user_id == user_id)

            # Apply status filter
            if project_status:
                query = query.filter(SongProject.project_status == project_status)
            else:
                # Default: exclude archived projects (for 'all' tab)
                query = query.filter(SongProject.project_status != "archived")

            # Apply search filter
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        SongProject.project_name.ilike(search_term),
                        SongProject.description.ilike(search_term),
                    )
                )

            # Apply tags filter (if provided)
            if tags:
                tag_list = [tag.strip() for tag in tags.split(",")]
                # PostgreSQL ARRAY overlap operator
                query = query.filter(SongProject.tags.overlap(tag_list))

            # Get total count before pagination
            total_count = query.count()

            # Apply sorting (COALESCE: updated_at if exists, else created_at)
            effective_date = case(
                (SongProject.updated_at.is_(None), SongProject.created_at), else_=SongProject.updated_at
            )

            if sort_by == "project_name":
                if sort_direction == "desc":
                    query = query.order_by(SongProject.project_name.desc())
                else:
                    query = query.order_by(SongProject.project_name.asc())
            elif sort_by == "updated_at":
                if sort_direction == "desc":
                    query = query.order_by(effective_date.desc())
                else:
                    query = query.order_by(effective_date.asc())
            else:  # default to created_at (but use effective_date for consistency)
                if sort_direction == "desc":
                    query = query.order_by(effective_date.desc())
                else:
                    query = query.order_by(effective_date.asc())

            # Apply pagination
            projects = query.limit(limit).offset(offset).all()

            logger.debug(
                "Projects retrieved paginated",
                count=len(projects),
                total=total_count,
                limit=limit,
                offset=offset,
                user_id=str(user_id),
                search=search,
                tags=tags,
                project_status=project_status,
            )

            return {"items": projects, "total": total_count}
        except Exception as e:
            logger.error(
                "Error getting paginated projects",
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return {"items": [], "total": 0}

    def update_project(
        self,
        db: Session,
        project_id: UUID,
        user_id: UUID,
        update_data: dict[str, Any],
    ) -> SongProject | None:
        """
        Update an existing project

        Args:
            db: Database session
            project_id: Project UUID
            user_id: User ID (for ownership check)
            update_data: Dictionary with fields to update

        Returns:
            Updated SongProject instance if successful, None otherwise
        """
        try:
            project = db.query(SongProject).filter(SongProject.id == project_id).first()
            if not project:
                logger.warning("Project not found for update", project_id=str(project_id))
                return None

            # Ownership check
            if project.user_id != user_id:
                logger.warning("Unauthorized project update", project_id=str(project_id), user_id=str(user_id))
                return None

            # Validate project_status if provided
            if "project_status" in update_data:
                from business.song_project_transformer import validate_project_status

                if not validate_project_status(update_data["project_status"]):
                    raise ValueError(f"Invalid project_status: {update_data['project_status']}")

            # Track which fields are being updated
            updated_fields = []

            # Update only provided fields
            for field, value in update_data.items():
                if hasattr(project, field):
                    setattr(project, field, value)
                    updated_fields.append(field)

            # Update timestamp
            project.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(project)

            logger.info("Project updated", project_id=str(project_id), fields_updated=updated_fields)
            return project

        except ValueError as e:
            db.rollback()
            logger.error("Project update validation error", error=str(e), error_type=type(e).__name__)
            return None
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Project update DB error", project_id=str(project_id), error=str(e), error_type=type(e).__name__
            )
            return None
        except Exception as e:
            logger.error(
                "Project update failed",
                project_id=str(project_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return None

    def delete_project(self, db: Session, project_id: UUID) -> bool:
        """
        Delete a project by ID (cascade deletes folders, files)

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            project = db.query(SongProject).filter(SongProject.id == project_id).first()
            if project:
                db.delete(project)
                db.commit()
                logger.info("Project deleted", project_id=str(project_id))
                return True
            logger.warning("Project not found for deletion", project_id=str(project_id))
            return False
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Project deletion DB error", project_id=str(project_id), error=str(e), error_type=type(e).__name__
            )
            return False
        except Exception as e:
            logger.error(
                "Project deletion failed",
                project_id=str(project_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return False

    def create_folder(
        self,
        db: Session,
        project_id: UUID,
        folder_name: str,
        folder_type: str | None = None,
        s3_prefix: str | None = None,
        custom_icon: str | None = None,
    ) -> ProjectFolder | None:
        """
        Create a project folder

        Args:
            db: Database session
            project_id: Parent project UUID
            folder_name: Folder name
            folder_type: Folder type (arrangement, ai, cover, etc.)
            s3_prefix: S3 prefix for this folder
            custom_icon: Custom icon name

        Returns:
            ProjectFolder instance if successful, None otherwise
        """
        try:
            folder = ProjectFolder(
                project_id=project_id,
                folder_name=folder_name,
                folder_type=folder_type,
                s3_prefix=s3_prefix,
                custom_icon=custom_icon,
            )

            db.add(folder)
            db.commit()
            db.refresh(folder)

            logger.info("Folder created", folder_id=str(folder.id), folder_name=folder_name, project_id=str(project_id))
            return folder

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Folder creation DB error", error=str(e), error_type=type(e).__name__)
            return None
        except Exception as e:
            logger.error("Folder creation failed", error=str(e), error_type=type(e).__name__)
            return None

    def create_file(
        self,
        db: Session,
        project_id: UUID,
        folder_id: UUID | None,
        filename: str,
        relative_path: str,
        s3_key: str | None = None,
        file_type: str | None = None,
        mime_type: str | None = None,
        file_size_bytes: int | None = None,
        file_hash: str | None = None,
        storage_backend: str = "s3",
    ) -> ProjectFile | None:
        """
        Create a project file record

        Args:
            db: Database session
            project_id: Parent project UUID
            folder_id: Parent folder UUID (optional)
            filename: File name
            relative_path: Relative path within project
            s3_key: S3 key for storage
            file_type: File type (audio, image, document, etc.)
            mime_type: MIME type
            file_size_bytes: File size in bytes
            file_hash: File hash (SHA256)
            storage_backend: Storage backend (s3, local)

        Returns:
            ProjectFile instance if successful, None otherwise
        """
        try:
            logger.debug(
                "Creating file record",
                filename=filename,
                has_file_hash=file_hash is not None,
                hash_length=len(file_hash) if file_hash else 0,
            )

            file = ProjectFile(
                project_id=project_id,
                folder_id=folder_id,
                filename=filename,
                relative_path=relative_path,
                s3_key=s3_key,
                file_type=file_type,
                mime_type=mime_type,
                file_size_bytes=file_size_bytes,
                file_hash=file_hash,
                storage_backend=storage_backend,
                is_synced=False,
            )

            db.add(file)
            db.commit()
            db.refresh(file)

            logger.info(
                "File created",
                file_id=str(file.id),
                filename=filename,
                project_id=str(project_id),
                hash_in_db=file.file_hash is not None,
            )
            return file

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("File creation DB error", error=str(e), error_type=type(e).__name__)
            return None
        except Exception as e:
            logger.error("File creation failed", error=str(e), error_type=type(e).__name__)
            return None

    def get_files_by_folder(self, db: Session, folder_id: UUID) -> list[ProjectFile]:
        """
        Get all files in a specific folder (for Mirror compare)

        Args:
            db: Database session
            folder_id: Folder UUID

        Returns:
            List of ProjectFile instances
        """
        try:
            files = db.query(ProjectFile).filter(ProjectFile.folder_id == folder_id).all()
            return files or []

        except SQLAlchemyError as e:
            logger.error(
                "Get files by folder DB error", folder_id=str(folder_id), error=str(e), error_type=type(e).__name__
            )
            return []
        except Exception as e:
            logger.error(
                "Get files by folder failed", folder_id=str(folder_id), error=str(e), error_type=type(e).__name__
            )
            return []

    def get_file_by_id(self, db: Session, file_id: UUID) -> ProjectFile | None:
        """
        Get a file by its ID

        Args:
            db: Database session
            file_id: File UUID

        Returns:
            ProjectFile instance if found, None otherwise
        """
        try:
            file = db.query(ProjectFile).filter(ProjectFile.id == file_id).first()
            return file

        except SQLAlchemyError as e:
            logger.error("Get file by ID DB error", file_id=str(file_id), error=str(e), error_type=type(e).__name__)
            return None
        except Exception as e:
            logger.error("Get file by ID failed", file_id=str(file_id), error=str(e), error_type=type(e).__name__)
            return None

    def get_file_by_path(self, db: Session, project_id: UUID, relative_path: str) -> ProjectFile | None:
        """
        Get a file by its relative path (for Mirror update detection)

        Args:
            db: Database session
            project_id: Project UUID
            relative_path: Relative path within project (e.g., "03 Pictures/cover.afphoto")

        Returns:
            ProjectFile instance if found, None otherwise
        """
        try:
            file = (
                db.query(ProjectFile)
                .filter(ProjectFile.project_id == project_id, ProjectFile.relative_path == relative_path)
                .first()
            )
            return file

        except SQLAlchemyError as e:
            logger.error(
                "Get file by path DB error",
                project_id=str(project_id),
                relative_path=relative_path,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None
        except Exception as e:
            logger.error(
                "Get file by path failed",
                project_id=str(project_id),
                relative_path=relative_path,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def update_file(
        self,
        db: Session,
        file_id: UUID,
        s3_key: str | None = None,
        file_size_bytes: int | None = None,
        file_hash: str | None = None,
        mime_type: str | None = None,
    ) -> ProjectFile | None:
        """
        Update file record (for Mirror sync updates)

        Args:
            db: Database session
            file_id: File UUID
            s3_key: New S3 key (optional)
            file_size_bytes: New file size (optional)
            file_hash: New file hash (optional)
            mime_type: New MIME type (optional)

        Returns:
            Updated ProjectFile instance if successful, None otherwise
        """
        try:
            file = db.query(ProjectFile).filter(ProjectFile.id == file_id).first()

            if not file:
                logger.debug("File not found for update", file_id=str(file_id))
                return None

            # Update fields if provided
            if s3_key is not None:
                file.s3_key = s3_key
            if file_size_bytes is not None:
                file.file_size_bytes = file_size_bytes
            if file_hash is not None:
                file.file_hash = file_hash
            if mime_type is not None:
                file.mime_type = mime_type

            # Update timestamp
            file.updated_at = datetime.now(UTC)

            db.commit()
            db.refresh(file)

            logger.info("File updated", file_id=str(file_id), filename=file.filename)
            return file

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("File update DB error", file_id=str(file_id), error=str(e), error_type=type(e).__name__)
            return None
        except Exception as e:
            logger.error("File update failed", file_id=str(file_id), error=str(e), error_type=type(e).__name__)
            return None

    def delete_file(self, db: Session, file_id: UUID) -> bool:
        """
        Delete a file record from database

        Args:
            db: Database session
            file_id: File UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            file = db.query(ProjectFile).filter(ProjectFile.id == file_id).first()

            if not file:
                logger.debug("File not found for deletion", file_id=str(file_id))
                return False

            db.delete(file)
            db.commit()

            logger.info("File deleted", file_id=str(file_id), filename=file.filename)
            return True

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("File deletion DB error", file_id=str(file_id), error=str(e), error_type=type(e).__name__)
            return False
        except Exception as e:
            logger.error("File deletion failed", file_id=str(file_id), error=str(e), error_type=type(e).__name__)
            return False

    def move_file(
        self,
        db: Session,
        file_id: UUID,
        new_relative_path: str,
        new_s3_key: str,
    ) -> ProjectFile | None:
        """
        Move file to new path (update DB record only)

        Args:
            db: Database session
            file_id: File UUID
            new_relative_path: New relative path (e.g., "Audio/file.flac")
            new_s3_key: New S3 key (e.g., "projects/{uuid}/01 Arrangement/Audio/file.flac")

        Returns:
            Updated ProjectFile instance if successful, None otherwise

        Note:
            - S3 move must be done separately by orchestrator
            - This only updates the DB record
            - Preserves file_id (identity)
            - Updates updated_at timestamp
        """
        try:
            file = db.query(ProjectFile).filter(ProjectFile.id == file_id).first()

            if not file:
                logger.debug("File not found for move", file_id=str(file_id))
                return None

            # Extract new filename from relative_path
            new_filename = new_relative_path.split("/")[-1]

            # Update fields
            file.relative_path = new_relative_path
            file.s3_key = new_s3_key
            file.filename = new_filename
            file.updated_at = datetime.now(UTC)

            db.commit()
            db.refresh(file)

            logger.info("File moved in DB", file_id=str(file_id), new_path=new_relative_path)
            return file

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("File move DB error", file_id=str(file_id), error=str(e), error_type=type(e).__name__)
            return None

    def get_folder_by_id(self, db: Session, folder_id: UUID) -> ProjectFolder | None:
        """
        Get a folder by its ID

        Args:
            db: Database session
            folder_id: Folder UUID

        Returns:
            ProjectFolder instance if found, None otherwise
        """
        try:
            folder = db.query(ProjectFolder).filter(ProjectFolder.id == folder_id).first()
            if folder:
                logger.debug("Folder retrieved", folder_id=str(folder_id))
            return folder
        except SQLAlchemyError as e:
            logger.error(
                "Failed to get folder by ID", error=str(e), error_type=type(e).__name__, folder_id=str(folder_id)
            )
            return None

    def get_assigned_songs_for_folder(self, db: Session, project_id: UUID, folder_id: UUID) -> list[Any]:
        """
        Get all assigned songs for a project folder (CRUD only)

        Args:
            db: Database session
            project_id: Project UUID
            folder_id: Folder UUID

        Returns:
            List of Song instances
        """
        try:
            from db.models import Song

            songs = (
                db.query(Song)
                .filter(Song.project_id == project_id, Song.project_folder_id == folder_id)
                .order_by(Song.created_at.desc())
                .all()
            )
            logger.debug(
                "Assigned songs retrieved", project_id=str(project_id), folder_id=str(folder_id), count=len(songs)
            )
            return songs
        except SQLAlchemyError as e:
            logger.error(
                "Failed to get assigned songs",
                error=str(e),
                error_type=type(e).__name__,
                project_id=str(project_id),
                folder_id=str(folder_id),
            )
            return []

    def get_assigned_sketches_for_folder(self, db: Session, project_id: UUID, folder_id: UUID) -> list[Any]:
        """
        Get all assigned sketches for a project folder (CRUD only)

        Args:
            db: Database session
            project_id: Project UUID
            folder_id: Folder UUID

        Returns:
            List of SongSketch instances
        """
        try:
            from db.models import SongSketch

            sketches = (
                db.query(SongSketch)
                .filter(SongSketch.project_id == project_id, SongSketch.project_folder_id == folder_id)
                .order_by(SongSketch.created_at.desc())
                .all()
            )
            logger.debug(
                "Assigned sketches retrieved", project_id=str(project_id), folder_id=str(folder_id), count=len(sketches)
            )
            return sketches
        except SQLAlchemyError as e:
            logger.error(
                "Failed to get assigned sketches",
                error=str(e),
                error_type=type(e).__name__,
                project_id=str(project_id),
                folder_id=str(folder_id),
            )
            return []

    def get_assigned_images_for_folder(self, db: Session, project_id: UUID, folder_id: UUID) -> list[Any]:
        """
        Get all assigned images for a project folder (CRUD only)

        Args:
            db: Database session
            project_id: Project UUID
            folder_id: Folder UUID

        Returns:
            List of GeneratedImage instances
        """
        try:
            from db.models import GeneratedImage, ProjectImageReference

            images = (
                db.query(GeneratedImage)
                .join(ProjectImageReference, ProjectImageReference.image_id == GeneratedImage.id)
                .filter(ProjectImageReference.project_id == project_id, ProjectImageReference.folder_id == folder_id)
                .order_by(GeneratedImage.created_at.desc())
                .all()
            )
            logger.debug(
                "Assigned images retrieved", project_id=str(project_id), folder_id=str(folder_id), count=len(images)
            )
            return images
        except SQLAlchemyError as e:
            logger.error(
                "Failed to get assigned images",
                error=str(e),
                error_type=type(e).__name__,
                project_id=str(project_id),
                folder_id=str(folder_id),
            )
            return []

    def get_all_assigned_songs_for_project(self, db: Session, project_id: UUID) -> list[Any]:
        """
        Get ALL assigned songs for a project (regardless of folder assignment)

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            List of Song instances
        """
        try:
            from db.models import Song

            songs = db.query(Song).filter(Song.project_id == project_id).order_by(Song.created_at.desc()).all()
            logger.debug("All assigned songs retrieved", project_id=str(project_id), count=len(songs))
            return songs
        except SQLAlchemyError as e:
            logger.error(
                "Failed to get all assigned songs",
                error=str(e),
                error_type=type(e).__name__,
                project_id=str(project_id),
            )
            return []

    def get_all_assigned_sketches_for_project(self, db: Session, project_id: UUID) -> list[Any]:
        """
        Get ALL assigned sketches for a project (regardless of folder assignment)

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            List of SongSketch instances
        """
        try:
            from db.models import SongSketch

            sketches = (
                db.query(SongSketch)
                .filter(SongSketch.project_id == project_id)
                .order_by(SongSketch.created_at.desc())
                .all()
            )
            logger.debug("All assigned sketches retrieved", project_id=str(project_id), count=len(sketches))
            return sketches
        except SQLAlchemyError as e:
            logger.error(
                "Failed to get all assigned sketches",
                error=str(e),
                error_type=type(e).__name__,
                project_id=str(project_id),
            )
            return []

    def get_all_assigned_images_for_project(self, db: Session, project_id: UUID) -> list[Any]:
        """
        Get ALL assigned images for a project (regardless of folder assignment)

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            List of GeneratedImage instances
        """
        try:
            from db.models import GeneratedImage, ProjectImageReference

            images = (
                db.query(GeneratedImage)
                .join(ProjectImageReference, ProjectImageReference.image_id == GeneratedImage.id)
                .filter(ProjectImageReference.project_id == project_id)
                .order_by(GeneratedImage.created_at.desc())
                .all()
            )
            logger.debug("All assigned images retrieved", project_id=str(project_id), count=len(images))
            return images
        except SQLAlchemyError as e:
            logger.error(
                "Failed to get all assigned images",
                error=str(e),
                error_type=type(e).__name__,
                project_id=str(project_id),
            )
            return []

    def get_assigned_releases_for_project(self, db: Session, project_id: UUID) -> list[Any]:
        """
        Get all releases assigned to a project

        Args:
            db: Database session
            project_id: Project UUID

        Returns:
            List of SongRelease instances
        """
        try:
            from db.models import ReleaseProjectReference, SongRelease

            releases = (
                db.query(SongRelease)
                .join(ReleaseProjectReference, ReleaseProjectReference.release_id == SongRelease.id)
                .filter(ReleaseProjectReference.project_id == project_id)
                .order_by(SongRelease.name)
                .all()
            )

            logger.debug("Assigned releases retrieved", project_id=str(project_id), count=len(releases))
            return releases

        except SQLAlchemyError as e:
            logger.error(
                "Failed to get assigned releases",
                error=str(e),
                error_type=type(e).__name__,
                project_id=str(project_id),
            )
            return []


# Global service instance
song_project_service = SongProjectService()


# Standalone wrapper functions for orchestrator imports
def get_project_by_id(db: Session, project_id: UUID) -> SongProject | None:
    """Wrapper function for service method"""
    return song_project_service.get_project_by_id(db, project_id)


def get_folder_by_id(db: Session, folder_id: UUID) -> ProjectFolder | None:
    """Wrapper function for service method"""
    return song_project_service.get_folder_by_id(db, folder_id)
