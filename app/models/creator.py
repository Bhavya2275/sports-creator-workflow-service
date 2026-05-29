import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.workflow.states import CreatorState


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Creator(Base):
    __tablename__ = "creators"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    followers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bio: Mapped[str] = mapped_column(String(2000), nullable=True)

    state: Mapped[CreatorState] = mapped_column(
        SAEnum(CreatorState, name="creator_state_enum"),
        nullable=False,
        default=CreatorState.DISCOVERED,
    )

    # Filled in after AI qualification
    qualification_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    qualification_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    def __repr__(self) -> str:
        return f"<Creator id={self.id} name={self.name!r} state={self.state}>"
