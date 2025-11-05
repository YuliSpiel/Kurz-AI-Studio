"""
JSON conversion utilities with characters.json support.
"""
import logging
import csv
import json
from pathlib import Path
from typing import List, Dict

from app.utils.seeds import generate_char_seed, generate_bg_seed
from app.utils.sfx_tags import extract_sfx_tags

logger = logging.getLogger(__name__)


def convert_plot_to_json(
    csv_path: str,
    run_id: str,
    art_style: str = "파스텔 수채화",
    music_genre: str = "ambient"
) -> Path:
    """
    Convert plot CSV and characters.json to final layout JSON.

    Args:
        csv_path: Path to plot CSV file
        run_id: Run identifier
        art_style: Art style for image generation
        music_genre: Music genre for BGM

    Returns:
        Path to generated JSON file
    """
    logger.info(f"Converting plot to JSON: {csv_path}")

    csv_path = Path(csv_path)
    characters_json_path = csv_path.parent / "characters.json"

    # Read characters.json
    characters_data = []
    if characters_json_path.exists():
        logger.info(f"Loading characters from: {characters_json_path}")
        with open(characters_json_path, "r", encoding="utf-8") as f:
            char_json = json.load(f)
            characters_data = char_json.get("characters", [])
    else:
        logger.warning(f"characters.json not found, will extract from CSV")

    # Read plot CSV
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError("CSV is empty")

    # Build JSON structure
    from app.schemas.json_layout import (
        ShortsJSON, Timeline, Character, Scene, ImageSlot,
        Subtitle, DialogueLine, BGM
    )

    # Build characters list
    characters = []
    if characters_data:
        # Use characters from characters.json
        for char in characters_data:
            characters.append(
                Character(
                    char_id=char["char_id"],
                    name=char["name"],
                    persona=char.get("personality", f"{char['name']} 설정"),
                    voice_profile=char.get("voice_profile", "default"),
                    seed=char.get("seed", generate_char_seed(char["char_id"]))
                ).model_dump()
            )
    else:
        # Fallback: extract from CSV (old behavior)
        characters_set = set()
        for row in rows:
            char_id = row["char_id"]
            # Try char_name field (old CSV format)
            char_name = row.get("char_name", "Character")
            characters_set.add((char_id, char_name))

        for char_id, char_name in sorted(characters_set):
            characters.append(
                Character(
                    char_id=char_id,
                    name=char_name,
                    persona=f"{char_name} 설정",
                    voice_profile="default",
                    seed=generate_char_seed(char_id)
                ).model_dump()
            )

    # Build scenes
    scenes_data: Dict[str, List[dict]] = {}
    for row in rows:
        scene_id = row["scene_id"]
        if scene_id not in scenes_data:
            scenes_data[scene_id] = []
        scenes_data[scene_id].append(row)

    scenes = []
    total_duration = 0

    for scene_id, scene_rows in sorted(scenes_data.items(), key=lambda x: int(x[0].split("_")[1])):
        first_row = scene_rows[0]
        sequence = int(scene_id.split("_")[1])
        duration_ms = int(first_row["duration_ms"])
        total_duration += duration_ms

        # Create dialogue lines
        dialogue = []
        for idx, row in enumerate(scene_rows):
            line_id = f"{scene_id}_line_{idx+1}"
            dialogue.append(
                DialogueLine(
                    line_id=line_id,
                    char_id=row["char_id"],
                    text=row["text"],
                    emotion=row.get("emotion", "neutral"),
                    audio_url="",
                    start_ms=idx * 2000,
                    duration_ms=2000
                ).model_dump()
            )

        # Create subtitles
        subtitles = []
        if first_row.get("text"):
            text = first_row["text"]
            text_type = first_row.get("text_type", "dialogue")
            subtitle_text = f'"{text}"' if text_type == "dialogue" else text

            subtitles.append(
                Subtitle(
                    position=first_row.get("subtitle_position", "bottom"),
                    text=subtitle_text,
                    start_ms=0,
                    duration_ms=duration_ms
                ).model_dump()
            )

        # Create image slots
        # Get character's appearance from characters_data if available
        char_id = first_row["char_id"]
        char_appearance = ""
        if characters_data:
            for char in characters_data:
                if char["char_id"] == char_id:
                    char_appearance = char.get("appearance", "")
                    break

        expression = first_row.get("expression", "neutral")
        pose = first_row.get("pose", "standing")

        # Build image prompt
        if char_appearance and expression != "none" and pose != "none":
            image_prompt = f"{char_appearance}, {expression} expression, {pose} pose"
        elif char_appearance:
            image_prompt = char_appearance
        else:
            image_prompt = ""

        images = [
            ImageSlot(
                slot_id="center",
                type="character",
                ref_id=char_id,
                image_url="",  # Will be filled by designer
                z_index=1
            ).model_dump()
        ]

        # Store image_prompt in metadata (for designer task)
        images[0]["image_prompt"] = image_prompt

        # SFX
        sfx_list = []
        sfx_tags = extract_sfx_tags(first_row["text"], first_row.get("emotion", "neutral"))
        if sfx_tags:
            from app.schemas.json_layout import SFX
            sfx_list.append(
                SFX(
                    sfx_id=f"{scene_id}_sfx",
                    tags=sfx_tags,
                    audio_url="",
                    start_ms=0,
                    volume=0.5
                ).model_dump()
            )

        # Create scene
        scene = Scene(
            scene_id=scene_id,
            sequence=sequence,
            duration_ms=duration_ms,
            images=images,
            subtitles=subtitles,
            dialogue=dialogue,
            bgm=None,
            sfx=sfx_list,
            bg_seed=generate_bg_seed(sequence),
            transition="fade"
        )

        scenes.append(scene.model_dump())

    # Create timeline
    timeline = Timeline(
        total_duration_ms=total_duration,
        aspect_ratio="9:16",
        fps=30,
        resolution="1080x1920"
    )

    # Create final JSON
    shorts_json = ShortsJSON(
        project_id=run_id,
        title=f"AutoShorts {run_id}",
        mode="story",
        timeline=timeline.model_dump(),
        characters=characters,
        scenes=scenes,
        global_bgm=None,
        metadata={
            "art_style": art_style,
            "music_genre": music_genre,
            "generated_from": str(csv_path),
            "characters_file": str(characters_json_path) if characters_json_path.exists() else None
        }
    )

    # Write JSON
    json_path = csv_path.parent / "layout.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(shorts_json.model_dump(), f, indent=2, ensure_ascii=False)

    logger.info(f"✅ JSON generated: {json_path}")
    return json_path
