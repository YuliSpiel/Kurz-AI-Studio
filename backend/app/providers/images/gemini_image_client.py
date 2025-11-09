"""
Gemini 2.5 Flash Image (Nano Banana) client.
Google's image generation model via Gemini API.
"""
import logging
import httpx
import base64
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GeminiImageClient:
    """Gemini 2.5 Flash Image (Nano Banana) provider."""

    def __init__(self, api_key: str):
        """
        Initialize Gemini Image client.

        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-2.5-flash-image"
        logger.info("Gemini Image (Nano Banana) client initialized")

    def generate_image(
        self,
        prompt: str,
        seed: Optional[int] = None,
        width: int = 512,
        height: int = 768,
        output_prefix: str = "gemini_output",
        **kwargs
    ) -> Path:
        """
        Generate image using Gemini 2.5 Flash Image API.

        Args:
            prompt: Text prompt for image generation
            seed: Random seed (not directly supported by Gemini API, used for filename)
            width: Image width (used to determine aspect ratio)
            height: Image height (used to determine aspect ratio)
            output_prefix: Prefix for output filename
            **kwargs: Additional parameters (ignored)

        Returns:
            Path to generated image file
        """
        logger.info(f"Gemini (Nano Banana): Generating image with prompt: {prompt[:50]}...")

        # Determine aspect ratio from width/height
        aspect_ratio = self._get_aspect_ratio(width, height)

        # Prepare request payload
        url = f"{self.base_url}/models/{self.model}:generateContent"

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt}
                ]
            }],
            "generationConfig": {
                "responseModalities": ["Image"],
                "imageConfig": {
                    "aspectRatio": aspect_ratio
                }
            }
        }

        try:
            # Call Gemini API
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                result = response.json()

                # Log API response for debugging
                logger.debug(f"Gemini API response: {result}")

                # Extract image from response
                candidates = result.get("candidates", [])
                if not candidates:
                    logger.error(f"No candidates in Gemini API response: {result}")
                    raise ValueError("No candidates in Gemini API response")

                # Find image in parts
                image_data = None
                for part in candidates[0].get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        image_data = part["inlineData"].get("data")
                        break

                if not image_data:
                    logger.error(f"No image data in Gemini API response. Full response: {result}")
                    raise ValueError("No image data in Gemini API response")

                # Decode base64 image
                try:
                    image_bytes = base64.b64decode(image_data)
                except Exception as e:
                    raise ValueError(f"Failed to decode image: {e}")

                # Save image
                # Check if output_prefix contains path separators (full path)
                prefix_path = Path(output_prefix)
                if "/" in output_prefix or "\\" in output_prefix:
                    # Full path provided, use it directly
                    output_path = prefix_path.with_suffix(".png")
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                else:
                    # Only filename provided, use default directory
                    output_dir = Path("backend/app/data/outputs/images")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / f"{output_prefix}.png"

                with open(output_path, "wb") as f:
                    f.write(image_bytes)

                logger.info(f"Gemini (Nano Banana): Image saved to {output_path}")
                return output_path

        except httpx.HTTPError as e:
            logger.error(f"Gemini API HTTP error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response content: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Gemini image generation error: {e}")
            raise

    def _get_aspect_ratio(self, width: int, height: int) -> str:
        """
        Calculate aspect ratio string for Gemini API.

        Args:
            width: Image width
            height: Image height

        Returns:
            Aspect ratio string (e.g., "9:16", "16:9", "1:1")
        """
        # Calculate ratio
        ratio = width / height

        # Map common ratios
        if abs(ratio - 1.0) < 0.1:
            return "1:1"  # Square
        elif abs(ratio - 16/9) < 0.1:
            return "16:9"  # Landscape
        elif abs(ratio - 9/16) < 0.1:
            return "9:16"  # Portrait (vertical video)
        elif abs(ratio - 4/3) < 0.1:
            return "4:3"  # Traditional
        elif abs(ratio - 3/4) < 0.1:
            return "3:4"  # Portrait
        else:
            # Default based on orientation
            if ratio > 1:
                return "16:9"
            else:
                return "9:16"

    def check_status(self) -> bool:
        """
        Check if Gemini service is available.

        Returns:
            True if service is available
        """
        try:
            url = f"{self.base_url}/models/{self.model}"
            headers = {"x-goog-api-key": self.api_key}

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
