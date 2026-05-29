from datetime import datetime, timezone
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.qualification_job import QualificationJob, JobStatus
from app.models.creator import Creator
from app.schemas.qualification import QualifyRequest
from app.services.ai_service import qualify_creator
from app.core.logging import get_logger

logger = get_logger(__name__)


async def run_qualification_job(job_id: str) -> None:
    """Background task: call AI, persist result, update job status."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(QualificationJob).where(QualificationJob.id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            logger.error("qualification_job_not_found", job_id=job_id)
            return

        job.status = JobStatus.RUNNING
        await db.commit()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(QualificationJob).where(QualificationJob.id == job_id))
        job = result.scalar_one_or_none()

        try:
            request = QualifyRequest(**job.input_data)
            ai_response = await qualify_creator(request)
            qualification = ai_response.result

            job.status = JobStatus.COMPLETED
            job.result = qualification.model_dump()
            job.score = qualification.score
            job.prompt_tokens = ai_response.prompt_tokens
            job.completion_tokens = ai_response.completion_tokens
            job.total_tokens = ai_response.total_tokens
            job.completed_at = datetime.now(timezone.utc)

            # Optionally write score back to the linked Creator
            if job.creator_id:
                creator_result = await db.execute(
                    select(Creator).where(Creator.id == job.creator_id)
                )
                creator = creator_result.scalar_one_or_none()
                if creator:
                    creator.qualification_score = qualification.score
                    creator.qualification_result = qualification.model_dump()

            logger.info(
                "qualification_job_completed",
                job_id=job_id,
                score=qualification.score,
                prompt_tokens=job.prompt_tokens,
                completion_tokens=job.completion_tokens,
                total_tokens=job.total_tokens,
            )

        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            logger.error("qualification_job_failed", job_id=job_id, error=str(exc))

        await db.commit()
