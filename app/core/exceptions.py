from fastapi import HTTPException, status


class CreatorNotFoundError(HTTPException):
    def __init__(self, creator_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Creator '{creator_id}' not found.",
        )


class InvalidStateTransitionError(HTTPException):
    def __init__(self, from_state: str, to_state: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Transition from '{from_state}' to '{to_state}' is not allowed.",
        )


class TerminalStateError(HTTPException):
    def __init__(self, state: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Creator is in terminal state '{state}' and cannot be transitioned further.",
        )


class AIServiceError(HTTPException):
    def __init__(self, detail: str = "AI qualification service failed."):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        )


class QualificationJobNotFoundError(HTTPException):
    def __init__(self, job_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Qualification job '{job_id}' not found.",
        )
