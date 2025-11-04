"""
Mubert music generation client (stub).
"""
import logging
from pathlib import Path

from app.providers.music.base import MusicProvider

logger = logging.getLogger(__name__)


class MubertClient(MusicProvider):
    """Mubert music generation provider (placeholder)."""

    def __init__(self, api_key: str):
        """
        Initialize Mubert client.

        Args:
            api_key: Mubert API key
        """
        self.api_key = api_key
        logger.info("Mubert client initialized (stub)")

    def generate_music(
        self,
        genre: str,
        mood: str,
        duration_ms: int,
        output_filename: str = "bgm.mp3"
    ) -> Path:
        """
        Generate music using Mubert (stub).

        TODO: Implement actual Mubert API integration.

        Args:
            genre: Music genre
            mood: Mood
            duration_ms: Duration
            output_filename: Output filename

        Returns:
            Path to generated audio file
        """
        logger.warning(
            f"Mubert BGM (stub): genre={genre}, mood={mood}, "
            f"duration={duration_ms}ms"
        )

        # Create placeholder
        output_dir = Path("app/data/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename

        output_path.touch()

        logger.info(f"Mubert stub: created placeholder at {output_path}")
        return output_path
