from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.creator import Creator
from app.models.audit import WorkflowAudit
from app.workflow.states import CreatorState
from app.workflow.transitions import is_valid_transition
from app.core.exceptions import (
    CreatorNotFoundError,
    InvalidStateTransitionError,
    TerminalStateError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


async def transition_state(
    db: AsyncSession,
    creator_id: str,
    new_state: CreatorState,
    notes: str | None = None,
    changed_by: str | None = None,
) -> Creator:
    result = await db.execute(select(Creator).where(Creator.id == creator_id))
    creator = result.scalar_one_or_none()
    if creator is None:
        raise CreatorNotFoundError(creator_id)

    current = CreatorState(creator.state)

    if current.is_terminal:
        raise TerminalStateError(current.value)

    if not is_valid_transition(current, new_state):
        raise InvalidStateTransitionError(current.value, new_state.value)

    old_state = current.value
    creator.state = new_state

    audit = WorkflowAudit(
        creator_id=creator_id,
        from_state=old_state,
        to_state=new_state.value,
        notes=notes,
        changed_by=changed_by,
    )
    db.add(audit)

    logger.info("state_transition", creator_id=creator_id, from_state=old_state, to_state=new_state.value)
    return creator


async def get_creator_history(db: AsyncSession, creator_id: str) -> list[WorkflowAudit]:
    result = await db.execute(select(Creator).where(Creator.id == creator_id))
    if result.scalar_one_or_none() is None:
        raise CreatorNotFoundError(creator_id)

    audit_result = await db.execute(
        select(WorkflowAudit)
        .where(WorkflowAudit.creator_id == creator_id)
        .order_by(WorkflowAudit.timestamp.asc())
    )
    return list(audit_result.scalars().all())
