"""
디자이너 Agent: Image generation via ComfyUI.
"""
import logging
import json
from pathlib import Path

from app.celery_app import celery
from app.config import settings

logger = logging.getLogger(__name__)


@celery.task(bind=True, name="tasks.designer")
def designer_task(self, run_id: str, json_path: str, spec: dict):
    """
    Generate images for all scenes using ComfyUI.

    Args:
        run_id: Run identifier
        json_path: Path to JSON layout
        spec: RunSpec as dict

    Returns:
        Dict with generated image paths
    """
    logger.info(f"[{run_id}] Designer: Starting image generation...")

    try:
        # Load JSON
        with open(json_path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        # Get image provider
        if settings.IMAGE_PROVIDER == "comfyui":
            from app.providers.images.comfyui_client import ComfyUIClient
            client = ComfyUIClient(base_url=settings.COMFY_URL)
        else:
            raise ValueError(f"Unsupported image provider: {settings.IMAGE_PROVIDER}")

        image_results = []

        # Generate images for each scene
        for scene in layout.get("scenes", []):
            scene_id = scene["scene_id"]
            logger.info(f"[{run_id}] Generating images for {scene_id}...")

            # Process each image slot
            for img_slot in scene.get("images", []):
                slot_id = img_slot["slot_id"]
                img_type = img_type = img_slot["type"]

                # Prepare prompt based on type
                if img_type == "character":
                    # Get character info
                    char_id = img_slot.get("ref_id")
                    char = next(
                        (c for c in layout.get("characters", []) if c["char_id"] == char_id),
                        None
                    )
                    if char:
                        prompt = f"{char['name']}, {char['persona']}, {spec.get('art_style', '')}"
                        seed = char.get("seed", settings.BASE_CHAR_SEED)
                    else:
                        prompt = f"character, {spec.get('art_style', '')}"
                        seed = settings.BASE_CHAR_SEED
                elif img_type == "background":
                    prompt = f"background scene, {spec.get('art_style', '')}"
                    seed = scene.get("bg_seed", settings.BG_SEED_BASE)
                else:
                    prompt = f"prop, {spec.get('art_style', '')}"
                    seed = settings.BG_SEED_BASE + 100

                # Generate image
                logger.info(f"[{run_id}] Generating {scene_id}/{slot_id}: {prompt[:50]}...")

                image_path = client.generate_image(
                    prompt=prompt,
                    seed=seed,
                    lora_name=settings.ART_STYLE_LORA,
                    lora_strength=spec.get("lora_strength", 0.8),
                    reference_images=spec.get("reference_images", []),
                    output_prefix=f"{run_id}_{scene_id}_{slot_id}"
                )

                # Update JSON with image path
                img_slot["image_url"] = str(image_path)
                image_results.append({
                    "scene_id": scene_id,
                    "slot_id": slot_id,
                    "image_url": str(image_path)
                })

                logger.info(f"[{run_id}] Generated: {image_path}")

        # Save updated JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(layout, f, indent=2, ensure_ascii=False)

        logger.info(f"[{run_id}] Designer: Completed {len(image_results)} images")

        # Update progress
        from app.main import runs
        if run_id in runs:
            runs[run_id]["progress"] = 0.5
            runs[run_id]["artifacts"]["images"] = image_results

        return {
            "run_id": run_id,
            "agent": "designer",
            "images": image_results,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"[{run_id}] Designer task failed: {e}", exc_info=True)
        raise
