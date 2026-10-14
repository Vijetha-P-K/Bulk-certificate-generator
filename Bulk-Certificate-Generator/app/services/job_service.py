"""Bulk processing logic for a certificate generation job."""
from datetime import datetime

from app.database import SessionLocal
from app.models import Certificate, CertificateStatus, Job, JobStatus
from app.services import pdf_generator


def process_job(job_id: int) -> None:
    """
    Process every certificate belonging to `job_id`.

    Design notes
    ------------
    * Runs in its own DB session so it is safe to call from a background task.
    * Each certificate is committed individually, which means the job counters
      are observable while the job is still running (progress tracking).
    * A failure on one certificate is caught, recorded against that certificate
      and does NOT stop the remaining recipients from being processed.
    """
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return

        job.status = JobStatus.PROCESSING.value
        db.commit()

        certificate_ids = [
            row[0]
            for row in db.query(Certificate.id)
            .filter(Certificate.job_id == job_id)
            .order_by(Certificate.id)
            .all()
        ]

        success = 0
        failed = 0

        for cert_id in certificate_ids:
            cert = db.get(Certificate, cert_id)
            if cert is None:
                continue

            try:
                file_path = pdf_generator.generate_certificate(
                    job_id=job_id,
                    certificate_id=cert.id,
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    event_date=job.event_date,
                )
                cert.file_path = file_path
                cert.status = CertificateStatus.SUCCESS.value
                cert.error_message = None
                success += 1
            except Exception as exc:  # noqa: BLE001 - one failure must not kill the job
                db.rollback()
                cert = db.get(Certificate, cert_id)
                if cert is not None:
                    cert.status = CertificateStatus.FAILED.value
                    cert.file_path = None
                    cert.error_message = str(exc) or exc.__class__.__name__
                failed += 1

            db.commit()

            # Publish progress after every certificate.
            job = db.get(Job, job_id)
            job.success_count = success
            job.failed_count = failed
            db.commit()

        job = db.get(Job, job_id)
        job.success_count = success
        job.failed_count = failed
        job.completed_at = datetime.utcnow()

        if failed == 0:
            job.status = JobStatus.COMPLETED.value
        elif success == 0:
            job.status = JobStatus.FAILED.value
        else:
            job.status = JobStatus.COMPLETED_WITH_ERRORS.value

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()