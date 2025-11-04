"""
감독 Agent: Final video composition using MoviePy.
This is the chord callback that runs after all asset generation tasks complete.
"""
import logging
import json
from pathlib import Path

from app.celery_app import celery
from app.orchestrator.fsm import RunState

logger = logging.getLogger(__name__)


@celery.task(bind=True, name="tasks.director")
def director_task(self, asset_results: list, run_id: str, json_path: str):
    """
    Compose final 9:16 video from all generated assets.

    This task is called as a chord callback after designer, composer, and voice tasks complete.

    Args:
        asset_results: List of results from parallel tasks
        run_id: Run identifier
        json_path: Path to JSON layout with all asset URLs

    Returns:
        Dict with final video URL
    """
    logger.info(f"[{run_id}] Director: Starting video composition...")
    logger.info(f"[{run_id}] Asset results: {asset_results}")

    try:
        # Get FSM and transition to RENDERING
        from app.orchestrator.fsm import _fsm_registry
        fsm = _fsm_registry.get(run_id)
        if fsm and fsm.transition_to(RunState.RENDERING):
            logger.info(f"[{run_id}] Transitioned to RENDERING")

            from app.main import runs
            if run_id in runs:
                runs[run_id]["state"] = fsm.current_state.value
                runs[run_id]["progress"] = 0.7

        # Load JSON with all asset URLs
        with open(json_path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        # Import MoviePy for composition
        from moviepy.editor import (
            VideoClip, ImageClip, AudioFileClip, CompositeVideoClip,
            CompositeAudioClip, TextClip, concatenate_videoclips
        )
        import numpy as np

        # Video settings (9:16 format)
        width = 1080
        height = 1920
        fps = layout.get("timeline", {}).get("fps", 30)

        scenes_clips = []

        # Process each scene
        for scene in layout.get("scenes", []):
            scene_id = scene["scene_id"]
            duration_sec = scene["duration_ms"] / 1000.0

            logger.info(f"[{run_id}] Composing {scene_id}, duration={duration_sec}s")

            # Create base background
            bg_color = (20, 20, 40)  # Dark background
            base_clip = VideoClip(
                lambda t: np.full((height, width, 3), bg_color, dtype=np.uint8),
                duration=duration_sec
            )

            # Layer images
            image_clips = [base_clip]
            for img_slot in scene.get("images", []):
                img_url = img_slot.get("image_url")
                if img_url and Path(img_url).exists():
                    # Load and position image
                    img_clip = ImageClip(img_url).set_duration(duration_sec)

                    # Resize to fit
                    img_clip = img_clip.resize(height=height * 0.6)

                    # Position based on slot
                    slot_id = img_slot.get("slot_id", "center")
                    if slot_id == "left":
                        img_clip = img_clip.set_position(("left", "center"))
                    elif slot_id == "right":
                        img_clip = img_clip.set_position(("right", "center"))
                    else:
                        img_clip = img_clip.set_position(("center", "center"))

                    image_clips.append(img_clip)

            # Composite video
            video_clip = CompositeVideoClip(image_clips, size=(width, height))

            # Add subtitles (simplified - use TextClip)
            for subtitle in scene.get("subtitles", []):
                # MoviePy TextClip requires ImageMagick (complex setup)
                # For now, skip or use simple overlay
                pass

            scenes_clips.append(video_clip)

        # Concatenate all scenes
        logger.info(f"[{run_id}] Concatenating {len(scenes_clips)} scenes...")
        final_video = concatenate_videoclips(scenes_clips, method="compose")

        # Add audio tracks
        audio_clips = []

        # Global BGM
        global_bgm = layout.get("global_bgm")
        if global_bgm and global_bgm.get("audio_url"):
            bgm_path = global_bgm["audio_url"]
            if Path(bgm_path).exists():
                bgm_clip = AudioFileClip(bgm_path).volumex(global_bgm.get("volume", 0.3))
                audio_clips.append(bgm_clip)

        # Dialogue audio (simplified - just add sequentially)
        for scene in layout.get("scenes", []):
            for dialogue in scene.get("dialogue", []):
                audio_url = dialogue.get("audio_url")
                if audio_url and Path(audio_url).exists():
                    voice_clip = AudioFileClip(audio_url)
                    # Set start time based on dialogue["start_ms"]
                    # For simplicity, add to composite
                    audio_clips.append(voice_clip)

        # Composite audio
        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            final_video = final_video.set_audio(final_audio)

        # Export video
        output_dir = Path("app/data/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{run_id}_final.mp4"

        logger.info(f"[{run_id}] Exporting video to {output_path}...")

        final_video.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(output_dir / f"{run_id}_temp_audio.m4a"),
            remove_temp=True,
            logger=None  # Suppress MoviePy logs
        )

        logger.info(f"[{run_id}] Video exported: {output_path}")

        # Update FSM to END
        if fsm and fsm.transition_to(RunState.END):
            logger.info(f"[{run_id}] Transitioned to END")

            from app.main import runs
            if run_id in runs:
                runs[run_id]["state"] = fsm.current_state.value
                runs[run_id]["progress"] = 1.0
                runs[run_id]["artifacts"]["video_url"] = str(output_path)

        return {
            "run_id": run_id,
            "agent": "director",
            "video_url": str(output_path),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"[{run_id}] Director task failed: {e}", exc_info=True)

        # Mark FSM as failed
        from app.orchestrator.fsm import _fsm_registry
        if fsm := _fsm_registry.get(run_id):
            fsm.fail(str(e))

        from app.main import runs
        if run_id in runs:
            runs[run_id]["state"] = "FAILED"
            runs[run_id]["logs"].append(f"Rendering failed: {e}")

        raise
