"""
Stub TTS client for testing without API keys.
Creates silent MP3 files as placeholders.
"""
import logging
from pathlib import Path

from pydub import AudioSegment
from pydub.generators import Sine

from app.providers.tts.base import TTSProvider

logger = logging.getLogger(__name__)

# Default stub audio duration in milliseconds (2 seconds)
STUB_DURATION_MS = 2000


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

        # Create 2-second silent MP3 file using pydub
        # Generate silent audio segment (2 seconds at 44.1kHz stereo)
        silent_audio = AudioSegment.silent(duration=STUB_DURATION_MS, frame_rate=44100)

        # Export as MP3
        silent_audio.export(str(output_path), format="mp3", bitrate="128k")

        logger.info(f"Stub TTS: created {STUB_DURATION_MS}ms placeholder at {output_path}")
        return output_path
