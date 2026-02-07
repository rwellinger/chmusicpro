"""Song Transformer - Pure functions for song data transformations"""

import re
from typing import Any


class SongTransformer:
    """Transform song and choice data to various formats (pure functions)"""

    @staticmethod
    def transform_song_to_list_format(song) -> dict[str, Any]:
        """
        Transform song object to list display format

        Pure function - no DB, no file system, fully unit-testable

        Args:
            song: Song model object

        Returns:
            Dict with list format fields
        """
        # Extract project info if available (relationship may be lazy-loaded)
        project_id = None
        project_name = None
        if hasattr(song, "project_id") and song.project_id:
            project_id = str(song.project_id)
            # Try to get project name from relationship (if eager-loaded)
            if hasattr(song, "project") and song.project:
                project_name = song.project.project_name

        return {
            "id": str(song.id),
            "lyrics": song.lyrics,
            "title": song.title,
            "model": song.model,
            "tags": song.tags,
            "workflow": song.workflow,
            "is_instrumental": song.is_instrumental,
            "project_id": project_id,
            "project_name": project_name,
            "created_at": song.created_at.isoformat() if song.created_at else None,
        }

    @staticmethod
    def transform_song_to_detail_format(song) -> dict[str, Any]:
        """
        Transform song object to detailed format with all choices

        Pure function - no DB, no file system, fully unit-testable

        Args:
            song: Song model object with choices relationship loaded

        Returns:
            Dict with detailed format including all choices
        """
        # Format choices
        choices_list = []
        for choice in song.choices:
            choice_data = {
                "id": str(choice.id),
                "mureka_choice_id": choice.mureka_choice_id,
                "choice_index": choice.choice_index,
                # Legacy Mureka URLs (kept for backward compatibility)
                "mp3_url": choice.mp3_url,
                "flac_url": choice.flac_url,
                "wav_url": choice.wav_url,
                "video_url": choice.video_url,
                "image_url": choice.image_url,
                "stem_url": choice.stem_url,
                # S3 storage keys (new - for lazy migration)
                "mp3_s3_key": choice.mp3_s3_key,
                "flac_s3_key": choice.flac_s3_key,
                "wav_s3_key": choice.wav_s3_key,
                "stem_s3_key": choice.stem_s3_key,
                "stem_generated_at": choice.stem_generated_at.isoformat() if choice.stem_generated_at else None,
                "duration": choice.duration,
                "title": choice.title,
                "tags": choice.tags,
                "rating": choice.rating,
                "formattedDuration": SongTransformer.format_duration_from_ms(choice.duration)
                if choice.duration
                else None,
                "created_at": choice.created_at.isoformat() if choice.created_at else None,
            }
            choices_list.append(choice_data)

        # Format song data
        return {
            "id": str(song.id),
            "task_id": song.task_id,
            "job_id": song.job_id,
            "lyrics": song.lyrics,
            "prompt": song.prompt,
            "model": song.model,
            "title": song.title,
            "tags": song.tags,
            "workflow": song.workflow,
            "is_instrumental": song.is_instrumental,
            "status": song.status,
            "progress_info": song.progress_info,
            "error_message": song.error_message,
            "mureka_response": song.mureka_response,
            "mureka_status": song.mureka_status,
            "choices_count": len(choices_list),
            "choices": choices_list,
            "created_at": song.created_at.isoformat() if song.created_at else None,
            "updated_at": song.updated_at.isoformat() if song.updated_at else None,
            "completed_at": song.completed_at.isoformat() if song.completed_at else None,
        }

    @staticmethod
    def format_duration_from_ms(duration_ms: float) -> str:
        """
        Format duration from milliseconds to MM:SS format

        Pure function - no dependencies, fully unit-testable

        Args:
            duration_ms: Duration in milliseconds

        Returns:
            Formatted string in MM:SS format
        """
        if not duration_ms:
            return "00:00"

        total_seconds = int(duration_ms / 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


def sanitize_filename(title: str | None, max_length: int = 50) -> str:
    """
    Sanitize song title for use in S3 keys

    Pure function - no dependencies, fully unit-testable

    Args:
        title: Song title to sanitize (may be None)
        max_length: Maximum length of sanitized string

    Returns:
        Sanitized filename-safe string (lowercase, alphanumeric + hyphens)

    Examples:
        >>> sanitize_filename("My Rock Song!")
        'my-rock-song'
        >>> sanitize_filename("Epic Song (Remix) [2024]")
        'epic-song-remix-2024'
        >>> sanitize_filename(None)
        'untitled'
        >>> sanitize_filename("a" * 100, max_length=20)
        'aaaaaaaaaaaaaaaaaaaa'
    """
    if not title:
        return "untitled"

    # Convert to lowercase
    sanitized = title.lower()

    # Replace spaces and special chars with hyphens
    sanitized = re.sub(r"[^a-z0-9]+", "-", sanitized)

    # Remove leading/trailing hyphens
    sanitized = sanitized.strip("-")

    # Truncate to max_length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip("-")

    # Fallback if empty after sanitization
    return sanitized if sanitized else "untitled"


def generate_s3_song_key(song_id: str, song_title: str | None, choice_index: int, file_type: str) -> str:
    """
    Generate S3 key for song file upload (lazy migration pattern)

    NOTE: Key does NOT include bucket name (bucket is 'songs' in settings.py)

    Pure function - no dependencies, fully unit-testable

    Args:
        song_id: Song UUID (full)
        song_title: Song title (may be None, used for readability)
        choice_index: Choice index (0, 1, 2, ...)
        file_type: File type ('mp3', 'flac', 'stems')

    Returns:
        S3 key (e.g., "{sanitized_title}_{song_id_short}/choice-{index}/audio.{ext}")

    Examples:
        >>> generate_s3_song_key("abc-123-def-456", "My Rock Song", 0, "mp3")
        'my-rock-song_abc-123/choice-0/audio.mp3'
        >>> generate_s3_song_key("abc-123-def-456", "My Rock Song", 1, "flac")
        'my-rock-song_abc-123/choice-1/audio.flac'
        >>> generate_s3_song_key("abc-123-def-456", None, 0, "stems")
        'untitled_abc-123/choice-0/stems.zip'
        >>> generate_s3_song_key("abc-123-def-456-ghi-789", "Epic Song", 0, "mp3")
        'epic-song_abc-123/choice-0/audio.mp3'
    """
    # Sanitize title for filename
    sanitized_title = sanitize_filename(song_title)

    # Shorten song_id to first 7 chars (like git commit hash)
    song_id_short = song_id[:7] if len(song_id) >= 7 else song_id

    # Determine file extension and name based on type
    filename = "stems.zip" if file_type == "stems" else f"audio.{file_type}"

    # Build S3 key: {title_id-short}/choice-{index}/{filename}
    # NOTE: Bucket name ('songs') is NOT part of the key!
    return f"{sanitized_title}_{song_id_short}/choice-{choice_index}/{filename}"
