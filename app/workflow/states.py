from enum import Enum


class CreatorState(str, Enum):
    DISCOVERED = "DISCOVERED"
    QUALIFIED = "QUALIFIED"
    OUTREACH_PENDING = "OUTREACH_PENDING"
    CONTACTED = "CONTACTED"
    INTERESTED = "INTERESTED"
    ONBOARDED = "ONBOARDED"
    REJECTED = "REJECTED"

    @property
    def is_terminal(self) -> bool:
        return self in (CreatorState.ONBOARDED, CreatorState.REJECTED)
