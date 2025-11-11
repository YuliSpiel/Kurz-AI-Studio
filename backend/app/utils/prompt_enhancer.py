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


def enhance_prompt(original_prompt: str, mode: str = "general") -> Dict[str, Any]:
    """
    Analyze and enhance a user prompt for video generation.

    Args:
        original_prompt: Original user input prompt
        mode: Generation mode (general, story, ad)

    Returns:
        Dict containing:
        - enhanced_prompt: Enriched version of the prompt
        - suggested_num_cuts: Optimal number of cuts (1-10)
        - suggested_art_style: Recommended art style
        - suggested_music_genre: Recommended music genre
        - suggested_num_characters: Recommended number of characters (1-2)
        - reasoning: Brief explanation of suggestions
    """
    logger.info(f"[ENHANCE] Analyzing prompt: '{original_prompt[:50]}...'")

    # Build enhancement prompt (using English to avoid safety filters)
    system_prompt = f"""You are a short-form video production expert. Analyze the user's prompt and suggest optimal parameters.

Mode: {mode}

Please provide:
1. Enhanced prompt: Make it more specific and visual (output in Korean)
2. Number of cuts: 1-10 based on complexity
3. Art style: Match the theme
4. Music genre: Match the mood
5. Number of characters: 1-2

Return ONLY this JSON format:
{{
  "enhanced_prompt": "enhanced version in Korean",
  "suggested_num_cuts": 3,
  "suggested_art_style": "art style name",
  "suggested_music_genre": "genre name",
  "suggested_num_characters": 1,
  "reasoning": "explanation in Korean"
}}"""

    user_prompt = f"Original prompt: {original_prompt}"

    try:
        # Initialize Gemini client
        if not settings.GEMINI_API_KEY:
            raise ValueError("No Gemini API key configured")

        client = GeminiLLMClient(api_key=settings.GEMINI_API_KEY)

        # Call Gemini Flash
        response_text = client.generate_text(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        logger.info(f"[ENHANCE] Raw LLM response: {response_text[:200]}...")

        # Parse JSON response
        # Clean potential markdown code blocks
        cleaned_response = response_text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        result = json.loads(cleaned_response)

        # Validate fields
        required_fields = [
            "enhanced_prompt",
            "suggested_num_cuts",
            "suggested_art_style",
            "suggested_music_genre",
            "suggested_num_characters",
            "reasoning"
        ]

        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")

        # Validate ranges
        result["suggested_num_cuts"] = max(1, min(10, int(result["suggested_num_cuts"])))
        result["suggested_num_characters"] = max(1, min(2, int(result["suggested_num_characters"])))

        logger.info(f"[ENHANCE] Successfully enhanced prompt")
        logger.info(f"[ENHANCE] Suggested cuts: {result['suggested_num_cuts']}, "
                   f"characters: {result['suggested_num_characters']}, "
                   f"art_style: '{result['suggested_art_style']}'")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"[ENHANCE] Failed to parse JSON response: {e}")
        logger.error(f"[ENHANCE] Raw response was: {response_text}")
        raise ValueError(f"LLM returned invalid JSON: {e}")

    except Exception as e:
        logger.error(f"[ENHANCE] Failed to enhance prompt: {e}", exc_info=True)
        raise
