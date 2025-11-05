"""
CSV to JSON conversion utilities.
Handles plot planning CSV generation and conversion to final JSON schema.
"""
import logging
import csv
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

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
    Generate plot CSV from user prompt using GPT-4o-mini.

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

    # run_id가 이미 타임스탬프_프롬프트 형식으로 전달됨
    output_dir = Path(f"app/data/outputs/{run_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_filename = "plot.csv"
    csv_path = output_dir / csv_filename

    # GPT-4o-mini로 CSV 생성 시도
    try:
        from openai import OpenAI
        from app.config import settings

        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not set, using rule-based generation")
            raise ValueError("No OpenAI API key")

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # 시스템 프롬프트 작성
        system_prompt = f"""당신은 숏폼 영상 콘텐츠 시나리오 작가입니다.
사용자의 요청을 {num_cuts}개 장면으로 나누어 {'스토리' if mode == 'story' else '광고 콘텐츠'}를 만들어주세요.
등장인물은 {num_characters}명입니다.

각 장면마다 다음을 포함해야 합니다:
- scene_id: scene_1, scene_2, ... 형식
- sequence: 1, 2, 3, ... (장면 순서)
- char_id: char_1, char_2 (등장인물 ID)
- char_name: 캐릭터 이름 (창의적으로)
- text: 캐릭터의 대사 (자연스럽고 생동감 있게)
- emotion: neutral, happy, sad, excited, angry, surprised 중 하나
- subtitle_text: 화면에 표시될 자막 (간결하게)
- subtitle_position: top 또는 bottom
- duration_ms: 장면 지속시간 (보통 4000-6000)

**중요**: 반드시 CSV 형식으로만 출력하세요. 헤더와 데이터만 포함하고 다른 설명은 넣지 마세요.

CSV 형식:
scene_id,sequence,char_id,char_name,text,emotion,subtitle_text,subtitle_position,duration_ms"""

        logger.info(f"Calling GPT-4o-mini for plot generation...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1500
        )

        csv_content = response.choices[0].message.content.strip()

        # CSV 내용에서 마크다운 코드 블록 제거 (있을 경우)
        if csv_content.startswith("```"):
            lines = csv_content.split("\n")
            csv_content = "\n".join([line for line in lines if not line.startswith("```")])

        # CSV 파일로 저장
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_content.strip())

        logger.info(f"✅ CSV generated with GPT-4o-mini: {csv_path}")

        # CSV 검증 (행 개수 확인)
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            logger.info(f"Generated {len(rows)} scenes")

        return csv_path

    except Exception as e:
        logger.warning(f"GPT-4o-mini failed: {e}, falling back to rule-based generation")

        # 폴백: 룰 기반 생성
        rows = []
        char_names = ["주인공", "친구"] if num_characters == 2 else ["주인공"]

        for i in range(num_cuts):
            scene_id = f"scene_{i+1}"
            char_id = f"char_{(i % num_characters) + 1}"
            char_name = char_names[i % num_characters]

            if mode == "story":
                text = f"{prompt}의 {i+1}번째 장면입니다."
                subtitle = f"장면 {i+1}"
            else:
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
                "duration_ms": 5000
            })

        # CSV 작성
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            fieldnames = [
                "scene_id", "sequence", "char_id", "char_name", "text",
                "emotion", "subtitle_text", "subtitle_position", "duration_ms"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"CSV generated (rule-based fallback): {csv_path} ({len(rows)} rows)")
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

    # Write JSON (same folder as CSV)
    json_path = Path(csv_path).parent / "layout.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(shorts_json.model_dump(), f, indent=2, ensure_ascii=False)

    logger.info(f"JSON generated: {json_path}")
    return json_path
