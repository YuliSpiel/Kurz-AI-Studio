"""
Local filesystem storage provider.
"""
import logging
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class LocalStorage:
    """Local filesystem storage."""

    def __init__(self, base_path: str = "app/data"):
        """
        Initialize local storage.

        Args:
            base_path: Base directory for storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local storage initialized: {self.base_path}")

    def save(self, source_path: str, dest_path: str) -> str:
        """
        Copy file to storage.

        Args:
            source_path: Source file path
            dest_path: Destination path (relative to base_path)

        Returns:
            Final path
        """
        source = Path(source_path)
        dest = self.base_path / dest_path

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)

        logger.info(f"Saved {source} to {dest}")
        return str(dest)

    def get_url(self, file_path: str) -> str:
        """
        Get URL for file (local path).

        Args:
            file_path: File path

        Returns:
            File URL (local path)
        """
        return str(self.base_path / file_path)

    def delete(self, file_path: str):
        """Delete file from storage."""
        path = self.base_path / file_path
        if path.exists():
            path.unlink()
            logger.info(f"Deleted {path}")
