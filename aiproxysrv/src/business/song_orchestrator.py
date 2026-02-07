"""Song Orchestrator - Coordinates song operations (no testable business logic)"""

from typing import Any

import requests

from business.bulk_delete_transformer import BulkDeleteTransformer, DeleteResult
from business.song_transformer import SongTransformer, generate_s3_song_key
from business.song_validator import SongValidator
from config.settings import S3_SONGS_BUCKET
from db.song_service import get_choice_by_id_with_song, song_service, update_choice_s3_key
from infrastructure.storage import get_storage
from utils.logger import logger


class SongOrchestratorError(Exception):
    """Base exception for song orchestration errors"""

    pass


class SongS3MigrationError(SongOrchestratorError):
    """Exception raised when S3 migration fails"""

    pass


class SongOrchestrator:
    """Orchestrates song operations (calls transformers + repository)"""

    def __init__(self):
        """Initialize orchestrator with S3 storage"""
        self._s3_storage = None  # Lazy init to allow server startup when MinIO is down

    @property
    def s3_storage(self):
        """Lazy-load S3 storage (only when first accessed)"""
        if self._s3_storage is None:
            self._s3_storage = get_storage(bucket=S3_SONGS_BUCKET)
        return self._s3_storage

    def get_songs_with_pagination(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str = None,
        search: str = "",
        sort_by: str = "created_at",
        sort_direction: str = "desc",
        workflow: str = None,
    ) -> dict[str, Any]:
        """
        Get paginated list of songs with search and filtering

        Args:
            limit: Number of songs to return
            offset: Number of songs to skip
            status: Optional status filter
            search: Search term for filtering
            sort_by: Field to sort by
            sort_direction: Sort direction
            workflow: Optional workflow filter

        Returns:
            Dict containing songs and pagination info
        """
        try:
            songs = song_service.get_songs_paginated(
                limit=limit,
                offset=offset,
                status=status,
                search=search,
                sort_by=sort_by,
                sort_direction=sort_direction,
                workflow=workflow,
            )
            total_count = song_service.get_total_songs_count(status=status, search=search, workflow=workflow)

            # Transform to API response format
            songs_list = [SongTransformer.transform_song_to_list_format(song) for song in songs]

            return {
                "songs": songs_list,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count,
                },
            }

        except Exception as e:
            logger.error(f"Error retrieving songs: {e}")
            raise SongOrchestratorError(f"Failed to retrieve songs: {e}") from e

    def get_song_details(self, song_id: str) -> dict[str, Any] | None:
        """
        Get detailed information for a single song with all choices

        Args:
            song_id: ID of the song

        Returns:
            Dict containing song details with choices or None if not found
        """
        try:
            song = song_service.get_song_by_id(song_id)
            if not song:
                return None

            return SongTransformer.transform_song_to_detail_format(song)

        except Exception as e:
            logger.error(f"Error retrieving song {song_id}: {e}")
            raise SongOrchestratorError(f"Failed to retrieve song: {e}") from e

    def delete_single_song(self, song_id: str) -> bool:
        """
        Delete a single song including all choices

        Args:
            song_id: ID of the song to delete

        Returns:
            True if successful, False if song not found
        """
        try:
            song = song_service.get_song_by_id(song_id)
            if not song:
                return False

            success = song_service.delete_song_by_id(song_id)
            if success:
                logger.info(f"Song {song_id} and its choices deleted successfully")
                return True
            else:
                raise SongOrchestratorError("Failed to delete song")

        except Exception as e:
            logger.error(f"Error deleting song {song_id}: {type(e).__name__}: {e}")
            raise SongOrchestratorError(f"Failed to delete song: {e}") from e

    def bulk_delete_songs(self, song_ids: list[str]) -> dict[str, Any]:
        """
        Delete multiple songs with detailed results

        Args:
            song_ids: List of song IDs to delete

        Returns:
            Dict containing deletion results and summary
        """
        # Business logic: Validate bulk delete request (delegated to validator)
        from business.song_validator import SongValidationError

        try:
            SongValidator.validate_bulk_delete_count(song_ids)
        except SongValidationError as e:
            raise SongOrchestratorError(str(e)) from e

        # Orchestration: Process each delete operation
        delete_results = []
        for song_id in song_ids:
            try:
                song = song_service.get_song_by_id(song_id)
                if not song:
                    delete_results.append(DeleteResult(song_id, "not_found"))
                    continue

                success = song_service.delete_song_by_id(song_id)
                if success:
                    delete_results.append(DeleteResult(song_id, "deleted"))
                    logger.info(f"Song {song_id} and its choices deleted successfully")
                else:
                    delete_results.append(DeleteResult(song_id, "error", "Failed to delete song"))

            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}"
                delete_results.append(DeleteResult(song_id, "error", error_msg))
                logger.error(f"Error deleting song {song_id}: {error_msg}")

        # Business logic: Aggregate results (delegated to transformer)
        aggregated_results = BulkDeleteTransformer.aggregate_results(delete_results)
        response = BulkDeleteTransformer.format_bulk_delete_response(aggregated_results, len(song_ids))

        logger.info(f"Bulk delete completed: {response['summary']}")
        return response

    def update_choice_rating(self, choice_id: str, rating: int | None) -> dict[str, Any] | None:
        """
        Update rating for a song choice

        Args:
            choice_id: ID of the choice
            rating: Rating value (0, 1, or None)

        Returns:
            Updated choice data or None if not found
        """
        try:
            # Business logic: Validate rating value (delegated to validator)
            from business.song_validator import SongValidationError

            try:
                SongValidator.validate_rating(rating)
            except SongValidationError as e:
                raise SongOrchestratorError(str(e)) from e

            # Check if choice exists
            choice = song_service.get_choice_by_id(choice_id)
            if not choice:
                return None

            # Update rating
            success = song_service.update_choice_rating(choice_id, rating)
            if not success:
                raise SongOrchestratorError("Failed to update choice rating")

            logger.info(f"Choice {choice_id} rating updated to {rating}")
            return {"id": choice_id, "rating": rating, "message": "Rating updated successfully"}

        except Exception as e:
            logger.error(f"Error updating choice rating {choice_id}: {e}")
            raise SongOrchestratorError(f"Failed to update choice rating: {e}") from e

    def update_song(self, song_id: str, update_data: dict) -> dict | None:
        """
        Update song metadata (includes project_id and project_folder_id)

        Args:
            song_id: Song UUID
            update_data: Dict with fields to update

        Returns:
            dict: Updated song data or None if not found
        """
        from uuid import UUID

        from db.database import get_db
        from db.song_project_service import get_folder_by_id, get_project_by_id

        db = next(get_db())

        try:
            # Validate song exists
            song = song_service.get_song_by_id(song_id)
            if not song:
                return None

            # Validate project/folder if provided
            if "project_id" in update_data and update_data["project_id"]:
                project = get_project_by_id(db, UUID(update_data["project_id"]))
                if not project:
                    raise ValueError(f"Project not found: {update_data['project_id']}")

            if "project_folder_id" in update_data and update_data["project_folder_id"]:
                folder = get_folder_by_id(db, UUID(update_data["project_folder_id"]))
                if not folder:
                    raise ValueError(f"Folder not found: {update_data['project_folder_id']}")

            # Business logic: Convert tags from array to comma-separated string for DB storage
            if "tags" in update_data and isinstance(update_data["tags"], list):
                update_data["tags"] = ", ".join(update_data["tags"])

            # Update song (using service instance, NOT wrapper function)
            updated_song = song_service.update_song(song_id, update_data)

            if not updated_song:
                return None

            logger.info("Song updated", song_id=song_id, updated_fields=list(update_data.keys()))

            return {
                "id": str(updated_song.id),
                "title": updated_song.title,
                "project_id": str(updated_song.project_id) if updated_song.project_id else None,
                "project_folder_id": str(updated_song.project_folder_id) if updated_song.project_folder_id else None,
            }

        finally:
            db.close()

    def assign_song_to_project(
        self,
        song_id: str,
        project_id: str,
        folder_id: str | None = None,
    ) -> dict:
        """
        Assign a song to a project (1:1 relationship)

        Args:
            song_id: Song UUID
            project_id: Project UUID
            folder_id: Optional folder UUID

        Returns:
            dict: Assignment result

        Raises:
            ValueError: If song or project not found
        """
        update_data = {
            "project_id": project_id,
            "project_folder_id": folder_id,
        }

        result = self.update_song(song_id, update_data)

        if not result:
            raise ValueError(f"Song not found: {song_id}")

        logger.info(
            "Song assigned to project",
            song_id=song_id,
            project_id=project_id,
            folder_id=folder_id,
        )

        return result

    def unassign_song_from_project(self, song_id: str) -> dict:
        """
        Remove song from its assigned project (link only, song remains)

        Args:
            song_id: Song UUID

        Returns:
            dict: Unassignment result

        Raises:
            ValueError: If song not found
        """
        update_data = {
            "project_id": None,
            "project_folder_id": None,
        }

        result = self.update_song(song_id, update_data)

        if not result:
            raise ValueError(f"Song not found: {song_id}")

        logger.info("Song unassigned from project", song_id=song_id)

        return result

    def migrate_choice_to_s3(self, db, choice_id: str, file_type: str) -> str:
        """
        Lazy migration: Download file from Mureka URL to S3 if not already migrated

        This is the core lazy migration logic - checks if s3_key exists,
        if not downloads from mureka_url and uploads to S3.

        Args:
            db: Database session
            choice_id: UUID of the song choice
            file_type: File type to migrate ('mp3', 'flac', 'stems')

        Returns:
            S3 key of the migrated file

        Raises:
            SongS3MigrationError: If migration fails (choice not found, no URL, download fails, etc.)
        """
        # 1. Load choice with song relationship from DB
        choice = get_choice_by_id_with_song(db, choice_id)
        if not choice:
            raise SongS3MigrationError(f"Choice not found: {choice_id}")

        # 2. Check if already migrated to S3
        existing_s3_key = self._get_existing_s3_key(choice, file_type)
        if existing_s3_key:
            logger.debug(
                "Choice already migrated to S3",
                choice_id=choice_id,
                file_type=file_type,
                s3_key=existing_s3_key[:50] + "...",
            )
            return existing_s3_key

        # 3. Get Mureka URL for download
        mureka_url = self._get_mureka_url(choice, file_type)
        if not mureka_url:
            raise SongS3MigrationError(f"No Mureka URL found for choice {choice_id}, file_type={file_type}")

        # 4. Download file from Mureka CDN
        logger.info("Downloading from Mureka", choice_id=choice_id, file_type=file_type, url_preview=mureka_url[:80])
        try:
            file_data = self._download_from_url(mureka_url)
        except Exception as e:
            raise SongS3MigrationError(f"Failed to download from Mureka: {str(e)}") from e

        # 5. Generate S3 key (readable format with title + song_id)
        song_title = choice.song.title if choice.song else None
        song_id = str(choice.song.id) if choice.song else str(choice.song_id)
        choice_index = choice.choice_index if choice.choice_index is not None else 0

        s3_key = generate_s3_song_key(song_id, song_title, choice_index, file_type)

        # 6. Upload to S3
        logger.info("Uploading to S3", choice_id=choice_id, file_type=file_type, s3_key=s3_key)
        try:
            content_type = self._get_content_type(file_type)
            self.s3_storage.upload(file_data, s3_key, content_type=content_type)
        except Exception as e:
            raise SongS3MigrationError(f"Failed to upload to S3: {str(e)}") from e

        # 7. Update DB with new s3_key
        success = update_choice_s3_key(db, choice_id, file_type, s3_key)
        if not success:
            logger.warning("Failed to update DB with s3_key, but file uploaded", choice_id=choice_id, s3_key=s3_key)

        logger.info(
            "Choice migrated to S3 successfully",
            choice_id=choice_id,
            file_type=file_type,
            s3_key=s3_key,
            file_size=len(file_data),
        )
        return s3_key

    def _get_existing_s3_key(self, choice, file_type: str) -> str | None:
        """Get existing S3 key if already migrated"""
        s3_key_map = {
            "mp3": choice.mp3_s3_key,
            "flac": choice.flac_s3_key,
            "wav": choice.wav_s3_key,
            "stems": choice.stem_s3_key,
        }
        return s3_key_map.get(file_type)

    def _get_mureka_url(self, choice, file_type: str) -> str | None:
        """Get Mureka URL for download"""
        url_map = {
            "mp3": choice.mp3_url,
            "flac": choice.flac_url,
            "wav": choice.wav_url,
            "stems": choice.stem_url,
        }
        return url_map.get(file_type)

    def _download_from_url(self, url: str, timeout: int = 300) -> bytes:
        """
        Download file from URL (Mureka CDN)

        Args:
            url: URL to download from
            timeout: Request timeout in seconds (default 300s = 5min for large files)

        Returns:
            File content as bytes

        Raises:
            requests.RequestException: If download fails
        """
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)
        return response.content

    def _get_content_type(self, file_type: str) -> str:
        """Get MIME type for file type"""
        content_types = {
            "mp3": "audio/mpeg",
            "flac": "audio/flac",
            "wav": "audio/wav",
            "stems": "application/zip",
        }
        return content_types.get(file_type, "application/octet-stream")


# Global instance for use in routes
song_orchestrator = SongOrchestrator()
