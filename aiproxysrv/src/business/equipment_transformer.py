"""
Equipment Transformer - Business logic for equipment file operations.

CRITICAL: Pure functions for unit testing (NO orchestration, NO database, NO S3).
Business logic ONLY.
"""

import mimetypes

from utils.logger import logger


# Blocked extensions (executables and scripts)
BLOCKED_EXTENSIONS = {
    "exe",
    "dll",
    "bat",
    "sh",
    "cmd",
    "msi",
    "app",
    "dmg",
    "deb",
    "rpm",
    "run",
    "com",
    "scr",
    "vbs",
    "ps1",
    "jar",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB in bytes


def validate_file_extension(filename: str) -> tuple[bool, str | None]:
    """
    Validate file extension (block executables).

    Args:
        filename: Original filename with extension

    Returns:
        Tuple of (is_valid: bool, error_message: str | None)

    Example:
        >>> validate_file_extension("manual.pdf")
        (True, None)
        >>> validate_file_extension("installer.exe")
        (False, "File type '.exe' is not allowed (executables blocked)")
    """
    if "." not in filename:
        return False, "File must have an extension"

    extension = filename.rsplit(".", 1)[-1].lower()

    if extension in BLOCKED_EXTENSIONS:
        logger.warning("Blocked file extension", filename=filename, extension=extension)
        return False, f"File type '.{extension}' is not allowed (executables blocked)"

    return True, None


def validate_file_size(file_size: int) -> tuple[bool, str | None]:
    """
    Validate file size (max 50 MB).

    Args:
        file_size: File size in bytes

    Returns:
        Tuple of (is_valid: bool, error_message: str | None)

    Example:
        >>> validate_file_size(1024)
        (True, None)
        >>> validate_file_size(60 * 1024 * 1024)
        (False, "File size exceeds 50 MB limit")
    """
    if file_size > MAX_FILE_SIZE:
        logger.warning("File too large", file_size_mb=file_size / (1024 * 1024))
        return False, f"File size exceeds {MAX_FILE_SIZE // (1024 * 1024)} MB limit"

    return True, None


def generate_s3_attachment_key(user_id: str, equipment_id: str, attachment_id: str, filename: str) -> str:
    """
    Generate S3 key for equipment attachment.

    Args:
        user_id: User UUID
        equipment_id: Equipment UUID
        attachment_id: Attachment UUID
        filename: Original filename

    Returns:
        S3 key string

    Example:
        >>> generate_s3_attachment_key("user123", "eq456", "att789", "manual.pdf")
        'user123/eq456/att789_manual.pdf'
    """
    # Sanitize filename (keep extension)
    safe_filename = filename.replace(" ", "_").replace("/", "_")
    return f"{user_id}/{equipment_id}/{attachment_id}_{safe_filename}"


def get_content_type_from_filename(filename: str) -> str:
    """
    Determine MIME type from filename extension.

    Args:
        filename: Original filename

    Returns:
        MIME type string

    Example:
        >>> get_content_type_from_filename("manual.pdf")
        'application/pdf'
        >>> get_content_type_from_filename("screenshot.png")
        'image/png'
    """
    # Fallback to Python mimetypes
    guessed_type, _ = mimetypes.guess_type(filename)
    if guessed_type:
        return guessed_type

    # Default
    return "application/octet-stream"
