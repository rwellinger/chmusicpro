"""Song Release Orchestrator - Coordinates services for song release operations

IMPORTANT: This orchestrator coordinates services but contains NO business logic.
Business logic is in song_release_transformer.py (100% testable).
This orchestrator is NOT unit-tested (orchestration only).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from config.settings import S3_SONG_RELEASES_BUCKET
from infrastructure.storage import get_storage


if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from business.song_release_transformer import (
    generate_s3_cover_key,
    transform_release_to_list_response,
    transform_release_to_response,
    validate_cover_dimensions,
    validate_required_fields_for_status,
)
from db.song_release_service import song_release_service
from utils.logger import logger


class SongReleaseOrchestrator:
    """Orchestrator for song release operations (coordinates services, NO business logic)"""

    def __init__(self):
        """Initialize orchestrator with services"""
        self.db_service = song_release_service
        self._storage = None  # Lazy init to allow server startup when MinIO is down

    @property
    def storage(self):
        """Lazy-load S3 storage (only when first accessed)"""
        if self._storage is None:
            self._storage = get_storage(bucket=S3_SONG_RELEASES_BUCKET)
        return self._storage

    def create_release_with_projects(
        self,
        db: Session,
        user_id: UUID,
        type: str,
        name: str,
        status: str,
        genre: str,
        project_ids: list[UUID],
        description: str | None = None,
        tags: str | None = None,
        cover_file: tuple[bytes, str, int, int] | None = None,  # (data, filename, width, height)
        **optional_fields,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """
        Create release with project assignments and optional cover upload

        Args:
            db: Database session
            user_id: User ID (from JWT)
            type: Release type ('single', 'album')
            name: Release name
            status: Release status
            genre: Music genre
            project_ids: List of project UUIDs to assign
            description: Optional description
            tags: Optional comma-separated tags
            cover_file: Optional tuple of (file_data, filename, width, height)
            **optional_fields: Additional optional fields

        Returns:
            Tuple of (release_data_dict, error_message)
            - (dict, None) if successful
            - (None, "error message") if failed
        """
        try:
            # 1. Validate cover dimensions if provided (business logic in transformer)
            cover_s3_key = None
            if cover_file:
                file_data, filename, width, height = cover_file
                is_valid, error_msg = validate_cover_dimensions(width, height)
                if not is_valid:
                    logger.warning("Cover validation failed", error=error_msg)
                    return None, error_msg

                # Generate S3 key (business logic in transformer)
                # Note: We create a temporary release_id for S3 key generation
                # The actual release will be created below
                temp_release_id = "temp"
                cover_s3_key = generate_s3_cover_key(str(user_id), temp_release_id, filename)

            # 2. Prepare release data
            release_data = {
                "type": type,
                "name": name,
                "status": status,
                "genre": genre,
                "description": description,
                "tags": tags,
                "cover_s3_key": cover_s3_key,
                **optional_fields,
            }

            # 3. Validate required fields for status (business logic in transformer)
            is_valid, error_msg = validate_required_fields_for_status(status, release_data)
            if not is_valid:
                logger.warning("Validation failed", error=error_msg, status=status)
                return None, error_msg

            # 4. Create release in DB (CRUD in db_service)
            release = self.db_service.create_release(db=db, user_id=user_id, **release_data)

            if not release:
                logger.error("Failed to create release in DB")
                return None, "Database creation failed"

            # 5. Update S3 key with real release ID and upload cover if provided
            if cover_file:
                file_data, filename, _, _ = cover_file
                # Regenerate S3 key with real release ID
                cover_s3_key = generate_s3_cover_key(str(user_id), str(release.id), filename)

                # Determine content type from filename
                extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
                content_type = "image/jpeg" if extension in ["jpg", "jpeg"] else f"image/{extension}"

                # Upload to S3 (infrastructure)
                try:
                    self.storage.upload(file_data, cover_s3_key, content_type=content_type)
                except Exception as e:
                    logger.error("Failed to upload cover to S3", release_id=str(release.id), error=str(e))
                    # Rollback DB creation
                    self.db_service.delete_release(db, release.id, user_id)
                    return None, f"Failed to upload cover: {str(e)}"

                # Update release with final S3 key
                update_success = self.db_service.update_release(db, release.id, user_id, {"cover_s3_key": cover_s3_key})
                if not update_success:
                    logger.error("Failed to update release with cover S3 key")
                    # Cleanup S3
                    self.storage.delete(cover_s3_key)
                    self.db_service.delete_release(db, release.id, user_id)
                    return None, "Failed to update cover reference in database"

                release.cover_s3_key = cover_s3_key

            # 6. Assign projects (CRUD in db_service)
            if project_ids:
                assign_success = self.db_service.assign_projects(db, release.id, project_ids)
                if not assign_success:
                    logger.error("Failed to assign projects to release")
                    # Cleanup
                    if cover_s3_key:
                        self.storage.delete(cover_s3_key)
                    self.db_service.delete_release(db, release.id, user_id)
                    return None, "Failed to assign projects"

            # 7. Get assigned projects for response
            projects = self.db_service.get_assigned_projects(db, release.id)

            # 8. Transform to response (business logic in transformer)
            response = transform_release_to_response(release, projects)

            # 9. Replace S3 placeholder with backend proxy path
            # CRITICAL: NEVER return presigned URLs - use backend proxy route!
            if release.cover_s3_key:
                response["cover_url"] = f"/api/v1/song-releases/{release.id}/cover"

            logger.info("Release created with projects", release_id=str(release.id), project_count=len(project_ids))
            return response, None

        except Exception as e:
            logger.error("Create release orchestration failed", error=str(e), error_type=e.__class__.__name__)
            return None, f"Creation failed: {str(e)}"

    def get_release_with_details(self, db: Session, release_id: UUID, user_id: UUID) -> dict[str, Any] | None:
        """
        Get release with all details and presigned cover URL

        Args:
            db: Database session
            release_id: Release UUID
            user_id: User ID (from JWT)

        Returns:
            Release data dictionary or None if not found
        """
        try:
            # 1. Get release from DB (CRUD in db_service)
            release = self.db_service.get_release_by_id(db, release_id, user_id)
            if not release:
                logger.debug("Release not found", release_id=str(release_id))
                return None

            # 2. Get assigned projects (CRUD in db_service)
            projects = self.db_service.get_assigned_projects(db, release_id)

            # 3. Transform to response (business logic in transformer)
            response = transform_release_to_response(release, projects)

            # 4. Replace S3 placeholder with backend proxy path
            # CRITICAL: NEVER return presigned URLs - use backend proxy route!
            if release.cover_s3_key:
                response["cover_url"] = f"/api/v1/song-releases/{release_id}/cover"

            return response

        except Exception as e:
            logger.error("Get release orchestration failed", error=str(e), release_id=str(release_id))
            return None

    def list_releases(
        self,
        db: Session,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        status_filter: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """
        List releases with pagination and filters

        Args:
            db: Database session
            user_id: User ID (from JWT)
            limit: Max results per page
            offset: Skip first N results
            status_filter: Filter by status group
            search: Search in name/genre

        Returns:
            Dictionary with releases list and metadata
        """
        try:
            # 1. Get releases from DB (CRUD in db_service)
            releases, total = self.db_service.get_releases_paginated(
                db, user_id, limit=limit, offset=offset, status_filter=status_filter, search=search
            )

            # 2. Transform to list responses (business logic in transformer)
            items = [transform_release_to_list_response(release) for release in releases]

            # 3. Add backend proxy paths for covers
            # CRITICAL: NEVER return presigned URLs - use backend proxy route!
            for i, release in enumerate(releases):
                if release.cover_s3_key:
                    items[i]["cover_url"] = f"/api/v1/song-releases/{release.id}/cover"

            return {"items": items, "total": total, "limit": limit, "offset": offset}

        except Exception as e:
            logger.error("List releases orchestration failed", error=str(e), user_id=str(user_id))
            return {"items": [], "total": 0, "limit": limit, "offset": offset}

    def update_release_with_projects(
        self,
        db: Session,
        release_id: UUID,
        user_id: UUID,
        update_data: dict[str, Any],
        project_ids: list[UUID] | None = None,
        cover_file: tuple[bytes, str, int, int] | None = None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """
        Update release with optional cover upload and project reassignment

        Args:
            db: Database session
            release_id: Release UUID
            user_id: User ID (from JWT)
            update_data: Dictionary of fields to update
            project_ids: Optional list of project UUIDs (replaces existing)
            cover_file: Optional tuple of (file_data, filename, width, height)

        Returns:
            Tuple of (release_data_dict, error_message)
            - (dict, None) if successful
            - (None, "error message") if failed
        """
        try:
            # 1. Get existing release
            release = self.db_service.get_release_by_id(db, release_id, user_id)
            if not release:
                logger.warning("Release not found for update", release_id=str(release_id))
                return None, "Release not found"

            old_cover_s3_key = release.cover_s3_key

            # 2. Handle cover upload if provided
            if cover_file:
                file_data, filename, width, height = cover_file

                # Validate dimensions (business logic in transformer)
                is_valid, error_msg = validate_cover_dimensions(width, height)
                if not is_valid:
                    logger.warning("Cover validation failed", error=error_msg)
                    return None, error_msg

                # Generate S3 key (business logic in transformer)
                new_cover_s3_key = generate_s3_cover_key(str(user_id), str(release_id), filename)

                # Determine content type from filename
                extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
                content_type = "image/jpeg" if extension in ["jpg", "jpeg"] else f"image/{extension}"

                # Upload to S3 (infrastructure)
                try:
                    self.storage.upload(file_data, new_cover_s3_key, content_type=content_type)
                except Exception as e:
                    logger.error("Failed to upload new cover to S3", error=str(e))
                    return None, f"Failed to upload cover: {str(e)}"

                update_data["cover_s3_key"] = new_cover_s3_key

            # 3. Validate required fields if status changed (business logic in transformer)
            new_status = update_data.get("status", release.status)

            # Build merged data from actual release attributes (NOT transformed response)
            # This ensures cover_s3_key (not cover_url) is available for validation
            merged_data = {
                "type": release.type,
                "name": release.name,
                "status": release.status,
                "genre": release.genre,
                "description": release.description,
                "tags": release.tags,
                "upload_date": release.upload_date,
                "release_date": release.release_date,
                "downtaken_date": release.downtaken_date,
                "downtaken_reason": release.downtaken_reason,
                "rejected_reason": release.rejected_reason,
                "upc": release.upc,
                "isrc": release.isrc,
                "copyright_info": release.copyright_info,
                "smart_link": release.smart_link,
                "cover_s3_key": release.cover_s3_key,
                **update_data,  # Override with update data
            }

            is_valid, error_msg = validate_required_fields_for_status(new_status, merged_data)
            if not is_valid:
                logger.warning(
                    "Update validation failed",
                    error=error_msg,
                    status=new_status,
                    release_id=str(release_id),
                    merged_keys=list(merged_data.keys()),
                )
                # Cleanup uploaded cover if any
                if cover_file and "cover_s3_key" in update_data:
                    self.storage.delete(update_data["cover_s3_key"])
                return None, error_msg

            # 4. Update release in DB (CRUD in db_service)
            updated_release = self.db_service.update_release(db, release_id, user_id, update_data)
            if not updated_release:
                logger.error("Failed to update release in DB")
                # Cleanup uploaded cover if any
                if cover_file and "cover_s3_key" in update_data:
                    self.storage.delete(update_data["cover_s3_key"])
                return None, "Database update failed"

            # 5. Delete old cover from S3 if replaced
            if cover_file and old_cover_s3_key and old_cover_s3_key != update_data.get("cover_s3_key"):
                self.storage.delete(old_cover_s3_key)

            # 6. Update project assignments if provided (CRUD in db_service)
            if project_ids is not None:
                assign_success = self.db_service.assign_projects(db, release_id, project_ids)
                if not assign_success:
                    logger.error("Failed to update project assignments")

            # 7. Get updated details
            result = self.get_release_with_details(db, release_id, user_id)
            return result, None

        except Exception as e:
            logger.error("Update release orchestration failed", error=str(e), release_id=str(release_id))
            return None, f"Update failed: {str(e)}"

    def delete_release_with_cleanup(self, db: Session, release_id: UUID, user_id: UUID) -> bool:
        """
        Delete release and cleanup S3 cover

        Args:
            db: Database session
            release_id: Release UUID
            user_id: User ID (from JWT)

        Returns:
            True if successful, False otherwise
        """
        try:
            # 1. Get release to find cover S3 key
            release = self.db_service.get_release_by_id(db, release_id, user_id)
            if not release:
                logger.warning("Release not found for deletion", release_id=str(release_id))
                return False

            # 2. Delete from DB (cascade deletes project references) (CRUD in db_service)
            delete_success = self.db_service.delete_release(db, release_id, user_id)
            if not delete_success:
                logger.error("Failed to delete release from DB")
                return False

            # 3. Delete cover from S3 if exists (infrastructure)
            if release.cover_s3_key:
                self.storage.delete(release.cover_s3_key)
                logger.debug("Cover deleted from S3", s3_key=release.cover_s3_key)

            logger.info("Release deleted with cleanup", release_id=str(release_id))
            return True

        except Exception as e:
            logger.error("Delete release orchestration failed", error=str(e), release_id=str(release_id))
            return False


# Singleton instance
song_release_orchestrator = SongReleaseOrchestrator()
