"""
Cancel API endpoint for stopping running video generation tasks.
"""
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def cancel_run_handler(run_id: str, runs: dict):
    """
    Cancel a running video generation task.
    Revokes all pending/running Celery tasks and marks FSM as FAILED.

    Args:
        run_id: Run identifier
        runs: In-memory runs dictionary

    Returns:
        {
            "status": "success",
            "message": "Run cancelled successfully"
        }
    """
    from app.orchestrator.fsm import get_fsm, invalidate_fsm_cache
    from app.celery_app import celery
    from app.utils.progress import publish_progress

    logger.info(f"[{run_id}] Cancel requested")

    # CRITICAL: Clear in-memory cache to force reload from Redis
    invalidate_fsm_cache(run_id)

    fsm = get_fsm(run_id)
    if not fsm:
        raise HTTPException(status_code=404, detail=f"FSM not found for run {run_id}")

    # Check if already in terminal state
    if fsm.is_terminal():
        logger.info(f"[{run_id}] Run already in terminal state: {fsm.current_state.value}")
        return {
            "status": "already_terminated",
            "message": f"Run already in {fsm.current_state.value} state"
        }

    try:
        # Revoke all Celery tasks for this run_id
        # Get all active tasks from Celery
        inspect = celery.control.inspect()
        active_tasks = inspect.active()

        revoked_count = 0
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    # Check if task is for this run_id
                    if 'args' in task and run_id in str(task.get('args', '')):
                        task_id = task['id']
                        celery.control.revoke(task_id, terminate=True)
                        logger.info(f"[{run_id}] Revoked task {task_id} on worker {worker}")
                        revoked_count += 1

        # Mark FSM as FAILED
        fsm.fail("User cancelled")
        logger.info(f"[{run_id}] FSM marked as FAILED (user cancelled)")

        # Update run state in memory
        if run_id in runs:
            runs[run_id]["state"] = "FAILED"
            runs[run_id]["logs"].append("사용자가 제작을 취소했습니다")

        # Publish progress update
        publish_progress(
            run_id,
            state="FAILED",
            progress=0,
            log="제작이 취소되었습니다"
        )

        logger.info(f"[{run_id}] Run cancelled successfully (revoked {revoked_count} tasks)")

        return {
            "status": "success",
            "message": f"Run cancelled successfully (revoked {revoked_count} tasks)"
        }

    except Exception as e:
        logger.error(f"[{run_id}] Failed to cancel run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cancel run: {str(e)}")
