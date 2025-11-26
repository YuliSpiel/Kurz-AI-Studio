"""
Plot generation utilities with character separation.
Generates characters.json and plot.json from user prompts.
"""

import logging
import json
import re
import time
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def _try_repair_json(json_str: str) -> Optional[str]:
    """
    Try to repair truncated JSON by adding missing brackets/braces.
    Returns repaired JSON string or None if repair fails.
    """
    json_str = json_str.strip()

    # Count brackets and braces
    open_braces = json_str.count("{")
    close_braces = json_str.count("}")
    open_brackets = json_str.count("[")
    close_brackets = json_str.count("]")

    # Add missing closing brackets/braces
    missing_braces = open_braces - close_braces
    missing_brackets = open_brackets - close_brackets

    if missing_braces < 0 or missing_brackets < 0:
        return None  # More closing than opening - can't repair

    # Check for unterminated strings
    in_string = False
    escape_next = False
    for char in json_str:
        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string

    # If string is unterminated, try to close it
    if in_string:
        json_str = json_str + '"'

    # Add missing brackets (brackets before braces)
    json_str = json_str + ("]" * missing_brackets) + ("}" * missing_braces)

    return json_str


def _parse_json_with_retry(json_str: str, description: str = "JSON", max_attempts: int = 3) -> dict:
    """
    Parse JSON with retry and repair logic.

    Args:
        json_str: JSON string to parse
        description: Description for logging
        max_attempts: Number of repair attempts

    Returns:
        Parsed JSON dict

    Raises:
        json.JSONDecodeError: If parsing fails after all attempts
    """
    # First try: direct parse
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"[{description}] Initial JSON parse failed: {e}")

    # Second try: repair and parse
    for attempt in range(max_attempts):
        repaired = _try_repair_json(json_str)
        if repaired:
            try:
                result = json.loads(repaired)
                logger.info(f"[{description}] JSON repaired successfully on attempt {attempt + 1}")
                return result
            except json.JSONDecodeError:
                logger.warning(f"[{description}] Repair attempt {attempt + 1} failed")

    # All attempts failed, raise original error
    raise json.JSONDecodeError(
        f"Failed to parse {description} after {max_attempts} repair attempts", json_str, 0
    )


def _is_url(text: str) -> bool:
    """Check if text is a URL."""
    return text.startswith(("http://", "https://", "www."))


# ============ 말투(Narrative Tone) 예시 ============
NARRATIVE_TONE_EXAMPLES = {
    "격식형": {
        "description": "정중하고 격식있는 '-입니다/합니다' 체",
        "examples": [
            "오늘은 특별한 날입니다.",
            "이 제품은 정말 놀랍습니다.",
            "여러분께 소개해 드리겠습니다.",
            "함께 알아보시겠습니다.",
        ],
    },
    "친근존댓말": {
        "description": "부드럽고 친근한 '-아요/-어요/-해요' 체",
        "examples": [
            "오늘은 특별한 날이에요.",
            "이거 진짜 대박이에요!",
            "같이 알아볼까요?",
            "너무 좋지 않아요?",
            "제가 직접 해봤어요.",
        ],
    },
    "서술형": {
        "description": "간결하고 담백한 '-함/-임/-다' 체 (뉴스, 다큐 스타일)",
        "examples": [
            "오늘은 특별한 날임.",
            "이 제품, 진짜 대박임.",
            "지금부터 알아봄.",
            "결론은 이러함.",
        ],
    },
    "친근한반말": {
        "description": "친구에게 말하듯 편한 반말 '-야/-지?/-잖아' 체",
        "examples": [
            "야, 이거 진짜 대박이야.",
            "너 이거 알아? 완전 신기하지?",
            "솔직히 이건 좀 별로잖아.",
            "근데 진짜 웃긴 건 말이야...",
        ],
    },
    "진지한나레이션": {
        "description": "다큐멘터리 내레이터처럼 진중하고 무게감 있는 톤",
        "examples": [
            "그날, 모든 것이 변하기 시작했다.",
            "아무도 예상하지 못한 일이 벌어졌다.",
            "이것은 단순한 우연이 아니었다.",
            "역사는 이 순간을 기억할 것이다.",
        ],
    },
    "코믹풍자": {
        "description": "밈, 드립, 병맛 유머가 섞인 재미있는 톤",
        "examples": [
            "ㅋㅋㅋ 이게 뭐야 진짜",
            "아니 이건 좀 너무한 거 아님? ㄹㅇ",
            "개웃기네 ㅋㅋㅋㅋㅋ",
            "뭐? 이게 된다고? 실화냐?",
        ],
    },
}

# ============ 전개 구조(Plot Structure) 예시 ============
PLOT_STRUCTURE_EXAMPLES = {
    "기승전결": {
        "description": "전통적인 4단 구성: 도입 → 전개 → 절정 → 결말",
        "structure": [
            "기(起): 상황 소개, 인물 등장",
            "승(承): 사건 전개, 갈등 심화",
            "전(轉): 반전 또는 클라이막스",
            "결(結): 해결 및 마무리",
        ],
    },
    "고구마사이다": {
        "description": "답답함(고구마) → 시원한 해결(사이다) 구조",
        "structure": [
            "고구마: 문제 상황 발생, 점점 답답해지는 전개",
            "고구마 심화: 상황이 더 꼬이거나 악화됨",
            "사이다 복선: 해결의 실마리 등장",
            "사이다: 통쾌한 해결, 카타르시스",
        ],
    },
    "3막구조": {
        "description": "시작 → 위기 → 해결의 3막 구성",
        "structure": [
            "1막: 설정과 인물 소개, 일상",
            "2막: 위기/갈등 발생, 긴장 고조",
            "3막: 해결과 변화, 새로운 균형",
        ],
    },
    "비교형": {
        "description": "Before-After 또는 A vs B 비교 구조",
        "structure": [
            "Before/A 상태: 이전 상황 또는 첫 번째 대상",
            "문제점/차이점: 무엇이 다른지 설명",
            "After/B 상태: 변화된 상황 또는 두 번째 대상",
            "결론: 비교 결과 및 인사이트",
        ],
    },
    "반전형": {
        "description": "예상을 뒤엎는 반전이 핵심인 구조",
        "structure": [
            "평범한 시작: 예상 가능한 전개",
            "복선 깔기: 나중에 의미가 드러날 힌트",
            "반전 직전: 긴장감 조성",
            "반전: 예상을 완전히 뒤엎는 결말",
        ],
    },
    "정보나열": {
        "description": "팁, 리스트, 정보를 순차적으로 나열하는 구조",
        "structure": [
            "인트로: 주제 소개 (예: '알아두면 좋은 3가지')",
            "정보 1: 첫 번째 항목 설명",
            "정보 2: 두 번째 항목 설명",
            "정보 3+: 추가 항목들 + 마무리",
        ],
    },
    "공감스토리": {
        "description": "공감 → 위로 → 희망으로 이어지는 감성 구조",
        "structure": [
            "공감: 시청자가 겪는 어려움/상황에 공감",
            "위로: 혼자가 아니라는 메시지",
            "전환: 새로운 시각이나 해결책 제시",
            "희망: 긍정적 마무리, 응원의 메시지",
        ],
    },
    "질문형": {
        "description": "질문으로 호기심을 자극하며 시작하는 구조",
        "structure": [
            "질문 제기: 궁금증 유발하는 질문",
            "힌트/단서: 답에 접근하는 과정",
            "답변 공개: 질문에 대한 해답",
            "추가 인사이트: 부가 정보나 마무리",
        ],
    },
    "루프형": {
        "description": "처음과 끝이 연결되는 순환 구조",
        "structure": [
            "시작 장면: 특정 상황/이미지로 시작",
            "과거/배경: 어떻게 여기까지 왔는지",
            "전개: 스토리 진행",
            "회귀: 처음 장면으로 돌아와 의미 부여",
        ],
    },
}


