import pytest
from app.workflow.states import CreatorState
from app.workflow.transitions import is_valid_transition, get_allowed_next_states


def test_valid_forward_transitions():
    assert is_valid_transition(CreatorState.DISCOVERED, CreatorState.QUALIFIED)
    assert is_valid_transition(CreatorState.QUALIFIED, CreatorState.OUTREACH_PENDING)
    assert is_valid_transition(CreatorState.OUTREACH_PENDING, CreatorState.CONTACTED)
    assert is_valid_transition(CreatorState.CONTACTED, CreatorState.INTERESTED)
    assert is_valid_transition(CreatorState.INTERESTED, CreatorState.ONBOARDED)


def test_reject_allowed_from_any_non_terminal():
    non_terminal = [
        CreatorState.DISCOVERED,
        CreatorState.QUALIFIED,
        CreatorState.OUTREACH_PENDING,
        CreatorState.CONTACTED,
        CreatorState.INTERESTED,
    ]
    for state in non_terminal:
        assert is_valid_transition(state, CreatorState.REJECTED), f"REJECTED should be allowed from {state}"


def test_invalid_skip_transitions():
    assert not is_valid_transition(CreatorState.DISCOVERED, CreatorState.ONBOARDED)
    assert not is_valid_transition(CreatorState.DISCOVERED, CreatorState.CONTACTED)
    assert not is_valid_transition(CreatorState.QUALIFIED, CreatorState.INTERESTED)


def test_terminal_states_have_no_transitions():
    assert not is_valid_transition(CreatorState.ONBOARDED, CreatorState.REJECTED)
    assert not is_valid_transition(CreatorState.REJECTED, CreatorState.DISCOVERED)
    assert get_allowed_next_states(CreatorState.ONBOARDED) == []
    assert get_allowed_next_states(CreatorState.REJECTED) == []


def test_terminal_state_property():
    assert CreatorState.ONBOARDED.is_terminal
    assert CreatorState.REJECTED.is_terminal
    assert not CreatorState.DISCOVERED.is_terminal
    assert not CreatorState.INTERESTED.is_terminal
