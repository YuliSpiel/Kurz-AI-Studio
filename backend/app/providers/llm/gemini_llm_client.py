"""
Gemini LLM Client for text generation using Google's Generative AI.
Uses requests library for reliable API calls.
"""
import logging
import time
import requests
from typing import List, Dict

logger = logging.getLogger(__name__)


class GeminiLLMClient:
    """
    Client for interacting with Google's Gemini models (gemini-2.5-flash).
    Uses REST API directly for reliable performance.
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
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        logger.info(f"Initialized GeminiLLMClient with model: {self.model_name}")

    def generate_text(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_retries: int = 3,
        json_mode: bool = False
    ) -> str:
        """
        Generate text using Gemini model with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            max_retries: Maximum number of retry attempts
            json_mode: If True, request JSON response format

        Returns:
            Generated text as string

        Raises:
            Exception: If API call fails after all retries
        """
        # Combine system and user messages
        combined_prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                combined_prompt += f"{content}\n\n"
            elif role == "user":
                combined_prompt += f"{content}"

        logger.info(f"[GEMINI] Generating text with temperature={temperature}, max_tokens={max_tokens}")
        logger.info(f"[GEMINI] Prompt length: {len(combined_prompt)} chars")
        logger.info(f"[GEMINI] Prompt preview (first 500 chars): {combined_prompt[:500]}...")

        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"

        # Build request body
        request_body = {
            "contents": [{"parts": [{"text": combined_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        }

        if json_mode:
            request_body["generationConfig"]["responseMimeType"] = "application/json"

        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"[GEMINI] Attempt {attempt + 1}/{max_retries}")

                response = requests.post(
                    url,
                    json=request_body,
                    headers={"Content-Type": "application/json"},
                    timeout=60  # 60 second timeout
                )

                if response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = 10 * (2 ** attempt)
                    logger.warning(f"[GEMINI] Rate limit (429), waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    error_msg = f"API error {response.status_code}: {response.text[:500]}"
                    logger.error(f"[GEMINI] {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise ValueError(error_msg)

                data = response.json()

                # Extract text from response
                if "candidates" not in data or not data["candidates"]:
                    error_msg = "No candidates in response"
                    logger.warning(f"[GEMINI] {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise ValueError(error_msg)

                candidate = data["candidates"][0]

                # Check finish reason
                finish_reason = candidate.get("finishReason", "UNKNOWN")
                if finish_reason not in ["STOP", "MAX_TOKENS"]:
                    error_msg = f"Response blocked: {finish_reason}"
                    logger.warning(f"[GEMINI] {error_msg}")
                    if attempt < max_retries - 1:
                        temperature = max(0.3, temperature - 0.2)
                        request_body["generationConfig"]["temperature"] = temperature
                        time.sleep(2 ** attempt)
                        continue
                    raise ValueError(error_msg)

                # Extract text
                content = candidate.get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    error_msg = "No parts in response content"
                    logger.warning(f"[GEMINI] {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise ValueError(error_msg)

                result_text = parts[0].get("text", "")

                # Validate response - just check it's not empty
                if not result_text:
                    error_msg = "Empty response"
                    logger.warning(f"[GEMINI] {error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise ValueError(error_msg)

                logger.info(f"[GEMINI] ✅ Generated {len(result_text)} characters successfully")
                return result_text

            except requests.exceptions.Timeout:
                last_error = Exception("Request timeout")
                logger.error(f"[GEMINI] Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue

            except requests.exceptions.RequestException as e:
                last_error = e
                logger.error(f"[GEMINI] Request error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue

            except Exception as e:
                last_error = e
                logger.error(f"[GEMINI] Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue

        logger.error(f"[GEMINI] All {max_retries} attempts failed")
        raise last_error or Exception("All retries failed")