def _get_narrative_tone_instruction(tone: str) -> str:
    """Get detailed instruction for narrative tone with examples."""
    if tone not in NARRATIVE_TONE_EXAMPLES:
        return f"\n\n**말투/톤**: {tone}\n- 대사와 해설의 말투/어조를 반드시 이 톤에 맞춰 작성하세요.\n"

    info = NARRATIVE_TONE_EXAMPLES[tone]
    examples_str = "\n".join([f'  - "{ex}"' for ex in info["examples"]])

    return f"""

**말투/톤**: {tone}
- 설명: {info["description"]}
- 예시 문장:
{examples_str}
- ⚠️ 모든 대사(text)를 반드시 위 예시와 같은 말투로 작성하세요!
"""


def _get_plot_structure_instruction(structure: str) -> str:
    """Get detailed instruction for plot structure with examples."""
    if structure not in PLOT_STRUCTURE_EXAMPLES:
        return (
            f"\n**플롯 구조**: {structure}\n- 시나리오를 반드시 이 플롯 구조에 맞춰 전개하세요.\n"
        )

    info = PLOT_STRUCTURE_EXAMPLES[structure]
    structure_str = "\n".join([f"  {i+1}. {s}" for i, s in enumerate(info["structure"])])

    return f"""
**플롯 구조**: {structure}
- 설명: {info["description"]}
- 전개 순서:
{structure_str}
- ⚠️ 장면들을 반드시 위 구조에 맞춰 배치하세요!
"""


