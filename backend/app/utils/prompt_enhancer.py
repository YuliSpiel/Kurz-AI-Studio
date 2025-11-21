"""
Prompt Enhancement Module
Uses Gemini Flash to analyze and enrich user prompts for video generation.
"""
import logging
from typing import Dict, Any
import json

from app.providers.llm.gemini_llm_client import GeminiLLMClient
from app.config import settings

logger = logging.getLogger(__name__)


def _fix_truncated_json(json_str: str) -> str:
    """
    Attempt to fix truncated JSON by closing unclosed strings and brackets.
    """
    import re

    # Remove trailing incomplete content after the last complete value
    # Find the last complete key-value pair
    lines = json_str.split('\n')
    fixed_lines = []
    brace_count = 0
    bracket_count = 0
    in_string = False
    escape_next = False

    for line in lines:
        fixed_lines.append(line)
        for i, char in enumerate(line):
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1

    result = '\n'.join(fixed_lines)

    # If we're in an unclosed string, try to close it
    if in_string:
        # Find the last quote and truncate there, then close
        last_quote = result.rfind('"')
        if last_quote > 0:
            # Find the start of the current field value
            # Look for pattern like "key": "value...
            result = result[:last_quote] + '...(truncated)"'

    # Remove trailing comma if present
    result = re.sub(r',\s*$', '', result.rstrip())

    # Close any unclosed brackets/braces
    result += ']' * bracket_count
    result += '}' * brace_count

    return result


def enhance_prompt(original_prompt: str, mode: str = "general") -> Dict[str, Any]:
    """
    Analyze and enhance a user prompt for video generation.

    Args:
        original_prompt: Original user input prompt
        mode: Generation mode (general, story, ad)

    Returns:
        Dict containing:
        - enhanced_prompt: Enriched version of the prompt
        - suggested_title: Catchy video title (max 30 chars)
        - suggested_num_cuts: Optimal number of cuts (1-10)
        - suggested_art_style: Recommended art style
        - suggested_music_genre: Recommended music genre
        - suggested_num_characters: Recommended number of characters (1-2)
        - reasoning: Brief explanation of suggestions
    """
    logger.info(f"[ENHANCE] Analyzing prompt: '{original_prompt[:50]}...'")

    # Build enhancement prompt (concise to reduce tokens)
    system_prompt = f"""Analyze this video prompt and return JSON only. Be concise.

{{
  "enhanced_prompt": "detailed Korean description",
  "suggested_title": "catchy video title (max 30 chars)",
  "suggested_plot_outline": "brief 3-5 sentence plot summary in Korean (what scenes will appear, what characters will do)",
  "suggested_num_cuts": 1-10,
  "suggested_art_style": "style name",
  "suggested_music_genre": "genre",
  "suggested_num_characters": 1-3,
  "suggested_narrative_tone": "one of: 격식형, 서술형, 친근한반말, 진지한나레이션, 감정강조, 코믹풍자",
  "suggested_plot_structure": "one of: 기승전결, 고구마사이다, 3막구조, 비교형, 반전형, 정보나열, 감정곡선, 질문형, 루프형",
  "reasoning": "brief Korean explanation (max 2 sentences)"
}}

IMPORTANT: suggested_num_characters should match the plot_outline (if dialogue between 2 people → 2, if solo narration → 1, if 3-way conversation → 3)."""

    user_prompt = f"Prompt: {original_prompt}\nMode: {mode}"

    try:
        # Initialize Gemini client
        if not settings.GEMINI_API_KEY:
            logger.error("[ENHANCE] No Gemini API key configured")
            raise ValueError("Gemini API 키가 설정되지 않았습니다")

        client = GeminiLLMClient(api_key=settings.GEMINI_API_KEY)

        # Call Gemini Flash with retry logic
        logger.info("[ENHANCE] Calling Gemini API for prompt enhancement...")
        response_text = client.generate_text(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4000,  # Increased to avoid truncation
            max_retries=3,
            json_mode=True  # Force JSON output for structured response
        )

        logger.info(f"[ENHANCE] Raw LLM response length: {len(response_text)} chars")
        logger.debug(f"[ENHANCE] First 200 chars: {response_text[:200]}...")

        # Parse JSON response
        # Clean potential markdown code blocks
        cleaned_response = response_text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        logger.debug(f"[ENHANCE] Cleaned response: {cleaned_response[:200]}...")

        try:
            result = json.loads(cleaned_response)
            logger.info("[ENHANCE] ✅ Successfully parsed JSON response")
        except json.JSONDecodeError as parse_error:
            logger.error(f"[ENHANCE] ❌ JSON parsing failed: {parse_error}")
            logger.error(f"[ENHANCE] Position: line {parse_error.lineno}, col {parse_error.colno}")
            logger.error(f"[ENHANCE] Cleaned response (first 500 chars):\n{cleaned_response[:500]}")
            logger.error(f"[ENHANCE] Cleaned response (last 500 chars):\n{cleaned_response[-500:]}")

            # Try to fix common issues
            logger.info("[ENHANCE] Attempting to fix JSON...")
            fixed_response = cleaned_response.replace(",\n]", "\n]").replace(",\n}", "\n}")

            # Try to fix truncated JSON (unterminated strings)
            if "Unterminated string" in str(parse_error):
                logger.info("[ENHANCE] Attempting to fix truncated JSON...")
                # Find the last complete field and close the JSON
                fixed_response = _fix_truncated_json(cleaned_response)

            try:
                result = json.loads(fixed_response)
                logger.info("[ENHANCE] ✅ Fixed and parsed JSON successfully")
            except Exception as fix_error:
                logger.error(f"[ENHANCE] ❌ Fix attempt also failed: {fix_error}")
                raise ValueError(f"LLM 응답을 파싱할 수 없습니다: {parse_error}")

        # Validate fields
        required_fields = [
            "enhanced_prompt",
            "suggested_title",
            "suggested_plot_outline",
            "suggested_num_cuts",
            "suggested_art_style",
            "suggested_music_genre",
            "suggested_num_characters",
            "suggested_narrative_tone",
            "suggested_plot_structure",
            "reasoning"
        ]

        missing_fields = [field for field in required_fields if field not in result]
        if missing_fields:
            logger.error(f"[ENHANCE] ❌ Missing required fields: {missing_fields}")
            raise ValueError(f"필수 필드 누락: {', '.join(missing_fields)}")

        # Validate ranges
        try:
            result["suggested_num_cuts"] = max(1, min(10, int(result["suggested_num_cuts"])))
            result["suggested_num_characters"] = max(1, min(3, int(result["suggested_num_characters"])))
        except (ValueError, TypeError) as e:
            logger.error(f"[ENHANCE] ❌ Invalid numeric values: {e}")
            raise ValueError("숫자 필드의 값이 올바르지 않습니다")

        logger.info("[ENHANCE] ✅ Successfully enhanced prompt")
        logger.info(f"[ENHANCE] Title: '{result['suggested_title']}', "
                   f"cuts: {result['suggested_num_cuts']}, "
                   f"chars: {result['suggested_num_characters']}, "
                   f"style: '{result['suggested_art_style']}', "
                   f"tone: '{result['suggested_narrative_tone']}', "
                   f"structure: '{result['suggested_plot_structure']}'")

        return result

    except ValueError as e:
        # Re-raise ValueError as-is (these are user-facing)
        logger.error(f"[ENHANCE] ValueError: {e}")
        raise

    except Exception as e:
        logger.error(f"[ENHANCE] ❌ Unexpected error: {e}", exc_info=True)
        raise ValueError(f"프롬프트 분석 중 오류 발생: {str(e)}")
