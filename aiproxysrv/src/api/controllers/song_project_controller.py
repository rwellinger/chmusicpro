"""Controller for song project management"""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from business.song_project_orchestrator import song_project_orchestrator
from db.song_project_service import song_project_service
from schemas.common_schemas import PaginationMeta
from schemas.song_project_schemas import (
    BatchDeleteRequest,
    BatchDeleteResponse,
    MirrorRequest,
    MirrorResponse,
    ProjectCompleteDownloadResponse,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from utils.logger import logger


class SongProjectController:
    """Controller for song project operations (HTTP handling only)"""

    @staticmethod
    def create_project(db: Session, user_id: UUID, project_data: ProjectCreateRequest) -> tuple[dict[str, Any], int]:
        """
        Create a new project with default folder structure

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_data: Project creation data (Pydantic model)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = song_project_orchestrator.create_project_with_structure(
                db=db,
                user_id=user_id,
                project_name=project_data.project_name,
                tags=project_data.tags,
                description=project_data.description,
            )

            if not result:
                return {"error": "Failed to create project"}, 500

            response = ProjectResponse(**result)
            return {"data": response.model_dump(), "message": "Project created successfully"}, 201

        except Exception as e:
            logger.error("Project creation error", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to create project: {str(e)}"}, 500

    @staticmethod
    def get_projects(
        db: Session,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
        tags: str | None = None,
        project_status: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Get list of projects for user (paginated)

        Args:
            db: Database session
            user_id: User ID (from JWT)
            limit: Items per page
            offset: Offset for pagination
            search: Search term
            tags: Comma-separated tags
            project_status: Status filter ('new', 'progress', 'archived', or None for all non-archived)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = song_project_orchestrator.list_projects(
                db=db,
                user_id=user_id,
                limit=limit,
                offset=offset,
                search=search,
                tags=tags,
                project_status=project_status,
            )

            projects = result.get("projects", [])
            pagination_data = result.get("pagination", {})

            # Convert to Pydantic models
            project_responses = [ProjectResponse(**p) for p in projects]

            # Create pagination metadata
            pagination = PaginationMeta(
                total=pagination_data.get("total", 0),
                offset=pagination_data.get("offset", 0),
                limit=pagination_data.get("limit", limit),
                has_more=pagination_data.get("has_more", False),
            )

            response = ProjectListResponse(
                data=project_responses,
                pagination=pagination,
            )

            return response.model_dump(), 200

        except Exception as e:
            logger.error("Project list error", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve projects: {str(e)}"}, 500

    @staticmethod
    def get_project_by_id(db: Session, user_id: UUID, project_id: str) -> tuple[dict[str, Any], int]:
        """
        Get a specific project by ID (without details)

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID format
            try:
                project_uuid = UUID(project_id)
            except ValueError:
                return {"error": "Invalid project ID format"}, 400

            result = song_project_orchestrator.get_project_by_id(
                db=db,
                project_id=project_uuid,
                user_id=user_id,
            )

            if not result:
                return {"error": f"Project not found with ID: {project_id}"}, 404

            response = ProjectResponse(**result)
            return {"data": response.model_dump()}, 200

        except Exception as e:
            logger.error("Project get error", project_id=project_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve project: {str(e)}"}, 500

    @staticmethod
    def get_project_with_details(db: Session, user_id: UUID, project_id: str) -> tuple[dict[str, Any], int]:
        """
        Get a specific project with all folders and files

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID format
            try:
                project_uuid = UUID(project_id)
            except ValueError:
                return {"error": "Invalid project ID format"}, 400

            result = song_project_orchestrator.get_project_with_details(
                db=db,
                project_id=project_uuid,
                user_id=user_id,
            )

            if not result:
                return {"error": f"Project not found with ID: {project_id}"}, 404

            response = ProjectDetailResponse(**result)
            return {"data": response.model_dump()}, 200

        except Exception as e:
            logger.error("Project detail error", project_id=project_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve project details: {str(e)}"}, 500

    @staticmethod
    def update_project(
        db: Session,
        user_id: UUID,
        project_id: str,
        update_data: ProjectUpdateRequest,
    ) -> tuple[dict[str, Any], int]:
        """
        Update an existing project

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID
            update_data: Update data (Pydantic model)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID format
            try:
                project_uuid = UUID(project_id)
            except ValueError:
                return {"error": "Invalid project ID format"}, 400

            # Convert Pydantic model to dict (exclude None values)
            update_dict = update_data.model_dump(exclude_none=True)

            if not update_dict:
                return {"error": "No fields to update"}, 400

            result = song_project_orchestrator.update_project(
                db=db,
                project_id=project_uuid,
                user_id=user_id,
                update_data=update_dict,
            )

            if not result:
                return {"error": "Failed to update project"}, 500

            response = ProjectResponse(**result)
            return {"data": response.model_dump(), "message": "Project updated successfully"}, 200

        except Exception as e:
            logger.error("Project update error", project_id=project_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to update project: {str(e)}"}, 500

    @staticmethod
    def delete_project(db: Session, user_id: UUID, project_id: str) -> tuple[dict[str, Any], int]:
        """
        Delete a project (with S3 cleanup)

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID format
            try:
                project_uuid = UUID(project_id)
            except ValueError:
                return {"error": "Invalid project ID format"}, 400

            # Check if project is archived
            project = song_project_orchestrator.get_project_by_id(db=db, project_id=project_uuid, user_id=user_id)
            if project and project.get("project_status") == "archived":
                return {"error": "Cannot delete archived project. Unarchive it first."}, 403

            success = song_project_orchestrator.delete_project_with_cleanup(
                db=db,
                project_id=project_uuid,
                user_id=user_id,
            )

            if not success:
                return {"error": "Failed to delete project"}, 500

            return {"message": "Project deleted successfully"}, 200

        except Exception as e:
            logger.error("Project deletion error", project_id=project_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to delete project: {str(e)}"}, 500

    @staticmethod
    def upload_file(
        db: Session, user_id: UUID, project_id: str, folder_id: str, filename: str, file_data: bytes
    ) -> tuple[dict[str, Any], int]:
        """
        Upload file to project folder

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID
            folder_id: Folder UUID
            filename: File name
            file_data: File bytes

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID formats
            try:
                project_uuid = UUID(project_id)
                folder_uuid = UUID(folder_id)
            except ValueError:
                return {"error": "Invalid ID format"}, 400

            # Get project with details to find folder name
            project_details = song_project_orchestrator.get_project_with_details(
                db=db, project_id=project_uuid, user_id=user_id
            )

            if not project_details:
                return {"error": "Project not found or unauthorized"}, 404

            # Check if project is archived
            if project_details.get("project_status") == "archived":
                return {"error": "Cannot upload to archived project. Unarchive it first."}, 403

            # Find folder by ID (project_details is a dict, not an object)
            folders = project_details.get("folders", [])
            folder = next((f for f in folders if str(f.get("id")) == str(folder_uuid)), None)
            if not folder:
                return {"error": f"Folder not found with ID: {folder_id}"}, 404

            # Upload via orchestrator
            result = song_project_orchestrator.upload_file_to_project(
                db=db,
                project_id=project_uuid,
                user_id=user_id,
                folder_name=folder.get("folder_name"),
                filename=filename,
                file_data=file_data,
            )

            if not result:
                return {"error": "Failed to upload file"}, 500

            return {"data": result, "message": "File uploaded successfully"}, 201

        except Exception as e:
            logger.error("File upload error", project_id=project_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to upload file: {str(e)}"}, 500

    @staticmethod
    def batch_upload_files(
        db: Session, user_id: UUID, project_id: str, folder_id: str, files: list
    ) -> tuple[dict[str, Any], int]:
        """
        Batch upload multiple files to project folder

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID
            folder_id: Folder UUID
            files: List of FileStorage objects from request.files.getlist()

        Returns:
            Tuple of (response_data, status_code)
            response_data: {'data': {'uploaded': int, 'failed': int, 'errors': [...]}, 'message': str}
        """
        try:
            # Validate UUID formats
            try:
                project_uuid = UUID(project_id)
                folder_uuid = UUID(folder_id)
            except ValueError:
                return {"error": "Invalid ID format"}, 400

            # Get project with details to find folder name
            project_details = song_project_orchestrator.get_project_with_details(
                db=db, project_id=project_uuid, user_id=user_id
            )

            if not project_details:
                return {"error": "Project not found or unauthorized"}, 404

            # Find folder by ID
            folders = project_details.get("folders", [])
            folder = next((f for f in folders if str(f.get("id")) == str(folder_uuid)), None)
            if not folder:
                return {"error": f"Folder not found: {folder_id}"}, 404

            # Orchestrator handles batch upload
            result = song_project_orchestrator.batch_upload_files_to_project(
                db=db,
                project_id=project_uuid,
                user_id=user_id,
                folder_name=folder.get("folder_name"),
                files=files,
            )

            return {"data": result, "message": "Batch upload completed"}, 200

        except Exception as e:
            logger.error("Batch upload error", project_id=project_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Batch upload failed: {str(e)}"}, 500

    @staticmethod
    def get_folder_files(db: Session, user_id: UUID, project_id: str, folder_id: str) -> tuple[dict[str, Any], int]:
        """
        Get all files in a folder with download URLs (for CLI download)

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID
            folder_id: Folder UUID

        Returns:
            Tuple of (response_data, status_code)
            response_data: {'data': [{'id': '...', 'filename': '...', 'relative_path': '...', 'download_url': '...', 'file_size_bytes': 123}]}
        """
        try:
            # Validate UUID formats
            try:
                project_uuid = UUID(project_id)
                folder_uuid = UUID(folder_id)
            except ValueError:
                return {"error": "Invalid ID format"}, 400

            # Get project details (checks ownership)
            project_details = song_project_orchestrator.get_project_with_details(
                db=db, project_id=project_uuid, user_id=user_id
            )

            if not project_details:
                return {"error": "Project not found or unauthorized"}, 404

            # Find folder by ID
            folders = project_details.get("folders", [])
            folder = next((f for f in folders if str(f.get("id")) == str(folder_uuid)), None)
            if not folder:
                return {"error": f"Folder not found: {folder_id}"}, 404

            # Get files from folder
            files = folder.get("files", [])

            # Generate backend proxy URLs (instead of presigned S3 URLs)
            file_list = []
            for f in files:
                file_id = f.get("id")
                s3_key = f.get("s3_key")

                # Generate backend proxy URL (CLI will combine with api_url)
                download_url = None
                if s3_key and file_id:
                    download_url = f"/api/v1/song-projects/{project_id}/files/{file_id}/download"

                file_list.append(
                    {
                        "id": file_id,
                        "filename": f.get("filename"),
                        "relative_path": f.get("relative_path"),
                        "download_url": download_url,
                        "file_size_bytes": f.get("file_size_bytes"),
                        "s3_key": s3_key,
                    }
                )

            return {"data": file_list}, 200

        except Exception as e:
            logger.error("Get folder files error", project_id=project_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to get folder files: {str(e)}"}, 500

    @staticmethod
    def mirror_compare(
        db: Session, user_id: UUID, project_id: str, folder_id: str, mirror_data: MirrorRequest
    ) -> tuple[dict[str, Any], int]:
        """
        Compare local files vs remote files (for Mirror sync)

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID string
            folder_id: Folder UUID string
            mirror_data: Mirror request data (local files with hashes)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Convert string UUIDs to UUID objects
            project_uuid = UUID(project_id)
            folder_uuid = UUID(folder_id)

            # Check if project is archived
            project = song_project_orchestrator.get_project_by_id(db=db, project_id=project_uuid, user_id=user_id)
            if project and project.get("project_status") == "archived":
                return {"error": "Cannot mirror to archived project. Unarchive it first."}, 403

            # Convert Pydantic models to dicts
            local_files = [
                {"relative_path": f.relative_path, "file_hash": f.file_hash, "file_size_bytes": f.file_size_bytes}
                for f in mirror_data.files
            ]

            # Call orchestrator
            result = song_project_orchestrator.mirror_compare_files(
                db=db, project_id=project_uuid, user_id=user_id, folder_id=folder_uuid, local_files=local_files
            )

            if not result:
                return {"error": "Mirror compare failed"}, 500

            # Convert to response model
            response = MirrorResponse(**result)
            return {"data": response.model_dump()}, 200

        except ValueError as e:
            logger.error("Mirror compare validation error", error=str(e))
            return {"error": f"Invalid UUID: {str(e)}"}, 400
        except Exception as e:
            logger.error(
                "Mirror compare error",
                project_id=project_id,
                folder_id=folder_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Mirror compare failed: {str(e)}"}, 500

    @staticmethod
    def batch_delete_files(
        db: Session, user_id: UUID, project_id: str, delete_data: BatchDeleteRequest
    ) -> tuple[dict[str, Any], int]:
        """
        Delete multiple files from project (S3 + DB)

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID string
            delete_data: Batch delete request data (file IDs)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Convert string UUID to UUID object
            project_uuid = UUID(project_id)

            # Call orchestrator
            result = song_project_orchestrator.batch_delete_files(
                db=db, project_id=project_uuid, user_id=user_id, file_ids=delete_data.file_ids
            )

            # Convert to response model
            response = BatchDeleteResponse(**result)
            return {"data": response.model_dump()}, 200

        except ValueError as e:
            logger.error("Batch delete validation error", error=str(e))
            return {"error": f"Invalid UUID: {str(e)}"}, 400
        except Exception as e:
            logger.error(
                "Batch delete error",
                project_id=project_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Batch delete failed: {str(e)}"}, 500

    @staticmethod
    def batch_move_files(
        db: Session, user_id: UUID, project_id: str, move_actions: list[dict]
    ) -> tuple[dict[str, Any], int]:
        """
        Move multiple files in S3 and update DB (for Mirror sync)

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID string
            move_actions: List of move action dicts

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Convert string UUID to UUID object
            project_uuid = UUID(project_id)

            # Call orchestrator
            result = song_project_orchestrator.batch_move_files(
                db=db, project_id=project_uuid, user_id=user_id, move_actions=move_actions
            )

            return {"data": result}, 200

        except ValueError as e:
            logger.error("Batch move validation error", error=str(e))
            return {"error": f"Invalid UUID: {str(e)}"}, 400
        except Exception as e:
            logger.error(
                "Batch move controller error",
                project_id=project_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Batch move failed: {str(e)}"}, 500

    @staticmethod
    def fix_mime_types(
        db: Session, user_id: UUID, project_id: str, folder_id: str | None, dry_run: bool
    ) -> tuple[dict[str, Any], int]:
        """
        Fix missing/wrong MIME types for files in project

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID string
            folder_id: Optional folder UUID string (None = all folders)
            dry_run: If True, preview changes without updating

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Import here to avoid circular dependency
            from adapters.s3.s3_proxy_service import S3ProxyService
            from db.models import SongProjectFile

            # Convert string UUID to UUID object
            project_uuid = UUID(project_id)
            folder_uuid = UUID(folder_id) if folder_id else None

            # Verify user owns project
            project = song_project_service.get_project_by_id(db, project_uuid)
            if not project or project.user_id != user_id:
                return {"error": "Project not found or unauthorized"}, 404

            # Query files with missing/wrong MIME types
            query = db.query(SongProjectFile).filter(
                SongProjectFile.project_id == project_uuid,
                (SongProjectFile.mime_type.is_(None) | (SongProjectFile.mime_type == "application/octet-stream")),
            )

            # Filter by folder if specified
            if folder_uuid:
                query = query.filter(SongProjectFile.folder_id == folder_uuid)

            files = query.all()

            # Calculate new MIME types
            updates = []
            for file in files:
                old_mime = file.mime_type
                new_mime = S3ProxyService._get_content_type(file.filename)

                # Only update if different
                if new_mime != old_mime:
                    updates.append(
                        {
                            "file_id": str(file.id),
                            "filename": file.filename,
                            "old_mime": old_mime,
                            "new_mime": new_mime,
                        }
                    )

                    # Update DB (unless dry-run)
                    if not dry_run:
                        file.mime_type = new_mime

            # Commit changes (unless dry-run)
            if not dry_run and updates:
                db.commit()

            logger.info(
                "MIME types fix completed",
                project_id=str(project_uuid),
                folder_id=str(folder_uuid) if folder_uuid else None,
                scanned=len(files),
                updated=len(updates),
                dry_run=dry_run,
            )

            return {
                "data": {
                    "scanned": len(files),
                    "updated": len(updates),
                    "unchanged": len(files) - len(updates),
                    "files": updates,
                }
            }, 200

        except ValueError as e:
            logger.error("Fix MIME types validation error", error=str(e))
            return {"error": f"Invalid UUID: {str(e)}"}, 400
        except Exception as e:
            logger.error(
                "Fix MIME types error",
                project_id=project_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to fix MIME types: {str(e)}"}, 500

    @staticmethod
    def get_all_project_files_with_urls(db: Session, user_id: UUID, project_id: str) -> tuple[dict[str, Any], int]:
        """
        Get all files from all folders for complete project download

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID string

        Returns:
            Tuple of (response_data, status_code)
            response_data: {'data': {'project_name': str, 'folders': [...]}}
        """
        try:
            # Validate UUID format
            try:
                project_uuid = UUID(project_id)
            except ValueError:
                return {"error": "Invalid project ID format"}, 400

            # Call orchestrator
            result = song_project_orchestrator.get_all_project_files_with_urls(
                db=db, project_id=project_uuid, user_id=user_id
            )

            if not result:
                return {"error": f"Project not found or unauthorized: {project_id}"}, 404

            # Convert to response model
            response = ProjectCompleteDownloadResponse(**result)
            return {"data": response.model_dump()}, 200

        except Exception as e:
            logger.error(
                "Get all project files error", project_id=project_id, error=str(e), error_type=type(e).__name__
            )
            return {"error": f"Failed to get all project files: {str(e)}"}, 500

    @staticmethod
    def clear_folder_files(
        db: Session,
        user_id: UUID,
        project_id: str,
        folder_id: str,
    ) -> tuple[dict[str, Any], int]:
        """
        Clear all files in a folder

        Args:
            db: Database session
            user_id: User ID (from JWT)
            project_id: Project UUID
            folder_id: Folder UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID formats
            try:
                project_uuid = UUID(project_id)
                folder_uuid = UUID(folder_id)
            except ValueError:
                return {"error": "Invalid project or folder ID format"}, 400

            # Call orchestrator
            result = song_project_orchestrator.clear_folder_files(
                db=db,
                project_id=project_uuid,
                folder_id=folder_uuid,
                user_id=user_id,
            )

            return {"data": result, "message": f"{result['deleted']} files deleted successfully"}, 200

        except ValueError as e:
            # Validation errors (archived project, not found, etc.)
            logger.warning("Clear folder validation error", error=str(e))
            return {"error": str(e)}, 403
        except Exception as e:
            logger.error(
                "Clear folder error",
                project_id=project_id,
                folder_id=folder_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to clear folder: {str(e)}"}, 500


# Global controller instance
song_project_controller = SongProjectController()
