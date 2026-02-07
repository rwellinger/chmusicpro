"""Controller for song release management"""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from business.song_release_orchestrator import song_release_orchestrator
from schemas.song_release_schemas import (
    ReleaseCreateRequest,
    ReleaseFilterRequest,
    ReleaseListResponse,
    ReleaseResponse,
    ReleaseUpdateRequest,
)
from utils.logger import logger


class SongReleaseController:
    """Controller for song release operations (HTTP handling only)"""

    @staticmethod
    def create_release(
        db: Session,
        user_id: UUID,
        release_data: ReleaseCreateRequest,
        cover_file: tuple[bytes, str, int, int] | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Create a new release with project assignments and optional cover upload

        Args:
            db: Database session
            user_id: User ID (from JWT)
            release_data: Release creation data (Pydantic model)
            cover_file: Optional tuple of (file_data, filename, width, height)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Convert project_ids from strings to UUIDs
            project_uuids = [UUID(pid) for pid in release_data.project_ids]

            # Prepare optional fields
            optional_fields = {
                "upload_date": release_data.upload_date,
                "release_date": release_data.release_date,
                "downtaken_date": release_data.downtaken_date,
                "downtaken_reason": release_data.downtaken_reason,
                "rejected_reason": release_data.rejected_reason,
                "upc": release_data.upc,
                "isrc": release_data.isrc,
                "copyright_info": release_data.copyright_info,
                "smart_link": release_data.smart_link,
            }

            result, error_msg = song_release_orchestrator.create_release_with_projects(
                db=db,
                user_id=user_id,
                type=release_data.type,
                name=release_data.name,
                status=release_data.status,
                genre=release_data.genre,
                project_ids=project_uuids,
                description=release_data.description,
                tags=release_data.tags,
                cover_file=cover_file,
                **optional_fields,
            )

            if not result:
                # Return validation errors as 400, other errors as 500
                if error_msg and any(
                    keyword in error_msg.lower() for keyword in ["missing", "required", "invalid", "must be"]
                ):
                    return {"error": error_msg}, 400
                else:
                    return {"error": error_msg or "Failed to create release"}, 500

            response = ReleaseResponse(**result)
            return {"data": response.model_dump(), "message": "Release created successfully"}, 201

        except ValueError as e:
            logger.warning("Invalid UUID in project_ids", error=str(e))
            return {"error": f"Invalid project ID format: {str(e)}"}, 400
        except Exception as e:
            logger.error("Release creation error", error=str(e), error_type=e.__class__.__name__)
            return {"error": f"Failed to create release: {str(e)}"}, 500

    @staticmethod
    def get_releases(db: Session, user_id: UUID, filters: ReleaseFilterRequest) -> tuple[dict[str, Any], int]:
        """
        Get list of releases for user (paginated)

        Args:
            db: Database session
            user_id: User ID (from JWT)
            filters: Filter parameters (Pydantic model)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = song_release_orchestrator.list_releases(
                db=db,
                user_id=user_id,
                limit=filters.limit,
                offset=filters.offset,
                status_filter=filters.status_filter,
                search=filters.search,
            )

            response = ReleaseListResponse(**result)
            return response.model_dump(), 200

        except Exception as e:
            logger.error("Get releases error", error=str(e), error_type=e.__class__.__name__)
            return {"error": f"Failed to retrieve releases: {str(e)}"}, 500

    @staticmethod
    def get_release(db: Session, user_id: UUID, release_id: UUID) -> tuple[dict[str, Any], int]:
        """
        Get release details by ID

        Args:
            db: Database session
            user_id: User ID (from JWT)
            release_id: Release UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = song_release_orchestrator.get_release_with_details(db=db, release_id=release_id, user_id=user_id)

            if not result:
                return {"error": "Release not found"}, 404

            response = ReleaseResponse(**result)
            return {"data": response.model_dump()}, 200

        except Exception as e:
            logger.error("Get release error", error=str(e), release_id=str(release_id), error_type=e.__class__.__name__)
            return {"error": f"Failed to retrieve release: {str(e)}"}, 500

    @staticmethod
    def update_release(
        db: Session,
        user_id: UUID,
        release_id: UUID,
        update_data: ReleaseUpdateRequest,
        cover_file: tuple[bytes, str, int, int] | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Update release with optional cover upload and project reassignment

        Args:
            db: Database session
            user_id: User ID (from JWT)
            release_id: Release UUID
            update_data: Update data (Pydantic model)
            cover_file: Optional tuple of (file_data, filename, width, height)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Convert update_data to dict and remove None values
            update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

            # Convert project_ids from strings to UUIDs if provided
            project_uuids = None
            if "project_ids" in update_dict:
                project_uuids = [UUID(pid) for pid in update_dict.pop("project_ids")]

            result, error_msg = song_release_orchestrator.update_release_with_projects(
                db=db,
                release_id=release_id,
                user_id=user_id,
                update_data=update_dict,
                project_ids=project_uuids,
                cover_file=cover_file,
            )

            if not result:
                # Distinguish between validation errors (400) and not found (404)
                if error_msg and "not found" in error_msg.lower():
                    return {"error": error_msg}, 404
                else:
                    # Validation or other business logic error
                    return {"error": error_msg or "Update failed"}, 400

            response = ReleaseResponse(**result)
            return {"data": response.model_dump(), "message": "Release updated successfully"}, 200

        except ValueError as e:
            logger.warning("Invalid UUID in project_ids", error=str(e))
            return {"error": f"Invalid project ID format: {str(e)}"}, 400
        except Exception as e:
            logger.error(
                "Update release error", error=str(e), release_id=str(release_id), error_type=e.__class__.__name__
            )
            return {"error": f"Failed to update release: {str(e)}"}, 500

    @staticmethod
    def delete_release(db: Session, user_id: UUID, release_id: UUID) -> tuple[dict[str, Any], int]:
        """
        Delete release and cleanup S3 cover

        Args:
            db: Database session
            user_id: User ID (from JWT)
            release_id: Release UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            success = song_release_orchestrator.delete_release_with_cleanup(
                db=db, release_id=release_id, user_id=user_id
            )

            if not success:
                return {"error": "Release not found or deletion failed"}, 404

            return {"message": "Release deleted successfully"}, 200

        except Exception as e:
            logger.error(
                "Delete release error", error=str(e), release_id=str(release_id), error_type=e.__class__.__name__
            )
            return {"error": f"Failed to delete release: {str(e)}"}, 500


# Singleton instance
song_release_controller = SongReleaseController()
