"""
Stub music generation client for testing without API keys.
"""
import logging
from pathlib import Path

from app.providers.music.base import MusicProvider

logger = logging.getLogger(__name__)


class StubMusicClient(MusicProvider):
    """Stub music generation provider for testing."""

    def __init__(self, api_key: str = ""):
        """Initialize Stub music client."""
        self.api_key = api_key
        logger.info("Stub music client initialized (no API keys)")

    def generate_music(
        self,
        genre: str,
        mood: str,
        duration_ms: int,
        output_filename: str = "bgm.mp3"
    ) -> Path:
        """
        Generate stub music file (empty MP3).

        Args:
            genre: Music genre (e.g., ambient, cinematic)
            mood: Mood/emotion (e.g., calm, energetic)
            duration_ms: Duration in milliseconds
            output_filename: Output filename (full path or relative)

        Returns:
            Path to generated stub audio file
        """
        logger.warning(f"Stub BGM: {genre}, {mood}, {duration_ms}ms")

        # Convert to Path and ensure parent directory exists
        output_path = Path(output_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create empty MP3 file
        output_path.touch()

        logger.info(f"Stub BGM created: {output_path}")
        return output_path
