"""
Font management utilities for MoviePy text rendering.
"""
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

# Font directory
FONTS_DIR = Path(__file__).parent.parent / "assets" / "fonts"
FONTS_DIR.mkdir(parents=True, exist_ok=True)

# Default font fallback (system font that supports Korean)
DEFAULT_FONT = "AppleGothic"  # macOS system font with Korean support


def get_available_fonts() -> List[Dict[str, str]]:
    """
    Get list of available custom fonts from the fonts directory.

    Returns:
        List of dicts with font info: [{"id": "KimjungchulGothic-Regular", "name": "김중철고딕 Regular", "path": "/path/to/font.ttf"}, ...]
    """
    fonts = []

    # Check custom fonts directory
    if FONTS_DIR.exists():
        for font_file in FONTS_DIR.glob("*.ttf"):
            font_id = font_file.stem  # Filename without extension
            friendly_name = FONT_NAME_MAPPING.get(font_id, font_id)
            fonts.append({
                "id": font_id,
                "name": friendly_name,
                "path": str(font_file)
            })

        for font_file in FONTS_DIR.glob("*.otf"):
            font_id = font_file.stem
            friendly_name = FONT_NAME_MAPPING.get(font_id, font_id)
            fonts.append({
                "id": font_id,
                "name": friendly_name,
                "path": str(font_file)
            })

    # Add system fonts with Korean support
    system_fonts = [
        {"id": "AppleGothic", "name": "Apple Gothic (시스템)", "path": "AppleGothic"},
        {"id": "AppleMyungjo", "name": "Apple Myungjo (시스템)", "path": "AppleMyungjo"},
    ]

    fonts.extend(system_fonts)

    logger.info(f"Found {len(fonts)} available fonts")
    return fonts


def get_font_path(font_id: str) -> str:
    """
    Get the file path for a font by its ID.

    Args:
        font_id: Font identifier (e.g., "NanumGothic", "AppleGothic")

    Returns:
        Path to font file, or default font if not found
    """
    # Check custom fonts first
    for ext in [".ttf", ".otf"]:
        font_path = FONTS_DIR / f"{font_id}{ext}"
        if font_path.exists():
            logger.info(f"Using custom font: {font_path}")
            return str(font_path)

    # Check if it's a system font
    system_fonts = ["AppleGothic", "AppleMyungjo", "Helvetica", "Arial"]
    if font_id in system_fonts:
        logger.info(f"Using system font: {font_id}")
        return font_id

    # Fallback to default
    logger.warning(f"Font '{font_id}' not found, using default: {DEFAULT_FONT}")
    return DEFAULT_FONT


# Friendly font name mapping (optional customization)
FONT_NAME_MAPPING = {
    "KimjungchulGothic-Regular": "김중철고딕 Regular",
    "KimjungchulGothic-Bold": "김중철고딕 Bold",
    "KimjungchulMyungjo-Regular": "김중철명조 Regular",
    "KimjungchulMyungjo-Bold": "김중철명조 Bold",
    "KimjungchulScript-Regular": "김중철손글씨 Regular",
    "KimjungchulScript-Bold": "김중철손글씨 Bold",
    "Paperlogy-4Regular": "Paperlogy Regular",
    "Paperlogy-7Bold": "Paperlogy Bold",
    "AppleGothic": "Apple Gothic (시스템)",
    "AppleMyungjo": "Apple Myungjo (시스템)",
}
