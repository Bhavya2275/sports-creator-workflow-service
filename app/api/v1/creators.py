from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.schemas.creator import (
    CreatorCreate,
    CreatorRead,
    CreatorListItem,
    StateTransitionRequest,
    AuditEntryRead,
)
from app.services import creator_service, workflow_service
from app.workflow.states import CreatorState

router = APIRouter(prefix="/creators", tags=["creators"])


@router.post("", response_model=CreatorRead, status_code=201)
async def create_creator(body: CreatorCreate, db: AsyncSession = Depends(get_db)):
    creator = await creator_service.create_creator(db, body)
    return creator


@router.get("", response_model=list[CreatorListItem])
async def list_creators(
    state: CreatorState | None = Query(None, description="Filter by workflow state"),
    platform: str | None = Query(None, description="Filter by platform"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await creator_service.list_creators(db, state=state, platform=platform, limit=limit, offset=offset)


@router.get("/{creator_id}", response_model=CreatorRead)
async def get_creator(creator_id: str, db: AsyncSession = Depends(get_db)):
    return await creator_service.get_creator(db, creator_id)


@router.patch("/{creator_id}/state", response_model=CreatorRead)
async def update_creator_state(
    creator_id: str,
    body: StateTransitionRequest,
    db: AsyncSession = Depends(get_db),
):
    creator = await workflow_service.transition_state(
        db,
        creator_id=creator_id,
        new_state=body.new_state,
        notes=body.notes,
        changed_by=body.changed_by,
    )
    return creator


@router.get("/{creator_id}/history", response_model=list[AuditEntryRead])
async def get_creator_history(creator_id: str, db: AsyncSession = Depends(get_db)):
    return await workflow_service.get_creator_history(db, creator_id)
