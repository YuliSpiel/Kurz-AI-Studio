"""
Local BGM selector: Selects the most appropriate BGM from local assets folder.
Uses Gemini to match bgm_prompt with available BGM files.
"""
import logging
import shutil
import json
import os
import requests
from pathlib import Path
from typing import Optional

from app.providers.music.base import MusicProvider
from app.config import settings

logger = logging.getLogger(__name__)

# BGM assets directory
BGM_ASSETS_DIR = Path(__file__).parent.parent.parent / "assets" / "bgms"


class LocalBGMClient(MusicProvider):
    """
    Selects BGM from local assets folder based on genre/mood matching.
    Uses Gemini to find the best match from available files.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LocalBGMClient.

        Args:
            api_key: Gemini API key for intelligent matching (optional)
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.bgm_dir = BGM_ASSETS_DIR

    def _get_available_bgms(self) -> list[str]:
        """Get list of available BGM files."""
        if not self.bgm_dir.exists():
            logger.warning(f"BGM directory not found: {self.bgm_dir}")
            return []

        bgms = [f.stem for f in self.bgm_dir.glob("*.mp3")]
        logger.info(f"Found {len(bgms)} BGM files in {self.bgm_dir}")
        return bgms

    def _select_bgm_with_gemini(self, prompt: str, available_bgms: list[str]) -> str:
        """
        Use Gemini to select the best matching BGM.

        Args:
            prompt: BGM prompt describing desired music
            available_bgms: List of available BGM filenames (without extension)

        Returns:
            Selected BGM filename (without extension)
        """
        if not self.api_key:
            logger.warning("No Gemini API key, falling back to simple matching")
            return self._simple_match(prompt, available_bgms)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"

        system_prompt = f"""You are a music curator. Given a BGM request and a list of available BGM files, select the BEST matching file.

Available BGM files (format: genre_mood_number):
{json.dumps(available_bgms, ensure_ascii=False)}

Return ONLY the exact filename from the list above (without .mp3 extension).
Do not explain, just return the filename.

Example:
- Request: "upbeat cheerful music for a fun video"
- Available: ["acoustic_cheerful_01", "jazz_noir_01", "kpop_upbeat_01"]
- Response: kpop_upbeat_01"""

        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt}\n\nBGM Request: {prompt}"}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 50}
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            selected = result["candidates"][0]["content"]["parts"][0]["text"].strip()

            # Validate selection
            if selected in available_bgms:
                logger.info(f"Gemini selected BGM: {selected}")
                return selected
            else:
                # Try to find partial match
                for bgm in available_bgms:
                    if selected.lower() in bgm.lower() or bgm.lower() in selected.lower():
                        logger.info(f"Gemini partial match: {bgm}")
                        return bgm

                logger.warning(f"Gemini returned invalid BGM '{selected}', falling back")
                return self._simple_match(prompt, available_bgms)

        except Exception as e:
            logger.error(f"Gemini BGM selection failed: {e}")
            return self._simple_match(prompt, available_bgms)

    def _simple_match(self, prompt: str, available_bgms: list[str]) -> str:
        """
        Simple keyword-based BGM matching fallback.

        Args:
            prompt: BGM prompt
            available_bgms: List of available BGM filenames

        Returns:
            Best matching BGM filename
        """
        prompt_lower = prompt.lower()

        # Keyword to genre/mood mapping
        keyword_scores = {}

        for bgm in available_bgms:
            score = 0
            bgm_lower = bgm.lower()

            # Check for keyword matches
            keywords = [
                ("acoustic", ["acoustic", "guitar", "folk", "warm", "gentle"]),
                ("kpop", ["kpop", "k-pop", "korean", "energetic", "dance"]),
                ("jazz", ["jazz", "saxophone", "noir", "smooth"]),
                ("piano", ["piano", "classical", "elegant", "emotional"]),
                ("orchestral", ["orchestra", "epic", "dramatic", "cinematic"]),
                ("cheerful", ["cheerful", "happy", "fun", "bright", "upbeat"]),
                ("melancholic", ["melancholic", "sad", "emotional", "touching"]),
                ("peaceful", ["peaceful", "calm", "relaxing", "serene"]),
                ("upbeat", ["upbeat", "energetic", "lively", "dynamic"]),
                ("warm", ["warm", "cozy", "heartwarming", "soft"]),
            ]

            for genre_key, keywords_list in keywords:
                if genre_key in bgm_lower:
                    for kw in keywords_list:
                        if kw in prompt_lower:
                            score += 2

            keyword_scores[bgm] = score

        # Return highest scoring or first available
        if keyword_scores:
            best_match = max(keyword_scores.items(), key=lambda x: x[1])
            if best_match[1] > 0:
                logger.info(f"Simple match selected: {best_match[0]} (score: {best_match[1]})")
                return best_match[0]

        # Default to first available
        default = available_bgms[0] if available_bgms else "acoustic_peaceful_01"
        logger.info(f"No match found, using default: {default}")
        return default

    def generate_music(
        self,
        genre: str,
        mood: str,
        duration_ms: int,
        output_filename: str = "bgm.mp3"
    ) -> Path:
        """
        Select and copy the most appropriate BGM from local assets.

        Args:
            genre: Music genre or full prompt
            mood: Mood/emotion (may be empty if genre contains full prompt)
            duration_ms: Duration in milliseconds (ignored for local files)
            output_filename: Output filename

        Returns:
            Path to copied audio file
        """
        # Combine genre and mood into prompt
        prompt = f"{genre} {mood}".strip() if mood else genre
        logger.info(f"LocalBGMClient: Selecting BGM for prompt: {prompt[:100]}...")

        # Get available BGMs
        available_bgms = self._get_available_bgms()

        if not available_bgms:
            raise FileNotFoundError(f"No BGM files found in {self.bgm_dir}")

        # Select best match
        selected_bgm = self._select_bgm_with_gemini(prompt, available_bgms)

        # Copy to output location
        source_path = self.bgm_dir / f"{selected_bgm}.mp3"
        output_path = Path(output_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_path, output_path)
        logger.info(f"LocalBGMClient: Copied {selected_bgm}.mp3 -> {output_path}")

        return output_path
