"""Endpoint for downloading a generated certificate."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Certificate, CertificateStatus

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("/{certificate_id}")
def download_certificate(certificate_id: int, db: Session = Depends(get_db)):
    """Stream the generated PDF for a certificate."""
    cert = db.get(Certificate, certificate_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if cert.status != CertificateStatus.SUCCESS.value:
        detail = f"Certificate is not available (status={cert.status})"
        if cert.error_message:
            detail = f"{detail}: {cert.error_message}"
        raise HTTPException(status_code=409, detail=detail)

    if not cert.file_path:
        raise HTTPException(status_code=409, detail="Certificate file path is missing")

    path = Path(cert.file_path)
    if not path.is_file():
        raise HTTPException(status_code=410, detail="Certificate file no longer exists on disk")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=path.name,
    )