"""Storage Infrastructure - S3-only storage backend"""

from infrastructure.storage.s3_storage import S3Storage
from infrastructure.storage.storage_interface import StorageInterface


def get_storage(bucket: str | None = None) -> StorageInterface:
    """
    Get S3 storage instance

    Args:
        bucket: Optional bucket name. If None, uses default from config.

    Returns:
        S3Storage instance
    """
    return S3Storage(bucket=bucket)


# Convenience exports
__all__ = ["get_storage", "StorageInterface"]
