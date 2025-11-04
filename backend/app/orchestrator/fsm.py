"""
Finite State Machine (FSM) for AutoShorts orchestration.
Manages state transitions: INIT → PLOT_PLANNING → ASSET_GENERATION → RECOVER → RENDERING → END
"""
import logging
from enum import Enum
from typing import Optional, Dict, Callable

logger = logging.getLogger(__name__)


class RunState(Enum):
    """State definitions for shorts generation workflow."""
    INIT = "INIT"
    PLOT_PLANNING = "PLOT_PLANNING"
    ASSET_GENERATION = "ASSET_GENERATION"
    RECOVER = "RECOVER"
    RENDERING = "RENDERING"
    END = "END"
    FAILED = "FAILED"


class FSM:
    """
    Finite State Machine for orchestrating shorts generation workflow.

    State transitions:
    INIT → PLOT_PLANNING → ASSET_GENERATION → RENDERING → END
                ↓               ↓
              FAILED         RECOVER → (retry)
    """

    # Valid state transitions
    TRANSITIONS: Dict[RunState, list[RunState]] = {
        RunState.INIT: [RunState.PLOT_PLANNING, RunState.FAILED],
        RunState.PLOT_PLANNING: [RunState.ASSET_GENERATION, RunState.RECOVER, RunState.FAILED],
        RunState.ASSET_GENERATION: [RunState.RENDERING, RunState.RECOVER, RunState.FAILED],
        RunState.RECOVER: [
            RunState.PLOT_PLANNING,
            RunState.ASSET_GENERATION,
            RunState.RENDERING,
            RunState.FAILED
        ],
        RunState.RENDERING: [RunState.END, RunState.RECOVER, RunState.FAILED],
        RunState.END: [],
        RunState.FAILED: [RunState.RECOVER],
    }

    def __init__(self, run_id: str, initial_state: RunState = RunState.INIT):
        """
        Initialize FSM for a run.

        Args:
            run_id: Unique run identifier
            initial_state: Starting state (default: INIT)
        """
        self.run_id = run_id
        self.current_state = initial_state
        self.history: list[RunState] = [initial_state]
        self.metadata: Dict = {}

        logger.info(f"FSM initialized for run {run_id} in state {initial_state.value}")

    def can_transition_to(self, target_state: RunState) -> bool:
        """
        Check if transition to target state is valid.

        Args:
            target_state: Target state

        Returns:
            True if transition is allowed, False otherwise
        """
        allowed_states = self.TRANSITIONS.get(self.current_state, [])
        return target_state in allowed_states

    def transition_to(
        self,
        target_state: RunState,
        guard: Optional[Callable[[], bool]] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Attempt to transition to target state.

        Args:
            target_state: Target state
            guard: Optional guard function that must return True for transition
            metadata: Optional metadata to attach to transition

        Returns:
            True if transition succeeded, False otherwise
        """
        # Check if transition is allowed
        if not self.can_transition_to(target_state):
            logger.warning(
                f"Invalid transition for run {self.run_id}: "
                f"{self.current_state.value} → {target_state.value}"
            )
            return False

        # Check guard condition
        if guard and not guard():
            logger.info(
                f"Guard failed for transition {self.run_id}: "
                f"{self.current_state.value} → {target_state.value}"
            )
            return False

        # Perform transition
        old_state = self.current_state
        self.current_state = target_state
        self.history.append(target_state)

        if metadata:
            self.metadata.update(metadata)

        logger.info(
            f"State transition for run {self.run_id}: "
            f"{old_state.value} → {target_state.value}"
        )

        return True

    def fail(self, error_message: str):
        """
        Mark run as failed.

        Args:
            error_message: Error description
        """
        self.transition_to(RunState.FAILED, metadata={"error": error_message})
        logger.error(f"Run {self.run_id} failed: {error_message}")

    def can_recover(self) -> bool:
        """Check if run can enter recovery state."""
        return self.can_transition_to(RunState.RECOVER)

    def get_retry_state(self) -> Optional[RunState]:
        """
        Determine which state to retry after recovery.

        Returns:
            State to retry, or None if cannot recover
        """
        if len(self.history) < 2:
            return None

        # Get the state before FAILED or RECOVER
        for state in reversed(self.history[:-1]):
            if state not in [RunState.FAILED, RunState.RECOVER]:
                return state

        return None

    def is_terminal(self) -> bool:
        """Check if current state is terminal (END or FAILED)."""
        return self.current_state in [RunState.END, RunState.FAILED]

    def __repr__(self) -> str:
        return f"FSM(run_id={self.run_id}, state={self.current_state.value})"


# Global FSM registry (production: use Redis/DB)
_fsm_registry: Dict[str, FSM] = {}


def get_fsm(run_id: str) -> Optional[FSM]:
    """Get FSM instance for run_id."""
    return _fsm_registry.get(run_id)


def register_fsm(fsm: FSM):
    """Register FSM instance."""
    _fsm_registry[fsm.run_id] = fsm


def unregister_fsm(run_id: str):
    """Unregister FSM instance."""
    _fsm_registry.pop(run_id, None)
