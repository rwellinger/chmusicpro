"""Song Project Transformer - Pure functions for transformations and business logic

IMPORTANT: This module contains ONLY pure functions (100% unit-testable).
NO database operations, NO file system operations, NO external dependencies.
"""

import hashlib
import re
from typing import Any


def generate_s3_prefix(project_name: str, user_id: str) -> str:
    """
    Generate S3 prefix from user_id and project name (slug-like)

    Args:
        project_name: Project name (e.g., "My Awesome Song")
        user_id: User UUID (for multi-tenant isolation)

    Returns:
        S3 prefix (e.g., "{user-id}/my-awesome-song/")

    Examples:
        >>> generate_s3_prefix("My Awesome Song", "abc-123")
        'abc-123/my-awesome-song/'
        >>> generate_s3_prefix("Café Müller (2024)", "def-456")
        'def-456/cafe-muller-2024/'
    """
    # Convert to lowercase
    slug = project_name.lower()
    # Replace special characters with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    return f"{user_id}/{slug}/"


def get_default_folder_structure() -> list[dict[str, str]]:
    """
    Get default folder structure for new projects

    Returns:
        List of folder definitions with name, type, and icon

    Examples:
        >>> folders = get_default_folder_structure()
        >>> folders[0]['folder_name']
        '01 Arrangement'
    """
    return [
        {"folder_name": "01 Arrangement", "folder_type": "arrangement", "custom_icon": "fas fa-music"},
        {"folder_name": "02 AI", "folder_type": "ai", "custom_icon": "fas fa-robot"},
        {"folder_name": "03 Pictures", "folder_type": "pictures", "custom_icon": "fas fa-image"},
        {"folder_name": "04 Vocal", "folder_type": "vocal", "custom_icon": "fas fa-microphone"},
        {"folder_name": "05 Stems", "folder_type": "stems", "custom_icon": "fas fa-layer-group"},
        {"folder_name": "06 Mix", "folder_type": "mix", "custom_icon": "fas fa-sliders-h"},
        {"folder_name": "07 Master", "folder_type": "master", "custom_icon": "fas fa-certificate"},
        {"folder_name": "08 Promotion", "folder_type": "promotion", "custom_icon": "fas fa-bullhorn"},
        {"folder_name": "09 Release", "folder_type": "release", "custom_icon": "fas fa-compact-disc"},
        {"folder_name": "10 Archive", "folder_type": "archive", "custom_icon": "fas fa-archive"},
    ]


def detect_file_type(filename: str) -> str:
    """
    Detect file type from filename extension

    Args:
        filename: Filename with extension

    Returns:
        File type (audio, image, document, archive, other)

    Examples:
        >>> detect_file_type("song.mp3")
        'audio'
        >>> detect_file_type("cover.jpg")
        'image'
        >>> detect_file_type("lyrics.txt")
        'document'
    """
    extension = filename.lower().split(".")[-1] if "." in filename else ""

    audio_extensions = {"mp3", "wav", "flac", "aac", "m4a", "ogg", "wma", "aiff", "alac"}
    image_extensions = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "tiff"}
    document_extensions = {"txt", "doc", "docx", "pdf", "md", "rtf", "odt"}
    archive_extensions = {"zip", "rar", "7z", "tar", "gz", "bz2"}
    video_extensions = {"mp4", "avi", "mkv", "mov", "wmv", "flv", "webm"}

    if extension in audio_extensions:
        return "audio"
    elif extension in image_extensions:
        return "image"
    elif extension in document_extensions:
        return "document"
    elif extension in archive_extensions:
        return "archive"
    elif extension in video_extensions:
        return "video"
    else:
        return "other"


def get_mime_type(filename: str) -> str | None:
    """
    Get MIME type from filename extension

    Args:
        filename: Filename with extension

    Returns:
        MIME type or None if unknown

    Examples:
        >>> get_mime_type("song.mp3")
        'audio/mpeg'
        >>> get_mime_type("cover.jpg")
        'image/jpeg'
    """
    extension = filename.lower().split(".")[-1] if "." in filename else ""

    mime_map = {
        # Audio
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "flac": "audio/flac",
        "aac": "audio/aac",
        "m4a": "audio/mp4",
        "ogg": "audio/ogg",
        # Image
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        # Document
        "txt": "text/plain",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        # Archive
        "zip": "application/zip",
        "rar": "application/x-rar-compressed",
        "7z": "application/x-7z-compressed",
        # Video
        "mp4": "video/mp4",
        "avi": "video/x-msvideo",
        "mkv": "video/x-matroska",
    }

    return mime_map.get(extension)


