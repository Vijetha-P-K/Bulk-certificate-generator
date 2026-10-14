"""Certificate generation and retrieval."""
from pathlib import Path


def test_certificates_are_generated_as_pdf_files(client, sample_payload):
    job_id = client.post("/jobs", json=sample_payload).json()["job_id"]

    certificates = client.get(f"/jobs/{job_id}/certificates").json()

    assert len(certificates) == 2
    for cert in certificates:
        assert cert["status"] == "success"
        assert cert["error_message"] is None
        assert cert["download_url"] == f"/certificates/{cert['id']}"


def test_generated_certificate_can_be_downloaded(client, sample_payload):
    job_id = client.post("/jobs", json=sample_payload).json()["job_id"]
    certificates = client.get(f"/jobs/{job_id}/certificates").json()

    download = client.get(certificates[0]["download_url"])

    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")
    assert len(download.content) > 1000


def test_unknown_certificate_returns_404(client):
    assert client.get("/certificates/999999").status_code == 404


def test_second_certificate_has_different_content(client, sample_payload):
    job_id = client.post("/jobs", json=sample_payload).json()["job_id"]
    certificates = client.get(f"/jobs/{job_id}/certificates").json()

    first = client.get(certificates[0]["download_url"]).content
    second = client.get(certificates[1]["download_url"]).content

    assert first != second


def test_pdf_file_exists_on_disk(client, sample_payload):
    job_id = client.post("/jobs", json=sample_payload).json()["job_id"]
    certificate_id = client.get(f"/jobs/{job_id}/certificates").json()[0]["id"]

    from app.database import SessionLocal
    from app.models import Certificate

    db = SessionLocal()
    try:
        cert = db.get(Certificate, certificate_id)
        path = Path(cert.file_path)
    finally:
        db.close()

    assert path.is_file()
    assert path.stat().st_size > 0