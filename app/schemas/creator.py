from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator
from app.workflow.states import CreatorState


class CreatorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(..., min_length=1, max_length=100, examples=["instagram", "youtube", "twitter"])
    followers: int = Field(..., ge=0)
    bio: str | None = Field(None, max_length=2000)


class CreatorRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    platform: str
    followers: int
    bio: str | None
    state: CreatorState
    qualification_score: float | None
    qualification_result: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class CreatorListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    platform: str
    followers: int
    state: CreatorState
    qualification_score: float | None
    created_at: datetime


class StateTransitionRequest(BaseModel):
    new_state: CreatorState
    notes: str | None = Field(None, max_length=500)
    changed_by: str | None = Field(None, max_length=255)


class AuditEntryRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    creator_id: str
    from_state: str
    to_state: str
    notes: str | None
    changed_by: str | None
    timestamp: datetime
