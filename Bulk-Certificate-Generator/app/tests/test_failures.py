"""An individual certificate failure must not stop the rest of the job."""
from app.services import pdf_generator


def test_one_failure_does_not_block_other_recipients(client, monkeypatch):
    real_generate = pdf_generator.generate_certificate

    def flaky_generate(*, recipient_name, **kwargs):
        if recipient_name == "Broken Recipient":
            raise pdf_generator.CertificateGenerationError("simulated render failure")
        return real_generate(recipient_name=recipient_name, **kwargs)

    monkeypatch.setattr(pdf_generator, "generate_certificate", flaky_generate)

    payload = {
        "event_name": "Python Workshop",
        "date": "2026-10-10",
        "recipients": [
            {"name": "Arun Kumar", "email": "arun@example.com"},
            {"name": "Broken Recipient", "email": "broken@example.com"},
            {"name": "Priya Kumar", "email": "priya@example.com"},
        ],
    }

    job_id = client.post("/jobs", json=payload).json()["job_id"]
    body = client.get(f"/jobs/{job_id}").json()

    assert body["status"] == "completed_with_errors"
    assert body["total_count"] == 3
    assert body["success_count"] == 2
    assert body["failed_count"] == 1
    assert body["progress_percent"] == 100.0

    by_name = {c["recipient_name"]: c for c in body["certificates"]}

    assert by_name["Arun Kumar"]["status"] == "success"
    assert by_name["Priya Kumar"]["status"] == "success"
    assert by_name["Broken Recipient"]["status"] == "failed"
    assert "simulated render failure" in by_name["Broken Recipient"]["error_message"]
    assert by_name["Broken Recipient"]["download_url"] is None


def test_downloading_a_failed_certificate_returns_409(client, monkeypatch):
    def always_fails(**kwargs):
        raise pdf_generator.CertificateGenerationError("boom")

    monkeypatch.setattr(pdf_generator, "generate_certificate", always_fails)

    payload = {
        "event_name": "Python Workshop",
        "date": "2026-10-10",
        "recipients": [{"name": "Arun Kumar", "email": "arun@example.com"}],
    }

    job_id = client.post("/jobs", json=payload).json()["job_id"]
    body = client.get(f"/jobs/{job_id}").json()

    assert body["status"] == "failed"
    assert body["failed_count"] == 1

    certificate_id = body["certificates"][0]["id"]
    response = client.get(f"/certificates/{certificate_id}")

    assert response.status_code == 409
    assert "boom" in response.json()["detail"]