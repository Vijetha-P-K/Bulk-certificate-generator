"""Endpoints for creating jobs and inspecting their progress."""
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import config
from app.database import get_db
from app.models import Certificate, CertificateStatus, Job, JobStatus
from app.schemas import (
    CertificateOut,
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
)
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_certificate_out(cert: Certificate) -> CertificateOut:
    return CertificateOut(
        id=cert.id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        status=cert.status,
        error_message=cert.error_message,
        download_url=(
            f"/certificates/{cert.id}"
            if cert.status == CertificateStatus.SUCCESS.value
            else None
        ),
    )


@router.post("", response_model=JobCreateResponse, status_code=201)
def create_job(
    payload: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Accept a bulk certificate generation request."""
    job = Job(
        event_name=payload.event_name.strip(),
        event_date=payload.date.isoformat(),
        status=JobStatus.PENDING.value,
        total_count=len(payload.recipients),
        success_count=0,
        failed_count=0,
    )
    db.add(job)
    db.flush()  # assign job.id

    db.add_all(
        [
            Certificate(
                job_id=job.id,
                recipient_name=recipient.name.strip(),
                recipient_email=str(recipient.email),
                status=CertificateStatus.PENDING.value,
            )
            for recipient in payload.recipients
        ]
    )
    db.commit()

    job_id = job.id

    if config.is_inline_mode():
        # Used by the test suite: deterministic, no polling required.
        job_service.process_job(job_id)
        db.expire_all()
        job = db.get(Job, job_id)
    else:
        # Default: hand off to FastAPI's background task runner.
        background_tasks.add_task(job_service.process_job, job_id)

    return JobCreateResponse(
        job_id=job_id,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Return job status, progress counters and per-certificate results."""
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    certificates = (
        db.query(Certificate)
        .filter(Certificate.job_id == job_id)
        .order_by(Certificate.id)
        .all()
    )

    processed = job.success_count + job.failed_count
    progress = round(processed / job.total_count * 100, 2) if job.total_count else 0.0

    return JobStatusResponse(
        job_id=job.id,
        event_name=job.event_name,
        date=job.event_date,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        processed_count=processed,
        progress_percent=progress,
        certificates=[_to_certificate_out(c) for c in certificates],
    )


@router.get("/{job_id}/certificates", response_model=List[CertificateOut])
def list_job_certificates(
    job_id: int,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    """List certificates for a job, optionally filtered by status."""
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    query = db.query(Certificate).filter(Certificate.job_id == job_id)
    if status_filter:
        query = query.filter(Certificate.status == status_filter)

    certificates = query.order_by(Certificate.id).all()
    return [_to_certificate_out(c) for c in certificates]