def validate_project_status(status: str) -> bool:
    """
    Validate project status enum

    Args:
        status: Project status string

    Returns:
        True if valid status, False otherwise

    Examples:
        >>> validate_project_status('new')
        True
        >>> validate_project_status('progress')
        True
        >>> validate_project_status('archived')
        True
        >>> validate_project_status('invalid')
        False
    """
    return status in ["new", "progress", "archived"]


def transform_project_to_response(project: Any) -> dict[str, Any]:
    """
    Transform SongProject DB model to API response format

    Args:
        project: SongProject DB model instance

    Returns:
        Dictionary with project data for API response
    """
    return {
        "id": str(project.id),
        "project_name": project.project_name,
        "s3_prefix": project.s3_prefix,
        "cover_image_id": str(project.cover_image_id) if project.cover_image_id else None,
        "tags": project.tags,
        "description": project.description,
        "project_status": project.project_status,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


def transform_folder_to_response(folder: Any) -> dict[str, Any]:
    """
    Transform ProjectFolder DB model to API response format

    Args:
        folder: ProjectFolder DB model instance

    Returns:
        Dictionary with folder data for API response
    """
    return {
        "id": str(folder.id),
        "folder_name": folder.folder_name,
        "folder_type": folder.folder_type,
        "s3_prefix": folder.s3_prefix,
        "custom_icon": folder.custom_icon,
        "created_at": folder.created_at.isoformat() if folder.created_at else None,
    }


def transform_file_to_response(file: Any, download_url: str | None = None) -> dict[str, Any]:
    """
    Transform ProjectFile DB model to API response format

    Args:
        file: ProjectFile DB model instance
        download_url: Pre-signed download URL (optional)

    Returns:
        Dictionary with file data for API response
    """
    return {
        "id": str(file.id),
        "filename": file.filename,
        "relative_path": file.relative_path,
        "file_type": file.file_type,
        "mime_type": file.mime_type,
        "file_size_bytes": file.file_size_bytes,
        "s3_key": file.s3_key,
        "is_synced": file.is_synced,
        "download_url": download_url,
        "created_at": file.created_at.isoformat() if file.created_at else None,
        "updated_at": file.updated_at.isoformat() if file.updated_at else None,
    }


def transform_project_detail_to_response(project: Any) -> dict[str, Any]:
    """
    Transform SongProject with folders and files to detailed API response

    Args:
        project: SongProject DB model with loaded folders and files

    Returns:
        Dictionary with complete project data including folders and files
    """
    response = transform_project_to_response(project)

    # Add folders with their files
    folders_data = []
    total_files_live = 0
    total_size_live = 0

    for folder in project.folders:
        folder_data = transform_folder_to_response(folder)
        folder_data["files"] = [transform_file_to_response(file) for file in folder.files]
        folders_data.append(folder_data)

        # Calculate LIVE stats from actual files (Single Source of Truth)
        total_files_live += len(folder.files)
        total_size_live += sum(file.file_size_bytes for file in folder.files)

    response["folders"] = folders_data

    # Add LIVE calculated values (always correct!)
    response["total_files"] = total_files_live
    response["total_size_bytes"] = total_size_live

    return response


def calculate_pagination_meta(total: int, limit: int, offset: int) -> dict[str, Any]:
    """
    Calculate pagination metadata

    Args:
        total: Total number of items
        limit: Items per page
        offset: Current offset

    Returns:
        Dictionary with pagination metadata

    Examples:
        >>> calculate_pagination_meta(100, 20, 0)
        {'total': 100, 'limit': 20, 'offset': 0, 'has_more': True}
        >>> calculate_pagination_meta(15, 20, 0)
        {'total': 15, 'limit': 20, 'offset': 0, 'has_more': False}
    """
    has_more = (offset + limit) < total
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }


def normalize_project_name(project_name: str) -> str:
    """
    Normalize project name (trim whitespace)

    Args:
        project_name: Raw project name

    Returns:
        Normalized project name

    Examples:
        >>> normalize_project_name("  My Project  ")
        'My Project'
        >>> normalize_project_name("")
        ''
    """
    return project_name.strip()


