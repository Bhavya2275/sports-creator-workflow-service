from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_db
from app.schemas.qualification import QualifyRequest, QualificationJobResponse
from app.models.qualification_job import QualificationJob, JobStatus
from app.models.creator import Creator
from app.tasks.qualification_task import run_qualification_job
from app.core.exceptions import QualificationJobNotFoundError, CreatorNotFoundError

router = APIRouter(prefix="/qualify", tags=["qualification"])


@router.post("", response_model=QualificationJobResponse, status_code=202)
async def submit_qualification(
    body: QualifyRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an async AI qualification request.
    Returns a job_id immediately; poll GET /qualify/{job_id} for results.
    """
    # Validate creator_id if provided — fail fast before spawning a background task
    if body.creator_id is not None:
        result = await db.execute(select(Creator).where(Creator.id == body.creator_id))
        if result.scalar_one_or_none() is None:
            raise CreatorNotFoundError(body.creator_id)

    job = QualificationJob(
        creator_id=body.creator_id,
        status=JobStatus.PENDING,
        input_data=body.model_dump(),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    job_id = job.id

    background_tasks.add_task(run_qualification_job, job_id)

    return QualificationJobResponse(
        job_id=job_id,
        status=job.status,
        creator_id=job.creator_id,
        prompt_tokens=job.prompt_tokens,
        completion_tokens=job.completion_tokens,
        total_tokens=job.total_tokens,
        created_at=job.created_at,
    )


@router.get("/{job_id}", response_model=QualificationJobResponse)
async def get_qualification_result(job_id: str, db: AsyncSession = Depends(get_db)):
    """Poll for the result of a previously submitted qualification job."""
    result = await db.execute(select(QualificationJob).where(QualificationJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise QualificationJobNotFoundError(job_id)

    from app.schemas.qualification import QualificationResult
    result_obj = QualificationResult(**job.result) if job.result else None

    return QualificationJobResponse(
        job_id=job.id,
        status=job.status,
        creator_id=job.creator_id,
        result=result_obj,
        error_message=job.error_message,
        prompt_tokens=job.prompt_tokens,
        completion_tokens=job.completion_tokens,
        total_tokens=job.total_tokens,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
