"""
CSV to JSON conversion utilities.
Handles plot planning CSV generation and conversion to final JSON schema.
"""
import logging
import csv
import json
from pathlib import Path
from typing import List, Dict

from app.utils.seeds import generate_char_seed, generate_bg_seed
from app.utils.sfx_tags import extract_sfx_tags

logger = logging.getLogger(__name__)


def generate_csv_from_prompt(
    run_id: str,
    prompt: str,
    num_characters: int,
    num_cuts: int,
    mode: str = "story"
) -> Path:
    """
    Generate plot CSV from user prompt.

    This is a placeholder implementation. In production, this would use
    an LLM (e.g., GPT-4) to generate structured plot data.

    Args:
        run_id: Run identifier
        prompt: User prompt
        num_characters: Number of characters
        num_cuts: Number of scenes/cuts
        mode: story or ad

    Returns:
        Path to generated CSV file
    """
    logger.info(f"Generating CSV for prompt: {prompt[:50]}...")

    # Output path
    output_dir = Path("app/data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{run_id}_plot.csv"

    # Generate simple plot structure (rule-based for now)
    # CSV columns: scene_id, sequence, char_id, text, emotion, subtitle_text, subtitle_position, duration_ms

    rows = []

    # Create character names based on num_characters
    char_names = ["주인공", "친구"] if num_characters == 2 else ["주인공"]

    # Generate simple scenes
    for i in range(num_cuts):
        scene_id = f"scene_{i+1}"
        char_id = f"char_{(i % num_characters) + 1}"
        char_name = char_names[i % num_characters]

        # Simple dialogue based on prompt
        if mode == "story":
            text = f"{prompt}의 {i+1}번째 장면입니다."
            subtitle = f"장면 {i+1}"
        else:  # ad
            text = f"{prompt}를 소개하는 {i+1}번째 내용입니다."
            subtitle = f"특징 {i+1}"

        emotion = "neutral" if i % 2 == 0 else "happy"

        rows.append({
            "scene_id": scene_id,
            "sequence": i + 1,
            "char_id": char_id,
            "char_name": char_name,
            "text": text,
            "emotion": emotion,
            "subtitle_text": subtitle,
            "subtitle_position": "bottom" if i % 2 == 0 else "top",
            "duration_ms": 5000  # 5 seconds per scene
        })

    # Write CSV
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "scene_id", "sequence", "char_id", "char_name", "text",
            "emotion", "subtitle_text", "subtitle_position", "duration_ms"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"CSV generated: {csv_path} ({len(rows)} rows)")
    return csv_path


def csv_to_json(
    csv_path: str,
    run_id: str,
    art_style: str = "파스텔 수채화",
    music_genre: str = "ambient"
) -> Path:
    """
    Convert plot CSV to final JSON schema.

    Args:
        csv_path: Path to CSV file
        run_id: Run identifier
        art_style: Art style for image generation
        music_genre: Music genre for BGM

    Returns:
        Path to generated JSON file
    """
    logger.info(f"Converting CSV to JSON: {csv_path}")

    # Read CSV
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError("CSV is empty")

    # Group rows by scene
    scenes_data: Dict[str, List[dict]] = {}
    characters_set = set()

    for row in rows:
        scene_id = row["scene_id"]
        char_id = row["char_id"]

        if scene_id not in scenes_data:
            scenes_data[scene_id] = []

        scenes_data[scene_id].append(row)
        characters_set.add((char_id, row.get("char_name", "Character")))

    # Build JSON structure
    from app.schemas.json_layout import (
        ShortsJSON, Timeline, Character, Scene, ImageSlot,
        Subtitle, DialogueLine, BGM
    )

    # Create characters
    characters = []
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

    # Create scenes
    scenes = []
    total_duration = 0

    for scene_id, scene_rows in sorted(scenes_data.items(), key=lambda x: int(x[0].split("_")[1])):
        first_row = scene_rows[0]
        sequence = int(first_row["sequence"])
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
                    audio_url="",  # Will be filled by voice task
                    start_ms=idx * 2000,  # Stagger by 2 seconds
                    duration_ms=2000
                ).model_dump()
            )

        # Create subtitles
        subtitles = []
        if first_row.get("subtitle_text"):
            subtitles.append(
                Subtitle(
                    position=first_row.get("subtitle_position", "bottom"),
                    text=first_row["subtitle_text"],
                    start_ms=0,
                    duration_ms=duration_ms
                ).model_dump()
            )

        # Create image slots (placeholder)
        images = [
            ImageSlot(
                slot_id="center",
                type="character",
                ref_id=first_row["char_id"],
                image_url="",  # Will be filled by designer task
                z_index=1
            ).model_dump()
        ]

        # SFX tags
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
            bgm=None,  # Will use global BGM
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
        global_bgm=None,  # Will be filled by composer task
        metadata={
            "art_style": art_style,
            "music_genre": music_genre,
            "generated_from": str(csv_path)
        }
    )

    # Write JSON
    json_path = Path(csv_path).parent / f"{run_id}_layout.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(shorts_json.model_dump(), f, indent=2, ensure_ascii=False)

    logger.info(f"JSON generated: {json_path}")
    return json_path
