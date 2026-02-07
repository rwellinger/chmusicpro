"""Song Release Transformer - Pure functions for transformations and business logic

IMPORTANT: This module contains ONLY pure functions (100% unit-testable).
NO database operations, NO file system operations, NO external dependencies.
"""

from datetime import date
from typing import Any


def validate_required_fields_for_status(status: str, data: dict[str, Any]) -> tuple[bool, str | None]:
    """
    Validate required fields based on release status

    Args:
        status: Release status
        data: Dictionary with release data

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_required_fields_for_status("draft", {"type": "single", "name": "Test", "genre": "Rock"})
        (True, None)
        >>> validate_required_fields_for_status("uploaded", {"type": "single", "name": "Test", "genre": "Rock"})
        (False, "Missing required fields for status 'uploaded': Upload Date, Copyright Info, Cover Image")
        >>> validate_required_fields_for_status("released", {"type": "single", "name": "Test", "genre": "Rock", "upload_date": "2024-01-01", "release_date": "2024-01-15", "copyright_info": "(C) 2024", "cover_s3_key": "cover.jpg"})
        (True, None)
        >>> validate_required_fields_for_status("rejected", {"type": "single", "name": "Test", "genre": "Rock", "rejected_reason": "Quality issues"})
        (True, None)
    """
    # Base fields (required for ALL statuses)
    base_fields = ["type", "name", "genre"]

    # User-friendly field names for error messages
    field_labels = {
        "type": "Type",
        "name": "Name",
        "genre": "Genre",
        "upload_date": "Upload Date",
        "release_date": "Release Date",
        "downtaken_date": "Downtaken Date",
        "downtaken_reason": "Downtaken Reason",
        "rejected_reason": "Rejected Reason",
        "upc": "UPC",
        "isrc": "ISRC",
        "copyright_info": "Copyright Info",
        "cover_s3_key": "Cover Image",  # User-friendly: "Cover Image" instead of "cover_s3_key"
    }

    # Status-specific required fields
    # Business Logic:
    # - uploaded: Has been uploaded to distributor (Ditto/DistroKid), release_date is OPTIONAL (might not be planned yet), UPC/ISRC are OPTIONAL (not all platforms require them, e.g., SoundCloud)
    # - released: Actually released, release_date is REQUIRED, UPC/ISRC are OPTIONAL (not all platforms require them)
    # - downtaken: Was released and then removed, both dates are REQUIRED, UPC/ISRC are OPTIONAL
    status_requirements = {
        "draft": base_fields,
        "arranging": base_fields,
        "mixing": base_fields,
        "mastering": base_fields,
        "pre_release": base_fields,  # Uploaded to SoundCloud, not yet to Ditto/Spotify
        "rejected": base_fields + ["rejected_reason"],
        "archived": base_fields,
        "uploaded": base_fields
        + ["upload_date", "copyright_info", "cover_s3_key"],  # UPC/ISRC optional, release_date optional
        "released": base_fields
        + ["upload_date", "release_date", "copyright_info", "cover_s3_key"],  # UPC/ISRC optional
        "downtaken": base_fields
        + [
            "upload_date",
            "release_date",
            "downtaken_date",
            "downtaken_reason",
            "copyright_info",
            "cover_s3_key",
        ],  # UPC/ISRC optional
    }

    required = status_requirements.get(status, base_fields)
    missing = [field for field in required if not data.get(field)]

    if missing:
        # Convert technical field names to user-friendly labels
        missing_labels = [field_labels.get(field, field) for field in missing]
        return False, f"Missing required fields for status '{status}': {', '.join(missing_labels)}"

    return True, None


def validate_cover_dimensions(image_width: int, image_height: int) -> tuple[bool, str | None]:
    """
    Validate cover image dimensions (must be 200x200 px)

    Args:
        image_width: Image width in pixels
        image_height: Image height in pixels

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_cover_dimensions(200, 200)
        (True, None)
        >>> validate_cover_dimensions(300, 200)
        (False, 'Cover image must be 200x200 pixels, got 300x200')
        >>> validate_cover_dimensions(199, 199)
        (False, 'Cover image must be 200x200 pixels, got 199x199')
    """
    if image_width != 200 or image_height != 200:
        return False, f"Cover image must be 200x200 pixels, got {image_width}x{image_height}"

    return True, None


def generate_s3_cover_key(user_id: str, release_id: str, filename: str) -> str:
    """
    Generate S3 key for cover image upload

    Args:
        user_id: User UUID
        release_id: Release UUID
        filename: Original filename

    Returns:
        S3 key (e.g., "releases/{user_id}/{release_id}/cover.jpg")

    Examples:
        >>> generate_s3_cover_key("abc-123", "def-456", "my-cover.jpg")
        'releases/abc-123/def-456/cover.jpg'
        >>> generate_s3_cover_key("user-1", "release-2", "album.png")
        'releases/user-1/release-2/cover.png'
    """
    # Extract file extension
    extension = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    return f"releases/{user_id}/{release_id}/cover.{extension}"


