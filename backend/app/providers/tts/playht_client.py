"""
PlayHT TTS client implementation (stub).
"""
import logging
from pathlib import Path

from app.providers.tts.base import TTSProvider

logger = logging.getLogger(__name__)


class PlayHTClient(TTSProvider):
    """PlayHT TTS provider (placeholder implementation)."""

    def __init__(self, api_key: str):
        """
        Initialize PlayHT client.

        Args:
            api_key: PlayHT API key
        """
        self.api_key = api_key
        logger.info("PlayHT client initialized (stub)")

    def generate_speech(
        self,
        text: str,
        voice_id: str = "default",
        emotion: str = "neutral",
        output_filename: str = "output.mp3"
    ) -> Path:
        """
        Generate speech using PlayHT (stub).

        TODO: Implement actual PlayHT API integration.

        Args:
            text: Text to synthesize
            voice_id: Voice ID
            emotion: Emotion
            output_filename: Output filename

        Returns:
            Path to generated audio file
        """
        logger.warning(f"PlayHT TTS (stub): {text[:50]}...")

        # For now, create a placeholder file
        output_dir = Path("app/data/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename

        # Create empty file as placeholder
        output_path.touch()

        logger.info(f"PlayHT stub: created placeholder at {output_path}")
        return output_path

    def list_voices(self) -> list:
        """List available voices (stub)."""
        return [{"id": "default", "name": "Default Voice"}]
