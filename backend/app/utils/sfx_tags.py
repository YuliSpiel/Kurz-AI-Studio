"""
SFX tagging utilities.
Extracts mood tags for sound effects based on text and emotion.
"""
import logging
from typing import List

logger = logging.getLogger(__name__)


# Simple rule-based SFX tag mapping
EMOTION_SFX_MAP = {
    "happy": ["upbeat_chime", "sparkle"],
    "sad": ["soft_piano", "rain"],
    "excited": ["energetic_swoosh", "pop"],
    "calm": ["gentle_bell", "ambient_pad"],
    "neutral": ["subtle_whoosh"],
    "angry": ["tense_drone"],
    "surprised": ["impact", "rise"]
}


def extract_sfx_tags(text: str, emotion: str = "neutral") -> List[str]:
    """
    Extract SFX tags based on dialogue text and emotion.

    This is a simple rule-based implementation. In production, you could
    use an LLM to extract more nuanced tags.

    Args:
        text: Dialogue text
        emotion: Emotion label

    Returns:
        List of SFX tags
    """
    tags = []

    # Get emotion-based tags
    emotion_lower = emotion.lower()
    if emotion_lower in EMOTION_SFX_MAP:
        tags.extend(EMOTION_SFX_MAP[emotion_lower])

    # Add text-based tags (simple keyword matching)
    text_lower = text.lower()

    if any(word in text_lower for word in ["문", "열다", "닫다"]):
        tags.append("door")

    if any(word in text_lower for word in ["발소리", "걷다", "뛰다"]):
        tags.append("footsteps")

    if any(word in text_lower for word in ["바람", "공기"]):
        tags.append("wind")

    if any(word in text_lower for word in ["물", "바다", "강"]):
        tags.append("water")

    # Remove duplicates
    tags = list(set(tags))

    logger.debug(f"Extracted SFX tags for '{text[:30]}...': {tags}")

    return tags if tags else ["ambient"]


def extract_sfx_tags_llm(text: str, emotion: str = "neutral") -> List[str]:
    """
    Extract SFX tags using LLM (placeholder).

    TODO: Implement LLM-based tag extraction for more nuanced results.

    Args:
        text: Dialogue text
        emotion: Emotion label

    Returns:
        List of SFX tags
    """
    # Placeholder - would call LLM API here
    logger.info("LLM-based SFX extraction not yet implemented")
    return extract_sfx_tags(text, emotion)
