"""
Stub TTS client for testing without API keys.
Creates silent MP3 files as placeholders.
"""
import logging
from pathlib import Path

from app.providers.tts.base import TTSProvider

logger = logging.getLogger(__name__)


class StubTTSClient(TTSProvider):
    """Stub TTS provider that creates placeholder audio files."""

    def __init__(self):
        """Initialize stub TTS client."""
        logger.info("Stub TTS client initialized (no API key)")

    def list_voices(self) -> list:
        """Return stub voice list."""
        return [
            {"id": "default", "name": "Default Voice"},
            {"id": "stub1", "name": "Stub Voice 1"},
            {"id": "stub2", "name": "Stub Voice 2"}
        ]

    def generate_speech(
        self,
        text: str,
        voice_id: str = "default",
        emotion: str = "neutral",
        output_filename: str = "output.mp3"
    ) -> Path:
        """
        Generate placeholder audio file.

        Args:
            text: Text to synthesize (ignored)
            voice_id: Voice ID (ignored)
            emotion: Emotion (ignored)
            output_filename: Output filename

        Returns:
            Path to placeholder audio file
        """
        logger.warning(f"Stub TTS (no API): {text[:50]}...")

        # output_filename에 전체 경로가 이미 포함되어 있음
        output_path = Path(output_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create minimal silent MP3 file (valid MP3 header)
        # This is a 0.1 second silent MP3 at 44.1kHz
        silent_mp3_data = bytes.fromhex(
            "fff3600000000000000000000000000000000000"
            "49443303000000000000545353450000000300"
        )

        with open(output_path, "wb") as f:
            f.write(silent_mp3_data)

        logger.info(f"Stub TTS: created placeholder at {output_path}")
        return output_path