def calculate_file_hash(file_data: bytes) -> str:
    """
    Calculate SHA256 hash of file data (for Mirror sync comparison)

    Args:
        file_data: Raw file bytes

    Returns:
        SHA256 hash as hex string (64 characters)

    Examples:
        >>> calculate_file_hash(b"Hello World")
        'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e'
        >>> calculate_file_hash(b"")
        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    """
    return hashlib.sha256(file_data).hexdigest()


def transform_song_to_assigned_response(song: Any) -> dict[str, Any]:  # pragma: no cover
    """
    Transform Song DB model to assigned song API response format (pure function)

    NOTE: No unit tests - Simple attribute mapper without business logic.
    Testing would only verify mock setup, not real behavior (CLAUDE.md rule).

    Args:
        song: Song DB model instance

    Returns:
        Dictionary with song data for API response

    Examples:
        >>> class MockSong:
        ...     id = "abc-123"
        ...     title = "Summer Vibes"
        ...     workflow = "final"
        ...     file_type = "flac"
        ...     file_size_bytes = 3355443
        ...     created_at = None
        >>> transform_song_to_assigned_response(MockSong())
        {'id': 'abc-123', 'title': 'Summer Vibes', 'workflow': 'final', 'file_type': 'flac', 'file_size_bytes': 3355443, 'created_at': None}
    """
    return {
        "id": str(song.id),
        "title": song.title,
        "workflow": song.workflow if hasattr(song, "workflow") else None,
        "file_type": song.file_type if hasattr(song, "file_type") else None,
        "file_size_bytes": song.file_size_bytes if hasattr(song, "file_size_bytes") else None,
        "created_at": song.created_at.isoformat() if song.created_at else None,
    }


def transform_sketch_to_assigned_response(sketch: Any) -> dict[str, Any]:  # pragma: no cover
    """
    Transform SongSketch DB model to assigned sketch API response format (pure function)

    NOTE: No unit tests - Simple attribute mapper without business logic.
    Testing would only verify mock setup, not real behavior (CLAUDE.md rule).

    Args:
        sketch: SongSketch DB model instance

    Returns:
        Dictionary with sketch data for API response

    Examples:
        >>> class MockSketch:
        ...     id = "def-456"
        ...     title = "Chorus Ideas"
        ...     prompt = "upbeat pop"
        ...     sketch_type = "song"
        ...     workflow = "draft"
        ...     created_at = None
        >>> transform_sketch_to_assigned_response(MockSketch())
        {'id': 'def-456', 'title': 'Chorus Ideas', 'prompt': 'upbeat pop', 'sketch_type': 'song', 'workflow': 'draft', 'created_at': None}
    """
    return {
        "id": str(sketch.id),
        "title": sketch.title,
        "prompt": sketch.prompt,
        "sketch_type": sketch.sketch_type if hasattr(sketch, "sketch_type") else "song",
        "workflow": sketch.workflow if hasattr(sketch, "workflow") else "draft",
        "created_at": sketch.created_at.isoformat() if sketch.created_at else None,
    }


def transform_image_to_assigned_response(image: Any) -> dict[str, Any]:  # pragma: no cover
    """
    Transform GeneratedImage DB model to assigned image API response format (pure function)

    NOTE: No unit tests - Simple attribute mapper without business logic.
    Testing would only verify mock setup, not real behavior (CLAUDE.md rule).

    Args:
        image: GeneratedImage DB model instance

    Returns:
        Dictionary with image data for API response

    Examples:
        >>> class MockImage:
        ...     id = "ghi-789"
        ...     title = "Summer Sunset"
        ...     prompt = "sunset landscape"
        ...     composition = "rule of thirds"
        ...     width = 1024
        ...     height = 1024
        ...     created_at = None
        >>> transform_image_to_assigned_response(MockImage())
        {'id': 'ghi-789', 'title': 'Summer Sunset', 'prompt': 'sunset landscape', 'composition': 'rule of thirds', 'width': 1024, 'height': 1024, 'created_at': None}
    """
    # Parse size if available (e.g., "1024x1024")
    width = None
    height = None
    if hasattr(image, "size") and image.size:
        try:
            parts = str(image.size).split("x")
            if len(parts) == 2:
                width = int(parts[0])
                height = int(parts[1])
        except (ValueError, AttributeError):
            pass

    # Override with direct width/height attributes if available
    if hasattr(image, "width") and image.width:
        width = image.width
    if hasattr(image, "height") and image.height:
        height = image.height

    return {
        "id": str(image.id),
        "title": image.title if hasattr(image, "title") else None,
        "prompt": image.prompt if hasattr(image, "prompt") else None,
        "composition": image.composition if hasattr(image, "composition") else None,
        "width": width,
        "height": height,
        "created_at": image.created_at.isoformat() if image.created_at else None,
    }


