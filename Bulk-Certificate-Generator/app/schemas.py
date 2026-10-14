"""Pydantic request/response models."""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.config import MAX_RECIPIENTS


class Recipient(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr


class JobCreateRequest(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=200)
    date: date
    recipients: List[Recipient] = Field(..., min_length=1, max_length=MAX_RECIPIENTS)


class JobCreateResponse(BaseModel):
    job_id: int
    status: str
    total_count: int
    success_count: int
    failed_count: int


class CertificateOut(BaseModel):
    id: int
    recipient_name: str
    recipient_email: str
    status: str
    error_message: Optional[str] = None
    download_url: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: int
    event_name: str
    date: str
    status: str
    total_count: int
    success_count: int
    failed_count: int
    processed_count: int
    progress_percent: float
    certificates: List[CertificateOut]