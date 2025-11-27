"""
감독 Agent: Final video composition using MoviePy.
This is the chord callback that runs after all asset generation tasks complete.
"""
import logging
import json
from pathlib import Path

from app.celery_app import celery
from app.orchestrator.fsm import RunState
from app.utils.progress import publish_progress

logger = logging.getLogger(__name__)


@celery.task(bind=True, name="tasks.layout_ready")
def layout_ready_task(self, asset_results: list, run_id: str, json_path: str):
    """
    Chord callback after asset generation completes.
    Updates layout.json with asset URLs and transitions to LAYOUT_REVIEW.

    Args:
        asset_results: List of results from parallel tasks (designer, composer, voice)
        run_id: Run identifier
        json_path: Path to layout.json

    Returns:
        Dict with status
    """
    logger.info(f"[{run_id}] Layout ready: All assets generated")
    logger.info(f"[{run_id}] Asset results: {asset_results}")
    publish_progress(run_id, progress=0.6, log="에셋 생성 완료 - 레이아웃 검수 대기 중...")

    try:
        # Load layout.json
        with open(json_path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        # Update layout.json with asset URLs from chord results
        logger.info(f"[{run_id}] Updating layout.json with asset URLs from chord results...")

        for result in asset_results:
            if not result or "agent" not in result:
                continue

            agent = result["agent"]

            # Update image URLs from designer
            if agent == "designer" and "images" in result:
                for img_result in result["images"]:
                    scene_id = img_result["scene_id"]
                    slot_id = img_result["slot_id"]
                    image_url = img_result["image_url"]

                    # Find scene and update image_url
                    for scene in layout.get("scenes", []):
                        if scene["scene_id"] == scene_id:
                            for img_slot in scene.get("images", []):
                                if img_slot["slot_id"] == slot_id:
                                    img_slot["image_url"] = image_url
                                    logger.info(f"[{run_id}] Updated {scene_id}/{slot_id} -> {image_url}")

            # Update audio URLs from voice agent
            elif agent == "voice" and "voice" in result:
                for audio_result in result["voice"]:
                    scene_id = audio_result["scene_id"]
                    line_id = audio_result["line_id"]
                    audio_url = audio_result["audio_url"]

                    # Find scene and update audio_url
                    for scene in layout.get("scenes", []):
                        if scene["scene_id"] == scene_id:
                            for text_line in scene.get("texts", []):
                                if text_line.get("line_id") == line_id:
                                    text_line["audio_url"] = audio_url
                                    logger.info(f"[{run_id}] Updated {scene_id}/{line_id} -> {audio_url}")

            # Update global BGM from composer
            elif agent == "composer" and "audio" in result:
                # Composer returns audio results in "audio" key
                audio_results = result["audio"]
                for audio_item in audio_results:
                    if audio_item.get("type") == "bgm" and audio_item.get("id") == "global_bgm":
                        bgm_url = audio_item.get("path")
                        if bgm_url:
                            if "global_bgm" not in layout or layout["global_bgm"] is None:
                                layout["global_bgm"] = {}
                            layout["global_bgm"]["audio_url"] = bgm_url
                            logger.info(f"[{run_id}] Updated global BGM -> {bgm_url}")

        # Save updated layout.json
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(layout, f, indent=2, ensure_ascii=False)

        logger.info(f"[{run_id}] layout.json updated with all asset URLs")

        # Check mode from layout.json
        mode = layout.get("metadata", {}).get("mode", "general")

        # Get review_mode from run spec or layout metadata (fallback)
        from app.main import runs
        review_mode = False
        if run_id in runs:
            spec = runs[run_id].get("spec", {})
            review_mode = spec.get("review_mode", False)

        # Fallback to metadata if not found in spec
        if not review_mode:
            review_mode = layout.get("metadata", {}).get("review_mode", False)

        logger.info(f"[{run_id}] Mode={mode}, review_mode={review_mode}")

        from app.orchestrator.fsm import get_fsm
        fsm = get_fsm(run_id)

        # State transition logic:
        # - review_mode=False (자동 모드): Skip all reviews, go directly to RENDERING
        # - review_mode=True (검수 모드): Go to ASSET_REVIEW first for image/BGM review

        if not review_mode:
            # Auto mode: skip all reviews, go directly to RENDERING
            logger.info(f"[{run_id}] Auto mode (review_mode=False), skipping reviews, going directly to RENDERING")
            if fsm and fsm.transition_to(RunState.RENDERING):
                logger.info(f"[{run_id}] Transitioned to RENDERING")
                publish_progress(
                    run_id,
                    state="RENDERING",
                    progress=0.7,
                    log="영상 합성 시작..."
                )

                if run_id in runs:
                    runs[run_id]["state"] = fsm.current_state.value
                    runs[run_id]["progress"] = 0.7

                # Trigger director task immediately
                logger.info(f"[{run_id}] Triggering director_task for immediate rendering")
                director_task.delay([], run_id, json_path)

            return {
                "status": "success",
                "message": "Assets generated, starting video composition",
                "run_id": run_id
            }

        # Review mode: go to ASSET_REVIEW for image/BGM review first
        else:
            if fsm and fsm.transition_to(RunState.ASSET_REVIEW):
                logger.info(f"[{run_id}] Transitioned to ASSET_REVIEW")
                publish_progress(
                    run_id,
                    state="ASSET_REVIEW",
                    progress=0.6,
                    log="에셋 검수 단계 - 이미지/BGM 확인 대기 중"
                )

                if run_id in runs:
                    runs[run_id]["state"] = fsm.current_state.value
                    runs[run_id]["progress"] = 0.6

            return {
                "status": "success",
                "message": "Assets generated, waiting for asset review",
                "run_id": run_id
            }

    except Exception as e:
        logger.error(f"[{run_id}] Failed in layout_ready_task: {e}", exc_info=True)
        from app.orchestrator.fsm import get_fsm
        fsm = get_fsm(run_id)
        if fsm:
            fsm.fail(f"Layout ready task failed: {str(e)}")
        raise


@celery.task(bind=True, name="tasks.director")
def director_task(self, asset_results: list, run_id: str, json_path: str):
    """
    Compose final 9:16 video from all generated assets.

    This task is called as chord callback after all asset generation tasks complete.

    Args:
        asset_results: List of results from parallel asset generation tasks (designer, composer, voice)
        run_id: Run identifier
        json_path: Path to JSON layout with all asset URLs

    Returns:
        Dict with final video URL
    """
    logger.info(f"[{run_id}] Director: Received asset results from chord: {asset_results}")
    logger.info(f"[{run_id}] Director: Starting video composition...")
    publish_progress(run_id, progress=0.7, log="감독: 최종 영상 합성 시작...")

    # TEST: 3초 대기
    import time
    time.sleep(3)

    try:
        # Get FSM and transition to RENDERING
        from app.orchestrator.fsm import get_fsm
        fsm = get_fsm(run_id)
        if fsm and fsm.transition_to(RunState.RENDERING):
            logger.info(f"[{run_id}] Transitioned to RENDERING")
            publish_progress(run_id, state="RENDERING", progress=0.75, log="렌더링 단계 시작")

            from app.main import runs
            if run_id in runs:
                runs[run_id]["state"] = fsm.current_state.value
                runs[run_id]["progress"] = 0.7

        # Load layout.json
        with open(json_path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        logger.info(f"[{run_id}] Layout loaded with {len(layout.get('scenes', []))} scenes")
        logger.info(f"[{run_id}] Mode: {layout.get('metadata', {}).get('mode', 'general')}")

        # Update layout with asset URLs from chord results (if not already updated)
        # This is needed when director_task is called directly from chord callback (auto mode)
        if asset_results:
            logger.info(f"[{run_id}] Updating layout with asset URLs from chord results...")
            for result in asset_results:
                if not result or "agent" not in result:
                    continue

                agent = result["agent"]

                # Update image URLs from designer
                if agent == "designer" and "images" in result:
                    for img_result in result["images"]:
                        scene_id = img_result["scene_id"]
                        slot_id = img_result["slot_id"]
                        image_url = img_result["image_url"]

                        for scene in layout.get("scenes", []):
                            if scene["scene_id"] == scene_id:
                                for img_slot in scene.get("images", []):
                                    if img_slot["slot_id"] == slot_id:
                                        img_slot["image_url"] = image_url

                # Update audio URLs from voice agent
                elif agent == "voice" and "voice" in result:
                    for audio_result in result["voice"]:
                        scene_id = audio_result["scene_id"]
                        line_id = audio_result["line_id"]
                        audio_url = audio_result["audio_url"]

                        for scene in layout.get("scenes", []):
                            if scene["scene_id"] == scene_id:
                                for text_line in scene.get("texts", []):
                                    if text_line.get("line_id") == line_id:
                                        text_line["audio_url"] = audio_url
                                        logger.info(f"[{run_id}] Updated {scene_id}/{line_id} audio -> {audio_url}")

                # Update global BGM from composer
                elif agent == "composer" and "audio" in result:
                    for audio_item in result["audio"]:
                        if audio_item.get("type") == "bgm" and audio_item.get("id") == "global_bgm":
                            bgm_url = audio_item.get("path")
                            if bgm_url:
                                if "global_bgm" not in layout or layout["global_bgm"] is None:
                                    layout["global_bgm"] = {}
                                layout["global_bgm"]["audio_url"] = bgm_url
                                logger.info(f"[{run_id}] Updated global BGM -> {bgm_url}")

        # Check if we're in stub mode (no real assets)
        from app.config import settings
        # Always use full rendering mode since MoviePy is installed
        stub_mode = False

        if stub_mode:
            logger.info(f"[{run_id}] ===== STUB RENDERING MODE =====")
            logger.info(f"[{run_id}] Video composition summary:")
            logger.info(f"[{run_id}]   Format: 1080x1920 (9:16)")
            logger.info(f"[{run_id}]   FPS: {layout.get('timeline', {}).get('fps', 30)}")
            logger.info(f"[{run_id}]   Scenes: {len(layout.get('scenes', []))}")

            for scene in layout.get("scenes", []):
                scene_id = scene["scene_id"]
                duration_sec = scene["duration_ms"] / 1000.0
                logger.info(f"[{run_id}]   - {scene_id}: {duration_sec}s")
                logger.info(f"[{run_id}]     Images: {len(scene.get('images', []))}")
                logger.info(f"[{run_id}]     Texts: {len(scene.get('texts', []))}")

            global_bgm = layout.get("global_bgm")
            if global_bgm:
                logger.info(f"[{run_id}]   BGM: {global_bgm.get('audio_url', 'N/A')}")

            # Create stub output file
            output_dir = Path(f"app/data/outputs/{run_id}")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "final_video.txt"

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("=== AutoShorts Video Composition Summary ===\n\n")
                f.write(f"Run ID: {run_id}\n")
                f.write(f"Format: 1080x1920 (9:16)\n")
                f.write(f"FPS: {layout.get('timeline', {}).get('fps', 30)}\n\n")

                for scene in layout.get("scenes", []):
                    scene_id = scene["scene_id"]
                    duration_sec = scene["duration_ms"] / 1000.0
                    f.write(f"\n[{scene_id}] ({duration_sec}s)\n")
                    f.write("-" * 40 + "\n")

                    for img_slot in scene.get("images", []):
                        f.write(f"  Image ({img_slot.get('slot_id', 'N/A')}): {img_slot.get('image_url', 'N/A')}\n")

                    for text_line in scene.get("texts", []):
                        f.write(f"  Audio: {text_line.get('audio_url', 'N/A')}\n")
                        f.write(f"    Text: {text_line.get('text', 'N/A')}\n")
                        f.write(f"    Type: {text_line.get('text_type', 'N/A')}\n")

                if global_bgm:
                    f.write(f"\nGlobal BGM: {global_bgm.get('audio_url', 'N/A')}\n")
                    f.write(f"  Volume: {global_bgm.get('volume', 0.3)}\n")

            logger.info(f"[{run_id}] Stub rendering complete: {output_path}")
            logger.info(f"[{run_id}] ===== END STUB RENDERING =====")
            publish_progress(run_id, progress=0.8, log=f"렌더링 완료: {output_path}")

            # Transition to QA
            if fsm and fsm.transition_to(RunState.QA):
                logger.info(f"[{run_id}] Transitioned to QA")
                publish_progress(run_id, state="QA", progress=0.82, log="QA 검수 단계로 전환...")

                from app.main import runs
                if run_id in runs:
                    runs[run_id]["state"] = fsm.current_state.value
                    runs[run_id]["progress"] = 0.82
                    # Set HTTP URL path for frontend to access video
                    runs[run_id]["artifacts"]["video_url"] = f"/outputs/{run_id}/final_video.mp4"

                # Trigger QA task
                from app.tasks.qa import qa_task
                qa_task.apply_async(args=[run_id, str(json_path), str(output_path)])
                logger.info(f"[{run_id}] QA task triggered")

            return {
                "run_id": run_id,
                "agent": "director",
                "video_url": str(output_path),
                "status": "success",
                "mode": "stub"
            }

        # Use FFmpeg-based renderer (faster and more memory-efficient than MoviePy)
        from app.utils.ffmpeg_renderer import FFmpegRenderer

        logger.info(f"[{run_id}] Using FFmpeg-based rendering pipeline")

        output_dir = Path(f"app/data/outputs/{run_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "final_video.mp4"

        # Create FFmpeg renderer
        renderer = FFmpegRenderer(run_id, layout, output_dir)

        # Render video using FFmpeg pipeline
        try:
            publish_progress(run_id, progress=0.72, log="프레임 생성 중...")
            final_video_path = renderer.render(output_path)
            publish_progress(run_id, progress=0.78, log="영상 파일 내보내기 완료")
        except Exception as e:
            logger.error(f"[{run_id}] FFmpeg rendering failed: {e}", exc_info=True)
            raise

        logger.info(f"[{run_id}] Video exported: {output_path}")
        publish_progress(run_id, progress=0.8, log=f"영상 내보내기 완료: {output_path}")

        # Transition to QA
        if fsm and fsm.transition_to(RunState.QA):
            logger.info(f"[{run_id}] Transitioned to QA")

            # Publish with video_url artifact
            video_url = f"/outputs/{run_id}/final_video.mp4"
            publish_progress(
                run_id,
                state="QA",
                progress=0.82,
                log="QA 검수 단계로 전환...",
                artifacts={"video_url": video_url}
            )

            # Trigger QA task
            from app.tasks.qa import qa_task
            qa_task.apply_async(args=[run_id, str(json_path), str(output_path)])
            logger.info(f"[{run_id}] QA task triggered with video_url: {video_url}")

        return {
            "run_id": run_id,
            "agent": "director",
            "video_url": str(output_path),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"[{run_id}] Director task failed: {e}", exc_info=True)

        # Mark FSM as failed
        from app.orchestrator.fsm import get_fsm
        if fsm := get_fsm(run_id):
            fsm.fail(str(e))

        from app.main import runs
        if run_id in runs:
            runs[run_id]["state"] = "FAILED"
            runs[run_id]["logs"].append(f"Rendering failed: {e}")

        raise


@celery.task(bind=True, name="tasks.director_pro")
def director_task_pro(self, asset_results: list, run_id: str, json_path: str):
    """
    Pro Mode director: Generate videos using Kling AI and compose final video.

    Flow:
    1. For each scene: Kling API (start_image + end_image → 5s video)
    2. If TTS > 5s, add freeze frame at the end
    3. Overlay subtitles
    4. Mix with global BGM
    5. Concatenate all scenes

    Args:
        asset_results: List of results from parallel tasks (designer_pro, composer, voice)
        run_id: Run identifier
        json_path: Path to plot.json

    Returns:
        Dict with final video URL
    """
    import asyncio

    logger.info(f"[{run_id}] Director Pro: Starting Pro mode video composition...")
    publish_progress(run_id, progress=0.5, log="감독: Pro 모드 영상 합성 시작...")

    try:
        # Get FSM and transition to RENDERING
        from app.orchestrator.fsm import get_fsm
        fsm = get_fsm(run_id)
        if fsm and fsm.transition_to(RunState.RENDERING):
            logger.info(f"[{run_id}] Transitioned to RENDERING")
            publish_progress(run_id, state="RENDERING", progress=0.55, log="렌더링 단계 시작")

            from app.main import runs
            if run_id in runs:
                runs[run_id]["state"] = fsm.current_state.value
                runs[run_id]["progress"] = 0.55

        # Load plot.json
        with open(json_path, "r", encoding="utf-8") as f:
            plot = json.load(f)

        logger.info(f"[{run_id}] Plot loaded with {len(plot.get('scenes', []))} scenes")

        # Load title and layout_config
        # Pro mode: title from plot.json, General mode: title from layout.json
        layout_json_path = Path(json_path).parent / "layout.json"
        title_text = ""
        layout_config = {}

        # First, try to get title from plot.json (Pro mode has it here)
        title_text = plot.get("title", "")

        # Then, try layout.json for additional config (General mode)
        if layout_json_path.exists():
            try:
                with open(layout_json_path, "r", encoding="utf-8") as f:
                    layout = json.load(f)
                # Use layout.json title if plot.json didn't have one
                if not title_text:
                    title_text = layout.get("title", "")
                layout_config = layout.get("metadata", {}).get("layout_config", {})
                logger.info(f"[{run_id}] Layout config loaded: title='{title_text[:30] if title_text else '(empty)'}', config={layout_config}")
            except Exception as e:
                logger.warning(f"[{run_id}] Failed to load layout.json: {e}")
        else:
            logger.info(f"[{run_id}] Pro mode: using title from plot.json: '{title_text[:30] if title_text else '(empty)'}'")

        # Update plot with asset URLs from chord results (if any)
        if asset_results:
            for result in asset_results:
                if not result or "agent" not in result:
                    continue

                agent = result["agent"]

                # Update image URLs from designer_pro
                if agent == "designer_pro" and "images" in result:
                    for img_result in result["images"]:
                        scene_id = img_result["scene_id"]
                        frame_type = img_result.get("frame_type", "start")
                        image_url = img_result["image_url"]

                        for scene in plot.get("scenes", []):
                            if scene["scene_id"] == scene_id:
                                if frame_type == "start":
                                    scene["start_image_url"] = image_url
                                else:
                                    scene["end_image_url"] = image_url
                                logger.info(f"[{run_id}] Updated {scene_id}/{frame_type} -> {image_url}")

                # Update audio URLs from voice agent
                elif agent == "voice" and "voice" in result:
                    for audio_result in result["voice"]:
                        scene_id = audio_result["scene_id"]
                        audio_url = audio_result["audio_url"]
                        duration_ms = audio_result.get("duration_ms")

                        for scene in plot.get("scenes", []):
                            if scene["scene_id"] == scene_id:
                                scene["audio_url"] = audio_url
                                if duration_ms:
                                    scene["tts_duration_ms"] = duration_ms
                                logger.info(f"[{run_id}] Updated {scene_id} audio -> {audio_url} ({duration_ms}ms)")

                # Update global BGM from composer
                elif agent == "composer" and "audio" in result:
                    for audio_item in result["audio"]:
                        if audio_item.get("type") == "bgm" and audio_item.get("id") == "global_bgm":
                            bgm_url = audio_item.get("path")
                            if bgm_url:
                                plot["bgm_url"] = bgm_url
                                logger.info(f"[{run_id}] Updated global BGM -> {bgm_url}")

        # Get Kling client
        from app.config import settings
        from app.utils.kling_client import get_kling_client

        stub_mode = not settings.KLING_ACCESS_KEY
        kling_client = get_kling_client(stub_mode=stub_mode)
        logger.info(f"[{run_id}] Using Kling client (stub_mode={stub_mode})")

        output_dir = Path(json_path).parent
        videos_dir = output_dir / "videos"
        videos_dir.mkdir(parents=True, exist_ok=True)

        # Generate video for each scene using Kling
        scenes = plot.get("scenes", [])

        scene_videos = []

        for idx, scene in enumerate(scenes):
            scene_id = scene["scene_id"]
            start_image = scene.get("start_image_url")
            end_image = scene.get("end_image_url")

            if not start_image or not end_image:
                logger.warning(f"[{run_id}] Missing images for {scene_id}, skipping")
                continue

            video_output = videos_dir / f"{scene_id}.mp4"

            # Get motion prompt from plot.json (generated by plot_generator)
            # Priority: motion_prompt > text (subtitle as fallback)
            motion_prompt = scene.get("motion_prompt", "")
            if not motion_prompt:
                # Fallback: use subtitle text as basic prompt
                motion_prompt = scene.get("text", "")

            negative_prompt = scene.get("negative_prompt", "blurry, shaky, distorted, low quality, sudden movement")

            logger.info(f"[{run_id}] Generating video for {scene_id}...")
            if motion_prompt:
                logger.info(f"[{run_id}]   Motion prompt: {motion_prompt[:50]}...")
            publish_progress(
                run_id,
                progress=0.55 + (0.2 * idx / len(scenes)),
                log=f"Kling: {scene_id} 영상 생성 중..."
            )

            # Call Kling API (async)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                video_path = loop.run_until_complete(
                    kling_client.image_to_video(
                        start_image_path=start_image,
                        end_image_path=end_image,
                        output_path=str(video_output),
                        prompt=motion_prompt,
                        negative_prompt=negative_prompt
                    )
                )
            finally:
                loop.close()

            scene["video_url"] = str(video_path)
            scene_videos.append({
                "scene_id": scene_id,
                "video_path": str(video_path),
                "tts_duration_ms": scene.get("tts_duration_ms"),
                "audio_url": scene.get("audio_url"),
                "text": scene.get("text", "")
            })

            logger.info(f"[{run_id}] ✓ Video generated for {scene_id}: {video_path}")

        # Save updated plot.json with video URLs
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(plot, f, indent=2, ensure_ascii=False)

        # Compose final video using FFmpeg/MoviePy
        publish_progress(run_id, progress=0.75, log="감독: 장면 합성 및 자막 오버레이 중...")

        final_video_path = _compose_pro_video(
            run_id=run_id,
            scene_videos=scene_videos,
            bgm_url=plot.get("bgm_url"),
            output_dir=output_dir,
            title_text=title_text,
            layout_config=layout_config
        )

        logger.info(f"[{run_id}] Final Pro mode video: {final_video_path}")
        publish_progress(run_id, progress=0.85, log=f"영상 합성 완료: {final_video_path}")

        # Transition to QA
        if fsm and fsm.transition_to(RunState.QA):
            logger.info(f"[{run_id}] Transitioned to QA")

            video_url = f"/outputs/{run_id}/final_video.mp4"
            publish_progress(
                run_id,
                state="QA",
                progress=0.88,
                log="QA 검수 단계로 전환...",
                artifacts={"video_url": video_url}
            )

            # Trigger QA task
            from app.tasks.qa import qa_task
            qa_task.apply_async(args=[run_id, str(json_path), str(final_video_path)])
            logger.info(f"[{run_id}] QA task triggered")

        return {
            "run_id": run_id,
            "agent": "director_pro",
            "video_url": str(final_video_path),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"[{run_id}] Director Pro task failed: {e}", exc_info=True)

        from app.orchestrator.fsm import get_fsm
        if fsm := get_fsm(run_id):
            fsm.fail(str(e))

        from app.main import runs
        if run_id in runs:
            runs[run_id]["state"] = "FAILED"
            runs[run_id]["logs"].append(f"Pro mode rendering failed: {e}")

        raise


def _compose_pro_video(
    run_id: str,
    scene_videos: list,
    bgm_url: str | None,
    output_dir: Path,
    title_text: str = "",
    layout_config: dict | None = None
) -> Path:
    """
    Compose final Pro mode video with General mode layout.

    Layout structure (1080x1920):
    - Title block: ~200px (top) - colored background + title text
    - Subtitle area: ~640px (middle) - text on white background
    - Video area: 1080x1080 (bottom) - 1:1 cropped video

    For each scene:
    1. Generate static frame with title + subtitle using PIL
    2. Crop Kling video to 1:1 and overlay on frame
    3. If TTS > 5s, extend with freeze frame
    4. Add TTS audio

    Then concatenate all scenes and add BGM.

    Args:
        run_id: Run identifier
        scene_videos: List of scene video info dicts
        bgm_url: Path to global BGM audio
        output_dir: Output directory (MUST be absolute path)
        title_text: Project title for title block
        layout_config: Layout configuration (colors, fonts, etc.)

    Returns:
        Path to final video
    """
    import subprocess
    import shutil
    from PIL import Image, ImageDraw, ImageFont
    from app.config import settings
    from app.utils.fonts import get_font_path

    logger.info(f"[{run_id}] === Pro Mode Video Composition Start (General Layout) ===")
    logger.info(f"[{run_id}] Scenes: {len(scene_videos)}")
    logger.info(f"[{run_id}] Title: {title_text[:50]}..." if title_text else f"[{run_id}] No title")

    # CRITICAL: Ensure output_dir is absolute from the start
    output_dir = Path(output_dir).resolve()
    logger.info(f"[{run_id}] Output dir (absolute): {output_dir}")

    # Create temp directories with absolute paths
    temp_dir = output_dir / "temp_pro"
    frames_dir = temp_dir / "frames"
    temp_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"[{run_id}] Temp dir: {temp_dir}")

    # Layout configuration
    layout_config = layout_config or {}
    FRAME_WIDTH = 1080
    FRAME_HEIGHT = 1920
    VIDEO_SIZE = 1080  # 1:1 square video area

    # Title block settings
    title_bg_color = _hex_to_rgb(layout_config.get("title_bg_color", "#323296"))
    title_font_size = layout_config.get("title_font_size", 100)
    subtitle_font_size = layout_config.get("subtitle_font_size", 80)

    # Load fonts
    title_font_id = layout_config.get("title_font", "AppleGothic")
    subtitle_font_id = layout_config.get("subtitle_font", "AppleGothic")
    title_font_path = get_font_path(title_font_id)
    subtitle_font_path = get_font_path(subtitle_font_id)

    try:
        title_font = ImageFont.truetype(title_font_path, title_font_size)
        subtitle_font = ImageFont.truetype(subtitle_font_path, subtitle_font_size)
    except Exception as e:
        logger.warning(f"[{run_id}] Font load error: {e}, using default")
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    processed_videos: list[Path] = []

    for idx, scene_info in enumerate(scene_videos):
        scene_id = scene_info["scene_id"]

        # CRITICAL: Convert all input paths to absolute immediately
        raw_video_path = scene_info["video_path"]
        video_path = Path(raw_video_path).resolve()

        if not video_path.exists():
            logger.error(f"[{run_id}] Video not found: {video_path}")
            raise FileNotFoundError(f"Scene video not found: {video_path}")

        tts_duration_ms = scene_info.get("tts_duration_ms") or 5000
        raw_audio_url = scene_info.get("audio_url")
        subtitle_text = scene_info.get("text", "")

        tts_duration_sec = tts_duration_ms / 1000.0
        video_duration_sec = float(settings.KLING_VIDEO_DURATION)  # 5 seconds

        logger.info(f"[{run_id}] [{idx+1}/{len(scene_videos)}] {scene_id}")
        logger.info(f"[{run_id}]   Video: {video_path}")
        logger.info(f"[{run_id}]   Duration: video={video_duration_sec}s, tts={tts_duration_sec}s")
        logger.info(f"[{run_id}]   Subtitle: {subtitle_text[:30]}..." if subtitle_text else f"[{run_id}]   No subtitle")

        # === Step 1: Create static frame with PIL (title + subtitle + white bg) ===
        frame_path = frames_dir / f"{scene_id}_frame.png"
        frame_img = Image.new('RGB', (FRAME_WIDTH, FRAME_HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(frame_img)

        # Calculate title block height with notch safe area
        title_block_height = 0
        notch_safe_area = 120  # Safe area for smartphone notch/dynamic island
        if title_text:
            title_lines = _wrap_text(title_text, title_font, int(FRAME_WIDTH * 0.9))
            line_height = int(title_font_size * 1.3)
            padding = 40
            title_block_height = notch_safe_area + padding + len(title_lines) * line_height + padding

            # Draw title background
            draw.rectangle([(0, 0), (FRAME_WIDTH, title_block_height)], fill=title_bg_color)

            # Draw title text (centered, below notch safe area)
            current_y = notch_safe_area + padding
            for line in title_lines:
                bbox = title_font.getbbox(line)
                text_width = bbox[2] - bbox[0]
                x_centered = (FRAME_WIDTH - text_width) // 2
                _draw_text_with_stroke(draw, line, (x_centered, current_y), title_font,
                                       fill_color=(255, 255, 255), stroke_color=(0, 0, 0), stroke_width=3)
                current_y += line_height

        # Video area starts at bottom (1080px height)
        video_area_top = FRAME_HEIGHT - VIDEO_SIZE  # 1920 - 1080 = 840

        # Subtitle area: between title block and video area
        subtitle_area_top = title_block_height
        subtitle_area_height = video_area_top - title_block_height

        # Draw subtitle (centered in subtitle area)
        if subtitle_text:
            subtitle_lines = _wrap_text(subtitle_text, subtitle_font, int(FRAME_WIDTH * 0.9))
            line_height = int(subtitle_font_size * 1.3)
            total_text_height = len(subtitle_lines) * line_height

            # Center vertically in subtitle area
            subtitle_y = subtitle_area_top + (subtitle_area_height - total_text_height) // 2

            for line in subtitle_lines:
                bbox = subtitle_font.getbbox(line)
                text_width = bbox[2] - bbox[0]
                x_centered = (FRAME_WIDTH - text_width) // 2
                _draw_text_with_stroke(draw, line, (x_centered, subtitle_y), subtitle_font,
                                       fill_color=(0, 0, 0), stroke_color=(255, 255, 255), stroke_width=2)
                subtitle_y += line_height

        # Save frame
        frame_img.save(frame_path, "PNG")
        logger.info(f"[{run_id}]   ✓ Frame created: {frame_path.name}")

        # === Step 2: Process video with FFmpeg ===
        output_scene_path = temp_dir / f"{scene_id}_processed.mp4"

        # Prepare audio input (absolute path)
        audio_path: Path | None = None
        if raw_audio_url:
            audio_path = Path(raw_audio_url).resolve()
            if not audio_path.exists():
                logger.warning(f"[{run_id}]   Audio not found: {audio_path}")
                audio_path = None
            else:
                logger.info(f"[{run_id}]   Audio: {audio_path}")

        # Build FFmpeg command
        # Input 0: Kling video
        # Input 1: Static frame (for overlay base)
        # Input 2: Audio (optional)

        inputs = [
            "-i", str(video_path),
            "-loop", "1", "-t", str(max(tts_duration_sec, video_duration_sec)), "-i", str(frame_path)
        ]
        input_count = 2

        audio_input_idx: int | None = None
        if audio_path:
            inputs.extend(["-i", str(audio_path)])
            audio_input_idx = input_count
            input_count += 1

        # Filter complex:
        # 1. Crop video to 1:1 (center crop)
        # 2. Scale to VIDEO_SIZE x VIDEO_SIZE
        # 3. If TTS > 5s, extend video with freeze frame (tpad)
        # 4. Overlay video on frame at bottom

        filter_parts = []

        # Crop and scale video to 1:1 (1080x1080)
        # crop=min(iw,ih):min(iw,ih) crops to square from center
        crop_scale = f"[0:v]crop=min(iw\\,ih):min(iw\\,ih),scale={VIDEO_SIZE}:{VIDEO_SIZE}"

        # Add freeze frame extension if needed
        if tts_duration_sec > video_duration_sec:
            extra_duration = tts_duration_sec - video_duration_sec
            logger.info(f"[{run_id}]   Freeze frame: +{extra_duration:.1f}s")
            crop_scale += f",tpad=stop_mode=clone:stop_duration={extra_duration}"

        crop_scale += "[vcropped]"
        filter_parts.append(crop_scale)

        # Overlay cropped video on frame at video_area_top position
        filter_parts.append(f"[1:v][vcropped]overlay=0:{video_area_top}[vout]")

        # Calculate scene duration (video length or TTS length, whichever is longer)
        scene_duration = max(tts_duration_sec, video_duration_sec)

        # Add audio padding to match scene duration
        # This ensures TTS plays at scene start and silence fills remaining time
        if audio_input_idx is not None:
            # apad pads with silence, then atrim cuts to exact duration
            filter_parts.append(f"[{audio_input_idx}:a]apad=whole_dur={scene_duration}[aout]")

        filter_complex = ";".join(filter_parts)

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
        ]

        # Add audio mapping (now using filtered audio with padding)
        if audio_input_idx is not None:
            cmd.extend(["-map", "[aout]"])
        else:
            cmd.extend(["-an"])

        cmd.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-t", str(scene_duration),
            str(output_scene_path)
        ])

        try:
            logger.debug(f"[{run_id}] FFmpeg: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            processed_videos.append(output_scene_path)
            logger.info(f"[{run_id}]   ✓ Processed -> {output_scene_path.name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"[{run_id}]   ✗ FFmpeg error: {e.stderr}")
            raise

    # === Concatenate all processed videos ===
    logger.info(f"[{run_id}] Concatenating {len(processed_videos)} videos...")

    concat_list_path = temp_dir / "concat_list.txt"
    with open(concat_list_path, "w") as f:
        for vpath in processed_videos:
            f.write(f"file '{vpath}'\n")
            logger.debug(f"[{run_id}]   - {vpath}")

    concat_output = temp_dir / "concat_no_bgm.mp4"

    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(concat_output)
    ]

    try:
        logger.debug(f"[{run_id}] Concat cmd: {' '.join(concat_cmd)}")
        subprocess.run(concat_cmd, check=True, capture_output=True, text=True)
        logger.info(f"[{run_id}] ✓ Concatenation complete: {concat_output.name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"[{run_id}] ✗ Concat error: {e.stderr}")
        logger.error(f"[{run_id}] Concat list contents:")
        with open(concat_list_path) as f:
            logger.error(f.read())
        raise

    # === Add BGM if available ===
    final_output = output_dir / "final_video.mp4"

    bgm_path: Path | None = None
    if bgm_url:
        bgm_path = Path(bgm_url).resolve()
        if not bgm_path.exists():
            logger.warning(f"[{run_id}] BGM not found: {bgm_path}")
            bgm_path = None

    if bgm_path:
        logger.info(f"[{run_id}] Adding BGM: {bgm_path}")

        # Get video duration for BGM trimming
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(concat_output)
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        video_duration = float(result.stdout.strip())
        logger.info(f"[{run_id}] Video duration: {video_duration:.1f}s")

        # Mix BGM with existing audio
        bgm_cmd = [
            "ffmpeg", "-y",
            "-i", str(concat_output),
            "-stream_loop", "-1",
            "-i", str(bgm_path),
            "-filter_complex",
            f"[1:a]volume=0.3,atrim=0:{video_duration}[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(final_output)
        ]

        try:
            subprocess.run(bgm_cmd, check=True, capture_output=True, text=True)
            logger.info(f"[{run_id}] ✓ BGM mixed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"[{run_id}] ✗ BGM mix error: {e.stderr}")
            shutil.copy(concat_output, final_output)
            logger.warning(f"[{run_id}] Using video without BGM as fallback")
    else:
        shutil.copy(concat_output, final_output)
        logger.info(f"[{run_id}] No BGM, using concatenated video as final")

    logger.info(f"[{run_id}] === Pro Mode Video Composition Complete ===")
    logger.info(f"[{run_id}] ✓ Final video: {final_output}")
    return final_output


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _wrap_text(text: str, font, max_width: int) -> list[str]:
    """Wrap text to fit within max_width."""
    from PIL import ImageFont
    lines = []
    words = text.split()
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines if lines else [text]


def _draw_text_with_stroke(
    draw,
    text: str,
    position: tuple[int, int],
    font,
    fill_color: tuple[int, int, int],
    stroke_color: tuple[int, int, int],
    stroke_width: int = 3
):
    """Draw text with stroke (outline)."""
    x, y = position

    # Draw stroke
    for offset_x in range(-stroke_width, stroke_width + 1):
        for offset_y in range(-stroke_width, stroke_width + 1):
            if offset_x != 0 or offset_y != 0:
                draw.text((x + offset_x, y + offset_y), text, font=font, fill=stroke_color)

    # Draw main text
    draw.text((x, y), text, font=font, fill=fill_color)
