"""
Seed generation utilities for consistent image generation.
"""
from app.config import settings


def generate_char_seed(char_id: str) -> int:
    """
    Generate fixed seed for character consistency.

    Args:
        char_id: Character identifier (e.g., "char_1")

    Returns:
        Character seed
    """
    # Extract number from char_id
    try:
        char_num = int(char_id.split("_")[-1])
    except (ValueError, IndexError):
        char_num = 1

    # Use base seed + offset
    return settings.BASE_CHAR_SEED + char_num


def generate_bg_seed(scene_id: int) -> int:
    """
    Generate seed for background/scene.

    Args:
        scene_id: Scene sequence number

    Returns:
        Background seed
    """
    return settings.BG_SEED_BASE + scene_id