def generate_plot_with_characters(
    run_id: str,
    prompt: str,
    num_characters: int,
    num_cuts: int,
    mode: str = "story",
    characters: list = None,
    narrative_tone: str = None,
    plot_structure: str = None,
) -> Tuple[Path, Path]:
    """
    Generate characters.json and plot.json from user prompt using Gemini 2.5 Flash.

    Args:
        run_id: Run identifier
        prompt: User prompt
        num_characters: Number of characters (None = auto-detect from prompt)
        num_cuts: Number of scenes/cuts
        mode: story or ad
        characters: Optional list of user-provided character data (Story Mode)
        narrative_tone: Narrative tone/style (e.g., 격식형, 친근한반말, 진지한나레이션)
        plot_structure: Plot structure (e.g., 기승전결, 고구마사이다, 3막구조)

    Returns:
        Tuple of (characters_json_path, plot_json_path)
    """
    logger.info(f"Generating plot with characters for: {prompt[:50]}...")

    # Auto-detect character count if not specified
    if num_characters is None:
        logger.info("[AUTO-DETECT] num_characters not specified, LLM will decide based on prompt")

    output_dir = Path(f"app/data/outputs/{run_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    characters_path = output_dir / "characters.json"
    plot_path = output_dir / "plot.json"

    # Ad Mode: Check if prompt is a URL and scrape product info
    product_data = None
    product_images = []
    if mode == "ad" and _is_url(prompt):
        logger.info(f"[AD MODE] Detected product URL: {prompt}")
        try:
            from app.utils.product_scraper import scrape_product, download_product_images

            product_data = scrape_product(prompt)
            logger.info(f"[AD MODE] Scraped product: {product_data.get('name', 'Unknown')}")

            # Download product images if available
            if product_data.get("images"):
                logger.info(
                    f"[AD MODE] Downloading {len(product_data['images'])} product images..."
                )
                product_images = download_product_images(product_data["images"], str(output_dir))
                logger.info(f"[AD MODE] Downloaded {len(product_images)} product images")

            # Create enriched prompt from scraped data
            enriched_prompt = f"""제품명: {product_data['name']}
설명: {product_data['description'][:200] if product_data['description'] else '없음'}
특징: {', '.join(product_data['features'][:3]) if product_data['features'] else '없음'}
가격: {product_data['price'] if product_data['price'] else '미정'}

위 제품을 홍보하는 매력적인 광고 숏츠를 만들어주세요. 제품의 핵심 특징과 장점을 강조하세요."""

            # Replace prompt with enriched version
            prompt = enriched_prompt
            logger.info("[AD MODE] Using enriched prompt from scraped data")

        except Exception as e:
            logger.warning(f"[AD MODE] Failed to scrape product URL: {e}")
            # Continue with original URL as prompt (GPT will do its best)

    try:
        from app.providers.llm.gemini_llm_client import GeminiLLMClient
        from app.config import settings

        if not settings.GEMINI_API_KEY:
            raise ValueError("No Gemini API key")

        client = GeminiLLMClient(api_key=settings.GEMINI_API_KEY)

        # Step 1: Generate or use provided characters
        if characters:
            # Story Mode: Use user-provided characters
            logger.info("Step 1: Using provided characters (Story Mode)...")

            # Load voices config based on TTS provider
            import os

            logger.info(f"Plot generator CWD: {os.getcwd()}")

            voices_data = {}
            # Use mm_voices.json for MiniMax, voices.json for ElevenLabs/PlayHT
            if settings.TTS_PROVIDER == "minimax":
                voices_paths = [Path("mm_voices.json"), Path("../mm_voices.json")]
                logger.info("[TTS] Using MiniMax voices config")
            else:
                voices_paths = [Path("voices.json"), Path("../voices.json")]
                logger.info(f"[TTS] Using {settings.TTS_PROVIDER} voices config")

            for voices_path in voices_paths:
                abs_path = voices_path.absolute()
                exists = voices_path.exists()
                logger.info(f"Checking voices at: {abs_path} - exists: {exists}")
                if exists:
                    with open(voices_path, "r", encoding="utf-8") as f:
                        voices_data = json.load(f)
                    logger.info(f"✅ Loaded voices from {voices_path}")
                    break

            if not voices_data:
                logger.warning("❌ voices config not found, using default voices")

            female_voices = voices_data.get("voices", {}).get("female", [])
            male_voices = voices_data.get("voices", {}).get("male", [])

            characters_data = {"characters": []}

            # Default fallback voice based on TTS provider
            default_female_voice = (
                "Calm_Woman" if settings.TTS_PROVIDER == "minimax" else "xi3rF0t7dg7uN2M0WUhr"
            )

            for i, char in enumerate(characters):
                gender = char.get("gender", "female")

                # Match voice_id based on gender
                if gender == "male" and male_voices:
                    # Use first male voice (can be randomized if needed)
                    voice_id = male_voices[0]["voice_id"]
                    logger.info(
                        f"[{char['name']}] Gender: male → Voice: {male_voices[0]['name']} ({voice_id})"
                    )
                elif gender == "female" and female_voices:
                    # Use first female voice (can be randomized if needed)
                    voice_id = female_voices[0]["voice_id"]
                    logger.info(
                        f"[{char['name']}] Gender: female → Voice: {female_voices[0]['name']} ({voice_id})"
                    )
                else:
                    # Fallback to first female voice
                    voice_id = (
                        female_voices[0]["voice_id"] if female_voices else default_female_voice
                    )
                    logger.warning(
                        f"[{char['name']}] Gender: {gender} → Using fallback female voice"
                    )

                characters_data["characters"].append(
                    {
                        "char_id": f"char_{i+1}",
                        "name": char["name"],
                        "appearance": char["appearance"],
                        "personality": char.get("personality", "기본 성격"),
                        "voice_id": voice_id,
                        "seed": 1002 + i,
                        "gender": gender,
                        "role": char.get("role", ""),
                    }
                )

            with open(characters_path, "w", encoding="utf-8") as f:
                json.dump(characters_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Characters saved with gender-matched voices: {characters_path}")
        else:
            # Auto-generate characters
            # Load voices config based on TTS provider
            import os

            logger.info(f"Plot generator CWD (auto-gen): {os.getcwd()}")

            voices_data = {}
            # Use mm_voices.json for MiniMax, voices.json for ElevenLabs/PlayHT
            if settings.TTS_PROVIDER == "minimax":
                voices_paths = [Path("mm_voices.json"), Path("../mm_voices.json")]
                logger.info("[TTS] Using MiniMax voices config (auto-gen)")
            else:
                voices_paths = [Path("voices.json"), Path("../voices.json")]
                logger.info(f"[TTS] Using {settings.TTS_PROVIDER} voices config (auto-gen)")

            for voices_path in voices_paths:
                abs_path = voices_path.absolute()
                exists = voices_path.exists()
                logger.info(f"Checking voices at: {abs_path} - exists: {exists}")
                if exists:
                    with open(voices_path, "r", encoding="utf-8") as f:
                        voices_data = json.load(f)
                    logger.info(f"✅ Loaded voices from {voices_path}")
                    break

            if not voices_data:
                logger.warning("❌ voices config not found, using default voices")

            # Build voice options description
            female_voices = voices_data.get("voices", {}).get("female", [])
            male_voices = voices_data.get("voices", {}).get("male", [])

            voice_options = "사용 가능한 목소리:\n"
            voice_options += "여성:\n"
            for v in female_voices:
                voice_options += f"  - {v['voice_id']}: {v['name']} - {v['description']}\n"
            voice_options += "남성:\n"
            for v in male_voices:
                voice_options += f"  - {v['voice_id']}: {v['name']} - {v['description']}\n"

            # Build character count instruction
            if num_characters:
                char_count_instruction = (
                    f"사용자의 요청에 맞는 {num_characters}명의 캐릭터를 만들어주세요."
                )
            else:
                char_count_instruction = (
                    "사용자의 요청을 분석하여 적절한 수의 캐릭터를 만들어주세요 (1-5명 사이)."
                )

            char_prompt = f"""당신은 숏폼 영상 콘텐츠의 캐릭터 디자이너입니다.
{char_count_instruction}

{voice_options}

각 캐릭터마다 다음 정보를 JSON 형식으로 제공하세요:
- char_id: char_1, char_2, ... 형식
- name: 캐릭터 이름 (창의적으로)
- appearance: 외형 묘사 (이미지 생성 프롬프트용, **매우 상세하게** - 이 프롬프트가 캐릭터 일관성의 핵심입니다!)
- voice_id: 위 목소리 중 캐릭터에 어울리는 voice_id 선택
- seed: 각 캐릭터마다 고유한 정수 (1000-9999 범위, 캐릭터 이미지 일관성 유지에 사용됨)

**중요**:
- 반드시 JSON 형식으로만 출력
- appearance는 이미지 생성 프롬프트로 사용되며, **캐릭터가 재등장할 때 동일한 외형을 유지하는 핵심**입니다
  - 나이, 성별, 헤어스타일, 헤어 색상, 눈 색상, 피부톤, 체형, 의상 스타일 등을 구체적으로 묘사
  - 예: "25세 여성, 긴 검은 머리에 파란 눈동자, 밝은 피부톤, 날씬한 체형, 캐주얼 티셔츠와 청바지 착용"
- 해설자가 필요하면 char_id를 "narration"으로, appearance는 null로 설정
- voice_id는 반드시 위 목록에서 선택
- seed는 각 캐릭터마다 다른 값 (예: char_1은 1001, char_2는 2003 등)

JSON 형식:
{{
  "characters": [
    {{
      "char_id": "char_1",
      "name": "캐릭터 이름",
      "appearance": "25세 여성, 긴 검은 머리에 파란 눈동자, 밝은 피부톤, 날씬한 체형, 흰색 티셔츠와 청바지 착용",
      "voice_id": "xi3rF0t7dg7uN2M0WUhr",
      "seed": 1001
    }},
    {{
      "char_id": "narration",
      "name": "해설",
      "appearance": null,
      "voice_id": "uyVNoMrnUku1dZyVEXwD",
      "seed": 9999
    }}
  ]
}}"""

            logger.info("Step 1: Generating characters...")
            char_response_text = client.generate_text(
                messages=[
                    {"role": "system", "content": char_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,  # Increased for more diverse character generation
                max_tokens=2000,
                json_mode=True,  # Force valid JSON output from Gemini
            )

            char_json_content = char_response_text.strip()

            # Remove markdown code blocks if present
            if char_json_content.startswith("```"):
                lines = char_json_content.split("\n")
                char_json_content = "\n".join(
                    [line for line in lines if not line.startswith("```")]
                )

            # Parse and save characters (with retry logic for truncated JSON)
            characters_data = _parse_json_with_retry(char_json_content, "CHARACTERS")

            # Validate and fix voice_id
            valid_voice_ids = [v["voice_id"] for v in female_voices] + [
                v["voice_id"] for v in male_voices
            ]
            for char in characters_data.get("characters", []):
                if "voice_id" in char and char["voice_id"] not in valid_voice_ids:
                    # Invalid voice_id (e.g., "남성", "여성"), fix it based on gender
                    invalid_voice = char["voice_id"]
                    logger.warning(
                        f"Invalid voice_id '{invalid_voice}' for {char.get('name')}, fixing..."
                    )

                    # Infer gender from appearance or fallback to female (handle None values)
                    appearance = (char.get("appearance") or "").lower()
                    if any(keyword in invalid_voice for keyword in ["남성", "male", "man"]) or any(
                        keyword in appearance for keyword in ["male", "남성", "man", "수컷"]
                    ):
                        # Male voice
                        char["voice_id"] = (
                            male_voices[0]["voice_id"]
                            if male_voices
                            else female_voices[0]["voice_id"]
                        )
                        logger.info(f"  → Assigned male voice: {char['voice_id']}")
                    else:
                        # Female voice (default) - use provider-specific fallback
                        default_female = (
                            "Calm_Woman"
                            if settings.TTS_PROVIDER == "minimax"
                            else "xi3rF0t7dg7uN2M0WUhr"
                        )
                        char["voice_id"] = (
                            female_voices[0]["voice_id"] if female_voices else default_female
                        )
                        logger.info(f"  → Assigned female voice: {char['voice_id']}")

            with open(characters_path, "w", encoding="utf-8") as f:
                json.dump(characters_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Characters generated and validated: {characters_path}")

        # Step 2: Generate plot JSON
        char_names = ", ".join([c["name"] for c in characters_data["characters"]])
        char_list = "\n".join(
            [
                f"- {c['char_id']}: {c['name']} ({c.get('role', c.get('personality', '캐릭터'))})"
                for c in characters_data["characters"]
            ]
        )

        # Add detailed character information when user provides characters
        char_details = ""
        if characters:
            char_details = "\n\n캐릭터 세부정보 (반드시 이 설정 그대로 사용할 것):\n"
            for c in characters_data["characters"]:
                char_details += f"- {c['name']} ({c['char_id']})\n"
                char_details += f"  외형: {c['appearance']}\n"
                char_details += f"  성격: {c.get('personality', '기본 성격')}\n"
                if c.get("role"):
                    char_details += f"  역할: {c['role']}\n"
                char_details += "\n"

        # Build style instructions with detailed examples
        style_instructions = ""
        if narrative_tone:
            logger.info(f"Applying narrative tone: {narrative_tone}")
            style_instructions += _get_narrative_tone_instruction(narrative_tone)

        if plot_structure:
            logger.info(f"Applying plot structure: {plot_structure}")
            style_instructions += _get_plot_structure_instruction(plot_structure)

        # Use new schema for Story Mode
        logger.info(
            f"[DEBUG] Preparing plot generation: mode='{mode}', characters={'provided' if characters else 'None'}, num_cuts={num_cuts}"
        )
        if mode == "story":
            logger.info(
                "[DEBUG] ✅ Using STORY MODE prompt (char1_id/char2_id/speaker/background_img schema)"
            )
            plot_prompt = f"""당신은 비주얼노벨 스타일 숏폼 영상 시나리오 작가입니다.
사용자의 스토리를 {num_cuts}개 장면으로 나누어 시나리오를 만들어주세요.
{style_instructions}
등장인물:
{char_list}{char_details}

각 장면마다 다음 정보를 JSON 형식으로 제공하세요:
- scene_id: scene_1, scene_2, ... 형식
- char1_id: 첫 번째 캐릭터 ID (char_1, char_2, char_3 중 하나, 또는 null)
- char1_pos: 위치 (left, center, right 중 하나, 또는 "" = 이전 위치 유지)
- char1_expression: 표정 (excited, happy, sad, angry, surprised, neutral, confident 등, 또는 "" = 이전 표정 유지)
- char1_pose: 포즈 (standing, sitting, walking, pointing 등, 또는 "" = 이전 포즈 유지)
- char1_outfit: 의상 (프롬프트에서 명시적으로 변경 지시가 없으면 **반드시 ""로 설정하여 이전 의상 유지**)
- char2_id: 두 번째 캐릭터 ID (char_1, char_2, char_3 중 하나, 또는 null = 캐릭터 없음)
- char2_pos: 위치 (left, center, right 중 하나, 또는 "" = 이전 위치 유지)
- char2_expression: 표정 ("" = 이전 표정 유지)
- char2_pose: 포즈 ("" = 이전 포즈 유지)
- char2_outfit: 의상 (프롬프트에서 명시적으로 변경 지시가 없으면 **반드시 ""로 설정하여 이전 의상 유지**)
- speaker: 발화자 (narration, char_1, char_2, char_3 중 하나)
- text: 대사 또는 해설 내용
  - **⚠️ 중요: 공백 포함 최대 28자 이내로 작성** (자막 표시를 위해 짧게!)
  - 긴 대사는 여러 장면으로 나누어 작성 (같은 캐릭터/배경 재사용 가능)
- text_type: dialogue (대사) 또는 narration (해설)
- emotion: neutral, happy, sad, excited, angry, surprised 중 하나
- subtitle_position: 항상 "top" (자막은 항상 상단에 표시)
- duration_ms: 장면 지속시간 (4000-6000)
- background_img: 배경 이미지 생성 프롬프트 (예: "calm farm", "busy city street", 또는 "" = 이전 배경 유지)

**중요 규칙**:
1. **캐릭터 배치**:
   - 모든 장면에 모든 캐릭터를 넣지 마세요. 스토리 흐름에 따라 필요한 캐릭터만 배치
   - 혼자 독백하거나 클로즈업이 필요하면 char1_id만 사용하고 char2_id는 null
   - 두 캐릭터가 대화할 때만 char1_id와 char2_id 모두 사용
   - 해설(narration)일 때는 캐릭터 없이 배경만 보여줄 수 있음 (char1_id, char2_id 모두 null)

2. **위치 충돌 방지**:
   - 두 캐릭터가 동시에 등장하면 반드시 다른 위치에 배치 (예: char1_pos="left", char2_pos="right")
   - 한 명만 등장하면 "center" 사용 가능
   - 절대 같은 위치에 두 캐릭터를 배치하지 마세요 (겹침)

3. **배경 재사용 (매우 중요)**:
   - 배경은 분위기가 바뀔 때만 변경하세요
   - 같은 장소에서 계속 대화하면 background_img를 ""로 두어 이전 배경 유지
   - 장소 이동이나 시간 변화가 있을 때만 새로운 배경 프롬프트 작성

4. **표정/포즈/의상 재사용 (최우선 규칙 - 반드시 준수)**:
   ⚠️ 이미지 생성 비용을 절감하기 위해 반드시 이전 이미지를 최대한 재사용하세요!
   - 캐릭터의 표정(expression)이 이전 장면과 같으면 **반드시** ""로 설정
   - 캐릭터의 포즈(pose)가 이전 장면과 같으면 **반드시** ""로 설정
   - 캐릭터의 의상(outfit)은 프롬프트에서 명시적으로 변경 지시가 없으면 **무조건 ""로 설정** (99%의 경우)
   - 감정 변화가 명확할 때만 새로운 expression 값 입력
   - 액션이 있을 때만 새로운 pose 값 입력
   - 의상은 "파티복으로 갈아입는다", "잠옷으로 갈아입는다" 등 명확한 지시가 있을 때만 변경
   - 일반 대화 장면에서는 대부분 "" 사용 (같은 캐릭터가 연속 대화하면 거의 항상 재사용)

   **예시**:
   - Scene 1: char1_expression="neutral", char1_pose="standing", char1_outfit="school uniform"
   - Scene 2: char1_expression="", char1_pose="", char1_outfit="" ← 같은 캐릭터가 계속 말하면 전부 재사용
   - Scene 3: char1_expression="happy", char1_pose="", char1_outfit="" ← 표정만 바뀌면 표정만 변경
   - Scene 4: char1_expression="", char1_pose="pointing", char1_outfit="" ← 포즈만 바뀌면 포즈만 변경
   - Scene 5: char1_expression="excited", char1_pose="standing", char1_outfit="party dress" ← 의상 변경 지시가 있을 때만

5. **기타**:
   - 반드시 JSON 형식으로만 출력
   - background_img는 간결한 영어 프롬프트로 작성 (5-10 단어)
   - 위에 제공된 캐릭터 세부정보가 있다면 반드시 그 이름, 성격, 역할을 그대로 사용할 것

JSON 예시 (캐릭터 이미지 재사용 패턴에 주목):
{{
  "scenes": [
    {{
      "scene_id": "scene_1",
      "char1_id": "char_1",
      "char1_pos": "center",
      "char1_expression": "excited",
      "char1_pose": "standing",
      "char1_outfit": "casual t-shirt and jeans",
      "char2_id": null,
      "char2_pos": null,
      "char2_expression": null,
      "char2_pose": null,
      "char2_outfit": null,
      "speaker": "char_1",
      "text": "안녕! 나는 용감한 고양이야!",
      "text_type": "dialogue",
      "emotion": "happy",
      "subtitle_position": "top",
      "duration_ms": 5000,
      "background_img": "sunny playground with swings"
    }},
    {{
      "scene_id": "scene_2",
      "char1_id": "char_1",
      "char1_pos": "center",
      "char1_expression": "",
      "char1_pose": "",
      "char1_outfit": "",
      "char2_id": null,
      "char2_pos": null,
      "char2_expression": null,
      "char2_pose": null,
      "char2_outfit": null,
      "speaker": "char_1",
      "text": "오늘은 친구를 만나러 갈 거야!",
      "text_type": "dialogue",
      "emotion": "happy",
      "subtitle_position": "top",
      "duration_ms": 4500,
      "background_img": ""
    }},
    {{
      "scene_id": "scene_3",
      "char1_id": "char_1",
      "char1_pos": "left",
      "char1_expression": "happy",
      "char1_pose": "",
      "char1_outfit": "",
      "char2_id": "char_2",
      "char2_pos": "right",
      "char2_expression": "surprised",
      "char2_pose": "standing",
      "char2_outfit": "space suit with helmet",
      "speaker": "char_2",
      "text": "우주로 출발하자!",
      "text_type": "dialogue",
      "emotion": "excited",
      "subtitle_position": "top",
      "duration_ms": 4500,
      "background_img": ""
    }},
    {{
      "scene_id": "scene_4",
      "char1_id": "char_1",
      "char1_pos": "left",
      "char1_expression": "",
      "char1_pose": "",
      "char1_outfit": "",
      "char2_id": "char_2",
      "char2_pos": "right",
      "char2_expression": "",
      "char2_pose": "",
      "char2_outfit": "",
      "speaker": "char_1",
      "text": "좋아! 같이 가자!",
      "text_type": "dialogue",
      "emotion": "excited",
      "subtitle_position": "top",
      "duration_ms": 4000,
      "background_img": ""
    }},
    {{
      "scene_id": "scene_5",
      "char1_id": null,
      "char1_pos": null,
      "char1_expression": null,
      "char1_pose": null,
      "char1_outfit": null,
      "char2_id": null,
      "char2_pos": null,
      "char2_expression": null,
      "char2_pose": null,
      "char2_outfit": null,
      "speaker": "narration",
      "text": "그들은 함께 우주선을 타고 떠났다.",
      "text_type": "narration",
      "emotion": "neutral",
      "subtitle_position": "top",
      "duration_ms": 5000,
      "background_img": "starry night sky with rocket launching"
    }}
  ]
}}"""
        else:
            # General/Ad Mode: Simplified schema with unified image prompts
            logger.info(
                f"[DEBUG] ✅ Using GENERAL MODE prompt (image_prompt + speaker schema) for mode='{mode}'"
            )

            # Include character appearance details for consistency
            char_appearance_details = ""
            for c in characters_data["characters"]:
                if c.get("appearance"):
                    char_appearance_details += f"- {c['char_id']}: {c['appearance']}\n"

            plot_prompt = f"""당신은 숏폼 영상 콘텐츠 시나리오 작가입니다.
사용자의 요청을 **정확히 {num_cuts}개의 이미지(컷)**로 나누어 {'광고' if mode == 'ad' else '영상'}를 만들어주세요.
{style_instructions}
등장인물:
{char_list}

캐릭터 외형 (이미지 일관성 유지용 - 아래 변수로 참조할 것):
{char_appearance_details}

각 장면마다 다음 정보를 JSON 형식으로 제공하세요:
- scene_id: scene_1, scene_2, ... 형식
- image_prompt: 이미지 생성 프롬프트
  - **캐릭터가 등장하는 장면**: **반드시 캐릭터 변수 {{char_1}}, {{char_2}} 등을 사용**하세요
  - **예시**: "{{char_1}} + 웃으며 손을 흔들고 있는 모습 + 밝은 아침 햇살이 비치는 작은 마을 배경"
  - ⚠️ **중요**: 한 이미지 위에 여러 대사를 띄우고 싶다면, image_prompt를 빈 문자열 ""로 설정하세요
  - 새로운 이미지가 필요한 경우에만 image_prompt를 작성하세요
  - 해설만 있는 장면은 배경 묘사만 작성 (변수 사용 안함)
- text: 대사 또는 해설 내용
  - **⚠️ 중요: 공백 포함 최대 28자 이내로 작성** (자막 표시를 위해 짧게!)
  - 긴 대사는 여러 장면으로 나누어 작성 (같은 이미지 재사용 가능)
  - 대사일 경우 반드시 큰따옴표로 감싸기 (예: "안녕!")
  - 해설일 경우 큰따옴표 없이 작성
- speaker: {', '.join([c['char_id'] for c in characters_data['characters']])}, narration 중 하나
- duration_ms: 장면 지속시간 (4000-6000)

**⚠️⚠️⚠️ 최우선 규칙 - 이미지 개수 엄수 ⚠️⚠️⚠️**:
**반드시 정확히 {num_cuts}개의 서로 다른 새로운 이미지를 생성해야 합니다!**
- 총 장면 수는 {num_cuts}개 이상이어야 함 (같은 이미지에 여러 대사를 표시하는 경우)
- image_prompt가 비어있지 않은 장면이 **정확히 {num_cuts}개**
- ❌ 잘못된 예 (3개 컷 요청 시): scene_1(이미지), scene_2(이미지), scene_3("") → 2개만 생성됨!
- ✅ 올바른 예 (3개 컷 요청 시): scene_1(이미지1), scene_2(이미지2), scene_3(이미지3) → 3개 생성됨
- ✅ 또는: scene_1(이미지1), scene_2(""), scene_3(이미지2), scene_4(이미지3) → 3개 생성됨 (scene_2는 scene_1 재사용)

**중요 규칙**:
1. **캐릭터 일관성**:
   ⚠️ 캐릭터가 등장하는 장면에서는 **반드시 변수 {{char_1}}, {{char_2}} 등을 사용**하세요!
   - ❌ 잘못된 예: "28세 여성, 긴 검은 머리... + 웃으며 손을 흔드는 모습"
   - ✅ 올바른 예: "{{char_1}} + 웃으며 손을 흔드는 모습 + 밝은 배경"
   - 변수 뒤에 "+ 동작/표정 + 배경" 형식으로 작성
   - **절대로 캐릭터 외형 설명을 직접 작성하지 마세요 - 변수만 사용!**

2. **이미지 프롬프트**:
   - 캐릭터 장면: "{{변수}} + 동작/표정 + 배경" 형식으로 작성
   - 배경 장면 (캐릭터 없음): 배경 묘사만 작성
   - 이미지는 1:1 비율로 생성되며 화면 중앙에 배치됨

3. **텍스트 형식**:
   - speaker가 narration이 아닌 경우 text에 큰따옴표 추가
   - speaker가 narration인 경우 큰따옴표 없이 작성

4. **기타**:
   - 반드시 JSON 형식으로만 출력
   - title: 영상 제목 (간결하고 임팩트 있게, 10자 이내)
   - bgm_prompt도 포함 (음악 스타일, 장르, 분위기 등)

JSON 형식 (예시: 3개 컷을 요청받은 경우):
{{
  "title": "용감한 고양이의 모험",
  "bgm_prompt": "upbeat, cheerful, acoustic guitar, warm atmosphere",
  "scenes": [
    {{
      "scene_id": "scene_1",
      "image_prompt": "{{char_1}} + 신나게 웃으며 손을 흔들고 있는 모습 + 밝은 아침 햇살이 비치는 작은 마을 배경",
      "text": "\\"안녕! 나는 용감한 고양이야!\\"",
      "speaker": "char_1",
      "duration_ms": 5000
    }},
    {{
      "scene_id": "scene_2",
      "image_prompt": "",
      "text": "\\"모험을 떠나볼까?\\"",
      "speaker": "char_1",
      "duration_ms": 4000
    }},
    {{
      "scene_id": "scene_3",
      "image_prompt": "{{char_1}} + 배낭을 메고 숲 속 오솔길을 걷고 있는 모습 + 햇살이 나뭇잎 사이로 비치는 신비로운 숲 배경",
      "text": "그는 새로운 모험을 시작했다.",
      "speaker": "narration",
      "duration_ms": 5000
    }},
    {{
      "scene_id": "scene_4",
      "image_prompt": "{{char_1}} + 산 정상에서 팔을 벌리고 환호하는 모습 + 푸른 하늘과 구름이 펼쳐진 배경",
      "text": "\\"드디어 해냈어!\\"",
      "speaker": "char_1",
      "duration_ms": 4500
    }}
  ]
}}

위 예시에서:
- 이미지 1: scene_1 (새 이미지)
- 이미지 2: scene_3 (새 이미지) - scene_2는 scene_1 이미지 재사용
- 이미지 3: scene_4 (새 이미지)
→ 총 3개의 이미지(컷) 생성됨"""

        logger.info("Step 2: Generating plot...")
        plot_response_text = client.generate_text(
            messages=[
                {"role": "system", "content": plot_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=1.0,  # Increased for more creative and diverse plot generation
            max_tokens=8000,
            json_mode=True,  # Force valid JSON output from Gemini
        )

        plot_json_content = plot_response_text.strip()

        # Remove markdown code blocks if present
        if plot_json_content.startswith("```json"):
            plot_json_content = plot_json_content[7:]
        if plot_json_content.startswith("```"):
            plot_json_content = plot_json_content[3:]
        if plot_json_content.endswith("```"):
            plot_json_content = plot_json_content[:-3]
        plot_json_content = plot_json_content.strip()

        # Parse and save plot JSON (with retry logic for truncated JSON)
        try:
            plot_data = _parse_json_with_retry(plot_json_content, "PLOT")
            logger.info(f"Successfully parsed plot JSON: {len(plot_data.get('scenes', []))} scenes")
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed at position {e.pos}: {e.msg}")
            logger.error(f"Error at line {e.lineno}, column {e.colno}")
            logger.error(f"Raw JSON content (first 500 chars):\n{plot_json_content[:500]}")
            logger.error(f"Raw JSON content (last 500 chars):\n{plot_json_content[-500:]}")

            # Try to fix common JSON errors
            logger.info("Attempting to fix common JSON errors...")

            fixed_content = plot_json_content

            # Fix 1: Remove trailing commas
            fixed_content = fixed_content.replace(",\n]", "\n]").replace(",\n}", "\n}")
            fixed_content = fixed_content.replace(", ]", " ]").replace(", }", " }")

            # Fix 2: Handle unterminated strings by finding incomplete JSON
            # If the error is "Unterminated string", try to truncate to the last complete object
            if "Unterminated string" in e.msg or "Expecting ',' delimiter" in e.msg:
                logger.warning(
                    "Detected unterminated string or delimiter error - attempting truncation fix"
                )

                # Try to find the last complete scene object
                import re

                # Find all complete scene objects
                scene_pattern = r'\{\s*"scene_id"\s*:\s*"scene_\d+".+?\}\s*(?=,\s*\{|\s*\])'
                scenes = re.findall(scene_pattern, fixed_content, re.DOTALL)

                if scenes:
                    logger.info(f"Found {len(scenes)} potentially complete scene objects")
                    # Reconstruct JSON with only complete scenes
                    # Try to extract metadata (title, bgm_prompt)
                    title_match = re.search(r'"title"\s*:\s*"([^"]*)"', fixed_content)
                    bgm_match = re.search(r'"bgm_prompt"\s*:\s*"([^"]*)"', fixed_content)

                    reconstructed = "{\n"
                    if title_match:
                        reconstructed += f'  "title": "{title_match.group(1)}",\n'
                    if bgm_match:
                        reconstructed += f'  "bgm_prompt": "{bgm_match.group(1)}",\n'

                    reconstructed += '  "scenes": [\n'
                    reconstructed += ",\n".join(scenes)
                    reconstructed += "\n  ]\n}"

                    fixed_content = reconstructed
                    logger.info(f"Reconstructed JSON with {len(scenes)} complete scenes")

            # Fix 3: Ensure proper quote escaping in text fields
            # (Gemini sometimes forgets to escape quotes in text fields)

            try:
                plot_data = json.loads(fixed_content)
                logger.info("✅ Successfully parsed after JSON repair")
            except Exception as fix_error:
                logger.error(f"❌ Still failed after fixes: {fix_error}")
                # Save raw response for debugging
                debug_path = Path(f"app/data/outputs/{run_id}") / "plot_raw_response.txt"
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(plot_response_text)
                logger.error(f"Saved raw response to {debug_path} for debugging")

                # Try one more time: extract just the scenes array if possible
                logger.info("Final attempt: extracting scenes array only...")
                try:
                    scenes_match = re.search(r'"scenes"\s*:\s*\[(.*)\]', fixed_content, re.DOTALL)
                    if scenes_match:
                        scenes_str = scenes_match.group(1)
                        # Create minimal valid structure
                        minimal_json = f'{{"scenes": [{scenes_str}]}}'
                        plot_data = json.loads(minimal_json)
                        logger.info("✅ Successfully extracted scenes array")
                    else:
                        raise ValueError("Could not extract scenes array")
                except Exception as final_error:
                    logger.error(f"❌ Final extraction attempt failed: {final_error}")
                    raise  # Re-raise original error to trigger fallback

        # VALIDATION: Check if text/speaker/image_prompt fields are swapped (General/Ad Mode only)
        if mode in ["general", "ad"]:
            logger.info(
                "[VALIDATION] Checking for text/speaker/image_prompt field swap in General/Ad Mode..."
            )
            for scene in plot_data.get("scenes", []):
                text_value = scene.get("text", "")
                speaker_value = scene.get("speaker", "")
                image_prompt_value = scene.get("image_prompt", "")

                # Check 1: text and image_prompt swapped
                # - text should be dialogue (usually < 100 chars, has quotes)
                # - image_prompt should be image description (usually > 100 chars, no quotes)
                if len(text_value) > 100 and len(image_prompt_value) < 50:
                    logger.warning(
                        f"[VALIDATION] Detected text/image_prompt swap in {scene['scene_id']}"
                    )
                    logger.warning(
                        f"[VALIDATION]   text (len={len(text_value)}): '{text_value[:80]}...'"
                    )
                    logger.warning(
                        f"[VALIDATION]   image_prompt (len={len(image_prompt_value)}): '{image_prompt_value}'"
                    )
                    logger.warning(f"[VALIDATION] Swapping text <-> image_prompt")
                    scene["text"], scene["image_prompt"] = scene["image_prompt"], scene["text"]
                    # Update local variables after swap
                    text_value, image_prompt_value = scene["text"], scene["image_prompt"]

                # Check 2: speaker and text swapped
                # - speaker should be a char_id or "narration" (short string)
                # - text should be the actual dialogue/narration content (longer string)
                if len(speaker_value) > 30 or (speaker_value and "," in speaker_value):
                    logger.warning(
                        f"[VALIDATION] Detected speaker/text swap in {scene['scene_id']}: speaker='{speaker_value[:50]}...', text='{text_value}'"
                    )
                    logger.warning(f"[VALIDATION] Swapping text <-> speaker")
                    scene["text"], scene["speaker"] = scene["speaker"], scene["text"]

                # Check 3: if text is "narration" or a char_id, likely swapped with speaker
                if text_value in ["narration"] or text_value.startswith("char_"):
                    logger.warning(
                        f"[VALIDATION] Detected text='{text_value}' in {scene['scene_id']}, likely swapped"
                    )
                    logger.warning(f"[VALIDATION] Swapping text <-> speaker")
                    scene["text"], scene["speaker"] = scene["speaker"], scene["text"]

            logger.info("[VALIDATION] Field validation complete")

        # Add characters to plot.json for template substitution
        if mode in ["general", "ad"]:
            plot_data["characters"] = [
                {"char_id": c["char_id"], "name": c["name"], "description": c.get("appearance", "")}
                for c in characters_data.get("characters", [])
                if c.get("appearance")  # Exclude narration
            ]
            logger.info(
                f"[TEMPLATE] Added {len(plot_data.get('characters', []))} characters to plot.json for variable substitution"
            )

        # Store mode in plot.json for later retrieval (e.g., after server restart)
        plot_data["mode"] = mode
        logger.info(f"[PLOT] Mode '{mode}' stored in plot.json")

        with open(plot_path, "w", encoding="utf-8") as f:
            json.dump(plot_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Plot generated: {plot_path}")
        logger.info(f"Generated {len(plot_data.get('scenes', []))} scenes")

        return characters_path, plot_path

    except Exception as e:
        logger.warning(f"GPT generation failed: {e}, using fallback with mode='{mode}'")
        return _generate_fallback(output_dir, prompt, num_characters, num_cuts, mode, characters)


def generate_plot_pro_mode(
    run_id: str, prompt: str, num_cuts: int, narrative_tone: str = None, plot_structure: str = None
) -> Tuple[Path, Path]:
    """
    Generate plot.json for Pro Mode (Kling AI video generation).

    Pro Mode features:
    - Each scene has start_frame_prompt and end_frame_prompt (for image-to-video)
    - Fixed 5-second duration per scene
    - Text limited to ~20 characters (readable in 5 seconds)

    Args:
        run_id: Run identifier
        prompt: User prompt
        num_cuts: Number of scenes/cuts
        narrative_tone: Narrative tone/style
        plot_structure: Plot structure

    Returns:
        Tuple of (characters_json_path, plot_json_path)
    """
    from app.providers.llm.gemini_llm_client import GeminiLLMClient
    from app.config import settings

    logger.info(f"[PRO MODE] Generating plot for: {prompt[:50]}...")

    output_dir = Path(f"app/data/outputs/{run_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    characters_path = output_dir / "characters.json"
    plot_path = output_dir / "plot.json"

    if not settings.GEMINI_API_KEY:
        raise ValueError("No Gemini API key")

    client = GeminiLLMClient(api_key=settings.GEMINI_API_KEY)

    # Load voices config based on TTS provider
    voices_data = {}
    if settings.TTS_PROVIDER == "minimax":
        voices_paths = [Path("mm_voices.json"), Path("../mm_voices.json")]
        logger.info("[PRO MODE] Using MiniMax voices config")
    else:
        voices_paths = [Path("voices.json"), Path("../voices.json")]
        logger.info(f"[PRO MODE] Using {settings.TTS_PROVIDER} voices config")

    for voices_path in voices_paths:
        if voices_path.exists():
            with open(voices_path, "r", encoding="utf-8") as f:
                voices_data = json.load(f)
            logger.info(f"[PRO MODE] Loaded voices from {voices_path}")
            break

    female_voices = voices_data.get("voices", {}).get("female", [])
    male_voices = voices_data.get("voices", {}).get("male", [])

    # Build style instructions with detailed examples
    style_instructions = ""
    if narrative_tone:
        style_instructions += _get_narrative_tone_instruction(narrative_tone)
    if plot_structure:
        style_instructions += _get_plot_structure_instruction(plot_structure)

    # Step 1: Generate characters
    char_prompt = f"""당신은 숏폼 영상 콘텐츠의 캐릭터 디자이너입니다.
사용자의 요청에 맞는 1-3명의 캐릭터를 만들어주세요.

각 캐릭터마다 다음 정보를 JSON 형식으로 제공하세요:
- char_id: char_1, char_2, ... 형식
- name: 캐릭터 이름 (2-4글자)
- description: 외형 묘사 (50자 이내로 간결하게! 핵심 특징만)
- seed: 각 캐릭터마다 고유한 정수 (1000-9999)

**중요**: 반드시 완전한 JSON을 출력하세요. 중간에 끊지 마세요!

JSON 형식:
{{
  "characters": [
    {{
      "char_id": "char_1",
      "name": "이름",
      "description": "갈색 털의 카피바라, 온화한 눈, 둥근 체형",
      "seed": 1001
    }}
  ]
}}"""

    logger.info("[PRO MODE] Step 1: Generating characters...")

    # Retry logic for character generation (Gemini sometimes returns truncated JSON)
    max_api_retries = 3
    characters_data = None

    for api_attempt in range(max_api_retries):
        try:
            char_response = client.generate_text(
                messages=[
                    {"role": "system", "content": char_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                max_tokens=2000,
                json_mode=True,
            )

            char_json = char_response.strip()
            if char_json.startswith("```"):
                lines = char_json.split("\n")
                char_json = "\n".join([l for l in lines if not l.startswith("```")])

            # Use retry-enabled JSON parser
            characters_data = _parse_json_with_retry(char_json, "PRO_CHARACTERS")
            logger.info(
                f"[PRO MODE] Characters parsed successfully on API attempt {api_attempt + 1}"
            )
            break

        except json.JSONDecodeError as e:
            logger.warning(
                f"[PRO MODE] Character generation attempt {api_attempt + 1}/{max_api_retries} failed: {e}"
            )
            if api_attempt < max_api_retries - 1:
                time.sleep(1)  # Wait before retry
            else:
                raise ValueError(
                    f"Failed to generate valid characters JSON after {max_api_retries} attempts: {e}"
                )

    # Add voice_id to characters based on TTS provider
    default_female = "Calm_Woman" if settings.TTS_PROVIDER == "minimax" else "xi3rF0t7dg7uN2M0WUhr"
    default_narrator = (
        "Deep_Voice_Man" if settings.TTS_PROVIDER == "minimax" else "uyVNoMrnUku1dZyVEXwD"
    )

    for i, char in enumerate(characters_data.get("characters", [])):
        if female_voices:
            char["voice_id"] = female_voices[i % len(female_voices)]["voice_id"]
        else:
            char["voice_id"] = default_female

    # Add narrator
    characters_data["characters"].append(
        {
            "char_id": "narrator",
            "name": "내레이터",
            "description": None,
            "voice_id": male_voices[0]["voice_id"] if male_voices else default_narrator,
            "seed": 9999,
        }
    )

    with open(characters_path, "w", encoding="utf-8") as f:
        json.dump(characters_data, f, indent=2, ensure_ascii=False)

    logger.info(f"[PRO MODE] Characters saved: {characters_path}")

    # Build character list for plot prompt
    char_list = "\n".join(
        [
            f"- {{{c['char_id']}}}: {c['name']} - {c.get('description', '내레이터')}"
            for c in characters_data["characters"]
        ]
    )

    # Step 2: Generate Pro Mode plot
    plot_prompt = f"""당신은 Kling AI 영상 생성을 위한 시나리오 작가입니다.
사용자의 요청을 **정확히 {num_cuts}개의 5초 장면**으로 나누어주세요.
{style_instructions}

**Pro 모드 특징**:
- 각 장면은 정확히 5초 영상으로 생성됩니다
- 시작 프레임과 끝 프레임 이미지를 기반으로 AI가 그 사이 움직임을 생성합니다
- 자막은 5초 내에 읽을 수 있어야 합니다 (~20자)

등장인물 (변수로 사용):
{char_list}

각 장면마다 다음 정보를 JSON 형식으로 제공하세요:
- scene_id: scene_1, scene_2, ... 형식
- start_frame_prompt: 시작 프레임 이미지 프롬프트
  - **반드시 캐릭터 변수 {{char_1}}, {{char_2}} 등을 사용**
  - 형식: "{{변수}} + 동작/표정 + 배경"
- end_frame_prompt: 끝 프레임 이미지 프롬프트
  - 시작 프레임과 자연스럽게 이어지는 동작
  - 같은 캐릭터, 같은 배경, 다른 포즈/표정
- text: 자막 (5초 내 읽을 수 있도록 **최대 20자**)
- speaker: 화자 (char_1, char_2, narrator 등)
- duration_ms: 5000 (고정)

**중요 규칙**:
1. start_frame과 end_frame은 같은 배경, 같은 캐릭터여야 함
2. 동작이 자연스럽게 연결되어야 함 (예: 앉아있다 → 일어선다)
3. 텍스트는 반드시 20자 이내
4. 캐릭터 변수 반드시 사용
5. **[핵심!] 씬 N의 end_frame_prompt는 씬 N+1의 start_frame_prompt와 완전히 동일해야 함!**
   - 예: scene_1의 end_frame = scene_2의 start_frame
   - 이렇게 해야 영상이 끊김 없이 자연스럽게 연결됨

**Kling AI 영상 생성용 필드**:
- motion_prompt: 시작→끝 프레임 사이의 동작 설명 (영어로, 5-15 단어)
  - 예: "slowly opens eyes and looks around"
  - 예: "turns head to the right with a surprised expression"
- negative_prompt: 피해야 할 요소 (영어로)
  - 기본값: "blurry, shaky, distorted, low quality, sudden movement"
  - 씬에 따라 추가 가능: "text, watermark, logo"

JSON 형식 (씬 연결 예시):
{{
  "mode": "pro",
  "title": "영상 제목",
  "bgm_prompt": "음악 스타일 프롬프트",
  "characters": [
    {{ "char_id": "char_1", "name": "이름", "description": "외형 묘사" }}
  ],
  "scenes": [
    {{
      "scene_id": "scene_1",
      "start_frame_prompt": "{{char_1}} 창가에 앉아 책을 읽고 있다, 햇살 가득한 방",
      "end_frame_prompt": "{{char_1}} 고개를 들어 창밖을 바라본다, 햇살 가득한 방",
      "motion_prompt": "slowly lifts head from the book and looks out the window",
      "negative_prompt": "blurry, shaky, distorted, low quality, sudden movement",
      "text": "오늘도 평화로운 하루",
      "speaker": "narrator",
      "duration_ms": 5000
    }},
    {{
      "scene_id": "scene_2",
      "start_frame_prompt": "{{char_1}} 고개를 들어 창밖을 바라본다, 햇살 가득한 방",
      "end_frame_prompt": "{{char_1}} 미소 지으며 일어선다, 햇살 가득한 방",
      "motion_prompt": "smiles gently and stands up from the chair",
      "negative_prompt": "blurry, shaky, distorted, low quality, sudden movement",
      "text": "무언가 좋은 일이 있을 것 같아",
      "speaker": "char_1",
      "duration_ms": 5000
    }}
  ]
}}

**씬 연결 규칙**: scene_1.end_frame_prompt == scene_2.start_frame_prompt (동일해야 함!)"""

    logger.info("[PRO MODE] Step 2: Generating plot...")

    # Retry logic for plot generation
    plot_data = None
    for api_attempt in range(max_api_retries):
        try:
            plot_response = client.generate_text(
                messages=[
                    {"role": "system", "content": plot_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=1.0,
                max_tokens=8000,
                json_mode=True,
            )

            plot_json = plot_response.strip()
            if plot_json.startswith("```json"):
                plot_json = plot_json[7:]
            if plot_json.startswith("```"):
                plot_json = plot_json[3:]
            if plot_json.endswith("```"):
                plot_json = plot_json[:-3]

            # Use retry-enabled JSON parser
            plot_data = _parse_json_with_retry(plot_json.strip(), "PRO_PLOT")
            logger.info(f"[PRO MODE] Plot parsed successfully on API attempt {api_attempt + 1}")
            break

        except json.JSONDecodeError as e:
            logger.warning(
                f"[PRO MODE] Plot generation attempt {api_attempt + 1}/{max_api_retries} failed: {e}"
            )
            if api_attempt < max_api_retries - 1:
                time.sleep(1)
            else:
                raise ValueError(
                    f"Failed to generate valid plot JSON after {max_api_retries} attempts: {e}"
                )

    # Add characters from characters_data for template substitution
    plot_data["characters"] = [
        {"char_id": c["char_id"], "name": c["name"], "description": c.get("description", "")}
        for c in characters_data.get("characters", [])
        if c.get("description")  # Exclude narrator
    ]

    # Ensure mode is set
    plot_data["mode"] = "pro"

    with open(plot_path, "w", encoding="utf-8") as f:
        json.dump(plot_data, f, indent=2, ensure_ascii=False)

    logger.info(f"[PRO MODE] Plot saved: {plot_path}")
    logger.info(f"[PRO MODE] Generated {len(plot_data.get('scenes', []))} scenes")

    return characters_path, plot_path


def _generate_fallback(
    output_dir: Path,
    prompt: str,
    num_characters: int,
    num_cuts: int,
    mode: str,
    characters: list = None,
) -> Tuple[Path, Path]:
    """
    Fallback: rule-based generation when GPT fails.
    """
    from app.config import settings

    logger.info(f"[DEBUG] Fallback generation: mode='{mode}', num_cuts={num_cuts}")
    characters_path = output_dir / "characters.json"
    plot_path = output_dir / "plot.json"

    # Generate simple characters with default voices based on TTS provider
    if settings.TTS_PROVIDER == "minimax":
        # MiniMax voice IDs
        default_female_voice = "Calm_Woman"  # Yuna
        default_male_voice = "Deep_Voice_Man"  # June
        narration_voice = "Inspirational_girl"  # Anna Kim
        logger.info("[FALLBACK] Using MiniMax default voices")
    else:
        # ElevenLabs voice IDs
        default_female_voice = "xi3rF0t7dg7uN2M0WUhr"  # Yuna
        default_male_voice = "3MTvEr8xCMCC2mL9ujrI"  # June
        narration_voice = "uyVNoMrnUku1dZyVEXwD"  # Anna Kim
        logger.info(f"[FALLBACK] Using {settings.TTS_PROVIDER} default voices")

    if characters:
        # Use provided characters
        characters_data = {
            "characters": [
                {
                    "char_id": f"char_{i+1}",
                    "name": char["name"],
                    "appearance": char["appearance"],
                    "voice_id": (
                        default_female_voice
                        if char.get("gender") == "female"
                        else default_male_voice
                    ),
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
                    "voice_id": default_female_voice,
                }
                for i in range(num_characters)
            ]
            + [
                {
                    "char_id": "narration",
                    "name": "해설",
                    "appearance": None,
                    "voice_id": narration_voice,
                }
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
            # Story Mode: Use char1_id/char2_id schema
            logger.debug(f"[DEBUG] Fallback: generating story mode scene {i+1}")
            scenes.append(
                {
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
                    "text": f"장면 {i+1}",
                    "text_type": "dialogue",
                    "emotion": "neutral" if i % 2 == 0 else "happy",
                    "subtitle_position": "top",
                    "duration_ms": 5000,
                    "background_img": "simple background",
                }
            )
        else:
            # General/Ad Mode: Use image_prompt + speaker schema
            is_narration = i % 3 == 2  # Every 3rd scene is narration
            logger.debug(f"[DEBUG] Fallback: generating general mode scene {i+1}")

            if is_narration:
                scenes.append(
                    {
                        "scene_id": scene_id,
                        "image_prompt": f"{prompt} 관련 배경 이미지",
                        "text": f"장면 {i+1}",
                        "speaker": "narration",
                        "duration_ms": 5000,
                    }
                )
            else:
                scenes.append(
                    {
                        "scene_id": scene_id,
                        "image_prompt": f"캐릭터가 등장하는 장면, {prompt} 배경",
                        "text": f"장면 {i+1}",
                        "speaker": char_id,
                        "duration_ms": 5000,
                    }
                )

    if mode == "story":
        plot_data = {
            "title": prompt[:10] if len(prompt) <= 10 else prompt[:10] + "...",
            "mode": mode,
            "scenes": scenes,
        }
    else:
        plot_data = {
            "title": prompt[:10] if len(prompt) <= 10 else prompt[:10] + "...",
            "mode": mode,
            "bgm_prompt": "calm, atmospheric background music",
            "scenes": scenes,
        }

    with open(plot_path, "w", encoding="utf-8") as f:
        json.dump(plot_data, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Fallback generation complete")
    return characters_path, plot_path
