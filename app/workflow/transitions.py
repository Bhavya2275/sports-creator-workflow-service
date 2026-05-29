from typing import Dict, List
from app.workflow.states import CreatorState

# Defines every legal "from → to" move in the workflow.
# Terminal states (ONBOARDED, REJECTED) have empty lists — no exit.
ALLOWED_TRANSITIONS: Dict[CreatorState, List[CreatorState]] = {
    CreatorState.DISCOVERED:       [CreatorState.QUALIFIED,        CreatorState.REJECTED],
    CreatorState.QUALIFIED:        [CreatorState.OUTREACH_PENDING, CreatorState.REJECTED],
    CreatorState.OUTREACH_PENDING: [CreatorState.CONTACTED,        CreatorState.REJECTED],
    CreatorState.CONTACTED:        [CreatorState.INTERESTED,       CreatorState.REJECTED],
    CreatorState.INTERESTED:       [CreatorState.ONBOARDED,        CreatorState.REJECTED],
    CreatorState.ONBOARDED:        [],
    CreatorState.REJECTED:         [],
}


def is_valid_transition(from_state: CreatorState, to_state: CreatorState) -> bool:
    return to_state in ALLOWED_TRANSITIONS.get(from_state, [])


def get_allowed_next_states(from_state: CreatorState) -> List[CreatorState]:
    return ALLOWED_TRANSITIONS.get(from_state, [])
