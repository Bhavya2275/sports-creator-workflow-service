from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.creator import Creator
from app.schemas.creator import CreatorCreate
from app.workflow.states import CreatorState
from app.core.exceptions import CreatorNotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


async def create_creator(db: AsyncSession, data: CreatorCreate) -> Creator:
    creator = Creator(
        name=data.name,
        platform=data.platform,
        followers=data.followers,
        bio=data.bio,
        state=CreatorState.DISCOVERED,
    )
    db.add(creator)
    await db.flush()  # get the generated id before commit
    logger.info("creator_created", creator_id=creator.id, name=creator.name)
    return creator


async def get_creator(db: AsyncSession, creator_id: str) -> Creator:
    result = await db.execute(select(Creator).where(Creator.id == creator_id))
    creator = result.scalar_one_or_none()
    if creator is None:
        raise CreatorNotFoundError(creator_id)
    return creator


async def list_creators(
    db: AsyncSession,
    state: CreatorState | None = None,
    platform: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Creator]:
    query = select(Creator)
    if state:
        query = query.where(Creator.state == state)
    if platform:
        query = query.where(Creator.platform == platform)
    query = query.order_by(Creator.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())