def get_presigned_cover_url_placeholder(cover_s3_key: str | None) -> str | None:
    """
    Get placeholder URL for cover image (replaced by orchestrator with real presigned URL)

    Args:
        cover_s3_key: S3 key for cover image

    Returns:
        Placeholder URL or None

    Examples:
        >>> get_presigned_cover_url_placeholder("releases/user/release/cover.jpg")
        's3://releases/user/release/cover.jpg'
        >>> get_presigned_cover_url_placeholder(None)

    """
    if not cover_s3_key:
        return None
    return f"s3://{cover_s3_key}"


def transform_release_to_response(release: Any, projects: list[Any] | None = None) -> dict[str, Any]:
    """
    Transform SongRelease model to response dictionary

    Args:
        release: SongRelease SQLAlchemy model
        projects: Optional list of assigned SongProject models

    Returns:
        Response dictionary

    Examples:
        >>> class MockRelease:
        ...     id = UUID("abc-123-def-456")
        ...     user_id = UUID("user-1")
        ...     type = "single"
        ...     name = "Test Song"
        ...     status = "draft"
        ...     genre = "Rock"
        ...     description = "A test song"
        ...     tags = "rock,test"
        ...     upload_date = None
        ...     release_date = None
        ...     downtaken_date = None
        ...     downtaken_reason = None
        ...     rejected_reason = None
        ...     upc = None
        ...     isrc = None
        ...     copyright_info = None
        ...     smart_link = None
        ...     cover_s3_key = None
        ...     created_at = None
        ...     updated_at = None
        >>> transform_release_to_response(MockRelease())
        {...}
    """

    # Convert date fields to ISO format
    def date_to_iso(d: date | None) -> str | None:
        return d.isoformat() if d else None

    # Base response
    response = {
        "id": str(release.id),
        "user_id": str(release.user_id),
        "type": release.type,
        "name": release.name,
        "status": release.status,
        "genre": release.genre,
        "description": release.description,
        "tags": release.tags,
        "upload_date": date_to_iso(release.upload_date),
        "release_date": date_to_iso(release.release_date),
        "downtaken_date": date_to_iso(release.downtaken_date),
        "downtaken_reason": release.downtaken_reason,
        "rejected_reason": release.rejected_reason,
        "upc": release.upc,
        "isrc": release.isrc,
        "copyright_info": release.copyright_info,
        "smart_link": release.smart_link,
        "cover_url": get_presigned_cover_url_placeholder(release.cover_s3_key),
        "created_at": release.created_at.isoformat() if release.created_at else None,
        "updated_at": release.updated_at.isoformat() if release.updated_at else None,
    }

    # Add assigned projects if provided
    if projects is not None:
        response["assigned_projects"] = [transform_project_to_assigned_response(project) for project in projects]

    return response


def transform_release_to_list_response(release: Any) -> dict[str, Any]:
    """
    Transform SongRelease model to list item response (minimal fields)

    Args:
        release: SongRelease SQLAlchemy model

    Returns:
        List item response dictionary

    Examples:
        >>> class MockRelease:
        ...     id = UUID("abc-123")
        ...     name = "Test Song"
        ...     type = "single"
        ...     status = "draft"
        ...     genre = "Rock"
        ...     release_date = None
        ...     cover_s3_key = None
        >>> transform_release_to_list_response(MockRelease())
        {'id': 'abc-123', 'name': 'Test Song', 'type': 'single', 'status': 'draft', 'genre': 'Rock', 'release_date': None, 'cover_url': None}
    """

    def date_to_iso(d: date | None) -> str | None:
        return d.isoformat() if d else None

    return {
        "id": str(release.id),
        "name": release.name,
        "type": release.type,
        "status": release.status,
        "genre": release.genre,
        "release_date": date_to_iso(release.release_date),
        "cover_url": get_presigned_cover_url_placeholder(release.cover_s3_key),
    }


def transform_project_to_assigned_response(project: Any) -> dict[str, Any]:
    """
    Transform SongProject model to assigned project response

    Args:
        project: SongProject SQLAlchemy model

    Returns:
        Assigned project response dictionary

    Examples:
        >>> class MockProject:
        ...     id = UUID("project-1")
        ...     project_name = "My Song Project"
        ...     s3_prefix = "user-1/my-song-project/"
        ...     project_status = "progress"
        >>> transform_project_to_assigned_response(MockProject())
        {'id': 'project-1', 'project_name': 'My Song Project', 's3_prefix': 'user-1/my-song-project/', 'project_status': 'progress'}
    """
    return {
        "id": str(project.id),
        "project_name": project.project_name,
        "s3_prefix": project.s3_prefix,
        "project_status": project.project_status,
    }


def get_status_filter_values(status_filter: str) -> list[str] | None:
    """
    Get list of status values for a given filter group

    Args:
        status_filter: Filter group name ('all', 'progress', 'uploaded', 'released', 'archive')

    Returns:
        List of status values or None for no filter

    Examples:
        >>> get_status_filter_values("progress")
        ['arranging', 'mixing', 'mastering']
        >>> get_status_filter_values("archive")
        ['rejected', 'downtaken', 'archived']
        >>> get_status_filter_values("released")
        ['released']
        >>> get_status_filter_values("all")
    """
    filters = {
        "progress": ["arranging", "mixing", "mastering", "pre_release"],
        "uploaded": ["uploaded"],
        "released": ["released"],
        "archive": ["rejected", "downtaken", "archived"],
    }

    return filters.get(status_filter)
