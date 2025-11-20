"""
Gemini LLM Client for text generation using Google's Generative AI.
"""
import logging
from typing import List, Dict, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiLLMClient:
    """
    Client for interacting with Google's Gemini models (gemini-2.5-flash).
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the Gemini LLM client.

        Args:
            api_key: Google AI API key
            model_name: Model identifier (default: gemini-2.5-flash)
        """
        if not api_key:
            raise ValueError("Gemini API key is required")

        self.api_key = api_key
        self.model_name = model_name

        # Configure genai
        genai.configure(api_key=self.api_key)

        # Initialize model
        self.model = genai.GenerativeModel(self.model_name)

        logger.info(f"Initialized GeminiLLMClient with model: {self.model_name}")

    def generate_text(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_retries: int = 3
    ) -> str:
        """
        Generate text using Gemini model with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            max_retries: Maximum number of retry attempts

        Returns:
            Generated text as string

        Raises:
            Exception: If API call fails after all retries
        """
        import time

        # Combine system and user messages
        # Gemini doesn't have explicit system role, so we prepend system message to user prompt
        combined_prompt = ""

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                combined_prompt += f"{content}\n\n"
            elif role == "user":
                combined_prompt += f"{content}"

        logger.info(f"[GEMINI] Generating text with temperature={temperature}, max_tokens={max_tokens}")
        logger.debug(f"[GEMINI] Prompt length: {len(combined_prompt)} chars")

        # Generate content with safety settings
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        safety_settings = [
            {
                "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": HarmBlockThreshold.BLOCK_NONE,
            },
            {
                "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": HarmBlockThreshold.BLOCK_NONE,
            },
            {
                "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": HarmBlockThreshold.BLOCK_NONE,
            },
            {
                "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": HarmBlockThreshold.BLOCK_NONE,
            },
        ]

        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"[GEMINI] Attempt {attempt + 1}/{max_retries}")

                response = self.model.generate_content(
                    combined_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                    safety_settings=safety_settings,
                )

                # Extract text from response
                if not response.candidates:
                    error_msg = "No candidates in response"
                    logger.warning(f"[GEMINI] {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise ValueError(error_msg)

                # Check for blocked responses
                candidate = response.candidates[0]
                finish_reason = candidate.finish_reason

                logger.debug(f"[GEMINI] Finish reason: {finish_reason} ({finish_reason.name if hasattr(finish_reason, 'name') else 'unknown'})")
                logger.debug(f"[GEMINI] Safety ratings: {candidate.safety_ratings}")

                # finish_reason enum: 1=STOP (success), 2=MAX_TOKENS (hit limit), 3=SAFETY (blocked), 4=RECITATION, 5=OTHER
                # Allow STOP (1) and MAX_TOKENS (2) - both provide usable content
                if finish_reason not in [1, 2]:
                    error_msg = (
                        f"Response blocked with finish_reason={finish_reason} ({finish_reason.name if hasattr(finish_reason, 'name') else 'unknown'}). "
                        f"Safety ratings: {candidate.safety_ratings}"
                    )
                    logger.warning(f"[GEMINI] {error_msg}")

                    # If safety-blocked, retry with adjusted temperature
                    if attempt < max_retries - 1:
                        temperature = max(0.3, temperature - 0.2)  # Lower temperature
                        logger.info(f"[GEMINI] Retrying with lower temperature: {temperature}")
                        time.sleep(2 ** attempt)
                        continue
                    raise ValueError(error_msg)

                result_text = response.text

                if not result_text or len(result_text) < 50:
                    error_msg = f"Generated text too short ({len(result_text)} chars)"
                    logger.warning(f"[GEMINI] {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise ValueError(error_msg)

                logger.info(f"[GEMINI] ✅ Generated {len(result_text)} characters successfully")
                return result_text

            except Exception as e:
                last_error = e
                logger.error(f"[GEMINI] Attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"[GEMINI] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"[GEMINI] All {max_retries} attempts failed")
                    raise last_error
