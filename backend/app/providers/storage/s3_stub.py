"""
S3/R2 storage provider (stub).
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class S3Storage:
    """S3-compatible storage (placeholder)."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        """
        Initialize S3 storage.

        TODO: Implement with boto3.

        Args:
            endpoint: S3 endpoint URL
            access_key: Access key
            secret_key: Secret key
            bucket: Bucket name
        """
        self.endpoint = endpoint
        self.bucket = bucket
        logger.info(f"S3 storage initialized (stub): {bucket}")

    def save(self, source_path: str, dest_path: str) -> str:
        """Upload file to S3 (stub)."""
        logger.warning(f"S3 save (stub): {source_path} -> {dest_path}")
        return dest_path

    def get_url(self, file_path: str) -> str:
        """Get public URL (stub)."""
        return f"{self.endpoint}/{self.bucket}/{file_path}"

    def delete(self, file_path: str):
        """Delete file (stub)."""
        logger.warning(f"S3 delete (stub): {file_path}")
