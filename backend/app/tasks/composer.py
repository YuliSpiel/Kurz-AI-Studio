"""
작곡가 Agent: Music/BGM generation.
"""
import logging
import json
from pathlib import Path

from app.celery_app import celery
from app.config import settings
from app.utils.progress import publish_progress

logger = logging.getLogger(__name__)


@celery.task(bind=True, name="tasks.composer")
def composer_task(self, run_id: str, json_path: str, spec: dict):
    """
    Generate background music and SFX.

    Args:
        run_id: Run identifier
        json_path: Path to JSON layout
        spec: RunSpec as dict

    Returns:
        Dict with generated audio paths
    """
    logger.info(f"[{run_id}] Composer: Starting music generation...")
    publish_progress(run_id, progress=0.45, log="작곡가: 배경음악 생성 시작...")

    # Check stub mode
    stub_mode = spec.get("stub_music_mode", False)
    if stub_mode:
        logger.warning(f"[{run_id}] 🧪 STUB MUSIC MODE: Skipping ElevenLabs/Mubert API calls")
        publish_progress(run_id, progress=0.47, log="🧪 테스트: 더미 음원 사용 (API 생략)")

    # TEST: 3초 대기
    import time
    time.sleep(3)

    try:
        # Load JSON
        with open(json_path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        # Get music provider (stub mode bypasses all providers)
        # NOTE: Set USE_LOCAL_BGM=false in .env to enable API-based music generation
        use_local_bgm = getattr(settings, 'USE_LOCAL_BGM', True)

        if stub_mode:
            # Use stub client in test mode
            from app.providers.music.stub_client import StubMusicClient
            client = StubMusicClient()
            logger.info(f"[{run_id}] Using Stub client (test mode)")
        elif use_local_bgm:
            # Use local BGM assets (default - no API calls)
            from app.providers.music.local_bgm_client import LocalBGMClient
            client = LocalBGMClient()
            logger.info(f"[{run_id}] Using Local BGM client (selecting from assets)")
        # === API-based music generation (disabled by default) ===
        # To enable: set USE_LOCAL_BGM=false in .env
        elif settings.ELEVENLABS_API_KEY:
            # ElevenLabs Sound Effects로 BGM 생성 (저렴하고 TTS와 통합)
            from app.providers.music.elevenlabs_music_client import ElevenLabsMusicClient
            client = ElevenLabsMusicClient(api_key=settings.ELEVENLABS_API_KEY)
            logger.info(f"[{run_id}] Using ElevenLabs for music generation")
        elif settings.MUBERT_LICENSE:
            # Mubert 폴백
            from app.providers.music.mubert_client import MubertClient
            client = MubertClient(api_key=settings.MUBERT_LICENSE)
            logger.info(f"[{run_id}] Using Mubert for music generation")
        else:
            # Stub 모드 (API 키 없음)
            from app.providers.music.stub_client import StubMusicClient
            client = StubMusicClient()
            logger.warning(f"[{run_id}] Using Stub mode for music (no API keys)")

        audio_results = []

        # Generate global BGM if needed
        total_duration_ms = layout.get("timeline", {}).get("total_duration_ms", 30000)

        # Check for bgm_prompt in metadata (General/Ad Mode)
        metadata = layout.get("metadata", {})
        bgm_prompt = metadata.get("bgm_prompt")

        if bgm_prompt:
            # Use detailed BGM prompt from plot generation (General/Ad Mode)
            music_genre = bgm_prompt  # Pass full prompt as genre
            mood = None  # Don't override with generic mood
            logger.info(f"[{run_id}] Generating BGM from prompt: {bgm_prompt}")
        else:
            # Fallback to generic genre+mood (Story Mode or fallback)
            music_genre = spec.get("music_genre", "ambient")
            mood = "cinematic"
            logger.info(f"[{run_id}] Generating BGM: {music_genre}, {mood}, {total_duration_ms}ms")

        # Generate music in run_id folder
        audio_dir = Path(f"app/data/outputs/{run_id}/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)

        if mood:
            bgm_path = client.generate_music(
                genre=music_genre,
                mood=mood,
                duration_ms=total_duration_ms,
                output_filename=str(audio_dir / "global_bgm.mp3")
            )
        else:
            # Use prompt-based generation (pass as genre)
            bgm_path = client.generate_music(
                genre=music_genre,
                mood="",  # Empty mood to let prompt take precedence
                duration_ms=total_duration_ms,
                output_filename=str(audio_dir / "global_bgm.mp3")
            )

        # Update JSON
        if "global_bgm" not in layout or layout["global_bgm"] is None:
            layout["global_bgm"] = {
                "bgm_id": "global_bgm",
                "genre": music_genre,
                "mood": "cinematic",
                "audio_url": str(bgm_path),
                "start_ms": 0,
                "duration_ms": total_duration_ms,
                "volume": 0.3
            }
        else:
            layout["global_bgm"]["audio_url"] = str(bgm_path)

        publish_progress(run_id, progress=0.5, log=f"작곡가: 배경음악 생성 완료 - {bgm_path}")

        audio_results.append({
            "type": "bgm",
            "id": "global_bgm",
            "path": str(bgm_path)
        })

        logger.info(f"[{run_id}] BGM generated: {bgm_path}")

        # Generate SFX for scenes (placeholder)
        for scene in layout.get("scenes", []):
            for sfx in scene.get("sfx", []):
                # For now, use placeholder SFX
                sfx_path = Path("app/data/samples/placeholder_sfx.mp3")
                sfx["audio_url"] = str(sfx_path)

        # Save updated JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(layout, f, indent=2, ensure_ascii=False)

        logger.info(f"[{run_id}] Composer: Completed")

        # Update progress
        from app.main import runs
        if run_id in runs:
            runs[run_id]["artifacts"]["audio"] = audio_results

        return {
            "run_id": run_id,
            "agent": "composer",
            "audio": audio_results,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"[{run_id}] Composer task failed: {e}", exc_info=True)
        raise
