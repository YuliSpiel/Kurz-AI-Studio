"""
Kling AI Video Generation Client.
Generates Image-to-Video using Kling AI API (v1.6 + pro mode).
"""
import logging
import time
import base64
import hashlib
import hmac
import httpx
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class KlingVideoClient:
    """Kling AI Image-to-Video provider."""

    BASE_URL = "https://api.klingai.com"

    # Model versions
    MODEL_V1 = "kling-v1"
    MODEL_V1_5 = "kling-v1-5"
    MODEL_V1_6 = "kling-v1-6"  # Recommended: 195% better than v1.5

    # Quality modes
    MODE_STD = "std"   # 720p, faster
    MODE_PRO = "pro"   # 1080p, higher quality

    def __init__(self, access_key: str, secret_key: str):
        """
        Initialize Kling AI client.

        Args:
            access_key: Kling API access key
            secret_key: Kling API secret key
        """
        self.access_key = access_key
        self.secret_key = secret_key
        logger.info("Kling AI Video client initialized (v1.6 + pro mode)")

    def _generate_signature(self, timestamp: str) -> str:
        """Generate HMAC-SHA256 signature for API authentication."""
        message = f"{self.access_key}{timestamp}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_headers(self) -> dict:
        """Generate authenticated headers."""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp)
        return {
            "Content-Type": "application/json",
            "X-API-KEY": self.access_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature
        }

    def _image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def generate_video(
        self,
        start_image: str,
        end_image: Optional[str] = None,
        prompt: str = "",
        negative_prompt: str = "blurry, shaky, distorted, low quality, sudden movement",
        duration: str = "5",
        mode: str = "pro",
        model: str = "kling-v1-6",
        cfg_scale: float = 0.5,
        output_path: Optional[str] = None,
        timeout: int = 300,
        poll_interval: int = 10
    ) -> str:
        """
        Generate video using Kling AI Image-to-Video API.

        Args:
            start_image: Path to start frame image
            end_image: Path to end frame image (optional, for better transitions)
            prompt: Motion description prompt (English recommended)
            negative_prompt: Elements to avoid
            duration: Video duration in seconds ("5" or "10")
            mode: Quality mode ("std" for 720p, "pro" for 1080p)
            model: Model version (kling-v1, kling-v1-5, kling-v1-6)
            cfg_scale: Prompt adherence (0.0-1.0)
            output_path: Path to save output video (optional)
            timeout: Maximum wait time in seconds
            poll_interval: Seconds between status checks

        Returns:
            Path to generated video file
        """
        logger.info(f"Kling AI: Generating video with model={model}, mode={mode}")
        logger.info(f"  Start image: {start_image}")
        logger.info(f"  End image: {end_image}")
        logger.info(f"  Motion prompt: {prompt[:50]}..." if prompt else "  No motion prompt")

        # Prepare request payload
        payload = {
            "model_name": model,
            "mode": mode,
            "duration": duration,
            "cfg_scale": cfg_scale,
            "image": self._image_to_base64(start_image)
        }

        if end_image:
            payload["image_tail"] = self._image_to_base64(end_image)

        if prompt:
            payload["prompt"] = prompt

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        # Submit generation request
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.BASE_URL}/v1/videos/image2video",
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                result = response.json()

                if result.get("code") != 0:
                    raise ValueError(f"Kling API error: {result.get('message')}")

                task_id = result.get("data", {}).get("task_id")
                if not task_id:
                    raise ValueError("No task_id in response")

                logger.info(f"Kling AI: Task submitted, task_id={task_id}")

        except httpx.HTTPError as e:
            logger.error(f"Kling API HTTP error: {e}")
            raise

        # Poll for completion
        video_url = self._poll_task(task_id, timeout, poll_interval)

        # Download video
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"kling_video_{timestamp}.mp4"

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Kling AI: Downloading video to {output_path}")
        with httpx.Client(timeout=120.0) as client:
            response = client.get(video_url)
            response.raise_for_status()
            with open(output_file, "wb") as f:
                f.write(response.content)

        logger.info(f"Kling AI: Video saved to {output_path}")
        return str(output_file)

    def _poll_task(self, task_id: str, timeout: int, poll_interval: int) -> str:
        """
        Poll task status until completion.

        Args:
            task_id: Task ID to poll
            timeout: Maximum wait time in seconds
            poll_interval: Seconds between status checks

        Returns:
            URL of generated video

        Raises:
            TimeoutError: If task doesn't complete within timeout
            ValueError: If task fails
        """
        start_time = time.time()
        last_status = None

        with httpx.Client(timeout=30.0) as client:
            while time.time() - start_time < timeout:
                response = client.get(
                    f"{self.BASE_URL}/v1/videos/image2video/{task_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                result = response.json()

                if result.get("code") != 0:
                    raise ValueError(f"Kling API error: {result.get('message')}")

                data = result.get("data", {})
                status = data.get("task_status")

                # Only log when status changes
                if status != last_status:
                    logger.info(f"Kling AI: Task {task_id} status: {status}")
                    last_status = status

                if status == "succeed":
                    videos = data.get("task_result", {}).get("videos", [])
                    if videos:
                        return videos[0].get("url")
                    raise ValueError("No video URL in result")

                if status == "failed":
                    error_msg = data.get("task_status_msg", "Unknown error")
                    raise ValueError(f"Kling task failed: {error_msg}")

                time.sleep(poll_interval)

        raise TimeoutError(f"Kling task {task_id} timed out after {timeout}s")

    def check_status(self) -> bool:
        """
        Check if Kling service is available.

        Returns:
            True if service is available
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.BASE_URL}/v1/videos/image2video",
                    headers=self._get_headers()
                )
                # 405 Method Not Allowed is expected for GET on POST endpoint
                # but confirms the endpoint exists
                return response.status_code in [200, 405]
        except Exception as e:
            logger.error(f"Kling status check failed: {e}")
            return False
