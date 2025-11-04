"""
Suno music generation client (stub).
"""
import logging
from pathlib import Path

from app.providers.music.base import MusicProvider

logger = logging.getLogger(__name__)


class SunoClient(MusicProvider):
    """Suno music generation provider (placeholder)."""

    def __init__(self, api_key: str = ""):
        """Initialize Suno client."""
        self.api_key = api_key
        logger.info("Suno client initialized (stub)")

    def generate_music(
        self,
        genre: str,
        mood: str,
        duration_ms: int,
        output_filename: str = "bgm.mp3"
    ) -> Path:
        """Generate music using Suno (stub)."""
        logger.warning(f"Suno BGM (stub): {genre}, {mood}, {duration_ms}ms")

        output_dir = Path("app/data/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename
        output_path.touch()

        return output_path
