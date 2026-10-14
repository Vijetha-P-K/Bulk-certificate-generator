"""Creating a job and reading its status/progress."""


def test_create_job_returns_201_with_counts(client, sample_payload):
    response = client.post("/jobs", json=sample_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["job_id"] > 0
    assert body["total_count"] == 2
    assert body["status"] in {"completed", "completed_with_errors"}


def test_job_status_reports_progress_and_results(client, sample_payload):
    job_id = client.post("/jobs", json=sample_payload).json()["job_id"]

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job_id
    assert body["status"] == "completed"
    assert body["total_count"] == 2
    assert body["success_count"] == 2
    assert body["failed_count"] == 0
    assert body["processed_count"] == 2
    assert body["progress_percent"] == 100.0
    assert len(body["certificates"]) == 2
    assert all(c["status"] == "success" for c in body["certificates"])


def test_list_job_certificates_supports_status_filter(client, sample_payload):
    job_id = client.post("/jobs", json=sample_payload).json()["job_id"]

    success = client.get(f"/jobs/{job_id}/certificates?status=success").json()
    failed = client.get(f"/jobs/{job_id}/certificates?status=failed").json()

    assert len(success) == 2
    assert failed == []


def test_unknown_job_returns_404(client):
    assert client.get("/jobs/999999").status_code == 404


def test_health_endpoint(client):
    assert client.get("/health").json() == {"status": "healthy"}