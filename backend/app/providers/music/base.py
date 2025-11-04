"""
Base interface for music/BGM providers.
"""
from abc import ABC, abstractmethod
from pathlib import Path


class MusicProvider(ABC):
    """Abstract base class for music generation providers."""

    @abstractmethod
    def generate_music(
        self,
        genre: str,
        mood: str,
        duration_ms: int,
        output_filename: str = "bgm.mp3"
    ) -> Path:
        """
        Generate background music.

        Args:
            genre: Music genre (e.g., ambient, cinematic, upbeat)
            mood: Mood/emotion (e.g., calm, energetic, mysterious)
            duration_ms: Duration in milliseconds
            output_filename: Output filename

        Returns:
            Path to generated audio file
        """
        pass
