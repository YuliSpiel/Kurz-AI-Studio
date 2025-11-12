"""
기획자 Agent: Plot planning task.
Generates CSV from prompt, converts to JSON, and triggers asset generation.
"""
import logging
import json
from pathlib import Path
from celery import chord, group
from typing import List

from app.celery_app import celery
from app.orchestrator.fsm import RunState, get_fsm
from app.utils.plot_generator import generate_plot_with_characters
from app.utils.json_converter import convert_plot_to_json
from app.utils.progress import publish_progress

logger = logging.getLogger(__name__)


def _validate_plot_json(run_id: str, plot_json_path: Path, layout_json_path: Path, spec: dict) -> List[str]:
    """
    Validate plot.json and layout.json structure.

    Args:
        run_id: Run identifier
        plot_json_path: Path to plot.json
        layout_json_path: Path to layout.json
        spec: RunSpec dict

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    try:
        # Load plot.json
        with open(plot_json_path, "r", encoding="utf-8") as f:
            plot_data = json.load(f)

        # Load layout.json
        with open(layout_json_path, "r", encoding="utf-8") as f:
            layout_data = json.load(f)

        mode = spec.get("mode", "general")
        num_cuts = spec.get("num_cuts", 3)

        # Validation 1: Check plot.json has scenes
        if "scenes" not in plot_data or not plot_data["scenes"]:
            errors.append("plot.json에 scenes가 없거나 비어있음")
            return errors  # Critical error, stop validation

        # Validation 2: Check scene count matches num_cuts
        scene_count = len(plot_data["scenes"])
        if scene_count != num_cuts:
            errors.append(f"scenes 개수({scene_count})가 요청한 컷 수({num_cuts})와 불일치")

        # Validation 3: Check each scene has required fields
        for idx, scene in enumerate(plot_data["scenes"]):
            scene_id = scene.get("scene_id", f"scene_{idx}")

            # Check text field
            if "text" not in scene or not scene["text"].strip():
                errors.append(f"{scene_id}: text 필드가 비어있음")

            # Mode-specific validation
            if mode in ["general", "ad"]:
                # General/Ad Mode: image_prompt required
                if "image_prompt" not in scene:
                    errors.append(f"{scene_id}: image_prompt 필드 없음")
                elif scene.get("image_prompt") is None:
                    errors.append(f"{scene_id}: image_prompt가 None")
                # Note: empty string is allowed for image reuse

            elif mode == "story":
                # Story Mode: background_img required
                if "background_img" not in scene or not scene["background_img"]:
                    errors.append(f"{scene_id}: background_img 필드가 비어있음")

        # Validation 4: Check layout.json structure
        if "scenes" not in layout_data or not layout_data["scenes"]:
            errors.append("layout.json에 scenes가 없거나 비어있음")

        if "timeline" not in layout_data:
            errors.append("layout.json에 timeline 필드 없음")

        # Validation 5: Check layout scenes match plot scenes count
        if "scenes" in layout_data and len(layout_data["scenes"]) != scene_count:
            errors.append(f"layout.json scenes 개수({len(layout_data['scenes'])})가 plot.json과 불일치")

        # Validation 6: Check each layout scene has images
        for idx, scene in enumerate(layout_data.get("scenes", [])):
            scene_id = scene.get("scene_id", f"scene_{idx}")
            if "images" not in scene or not scene["images"]:
                errors.append(f"{scene_id}: layout.json에 images 슬롯이 없음")

        logger.info(f"[{run_id}] Validation completed: {len(errors)} errors found")
        return errors

    except json.JSONDecodeError as e:
        errors.append(f"JSON 파싱 실패: {e}")
        return errors
    except Exception as e:
        errors.append(f"검증 중 오류 발생: {e}")
        return errors


@celery.task(bind=True, name="tasks.plan")
def plan_task(self, run_id: str, spec: dict):
    """
    Generate plot and structure from prompt.

    Workflow:
    1. Generate CSV from prompt (LLM placeholder / rule-based)
    2. Convert CSV to JSON
    3. Transition to ASSET_GENERATION
    4. Trigger fan-out for designer, composer, voice actors

    Args:
        run_id: Run identifier
        spec: RunSpec as dict
    """
    logger.info(f"[{run_id}] Starting plot generation...")
    publish_progress(run_id, state="PLOT_GENERATION", progress=0.1, log="기획자: 시나리오 작성 중...")

    try:
        # TEST: 3초 대기
        import time
        time.sleep(3)

        # Get FSM (from Redis if needed)
        fsm = get_fsm(run_id)
        if not fsm:
            raise ValueError(f"FSM not found for run {run_id}")

        # Step 1: Generate characters and plot
        logger.info(f"[{run_id}] Generating characters and plot from prompt...")
        publish_progress(run_id, progress=0.12, log="기획자: 캐릭터 및 시나리오 생성 중 (Gemini 2.5 Flash)...")
        characters_path, plot_json_path = generate_plot_with_characters(
            run_id=run_id,
            prompt=spec["prompt"],
            num_characters=spec["num_characters"],
            num_cuts=spec["num_cuts"],
            mode=spec["mode"],
            characters=spec.get("characters")  # Pass user-provided characters (Story Mode)
        )
        logger.info(f"[{run_id}] Characters generated: {characters_path}")
        logger.info(f"[{run_id}] Plot JSON generated: {plot_json_path}")
        publish_progress(run_id, progress=0.15, log=f"기획자: 캐릭터 & 시나리오 생성 완료")

        # Step 2: Convert plot.json to layout.json
        logger.info(f"[{run_id}] Converting plot.json to layout.json...")
        publish_progress(run_id, progress=0.17, log="기획자: 레이아웃 JSON 변환 중...")
        json_path = convert_plot_to_json(
            plot_json_path=str(plot_json_path),
            run_id=run_id,
            art_style=spec.get("art_style", "파스텔 수채화"),
            music_genre=spec.get("music_genre", "ambient"),
            video_title=spec.get("video_title"),
            layout_config=spec.get("layout_config")
        )
        logger.info(f"[{run_id}] Layout JSON generated: {json_path}")
        publish_progress(run_id, progress=0.2, log=f"기획자: 레이아웃 JSON 생성 완료")

        # Step 2.5: Validate plot.json and layout.json
        logger.info(f"[{run_id}] Validating plot and layout JSON...")
        publish_progress(run_id, progress=0.21, log="기획자: JSON 검증 중...")
        validation_errors = _validate_plot_json(run_id, plot_json_path, json_path, spec)

        if validation_errors:
            error_msg = f"Plot validation failed: {', '.join(validation_errors)}"
            logger.error(f"[{run_id}] {error_msg}")
            publish_progress(run_id, progress=0.21, log=f"❌ JSON 검증 실패: {validation_errors[0]}")
            raise ValueError(error_msg)

        logger.info(f"[{run_id}] ✓ JSON validation passed")
        publish_progress(run_id, progress=0.22, log="✓ JSON 검증 완료")

        # Update FSM artifacts
        from app.main import runs
        if run_id in runs:
            runs[run_id]["artifacts"]["characters_path"] = str(characters_path)
            runs[run_id]["artifacts"]["plot_json_path"] = str(plot_json_path)
            runs[run_id]["artifacts"]["json_path"] = str(json_path)
            runs[run_id]["progress"] = 0.22

        # Step 3: Transition to ASSET_GENERATION
        publish_progress(run_id, progress=0.22, log="에셋 생성 단계로 전환 중...")
        if fsm.transition_to(RunState.ASSET_GENERATION):
            logger.info(f"[{run_id}] Transitioned to ASSET_GENERATION")
            publish_progress(run_id, state="ASSET_GENERATION", progress=0.25, log="에셋 생성 시작 (디자이너, 작곡가, 성우)")

            # Update state
            if run_id in runs:
                runs[run_id]["state"] = fsm.current_state.value

            # Step 4: Fan-out to asset generation tasks
            from app.tasks.designer import designer_task
            from app.tasks.composer import composer_task
            from app.tasks.voice import voice_task
            from app.tasks.director import director_task

            # Convert Path to string for JSON serialization
            json_path_str = str(json_path)

            # Create chord: parallel tasks → director callback
            asset_tasks = group(
                designer_task.s(run_id, json_path_str, spec),
                composer_task.s(run_id, json_path_str, spec),
                voice_task.s(run_id, json_path_str, spec),
            )

            # Chord: when all complete, trigger director
            workflow = chord(asset_tasks)(director_task.s(run_id, json_path_str))

            logger.info(f"[{run_id}] Asset generation chord started")

        return {
            "run_id": run_id,
            "plot_json_path": str(plot_json_path),
            "json_path": str(json_path),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"[{run_id}] Plan task failed: {e}", exc_info=True)

        # Mark FSM as failed
        if fsm := get_fsm(run_id):
            fsm.fail(str(e))

        # Update run state
        from app.main import runs
        if run_id in runs:
            runs[run_id]["state"] = "FAILED"
            runs[run_id]["logs"].append(f"Planning failed: {e}")

        raise
