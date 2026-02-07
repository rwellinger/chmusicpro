"""Song Controller - Handles song read/update/delete operations"""

from typing import Any

from business.song_orchestrator import SongOrchestrator, SongOrchestratorError
from utils.logger import logger


class SongController:
    """Controller for song read/update/delete operations"""

    def __init__(self):
        self.orchestrator = SongOrchestrator()

    def get_songs(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str = None,
        search: str = "",
        sort_by: str = "created_at",
        sort_direction: str = "desc",
        workflow: str = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Get list of songs with pagination, search and sorting

        Args:
            limit: Number of songs to return (default 20)
            offset: Number of songs to skip (default 0)
            status: Optional status filter (SUCCESS, PENDING, FAILURE, etc.)
            search: Search term to filter by title, lyrics, or tags
            sort_by: Field to sort by (created_at, title, lyrics)
            sort_direction: Sort direction (asc, desc)
            workflow: Optional workflow filter (onWork, inUse, notUsed)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.orchestrator.get_songs_with_pagination(
                limit=limit,
                offset=offset,
                status=status,
                search=search,
                sort_by=sort_by,
                sort_direction=sort_direction,
                workflow=workflow,
            )
            return result, 200

        except SongOrchestratorError as e:
            logger.error(f"Failed to retrieve songs: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error retrieving songs: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def get_song_by_id(self, song_id: str) -> tuple[dict[str, Any], int]:
        """
        Get single song by ID with all choices

        Args:
            song_id: UUID of the song

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.orchestrator.get_song_details(song_id)

            if result is None:
                return {"error": "Song not found"}, 404

            return result, 200

        except SongOrchestratorError as e:
            logger.error(f"Failed to retrieve song {song_id}: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error retrieving song {song_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def update_song(self, song_id: str, update_data: dict) -> tuple[dict, int]:
        """
        Update song metadata (title, workflow, rating, tags, project_id, project_folder_id)

        Args:
            song_id: Song UUID
            update_data: Dict with update fields

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.orchestrator.update_song(song_id, update_data)

            if result is None:
                return {"error": "Song not found"}, 404

            return {"success": True, "data": result}, 200

        except ValueError as e:
            logger.warning(f"Song update validation failed {song_id}: {e}")
            return {"error": str(e)}, 400
        except Exception as e:
            logger.error(f"Failed to update song {song_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def delete_song(self, song_id: str) -> tuple[dict[str, Any], int]:
        """
        Delete song by ID including all choices

        Args:
            song_id: UUID of the song to delete

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            success = self.orchestrator.delete_single_song(song_id)

            if not success:
                return {"error": "Song not found"}, 404

            return {"message": "Song deleted successfully"}, 200

        except SongOrchestratorError as e:
            logger.error(f"Failed to delete song {song_id}: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error deleting song {song_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def bulk_delete_songs(self, song_ids: list[str]) -> tuple[dict[str, Any], int]:
        """
        Delete multiple songs by IDs including all choices

        Args:
            song_ids: List of song IDs to delete

        Returns:
            Tuple of (response_data, status_code)
        """
        if not song_ids:
            return {"error": "No song IDs provided"}, 400

        if len(song_ids) > 100:
            return {"error": "Too many songs (max 100 per request)"}, 400

        try:
            result = self.orchestrator.bulk_delete_songs(song_ids)

            # Determine response status based on results
            summary = result["summary"]
            if summary["deleted"] > 0:
                status_code = 200
                if summary["not_found"] > 0 or summary["errors"] > 0:
                    status_code = 207  # Multi-Status
            else:
                status_code = 400 if summary["errors"] > 0 else 404

            return result, status_code

        except SongOrchestratorError as e:
            logger.error(f"Bulk delete failed: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error in bulk delete: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def update_choice_rating(self, choice_id: str, rating_data: dict[str, Any]) -> tuple[dict[str, Any], int]:
        """
        Update rating for a specific song choice

        Args:
            choice_id: UUID of the choice
            rating_data: Dictionary containing rating field

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            rating = rating_data.get("rating")
            result = self.orchestrator.update_choice_rating(choice_id, rating)

            if result is None:
                return {"error": "Song choice not found"}, 404

            return result, 200

        except SongOrchestratorError as e:
            logger.error(f"Failed to update choice rating {choice_id}: {e}")
            if "Rating must be" in str(e):
                return {"error": str(e)}, 400
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error updating choice rating {choice_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def assign_to_project(
        self,
        song_id: str,
        project_id: str,
        folder_id: str | None = None,
    ) -> tuple[dict, int]:
        """
        Assign song to a project (1:1 relationship)

        Args:
            song_id: Song UUID
            project_id: Project UUID
            folder_id: Optional folder UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.orchestrator.assign_song_to_project(
                song_id=song_id,
                project_id=project_id,
                folder_id=folder_id,
            )

            logger.info(f"Song assigned to project: {song_id} -> {project_id}")

            return {"success": True, "data": result}, 200

        except ValueError as e:
            logger.warning(f"Song assignment validation failed {song_id}: {e}")
            return {"error": str(e)}, 404
        except Exception as e:
            logger.error(f"Failed to assign song to project {song_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def unassign_from_project(self, song_id: str) -> tuple[dict, int]:
        """
        Remove song from its assigned project (link only, song remains)

        Args:
            song_id: Song UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.orchestrator.unassign_song_from_project(song_id)

            logger.info(f"Song unassigned from project: {song_id}")

            return {"success": True, "data": result}, 200

        except ValueError as e:
            logger.warning(f"Song unassign validation failed {song_id}: {e}")
            return {"error": str(e)}, 404
        except Exception as e:
            logger.error(f"Failed to unassign song from project {song_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500
