"""S3 Storage - S3-compatible storage implementation (MinIO, AWS, Backblaze, Wasabi)"""

from io import BytesIO

import boto3
from botocore.exceptions import ClientError

from config.settings import S3_ACCESS_KEY, S3_BUCKET, S3_ENDPOINT, S3_REGION, S3_SECRET_KEY
from infrastructure.storage.storage_interface import StorageInterface
from utils.logger import logger


class S3Storage(StorageInterface):
    """S3-compatible storage implementation (works with MinIO, AWS S3, Backblaze B2, Wasabi)"""

    def __init__(self, bucket: str | None = None, skip_bucket_check: bool = False):
        """
        Initialize S3 client

        Args:
            bucket: Bucket name (optional). If None, uses S3_BUCKET from config.
            skip_bucket_check: If True, skip bucket existence check (for health checks or when MinIO might be down)
        """
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            region_name=S3_REGION,
        )
        self.bucket = bucket or S3_BUCKET

        # Ensure bucket exists (skip if explicitly disabled for graceful degradation)
        if not skip_bucket_check:
            self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            logger.debug("S3 bucket exists", bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                # Bucket doesn't exist, create it
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket)
                    logger.info("S3 bucket created", bucket=self.bucket)
                except ClientError as create_error:
                    logger.error("Failed to create S3 bucket", bucket=self.bucket, error=str(create_error))
                    raise
            else:
                logger.error("Failed to check S3 bucket", bucket=self.bucket, error=str(e))
                raise

    def upload(self, file_data: bytes | BytesIO, key: str, content_type: str = None) -> str:
        """Upload file to S3"""
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            # Convert bytes to BytesIO if needed
            if isinstance(file_data, bytes):
                file_data = BytesIO(file_data)

            self.s3_client.upload_fileobj(file_data, self.bucket, key, ExtraArgs=extra_args)
            logger.info("File uploaded to S3", key=key, bucket=self.bucket)
            return key

        except ClientError as e:
            logger.error("S3 upload failed", key=key, error=str(e))
            raise

    def download(self, key: str) -> bytes:
        """Download file from S3"""
        try:
            buffer = BytesIO()
            self.s3_client.download_fileobj(self.bucket, key, buffer)
            buffer.seek(0)
            logger.debug("File downloaded from S3", key=key)
            return buffer.read()

        except ClientError as e:
            logger.error("S3 download failed", key=key, error=str(e))
            raise

    def delete(self, key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            logger.info("File deleted from S3", key=key)
            return True

        except ClientError as e:
            logger.error("S3 delete failed", key=key, error=str(e))
            return False

    def exists(self, key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate pre-signed URL for file access"""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_in
            )
            logger.debug("Pre-signed URL generated", key=key, expires_in=expires_in)
            return url

        except ClientError as e:
            logger.error("Failed to generate presigned URL", key=key, error=str(e))
            raise

    def list_files(self, prefix: str) -> list[str]:
        """List files with given prefix"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)

            if "Contents" not in response:
                return []

            files = [obj["Key"] for obj in response["Contents"]]
            logger.debug("Listed files", prefix=prefix, count=len(files))
            return files

        except ClientError as e:
            logger.error("S3 list failed", prefix=prefix, error=str(e))
            return []

    def move(self, source_key: str, dest_key: str) -> bool:
        """Move file in S3 (copy + delete)"""
        try:
            # Copy to new location
            copy_source = {"Bucket": self.bucket, "Key": source_key}
            self.s3_client.copy_object(CopySource=copy_source, Bucket=self.bucket, Key=dest_key)
            logger.debug("File copied in S3", source=source_key, dest=dest_key)

            # Delete original
            self.s3_client.delete_object(Bucket=self.bucket, Key=source_key)
            logger.info("File moved in S3", source=source_key, dest=dest_key)
            return True

        except ClientError as e:
            logger.error("S3 move failed", source=source_key, dest=dest_key, error=str(e))
            return False

    def health_check(self, timeout: int = 2) -> tuple[bool, str]:
        """
        Quick health check for S3 storage backend (MinIO/AWS S3)

        Args:
            timeout: Connection timeout in seconds (default: 2s for fail-fast)

        Returns:
            Tuple of (is_healthy: bool, message: str)
            - (True, "OK") if storage is reachable
            - (False, error_message) if storage is down/unreachable

        Example:
            >>> storage = S3Storage()
            >>> healthy, msg = storage.health_check()
            >>> if not healthy:
            ...     print(f"Storage down: {msg}")
        """
        try:
            # Create temporary client with short timeout for health check
            # (don't use self.s3_client to avoid affecting normal operations)
            from botocore.config import Config

            config = Config(connect_timeout=timeout, read_timeout=timeout)
            health_client = boto3.client(
                "s3",
                endpoint_url=S3_ENDPOINT,
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY,
                region_name=S3_REGION,
                config=config,
            )

            # Quick check: head_bucket (doesn't transfer data, just metadata)
            health_client.head_bucket(Bucket=self.bucket)
            logger.debug("Storage health check OK", bucket=self.bucket, endpoint=S3_ENDPOINT)
            return True, "OK"

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = str(e)
            logger.warning("Storage health check failed (ClientError)", error_code=error_code, error=error_msg)
            return False, f"S3 error: {error_code}"

        except Exception as e:
            # Connection errors, timeouts, DNS failures, etc.
            error_msg = str(e)
            logger.warning("Storage health check failed (Connection)", error=error_msg, endpoint=S3_ENDPOINT)

            # Provide user-friendly error messages
            if "Could not connect" in error_msg or "Connection" in error_msg:
                return False, f"Cannot reach storage backend at {S3_ENDPOINT}"
            elif "timed out" in error_msg.lower():
                return False, f"Storage backend timeout ({S3_ENDPOINT})"
            else:
                return False, f"Storage backend error: {error_msg}"
