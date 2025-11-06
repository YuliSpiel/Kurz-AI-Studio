"""
Plot generation utilities with character separation.
Generates characters.json and plot.json from user prompts.
"""
import logging
import json
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


def generate_plot_with_characters(
    run_id: str,
    prompt: str,
    num_characters: int,
    num_cuts: int,
    mode: str = "story",
    characters: list = None
) -> Tuple[Path, Path]:
    """
    Generate characters.json and plot.json from user prompt using GPT-4o-mini.

    Args:
        run_id: Run identifier
        prompt: User prompt
        num_characters: Number of characters
        num_cuts: Number of scenes/cuts
        mode: story or ad
        characters: Optional list of user-provided character data (Story Mode)

    Returns:
        Tuple of (characters_json_path, plot_json_path)
    """
    logger.info(f"Generating plot with characters for: {prompt[:50]}...")

    output_dir = Path(f"app/data/outputs/{run_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    characters_path = output_dir / "characters.json"
    plot_path = output_dir / "plot.json"

    try:
        from openai import OpenAI
        from app.config import settings

        if not settings.OPENAI_API_KEY:
            raise ValueError("No OpenAI API key")

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Step 1: Generate or use provided characters
        if characters:
            # Story Mode: Use user-provided characters
            logger.info("Step 1: Using provided characters (Story Mode)...")
            characters_data = {
                "characters": [
                    {
                        "char_id": f"char_{i+1}",
                        "name": char["name"],
                        "appearance": char["appearance"],
                        "personality": char["personality"],
                        "voice_profile": "default",  # Will be matched by voice.py
                        "seed": 1002 + i,
                        "gender": char.get("gender", "other"),
                        "role": char.get("role", "")
                    }
                    for i, char in enumerate(characters)
                ]
            }
            with open(characters_path, "w", encoding="utf-8") as f:
                json.dump(characters_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Characters saved: {characters_path}")
        else:
            # Auto-generate characters
            char_prompt = f"""당신은 숏폼 영상 콘텐츠의 캐릭터 디자이너입니다.
사용자의 요청에 맞는 {num_characters}명의 캐릭터를 만들어주세요.

각 캐릭터마다 다음 정보를 JSON 형식으로 제공하세요:
- char_id: char_1, char_2, ... 형식
- name: 캐릭터 이름 (창의적으로)
- appearance: 외형 묘사 (이미지 생성 프롬프트용, 상세하게)
- personality: 성격/특징
- voice_profile: "default"
- seed: char_1은 1002, char_2는 1003, ...

**중요**:
- 반드시 JSON 형식으로만 출력
- appearance는 이미지 생성 프롬프트로 사용되므로 시각적 특징 상세 작성
- 해설자는 appearance를 "음성만 있는 해설자 (이미지 없음)"으로 설정

JSON 형식:
{{
  "characters": [
    {{
      "char_id": "char_1",
      "name": "캐릭터 이름",
      "appearance": "상세한 외형 묘사",
      "personality": "성격 설명",
      "voice_profile": "default",
      "seed": 1002
    }}
  ]
}}"""

            logger.info("Step 1: Generating characters...")
            char_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": char_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            char_json_content = char_response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if char_json_content.startswith("```"):
                lines = char_json_content.split("\n")
                char_json_content = "\n".join([line for line in lines if not line.startswith("```")])

            # Parse and save characters
            characters_data = json.loads(char_json_content)
            with open(characters_path, "w", encoding="utf-8") as f:
                json.dump(characters_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Characters generated: {characters_path}")

        # Step 2: Generate plot JSON
        char_names = ", ".join([c["name"] for c in characters_data["characters"]])
        char_list = "\n".join([f"- {c['char_id']}: {c['name']} ({c.get('role', c['personality'])})"
                               for c in characters_data["characters"]])

        # Use new schema for Story Mode
        if mode == "story":
            plot_prompt = f"""당신은 비주얼노벨 스타일 숏폼 영상 시나리오 작가입니다.
사용자의 스토리를 {num_cuts}개 장면으로 나누어 시나리오를 만들어주세요.

등장인물:
{char_list}

각 장면마다 다음 정보를 JSON 형식으로 제공하세요:
- scene_id: scene_1, scene_2, ... 형식
- char1_id: 첫 번째 캐릭터 ID (char_1, char_2, char_3 중 하나, 필수)
- char1_pos: 위치 (left, center, right 중 하나)
- char1_expression: 표정 (excited, happy, sad, angry, surprised, neutral, confident 등)
- char1_pose: 포즈 (standing, sitting, walking, pointing 등)
- char2_id: 두 번째 캐릭터 ID (선택, 없으면 null)
- char2_pos: 위치 (left, center, right 중 하나, char2_id가 있을 때만)
- char2_expression: 표정 (char2_id가 있을 때만)
- char2_pose: 포즈 (char2_id가 있을 때만)
- speaker: 발화자 (narration, char_1, char_2, char_3 중 하나)
- text: 대사 또는 해설 내용
- text_type: dialogue (대사) 또는 narration (해설)
- emotion: neutral, happy, sad, excited, angry, surprised 중 하나
- subtitle_position: top 또는 bottom
- duration_ms: 장면 지속시간 (4000-6000)
- background_img: 배경 이미지 생성 프롬프트 (예: "calm farm", "busy city street", "cozy bedroom")

**중요**:
- 반드시 JSON 형식으로만 출력
- 한 장면에 최대 2명의 캐릭터만 등장 가능
- speaker가 narration이면 char1_id에 해설자를 배치하고 char2_id는 null
- background_img는 간결한 영어 프롬프트로 작성 (5-10 단어)

JSON 형식:
{{
  "scenes": [
    {{
      "scene_id": "scene_1",
      "char1_id": "char_1",
      "char1_pos": "center",
      "char1_expression": "excited",
      "char1_pose": "standing",
      "char2_id": null,
      "char2_pos": null,
      "char2_expression": null,
      "char2_pose": null,
      "speaker": "char_1",
      "text": "안녕! 나는 용감한 고양이야!",
      "text_type": "dialogue",
      "emotion": "happy",
      "subtitle_position": "top",
      "duration_ms": 5000,
      "background_img": "sunny playground"
    }},
    {{
      "scene_id": "scene_2",
      "char1_id": "char_1",
      "char1_pos": "left",
      "char1_expression": "happy",
      "char1_pose": "standing",
      "char2_id": "char_2",
      "char2_pos": "right",
      "char2_expression": "surprised",
      "char2_pose": "standing",
      "speaker": "char_2",
      "text": "우주로 출발하자!",
      "text_type": "dialogue",
      "emotion": "excited",
      "subtitle_position": "bottom",
      "duration_ms": 4500,
      "background_img": "starry night sky"
    }}
  ]
}}"""
        else:
            # Legacy schema for normal/ad modes
            plot_prompt = f"""당신은 숏폼 영상 콘텐츠 시나리오 작가입니다.
사용자의 요청을 {num_cuts}개 장면으로 나누어 {'광고' if mode == 'ad' else '영상'}를 만들어주세요.

등장인물: {char_names}

각 장면마다 다음 정보를 JSON 형식으로 제공하세요:
- scene_id: scene_1, scene_2, ... 형식
- char_id: char_1, char_2 (등장인물 ID)
- expression: 표정 (excited, happy, sad, angry, surprised, neutral, amazed, confident, brave 등)
- pose: 포즈 (standing, sitting, walking, running, pointing, looking_up, fist_raised 등, 해설자는 none)
- text: 대사 또는 해설 내용
- text_type: dialogue (대사) 또는 narration (해설)
- emotion: neutral, happy, sad, excited, angry, surprised 중 하나
- subtitle_position: top 또는 bottom
- duration_ms: 장면 지속시간 (4000-6000)

**중요**:
- 반드시 JSON 형식으로만 출력
- 해설자의 expression/pose는 "none"으로 설정

JSON 형식:
{{
  "scenes": [
    {{
      "scene_id": "scene_1",
      "char_id": "char_1",
      "expression": "excited",
      "pose": "standing",
      "text": "안녕! 나는 용감한 고양이야!",
      "text_type": "dialogue",
      "emotion": "happy",
      "subtitle_position": "top",
      "duration_ms": 5000
    }},
    {{
      "scene_id": "scene_2",
      "char_id": "char_2",
      "expression": "happy",
      "pose": "walking",
      "text": "우주로 출발하자!",
      "text_type": "dialogue",
      "emotion": "excited",
      "subtitle_position": "bottom",
      "duration_ms": 4500
    }}
  ]
}}"""

        logger.info("Step 2: Generating plot...")
        plot_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": plot_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=2000
        )

        plot_json_content = plot_response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if plot_json_content.startswith("```"):
            lines = plot_json_content.split("\n")
            plot_json_content = "\n".join([line for line in lines if not line.startswith("```")])

        # Parse and save plot JSON
        plot_data = json.loads(plot_json_content)
        with open(plot_path, "w", encoding="utf-8") as f:
            json.dump(plot_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Plot generated: {plot_path}")
        logger.info(f"Generated {len(plot_data.get('scenes', []))} scenes")

        return characters_path, plot_path

    except Exception as e:
        logger.warning(f"GPT generation failed: {e}, using fallback")
        return _generate_fallback(output_dir, prompt, num_characters, num_cuts, mode, characters)


def _generate_fallback(
    output_dir: Path,
    prompt: str,
    num_characters: int,
    num_cuts: int,
    mode: str,
    characters: list = None
) -> Tuple[Path, Path]:
    """
    Fallback: rule-based generation when GPT fails.
    """
    characters_path = output_dir / "characters.json"
    plot_path = output_dir / "plot.json"

    # Generate simple characters
    if characters:
        # Use provided characters
        characters_data = {
            "characters": [
                {
                    "char_id": f"char_{i+1}",
                    "name": char["name"],
                    "appearance": char["appearance"],
                    "personality": char["personality"],
                    "voice_profile": "default",
                    "seed": 1002 + i,
                    "gender": char.get("gender", "other"),
                    "role": char.get("role", "")
                }
                for i, char in enumerate(characters)
            ]
        }
    else:
        # Auto-generate characters
        characters_data = {
            "characters": [
                {
                    "char_id": f"char_{i+1}",
                    "name": f"캐릭터 {i+1}",
                    "appearance": f"캐릭터 {i+1}의 외형",
                    "personality": f"캐릭터 {i+1}의 성격",
                    "voice_profile": "default",
                    "seed": 1002 + i
                }
                for i in range(num_characters)
            ]
        }

    with open(characters_path, "w", encoding="utf-8") as f:
        json.dump(characters_data, f, indent=2, ensure_ascii=False)

    # Generate simple plot
    scenes = []
    for i in range(num_cuts):
        scene_id = f"scene_{i+1}"
        char_id = f"char_{(i % num_characters) + 1}"

        if mode == "story":
            # Story Mode: Use new schema
            scenes.append({
                "scene_id": scene_id,
                "char1_id": char_id,
                "char1_pos": "center",
                "char1_expression": "neutral",
                "char1_pose": "standing",
                "char2_id": None,
                "char2_pos": None,
                "char2_expression": None,
                "char2_pose": None,
                "speaker": char_id,
                "text": f"{prompt}의 {i+1}번째 장면입니다.",
                "text_type": "dialogue",
                "emotion": "neutral" if i % 2 == 0 else "happy",
                "subtitle_position": "bottom" if i % 2 == 0 else "top",
                "duration_ms": 5000,
                "background_img": "simple background"
            })
        else:
            # Legacy schema for normal/ad modes
            scenes.append({
                "scene_id": scene_id,
                "char_id": char_id,
                "expression": "neutral",
                "pose": "standing",
                "text": f"{prompt}의 {i+1}번째 장면입니다.",
                "text_type": "dialogue",
                "emotion": "neutral" if i % 2 == 0 else "happy",
                "subtitle_position": "bottom" if i % 2 == 0 else "top",
                "duration_ms": 5000
            })

    plot_data = {"scenes": scenes}
    with open(plot_path, "w", encoding="utf-8") as f:
        json.dump(plot_data, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Fallback generation complete")
    return characters_path, plot_path