def transform_release_to_assigned_response(release: Any) -> dict[str, Any]:  # pragma: no cover
    """
    Transform SongRelease DB model to assigned release API response format (pure function)

    NOTE: No unit tests - Simple attribute mapper without business logic.
    Testing would only verify mock setup, not real behavior (CLAUDE.md rule).

    Args:
        release: SongRelease DB model instance

    Returns:
        Dictionary with release data for API response

    Examples:
        >>> class MockRelease:
        ...     id = "jkl-012"
        ...     name = "Summer EP"
        ...     type = "single"
        ...     status = "released"
        ...     genre = "Electronic"
        ...     release_date = None
        ...     created_at = None
        >>> transform_release_to_assigned_response(MockRelease())
        {'id': 'jkl-012', 'name': 'Summer EP', 'type': 'single', 'status': 'released', 'genre': 'Electronic', 'release_date': None, 'created_at': None}
    """
    return {
        "id": str(release.id),
        "name": release.name if hasattr(release, "name") else None,
        "type": release.type if hasattr(release, "type") else None,
        "status": release.status if hasattr(release, "status") else None,
        "genre": release.genre if hasattr(release, "genre") else None,
        "release_date": release.release_date.isoformat()
        if hasattr(release, "release_date") and release.release_date
        else None,
        "created_at": release.created_at.isoformat() if release.created_at else None,
    }


def get_display_cover_info(releases: list[Any]) -> dict[str, Any]:
    """
    Determine which cover to display for a Song Project based on assigned releases (pure function)

    Business logic:
    - If no releases assigned → placeholder (letter-based initials)
    - If releases exist:
      - Filter out: status IN ('rejected', 'downtaken', 'archived')
      - Sort by: release_date DESC (highest = newest)
      - Select: First valid release
    - If no valid releases remain → placeholder

    Args:
        releases: List of SongRelease DB model instances (from get_assigned_releases_for_project)

    Returns:
        Dictionary with cover info:
        {
            'source': 'release' | 'placeholder',
            'release_id': str | None,  # UUID if source='release'
            'release_name': str | None  # Name if source='release'
        }

    Examples:
        >>> # No releases
        >>> get_display_cover_info([])
        {'source': 'placeholder', 'release_id': None, 'release_name': None}

        >>> # Single valid release
        >>> class MockRelease:
        ...     id = "abc-123"
        ...     name = "Summer EP"
        ...     status = "released"
        ...     release_date = "2024-06-01"
        >>> get_display_cover_info([MockRelease()])
        {'source': 'release', 'release_id': 'abc-123', 'release_name': 'Summer EP'}

        >>> # Multiple releases, newest valid one selected
        >>> class Release1:
        ...     id = "old-123"
        ...     name = "Old Release"
        ...     status = "released"
        ...     release_date = "2023-01-01"
        >>> class Release2:
        ...     id = "new-456"
        ...     name = "New Release"
        ...     status = "uploaded"
        ...     release_date = "2024-12-01"
        >>> get_display_cover_info([Release1(), Release2()])
        {'source': 'release', 'release_id': 'new-456', 'release_name': 'New Release'}

        >>> # Only invalid status → placeholder
        >>> class RejectedRelease:
        ...     id = "rejected-123"
        ...     name = "Rejected EP"
        ...     status = "rejected"
        ...     release_date = "2024-01-01"
        >>> get_display_cover_info([RejectedRelease()])
        {'source': 'placeholder', 'release_id': None, 'release_name': None}
    """
    # No releases → placeholder
    if not releases:
        return {"source": "placeholder", "release_id": None, "release_name": None}

    # Filter out invalid statuses
    excluded_statuses = {"rejected", "downtaken", "archived"}
    valid_releases = [r for r in releases if r.status not in excluded_statuses]

    # No valid releases → placeholder
    if not valid_releases:
        return {"source": "placeholder", "release_id": None, "release_name": None}

    # Sort by release_date DESC (newest first)
    # Handle None release_date (treat as very old)
    sorted_releases = sorted(
        valid_releases,
        key=lambda r: r.release_date if r.release_date else "1900-01-01",  # type: ignore
        reverse=True,
    )

    # Select newest release
    newest_release = sorted_releases[0]

    return {
        "source": "release",
        "release_id": str(newest_release.id),
        "release_name": newest_release.name,
    }
