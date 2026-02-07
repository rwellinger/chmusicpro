"""
S3 Proxy Service - Generic service for serving S3 resources via backend proxy.

CRITICAL Architecture Rule:
- Frontend MUST NEVER receive presigned URLs (MinIO, AWS, etc.)
- ALL S3 resources MUST be served via backend proxy routes
- This service provides generic resource streaming from S3 to browser

Usage:
    from adapters.s3.s3_proxy_service import s3_proxy_service

    # In Flask route:
    return s3_proxy_service.serve_resource(
        bucket="my-bucket",
        s3_key="path/to/file.jpg",
        filename="file.jpg"
    )
"""

import mimetypes
import traceback
from io import BytesIO

from flask import Response, send_file

from adapters.s3.mime_types_config import MIME_TYPE_MAPPING
from infrastructure.storage import get_storage
from utils.logger import logger


class S3ProxyService:
    """Generic service for proxying S3 resources to browser via backend"""

    @staticmethod
    def serve_resource(bucket: str, s3_key: str, filename: str) -> Response:
        """
        Stream S3 resource to browser (generic proxy method)

        Args:
            bucket: S3 bucket name
            s3_key: S3 object key (full path)
            filename: Original filename (for Content-Type detection)

        Returns:
            Flask Response with binary data

        Raises:
            Exception: If S3 download fails

        Example:
            >>> s3_proxy_service.serve_resource(
            ...     bucket="images",
            ...     s3_key="shared/abc-123.png",
            ...     filename="my-image.png"
            ... )
        """
        try:
            # Download from S3
            storage = get_storage(bucket=bucket)
            data = storage.download(s3_key)

            # Determine Content-Type from filename
            content_type = S3ProxyService._get_content_type(filename)

            logger.debug("Streaming S3 resource", bucket=bucket, s3_key=s3_key, content_type=content_type)

            return send_file(BytesIO(data), mimetype=content_type, as_attachment=False, download_name=filename)

        except Exception as e:
            logger.error(
                "Error serving S3 resource",
                bucket=bucket,
                s3_key=s3_key,
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            raise

    @staticmethod
    def _get_content_type(filename: str) -> str:
        """
        Determine Content-Type from filename extension using hybrid approach:
        1. Custom mapping (explicit control for critical formats)
        2. Python mimetypes library (automatic fallback)
        3. Default to 'application/octet-stream'

        Args:
            filename: Original filename

        Returns:
            MIME type string

        Examples:
            >>> S3ProxyService._get_content_type("image.png")
            'image/png'
            >>> S3ProxyService._get_content_type("photo.jpg")
            'image/jpeg'
            >>> S3ProxyService._get_content_type("project.cpr")
            'application/x-cubase-project'
            >>> S3ProxyService._get_content_type("archive.zip")
            'application/zip'
            >>> S3ProxyService._get_content_type("unknown.xyz")
            'application/octet-stream'
        """
        extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

        # 1. Custom mapping first (guaranteed behavior for critical formats)
        if extension in MIME_TYPE_MAPPING:
            return MIME_TYPE_MAPPING[extension]

        # 2. Fallback to Python's mimetypes library (automatic support)
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type:
            return guessed_type

        # 3. Ultimate fallback (binary data)
        return "application/octet-stream"


# Singleton instance
s3_proxy_service = S3ProxyService()
