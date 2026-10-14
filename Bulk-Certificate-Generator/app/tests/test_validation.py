"""Input validation on POST /jobs."""
import pytest


def _base(recipients):
    return {
        "event_name": "Python Workshop",
        "date": "2026-10-10",
        "recipients": recipients,
    }


@pytest.mark.parametrize(
    "payload, reason",
    [
        (_base([]), "empty recipients list"),
        (_base([{"name": "Arun", "email": "not-an-email"}]), "invalid email"),
        (_base([{"email": "arun@example.com"}]), "missing name"),
        (_base([{"name": "Arun"}]), "missing email"),
        (_base([{"name": "", "email": "arun@example.com"}]), "blank name"),
        (_base([{"name": "A" * 200, "email": "arun@example.com"}]), "name too long"),
        (
            {"date": "2026-10-10", "recipients": [{"name": "A", "email": "a@b.com"}]},
            "missing event_name",
        ),
        (
            {"event_name": "X", "date": "not-a-date", "recipients": [{"name": "A", "email": "a@b.com"}]},
            "invalid date",
        ),
    ],
)
def test_invalid_payloads_are_rejected(client, payload, reason):
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422, f"expected 422 for: {reason}"


def test_valid_payload_is_accepted(client, sample_payload):
    assert client.post("/jobs", json=sample_payload).status_code == 201