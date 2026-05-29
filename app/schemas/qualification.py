from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class QualifyRequest(BaseModel):
    creator_bio: str = Field(..., min_length=10, max_length=2000, description="Creator's bio or description")
    platform: str = Field(..., min_length=1, max_length=100, examples=["instagram", "youtube"])
    followers: int = Field(..., ge=0, description="Number of followers")
    recent_posts: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Sample recent post descriptions or captions",
    )
    creator_id: str | None = Field(None, description="Optional: link result to an existing creator")


class QualificationResult(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0, description="Qualification score 0-100")
    is_qualified: bool
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    category: Literal[
        "sports_creator",
        "fitness_creator",
        "sports_commentary",
        "fan_page",
        "athlete",
        "general_lifestyle",
        "unrelated",
        "unclear",
    ]
    reasoning: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    sports_relevance: str = Field(description="How relevant this creator is for a sports platform")
    recommended_next_state: Literal["QUALIFIED", "REJECTED"]
    suggested_outreach_angle: str
    risk_flags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result_consistency(self):
        expected_qualified = self.score >= 60
        if self.is_qualified != expected_qualified:
            raise ValueError("is_qualified must be true only when score is >= 60")

        expected_next_state = "QUALIFIED" if self.is_qualified else "REJECTED"
        if self.recommended_next_state != expected_next_state:
            raise ValueError("recommended_next_state must match is_qualified")

        if not self.is_qualified and self.suggested_outreach_angle:
            raise ValueError("suggested_outreach_angle must be empty when creator is not qualified")

        return self


class QualificationJobResponse(BaseModel):
    job_id: str
    status: str
    creator_id: str | None
    result: QualificationResult | None = None
    error_message: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    created_at: datetime
    completed_at: datetime | None = None
