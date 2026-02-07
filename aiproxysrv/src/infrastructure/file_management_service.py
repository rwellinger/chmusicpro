"""File Management Service - Handles file operations for the application"""

import os
from pathlib import Path

import requests

from utils.logger import logger


class FileDownloadError(Exception):
    """Custom exception for file download errors"""

    pass


class FileManagementService:
    """Service for file management operations"""

    def download_and_save_file(self, url: str, file_path: Path, timeout: int = 30) -> None:
        """
        Download file from URL and save to filesystem

        Args:
            url: URL to download from
            file_path: Local path where to save the file
            timeout: Request timeout in seconds

        Raises:
            FileDownloadError: If download or save fails
        """
        try:
            logger.info(f"Downloading file from {url}")
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save file
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"File downloaded and saved to: {file_path}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed for {url}: {e}")
            raise FileDownloadError(f"Download failed: {e}") from e
        except OSError as e:
            logger.error(f"File save failed for {file_path}: {e}")
            raise FileDownloadError(f"Save failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            raise FileDownloadError(f"Unexpected error: {e}") from e

    def delete_file_if_exists(self, file_path: str | None) -> bool:
        """
        Delete file if it exists

        Args:
            file_path: Path to the file to delete

        Returns:
            True if file was deleted or didn't exist, False if deletion failed
        """
        if not file_path:
            return True

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.debug(f"File doesn't exist, nothing to delete: {file_path}")
                return True

        except OSError as e:
            logger.warning(f"Could not delete file {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file {file_path}: {e}")
            return False

    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists

        Args:
            file_path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        return os.path.exists(file_path) if file_path else False

    def get_file_size(self, file_path: str) -> int | None:
        """
        Get file size in bytes

        Args:
            file_path: Path to the file

        Returns:
            File size in bytes, or None if file doesn't exist
        """
        try:
            if self.file_exists(file_path):
                return os.path.getsize(file_path)
            return None
        except OSError:
            return None

    def ensure_directory_exists(self, directory_path: Path) -> None:
        """
        Ensure directory exists, create if necessary

        Args:
            directory_path: Path to the directory
        """
        try:
            directory_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {directory_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory_path}: {e}")
            raise
