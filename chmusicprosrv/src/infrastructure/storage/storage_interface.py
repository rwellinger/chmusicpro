"""Storage Interface - Abstract Base Class for storage backends"""

from abc import ABC, abstractmethod
from typing import Any, BinaryIO


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
    def download_to_fileobj(self, key: str, fileobj: BinaryIO) -> None:
        """Stream file from storage directly into a file-like object."""
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

    @abstractmethod
    def create_multipart_upload(self, key: str, content_type: str | None = None) -> str:
        """
        Initiate a multipart upload session.

        Args:
            key: Storage key/path for the final object
            content_type: Optional MIME type

        Returns:
            Upload ID string (used to reference this upload session)
        """
        pass

    @abstractmethod
    def upload_part(self, key: str, upload_id: str, part_number: int, body: bytes | BinaryIO) -> str:
        """
        Upload a single part of a multipart upload.

        Args:
            key: Storage key/path (same as create_multipart_upload)
            upload_id: Upload ID from create_multipart_upload
            part_number: Part number (1-based, sequential)
            body: Binary data for this part

        Returns:
            ETag string for this part (needed for complete_multipart_upload)
        """
        pass

    @abstractmethod
    def complete_multipart_upload(self, key: str, upload_id: str, parts: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Complete a multipart upload by assembling all parts.

        Args:
            key: Storage key/path
            upload_id: Upload ID from create_multipart_upload
            parts: List of dicts with 'PartNumber' and 'ETag' for each uploaded part

        Returns:
            Response dict with upload completion details
        """
        pass

    @abstractmethod
    def list_parts(self, key: str, upload_id: str) -> list[dict[str, Any]]:
        """
        List already-uploaded parts for a multipart upload (for resume).

        Args:
            key: Storage key/path
            upload_id: Upload ID from create_multipart_upload

        Returns:
            List of dicts with 'part_number' and 'etag' keys
        """
        pass

    @abstractmethod
    def abort_multipart_upload(self, key: str, upload_id: str) -> bool:
        """
        Abort a multipart upload and clean up uploaded parts.

        Args:
            key: Storage key/path
            upload_id: Upload ID from create_multipart_upload

        Returns:
            True if successful, False otherwise
        """
        pass
