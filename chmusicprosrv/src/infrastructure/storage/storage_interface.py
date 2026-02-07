"""Storage Interface - Abstract Base Class for storage backends"""

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageInterface(ABC):
    """Abstract interface for storage backends (S3, Filesystem, etc.)"""

    @abstractmethod
    def upload(self, file_data: bytes | BinaryIO, key: str, content_type: str = None) -> str:
        """
        Upload file to storage

        Args:
            file_data: Binary file data or file-like object
            key: Storage key/path (e.g., 'projects/midnight-dreams/cover.png')
            content_type: Optional MIME type (e.g., 'image/png')

        Returns:
            Storage key where file was saved
        """
        pass

    @abstractmethod
    def download(self, key: str) -> bytes:
        """
        Download file from storage

        Args:
            key: Storage key/path

        Returns:
            File data as bytes
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete file from storage

        Args:
            key: Storage key/path

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if file exists in storage

        Args:
            key: Storage key/path

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Get accessible URL for file (pre-signed for S3)

        Args:
            key: Storage key/path
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Accessible URL (pre-signed for S3, direct for filesystem)
        """
        pass

    @abstractmethod
    def list_files(self, prefix: str) -> list[str]:
        """
        List files with given prefix

        Args:
            prefix: Key prefix (e.g., 'projects/midnight-dreams/')

        Returns:
            List of storage keys
        """
        pass

    @abstractmethod
    def move(self, source_key: str, dest_key: str) -> bool:
        """
        Move/rename file within storage (copy + delete)

        Args:
            source_key: Current storage key
            dest_key: New storage key

        Returns:
            True if successful, False otherwise
        """
        pass
