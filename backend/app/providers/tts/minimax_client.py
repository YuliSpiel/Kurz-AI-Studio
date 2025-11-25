"""
MiniMax TTS client implementation.
Uses speech-02-turbo model for Korean TTS.
"""
import logging
import json
from pathlib import Path
import httpx

from app.providers.tts.base import TTSProvider

logger = logging.getLogger(__name__)


class MiniMaxTTSClient(TTSProvider):
    """MiniMax TTS provider using speech-02-turbo model."""

    # Global endpoint (api.minimax.io) - NOT api.minimax.chat
    BASE_URL = "https://api.minimax.io/v1/t2a_v2"

    def __init__(self, api_key: str, group_id: str):
        """
        Initialize MiniMax TTS client.

        Args:
            api_key: MiniMax API key
            group_id: MiniMax Group ID
        """
        self.api_key = api_key
        self.group_id = group_id
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0
        )
        logger.info("MiniMax TTS client initialized")

    def generate_speech(
        self,
        text: str,
        voice_id: str = "Calm_Woman",
        emotion: str = "neutral",
        output_filename: str = "output.mp3"
    ) -> Path:
        """
        Generate speech using MiniMax speech-02-turbo.

        Args:
            text: Text to synthesize
            voice_id: Voice ID from mm_voices.json (e.g., "Calm_Woman", "Deep_Voice_Man")
            emotion: Emotion setting (neutral, happy, sad, angry, fear, surprise, disgust)
            output_filename: Output filename

        Returns:
            Path to generated audio file
        """
        logger.info(f"Generating speech with MiniMax: {text[:50]}... (voice={voice_id})")

        try:
            # Map default voice_id
            if voice_id == "default":
                voice_id = "Calm_Woman"  # Default Korean female voice

            # Build request URL
            url = f"{self.BASE_URL}?GroupId={self.group_id}"

            # Map emotion to MiniMax format
            mm_emotion = self._map_emotion(emotion)

            # Request payload for speech-02-turbo
            payload = {
                "model": "speech-02-turbo",
                "text": text,
                "stream": False,
                "voice_setting": {
                    "voice_id": voice_id,
                    "speed": 1.0,
                    "vol": 1.0,
                    "pitch": 0,
                    "emotion": mm_emotion
                },
                "audio_setting": {
                    "sample_rate": 32000,
                    "bitrate": 128000,
                    "format": "mp3"
                }
            }

            response = self.client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()

            # Check for errors
            if result.get("base_resp", {}).get("status_code") != 0:
                error_msg = result.get("base_resp", {}).get("status_msg", "Unknown error")
                raise Exception(f"MiniMax API error: {error_msg}")

            # Get audio data (hex encoded)
            audio_hex = result.get("data", {}).get("audio")
            if not audio_hex:
                raise Exception("No audio data in response")

            # Decode hex to bytes
            audio_bytes = bytes.fromhex(audio_hex)

            # Save audio
            output_path = Path(output_filename)

            if not output_path.parent or output_path.parent == Path('.'):
                output_dir = Path("app/data/outputs")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / output_filename
            else:
                output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            logger.info(f"Speech generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"MiniMax TTS failed: {e}")
            raise

    def _map_emotion(self, emotion: str) -> str:
        """Map generic emotion to MiniMax emotion format."""
        emotion_map = {
            "neutral": "neutral",
            "happy": "happy",
            "excited": "happy",
            "sad": "sad",
            "angry": "angry",
            "fear": "fear",
            "surprise": "surprise",
            "calm": "neutral",
            "warm": "neutral",
            "cool": "neutral",
            "disgust": "disgust"
        }
        return emotion_map.get(emotion.lower(), "neutral")

    def list_voices(self) -> list:
        """
        List available voices.
        Returns hardcoded list from mm_voices.json structure.
        """
        return [
            # Female voices
            {"voice_id": "Calm_Woman", "name": "Yuna", "gender": "female"},
            {"voice_id": "Inspirational_girl", "name": "Anna Kim", "gender": "female"},
            {"voice_id": "Wise_Woman", "name": "Rosa Oh", "gender": "female"},
            # Male voices
            {"voice_id": "Deep_Voice_Man", "name": "June", "gender": "male"},
            {"voice_id": "Patient_Man", "name": "Nobel Butler", "gender": "male"},
            {"voice_id": "Casual_Guy", "name": "Taemin", "gender": "male"},
        ]
