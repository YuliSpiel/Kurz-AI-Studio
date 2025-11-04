"""
Base interface for TTS providers.
"""
from abc import ABC, abstractmethod
from pathlib import Path


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    def generate_speech(
        self,
        text: str,
        voice_id: str,
        emotion: str = "neutral",
        output_filename: str = "output.mp3"
    ) -> Path:
        """
        Generate speech from text.

        Args:
            text: Text to synthesize
            voice_id: Voice profile identifier
            emotion: Emotion/style (provider-specific)
            output_filename: Output filename

        Returns:
            Path to generated audio file
        """
        pass

    @abstractmethod
    def list_voices(self) -> list:
        """
        List available voices.

        Returns:
            List of voice profiles
        """
        pass
