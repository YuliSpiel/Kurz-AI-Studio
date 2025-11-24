"""
Progress update utility for Celery tasks.
Publishes updates to Redis pub/sub which are then broadcast to WebSocket clients.
"""
import logging
import redis
import orjson
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# Sync database engine for Celery tasks (gevent compatible)
_sync_engine = None
_sync_session_maker = None


def get_sync_session_maker():
    """Get or create sync database session maker for Celery tasks."""
    global _sync_engine, _sync_session_maker
    if _sync_engine is None:
        # Convert async DATABASE_URL to sync URL using psycopg (v3) driver
        sync_db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")
        _sync_engine = create_engine(
            sync_db_url,
            echo=False,
            pool_pre_ping=True,
        )
        _sync_session_maker = sessionmaker(
            _sync_engine,
            expire_on_commit=False,
        )
    return _sync_session_maker

# Sync Redis client for Celery tasks
_redis_client = None


def get_redis_client():
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        # Handle SSL for rediss:// URLs (Upstash, etc.)
        redis_url = settings.REDIS_URL
        ssl_params = {}
        if redis_url.startswith("rediss://"):
            # Use string "none" instead of ssl.CERT_NONE for redis-py
            ssl_params["ssl_cert_reqs"] = "none"

        _redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=False,  # We'll handle encoding ourselves
            **ssl_params
        )
    return _redis_client


def publish_progress(
    run_id: str,
    state: str = None,
    progress: float = None,
    log: str = None,
    artifacts: dict = None
):
    """
    Publish progress update to Redis pub/sub AND update database.

    This function is called by Celery tasks to send progress updates
    to the FastAPI server, which then broadcasts them to WebSocket clients.
    Also syncs state and progress to the database Run model.

    Args:
        run_id: Run identifier
        state: FSM state (optional)
        progress: Progress value 0.0-1.0 (optional)
        log: Log message (optional)
        artifacts: Artifacts dict to update (optional)
    """
    try:
        client = get_redis_client()

        message = {"run_id": run_id}
        if state:
            message["state"] = state
        if progress is not None:
            message["progress"] = progress
        if log:
            message["log"] = log
        if artifacts:
            message["artifacts"] = artifacts

        # Publish to Redis channel
        client.publish(
            "autoshorts:progress",
            orjson.dumps(message)
        )

        logger.debug(f"[{run_id}] Published progress: state={state}, progress={progress}, artifacts={bool(artifacts)}")

    except Exception as e:
        logger.error(f"Failed to publish progress for {run_id}: {e}")
        # Don't raise - progress updates are non-critical

    # Update database if state, progress, or video_url changed
    video_url = artifacts.get("video_url") if artifacts else None
    if state is not None or progress is not None or video_url:
        try:
            _update_run_in_db_sync(run_id, state, progress, video_url)
        except Exception as e:
            logger.error(f"Failed to update database for {run_id}: {e}")
            # Don't raise - database updates are non-critical


def _update_run_in_db_sync(run_id: str, state: str = None, progress: float = None, video_url: str = None):
    """
    Update Run model in database with current state/progress/video_url (sync version for Celery).

    Args:
        run_id: Run identifier
        state: FSM state (optional)
        progress: Progress value 0.0-1.0 (optional)
        video_url: Video URL path (optional)
    """
    from app.models.run import Run, RunState

    session_maker = get_sync_session_maker()
    with session_maker() as db:
        try:
            # Find the run
            result = db.execute(
                select(Run).where(Run.run_id == run_id)
            )
            run = result.scalars().first()

            if not run:
                logger.warning(f"[{run_id}] Run not found in database")
                return

            # Update state if provided
            if state:
                # Map FSM state to DB state
                # FSM uses "END" but DB uses "COMPLETED"
                if state == "END":
                    state = "COMPLETED"

                try:
                    db_state = RunState(state)
                    run.state = db_state
                    logger.info(f"[{run_id}] Updated DB state to {state}")
                except ValueError:
                    logger.warning(f"[{run_id}] Invalid state for DB: {state}")

            # Update progress if provided (convert 0.0-1.0 to 0-100)
            if progress is not None:
                run.progress = int(progress * 100)
                logger.info(f"[{run_id}] Updated DB progress to {run.progress}%")

            # Update video_url if provided
            if video_url:
                run.video_url = video_url
                logger.info(f"[{run_id}] Updated DB video_url to {video_url}")

            db.commit()

        except Exception as e:
            logger.error(f"[{run_id}] Database update failed: {e}")
            db.rollback()
            raise
