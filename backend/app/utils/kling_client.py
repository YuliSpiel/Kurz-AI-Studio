"""
Kling AI API Client for Pro Mode video generation.
Uses Image-to-Video API to generate 5-second videos from start/end frames.

Recommended settings:
- Model: kling-v1-6 (195% better than v1.5)
- Mode: pro (1080p quality, ~2 min generation time)
"""
import httpx
import asyncio
import time
import jwt
import base64
import logging
from pathlib import Path
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Kling API endpoints
KLING_API_BASE = "https://api.klingai.com"
KLING_IMAGE_TO_VIDEO_ENDPOINT = "/v1/videos/image2video"
KLING_TASK_STATUS_ENDPOINT = "/v1/videos/image2video"

# Model versions
KLING_MODEL_V1 = "kling-v1"
KLING_MODEL_V1_5 = "kling-v1-5"
KLING_MODEL_V1_6 = "kling-v1-6"  # Recommended: 195% better than v1.5


class KlingClient:
    """Client for Kling AI Image-to-Video API."""

    def __init__(self):
        self.access_key = settings.KLING_ACCESS_KEY
        self.secret_key = settings.KLING_SECRET_KEY
        self.video_duration = settings.KLING_VIDEO_DURATION

    def _generate_jwt_token(self) -> str:
        """Generate JWT token for Kling API authentication."""
        headers = {
            "alg": "HS256",
            "typ": "JWT"
        }
        payload = {
            "iss": self.access_key,
            "exp": int(time.time()) + 1800,  # 30 minutes expiry
            "nbf": int(time.time()) - 5
        }
        token = jwt.encode(payload, self.secret_key, algorithm="HS256", headers=headers)
        return token

    def _image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def image_to_video(
        self,
        start_image_path: str,
        end_image_path: str,
        output_path: str,
        prompt: Optional[str] = None,
        negative_prompt: Optional[str] = "blurry, shaky, distorted, low quality, sudden movement",
        model: str = KLING_MODEL_V1_6,
        mode: str = "pro",
        cfg_scale: float = 0.5,
    ) -> str:
        """
        Generate video from start and end frames using Kling AI.

        Args:
            start_image_path: Path to the start frame image
            end_image_path: Path to the end frame image
            output_path: Path to save the generated video
            prompt: Optional motion prompt (English recommended)
            negative_prompt: Elements to avoid in generation
            model: Model version (kling-v1, kling-v1-5, kling-v1-6)
            mode: Quality mode ("std" for 720p, "pro" for 1080p)
            cfg_scale: Prompt adherence (0.0-1.0)

        Returns:
            Path to the generated video file
        """
        logger.info(f"[Kling] Starting image-to-video generation (model={model}, mode={mode})")
        logger.info(f"[Kling] Start image: {start_image_path}")
        logger.info(f"[Kling] End image: {end_image_path}")
        if prompt:
            logger.info(f"[Kling] Motion prompt: {prompt[:50]}...")

        # Generate auth token
        token = self._generate_jwt_token()

        # Convert images to base64
        start_image_b64 = self._image_to_base64(start_image_path)
        end_image_b64 = self._image_to_base64(end_image_path)

        # Prepare request payload
        payload = {
            "model_name": model,
            "image": start_image_b64,
            "image_tail": end_image_b64,  # End frame
            "duration": str(self.video_duration),  # "5" or "10"
            "mode": mode,  # "std" (720p) or "pro" (1080p)
            "cfg_scale": cfg_scale,
        }

        if prompt:
            payload["prompt"] = prompt
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Submit task
            logger.info(f"[Kling] Submitting video generation task...")
            response = await client.post(
                f"{KLING_API_BASE}{KLING_IMAGE_TO_VIDEO_ENDPOINT}",
                json=payload,
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"[Kling] API error: {response.status_code} - {response.text}")
                raise Exception(f"Kling API error: {response.status_code}")

            result = response.json()
            logger.info(f"[Kling] Task submitted successfully")

            if result.get("code") != 0:
                raise Exception(f"Kling API error: {result.get('message')}")

            task_id = result["data"]["task_id"]
            logger.info(f"[Kling] Task ID: {task_id}")

            # Poll for completion
            video_url = await self._poll_task_status(client, task_id, headers)

            # Download video
            logger.info(f"[Kling] Downloading video...")
            video_response = await client.get(video_url)

            # Save to file
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(video_response.content)

            logger.info(f"[Kling] ✓ Video saved to: {output_path}")
            return output_path

    async def _poll_task_status(
        self,
        client: httpx.AsyncClient,
        task_id: str,
        headers: dict,
        max_attempts: int = 120,
        poll_interval: int = 10
    ) -> str:
        """
        Poll task status until completion.

        Returns:
            URL of the generated video
        """
        last_status = None
        for attempt in range(max_attempts):
            response = await client.get(
                f"{KLING_API_BASE}{KLING_TASK_STATUS_ENDPOINT}/{task_id}",
                headers=headers
            )

            if response.status_code != 200:
                logger.warning(f"[Kling] Status check failed: {response.status_code}")
                await asyncio.sleep(poll_interval)
                continue

            result = response.json()
            status = result.get("data", {}).get("task_status")

            # Only log when status changes (reduce log spam)
            if status != last_status:
                logger.info(f"[Kling] Task status: {status}")
                last_status = status

            if status == "succeed":
                videos = result["data"].get("task_result", {}).get("videos", [])
                if videos:
                    return videos[0]["url"]
                raise Exception("No video URL in response")

            elif status == "failed":
                error_msg = result.get("data", {}).get("task_status_msg", "Unknown error")
                raise Exception(f"Kling task failed: {error_msg}")

            await asyncio.sleep(poll_interval)

        raise Exception(f"Kling task timed out after {max_attempts * poll_interval} seconds")


class KlingClientStub:
    """Stub client for testing without API calls."""

    def __init__(self):
        self.video_duration = settings.KLING_VIDEO_DURATION

    async def image_to_video(
        self,
        start_image_path: str,
        end_image_path: str,
        output_path: str,
        prompt: Optional[str] = None,
        negative_prompt: Optional[str] = None,
    ) -> str:
        """
        Stub implementation that creates a simple slideshow video.
        Uses FFmpeg to create a crossfade between start and end images.
        """
        import subprocess

        logger.info(f"[Kling STUB] Creating stub video from images")
        logger.info(f"[Kling STUB] Start: {start_image_path}")
        logger.info(f"[Kling STUB] End: {end_image_path}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Create a simple crossfade video using FFmpeg
        # First image for 2.5s, crossfade 0.5s, second image for 2s
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", "3", "-i", start_image_path,
            "-loop", "1", "-t", "3", "-i", end_image_path,
            "-filter_complex",
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v0];"
            "[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v1];"
            "[v0][v1]xfade=transition=fade:duration=1:offset=2,format=yuv420p[v]",
            "-map", "[v]",
            "-t", str(self.video_duration),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"[Kling STUB] Video created: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"[Kling STUB] FFmpeg error: {e.stderr.decode()}")
            raise

        return output_path


def get_kling_client(stub_mode: bool = False) -> KlingClient | KlingClientStub:
    """Get Kling client instance."""
    if stub_mode or not settings.KLING_ACCESS_KEY:
        logger.warning("[Kling] Using stub client (no API key or stub mode)")
        return KlingClientStub()
    return KlingClient()
