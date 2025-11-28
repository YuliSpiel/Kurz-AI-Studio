"""
State transition router endpoints (for testing and manual control).
In production, state transitions are primarily driven by Celery tasks.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.orchestrator.fsm import FSM, RunState, get_fsm, register_fsm

router = APIRouter(prefix="/api/fsm", tags=["FSM"])


class TransitionRequest(BaseModel):
    """Request to transition to a new state."""
    target_state: str
    metadata: dict = {}


@router.post("/{run_id}/transition")
async def transition_state(run_id: str, request: TransitionRequest):
    """
    Manually transition a run to a new state (testing only).

    Args:
        run_id: Run identifier
        request: Transition request with target state
    """
    fsm = get_fsm(run_id)
    if not fsm:
        raise HTTPException(status_code=404, detail="FSM not found for run")

    try:
        target_state = RunState(request.target_state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state")

    success = fsm.transition_to(target_state, metadata=request.metadata)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {fsm.current_state.value} to {target_state.value}"
        )

    return {
        "run_id": run_id,
        "previous_state": fsm.history[-2].value if len(fsm.history) > 1 else None,
        "current_state": fsm.current_state.value,
        "history": [s.value for s in fsm.history]
    }


@router.get("/{run_id}/state")
async def get_state(run_id: str):
    """Get current FSM state for a run."""
    fsm = get_fsm(run_id)
    if not fsm:
        raise HTTPException(status_code=404, detail="FSM not found for run")

    return {
        "run_id": run_id,
        "current_state": fsm.current_state.value,
        "history": [s.value for s in fsm.history],
        "is_terminal": fsm.is_terminal(),
        "can_recover": fsm.can_recover(),
        "metadata": fsm.metadata
    }


@router.post("/{run_id}/fail")
async def fail_run(run_id: str, error_message: str = "Manual failure"):
    """Mark a run as failed."""
    fsm = get_fsm(run_id)
    if not fsm:
        raise HTTPException(status_code=404, detail="FSM not found for run")

    fsm.fail(error_message)

    return {
        "run_id": run_id,
        "current_state": fsm.current_state.value,
        "error": error_message
    }
