"""Song Service - Database operations for song management"""

import traceback
from datetime import datetime
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from db.database import get_db
from db.models import Song, SongChoice
from utils.logger import logger


class SongService:
    """Service for song database operations"""

    def get_song_by_task_id(self, task_id: str) -> Song | None:
        """Get song by task_id with choices loaded"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).options(joinedload(Song.choices)).filter(Song.task_id == task_id).first()
                if song:
                    logger.debug(
                        "song_retrieved_by_task_id",
                        task_id=task_id,
                        song_id=str(song.id),
                        choices_count=len(song.choices),
                    )
                else:
                    logger.debug("Song not found", task_id=task_id)
                return song
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_song_by_task_id", task_id=task_id, error=str(e), error_type=type(e).__name__)
            return None

    def get_song_by_job_id(self, job_id: str) -> Song | None:
        """Get song by job_id (MUREKA job ID) with choices loaded"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).options(joinedload(Song.choices)).filter(Song.job_id == job_id).first()
                if song:
                    logger.debug(
                        "song_retrieved_by_job_id", job_id=job_id, song_id=str(song.id), choices_count=len(song.choices)
                    )
                else:
                    logger.debug("Song not found", job_id=job_id)
                return song
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_song_by_job_id", job_id=job_id, error=str(e), error_type=type(e).__name__)
            return None

    def get_song_choices(self, song_id) -> list[SongChoice]:
        """Get all choices for a specific song"""
        try:
            db = next(get_db())
            try:
                choices = (
                    db.query(SongChoice).filter(SongChoice.song_id == song_id).order_by(SongChoice.choice_index).all()
                )
                logger.debug("Song choices retrieved", song_id=str(song_id), choices_count=len(choices))
                return choices
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_song_choices", song_id=str(song_id), error=str(e), error_type=type(e).__name__)
            return []

    def get_choice_by_mureka_id(self, mureka_choice_id: str) -> SongChoice | None:
        """Get a specific choice by MUREKA choice ID"""
        try:
            db = next(get_db())
            try:
                choice = db.query(SongChoice).filter(SongChoice.mureka_choice_id == mureka_choice_id).first()
                if choice:
                    logger.debug(
                        "choice_retrieved_by_mureka_id", mureka_choice_id=mureka_choice_id, choice_id=str(choice.id)
                    )
                else:
                    logger.debug("Choice not found", mureka_choice_id=mureka_choice_id)
                return choice
            finally:
                db.close()
        except Exception as e:
            logger.error(
                "error_getting_choice_by_mureka_id",
                mureka_choice_id=mureka_choice_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def get_songs_paginated(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str = None,
        search: str = "",
        sort_by: str = "created_at",
        sort_direction: str = "desc",
        workflow: str = None,
    ) -> list[Song]:
        """
        Get songs with pagination, search and sorting

        Args:
            limit: Number of songs to return (default 20)
            offset: Number of songs to skip (default 0)
            status: Optional status filter (SUCCESS, PENDING, FAILURE, etc.)
            search: Search term to filter by title, lyrics, or tags
            sort_by: Field to sort by (created_at, title, lyrics)
            sort_direction: Sort direction (asc, desc)
            workflow: Optional workflow filter (onWork, inUse, notUsed)

        Returns:
            List of Song instances with loaded choices
        """
        try:
            db = next(get_db())
            try:
                query = db.query(Song).options(joinedload(Song.choices), joinedload(Song.project))

                # Apply status filter if provided
                if status:
                    query = query.filter(Song.status == status)

                # Apply workflow filter if provided
                if workflow:
                    if workflow == "all":
                        # "all" excludes only notUsed and fail workflows (NULL is allowed)
                        query = query.filter((Song.workflow.is_(None)) | (Song.workflow.notin_(["notUsed", "fail"])))
                    else:
                        # Specific workflow filter
                        query = query.filter(Song.workflow == workflow)

                # Apply search filter if provided
                if search:
                    search_term = f"%{search}%"
                    from sqlalchemy import or_

                    query = query.filter(
                        or_(Song.title.ilike(search_term), Song.lyrics.ilike(search_term), Song.tags.ilike(search_term))
                    )

                # Apply sorting
                if sort_by == "title":
                    # Handle null titles by treating them as empty strings for sorting
                    if sort_direction == "desc":
                        query = query.order_by(Song.title.desc().nullslast())
                    else:
                        query = query.order_by(Song.title.asc().nullsfirst())
                elif sort_by == "lyrics":
                    if sort_direction == "desc":
                        query = query.order_by(Song.lyrics.desc())
                    else:
                        query = query.order_by(Song.lyrics.asc())
                else:  # default to created_at
                    if sort_direction == "desc":
                        query = query.order_by(Song.created_at.desc())
                    else:
                        query = query.order_by(Song.created_at.asc())

                songs = query.limit(limit).offset(offset).all()
                logger.debug(
                    "songs_retrieved_paginated",
                    count=len(songs),
                    limit=limit,
                    offset=offset,
                    status=status,
                    search=search,
                    workflow=workflow,
                    sort_by=sort_by,
                    sort_direction=sort_direction,
                )
                return songs
            finally:
                db.close()
        except Exception as e:
            logger.error(
                "error_getting_paginated_songs",
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return []

    def get_total_songs_count(self, status: str = None, search: str = "", workflow: str = None) -> int:
        """
        Get total count of songs with optional search and workflow filter

        Args:
            status: Optional status filter
            search: Search term to filter by title, lyrics, or tags
            workflow: Optional workflow filter (onWork, inUse, notUsed)

        Returns:
            Total number of songs matching the criteria
        """
        try:
            db = next(get_db())
            try:
                query = db.query(Song)

                if status:
                    query = query.filter(Song.status == status)

                # Apply workflow filter if provided
                if workflow:
                    if workflow == "all":
                        # "all" excludes only notUsed and fail workflows (NULL is allowed)
                        query = query.filter((Song.workflow.is_(None)) | (Song.workflow.notin_(["notUsed", "fail"])))
                    else:
                        # Specific workflow filter
                        query = query.filter(Song.workflow == workflow)

                # Apply search filter if provided
                if search:
                    search_term = f"%{search}%"
                    from sqlalchemy import or_

                    query = query.filter(
                        or_(Song.title.ilike(search_term), Song.lyrics.ilike(search_term), Song.tags.ilike(search_term))
                    )

                count = query.count()
                logger.debug(
                    "total_songs_count_retrieved", count=count, status=status, search=search, workflow=workflow
                )
                return count
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_total_songs_count", error=str(e), error_type=type(e).__name__)
            return 0

    def get_song_by_id(self, song_id) -> Song | None:
        """
        Get song by ID with loaded choices

        Args:
            song_id: UUID of the song

        Returns:
            Song instance with loaded choices, or None if not found
        """
        try:
            db = next(get_db())
            try:
                song = db.query(Song).options(joinedload(Song.choices)).filter(Song.id == song_id).first()
                if song:
                    logger.debug("Song retrieved", song_id=str(song_id), choices_count=len(song.choices))
                else:
                    logger.debug("Song not found", song_id=str(song_id))
                return song
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_song_by_id", song_id=str(song_id), error=str(e), error_type=type(e).__name__)
            return None

    def get_recent_songs(self, limit: int = 10) -> list[Song]:
        """
        Get most recently created songs

        Args:
            limit: Number of songs to return

        Returns:
            List of Song instances with loaded choices
        """
        try:
            db = next(get_db())
            try:
                songs = (
                    db.query(Song).options(joinedload(Song.choices)).order_by(Song.created_at.desc()).limit(limit).all()
                )
                logger.debug("Recent songs retrieved", count=len(songs), limit=limit)
                return songs
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_recent_songs", error=str(e), error_type=type(e).__name__)
            return []

    def delete_song_by_id(self, song_id) -> bool:
        """
        Delete song and all its choices by ID

        Args:
            song_id: UUID of the song

        Returns:
            True if successful, False otherwise
        """
        try:
            db = next(get_db())
            try:
                song = db.query(Song).filter(Song.id == song_id).first()
                if song:
                    db.delete(song)  # Cascade will delete choices
                    db.commit()
                    logger.info("Song deleted", song_id=str(song_id))
                    return True
                logger.warning("Song not found for deletion", song_id=str(song_id))
                return False
            except SQLAlchemyError as e:
                db.rollback()
                logger.error("song_deletion_db_error", song_id=str(song_id), error=str(e), error_type=type(e).__name__)
                raise
            finally:
                db.close()
        except Exception as e:
            logger.error(
                "song_deletion_failed",
                song_id=str(song_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return False

    def update_song(self, song_id: str, update_data: dict[str, Any]) -> Song | None:
        """
        Update song fields by ID

        Args:
            song_id: UUID of the song
            update_data: Dictionary with fields to update (title, tags, etc.)

        Returns:
            Updated Song object if successful, None otherwise
        """
        try:
            db = next(get_db())
            try:
                song = db.query(Song).filter(Song.id == song_id).first()
                if not song:
                    logger.warning("Song not found for update", song_id=str(song_id))
                    return None

                # Update allowed fields
                if "title" in update_data:
                    song.title = update_data["title"]
                if "tags" in update_data:
                    song.tags = update_data["tags"]
                if "workflow" in update_data:
                    song.workflow = update_data["workflow"]
                if "project_id" in update_data:
                    song.project_id = update_data["project_id"]
                if "project_folder_id" in update_data:
                    song.project_folder_id = update_data["project_folder_id"]

                # Update timestamp
                song.updated_at = datetime.utcnow()

                db.commit()

                # Create a detached copy of the song object with updated fields
                updated_song_data = {
                    "id": song.id,
                    "title": song.title,
                    "tags": song.tags,
                    "workflow": song.workflow,
                    "project_id": song.project_id,
                    "project_folder_id": song.project_folder_id,
                    "updated_at": song.updated_at,
                }

                logger.info("Song updated", song_id=str(song_id), fields_updated=list(update_data.keys()))

                # Return a simple object with the data we need
                class UpdatedSong:
                    def __init__(self, data):
                        self.id = data["id"]
                        self.title = data["title"]
                        self.tags = data["tags"]
                        self.workflow = data["workflow"]
                        self.project_id = data["project_id"]
                        self.project_folder_id = data["project_folder_id"]
                        self.updated_at = data["updated_at"]

                return UpdatedSong(updated_song_data)

            except SQLAlchemyError as e:
                db.rollback()
                logger.error("song_update_db_error", song_id=str(song_id), error=str(e), error_type=type(e).__name__)
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error(
                "song_update_failed",
                song_id=str(song_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return None

    def update_choice_rating(self, choice_id: str, rating: int | None) -> bool:
        """
        Update rating for a specific song choice

        Args:
            choice_id: UUID of the choice
            rating: Rating value (None=unset, 0=thumbs down, 1=thumbs up)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate rating value
            if rating is not None and rating not in [0, 1]:
                logger.warning("Invalid rating value", choice_id=str(choice_id), rating=rating)
                return False

            db = next(get_db())
            try:
                choice = db.query(SongChoice).filter(SongChoice.id == choice_id).first()
                if not choice:
                    logger.warning("Choice not found for rating update", choice_id=str(choice_id))
                    return False

                choice.rating = rating
                choice.updated_at = datetime.utcnow()

                db.commit()
                logger.info("Choice rating updated", choice_id=str(choice_id), rating=rating)
                return True

            except SQLAlchemyError as e:
                db.rollback()
                logger.error(
                    "choice_rating_update_db_error", choice_id=str(choice_id), error=str(e), error_type=type(e).__name__
                )
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error(
                "choice_rating_update_failed",
                choice_id=str(choice_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return False

    def get_choice_by_id(self, choice_id: str) -> SongChoice | None:
        """
        Get a specific choice by ID

        Args:
            choice_id: UUID of the choice

        Returns:
            SongChoice instance or None if not found
        """
        try:
            db = next(get_db())
            try:
                choice = db.query(SongChoice).filter(SongChoice.id == choice_id).first()
                if choice:
                    logger.debug("Choice retrieved", choice_id=str(choice_id))
                else:
                    logger.debug("Choice not found", choice_id=str(choice_id))
                return choice
            finally:
                db.close()
        except Exception as e:
            logger.error(
                "error_getting_choice_by_id", choice_id=str(choice_id), error=str(e), error_type=type(e).__name__
            )
            return None

    def get_choice_by_id_with_song(self, db, choice_id: str) -> SongChoice | None:
        """
        Get a specific choice by ID with song relationship (for orchestrator use)

        CRUD ONLY - No business logic!

        Args:
            db: Database session
            choice_id: UUID of the choice

        Returns:
            SongChoice instance with song relationship loaded, or None if not found
        """
        try:
            from sqlalchemy.orm import joinedload

            choice = (
                db.query(SongChoice).options(joinedload(SongChoice.song)).filter(SongChoice.id == choice_id).first()
            )
            if choice:
                logger.debug("Choice with song retrieved", choice_id=str(choice_id))
            else:
                logger.debug("Choice not found", choice_id=str(choice_id))
            return choice
        except Exception as e:
            logger.error(
                "error_getting_choice_by_id_with_song",
                choice_id=str(choice_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def update_choice_s3_key(self, db, choice_id: str, file_type: str, s3_key: str) -> bool:
        """
        Update S3 key for a specific file type in song choice

        CRUD ONLY - No business logic!

        Args:
            db: Database session
            choice_id: UUID of the choice
            file_type: File type ('mp3', 'flac', 'stems')
            s3_key: S3 storage key

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            choice = db.query(SongChoice).filter(SongChoice.id == choice_id).first()
            if not choice:
                logger.debug("Choice not found for update", choice_id=str(choice_id))
                return False

            # Update corresponding s3_key field
            if file_type == "mp3":
                choice.mp3_s3_key = s3_key
            elif file_type == "flac":
                choice.flac_s3_key = s3_key
            elif file_type == "wav":
                choice.wav_s3_key = s3_key
            elif file_type == "stems":
                choice.stem_s3_key = s3_key
            else:
                logger.warning("Invalid file type for s3_key update", file_type=file_type)
                return False

            db.commit()
            logger.info(
                "choice_s3_key_updated", choice_id=str(choice_id), file_type=file_type, s3_key=s3_key[:50] + "..."
            )
            return True
        except Exception as e:
            logger.error(
                "error_updating_choice_s3_key",
                choice_id=str(choice_id),
                file_type=file_type,
                error=str(e),
                error_type=type(e).__name__,
            )
            db.rollback()
            return False


# Global service instance
song_service = SongService()


# Standalone wrapper functions for orchestrator imports
def get_song_by_id(db, song_id):
    """Wrapper function for service method"""
    return song_service.get_song_by_id(db, song_id)


def update_song(db, song_id, update_data):
    """Wrapper function for service method"""
    return song_service.update_song(db, song_id, update_data)


def get_choice_by_id_with_song(db, choice_id):
    """Wrapper function for service method"""
    return song_service.get_choice_by_id_with_song(db, choice_id)


def update_choice_s3_key(db, choice_id, file_type, s3_key):
    """Wrapper function for service method"""
    return song_service.update_choice_s3_key(db, choice_id, file_type, s3_key)
