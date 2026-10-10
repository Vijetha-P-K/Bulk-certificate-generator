# Bulk Certificate Generator

A Python backend API for generating certificates in bulk using a predefined certificate template. The application accepts recipient data, validates input, generates PDF certificates, tracks generation progress, and allows clients to retrieve generated certificates.

## Overview

Organizations often need to issue certificates to large numbers of participants after workshops, courses, training programs, and other events.

Generating each certificate individually is time-consuming. This project aims to automate the process through a REST API that accepts multiple recipients in a single request.

## Features

- Bulk certificate generation through a REST API
- Recipient data validation
- PDF certificate generation using a predefined template
- Generation job creation and status tracking
- Individual success and failure tracking
- Retrieval of generated certificates
- Automated tests for core functionality

> Features will be marked as complete as they are implemented and tested.

## Tech Stack

- **Language:** Python
- **Web framework:** FastAPI
- **Database:** SQLite
- **ORM:** SQLAlchemy
- **PDF generation:** ReportLab
- **Testing:** Pytest
- **API documentation:** FastAPI Swagger UI

## Planned API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/jobs` | Submit a bulk certificate generation job |
| GET | `/jobs/{job_id}` | Retrieve job status and progress |
| GET | `/jobs/{job_id}/certificates` | List certificates associated with a job |
| GET | `/certificates/{certificate_id}` | Retrieve or download a generated certificate |

## How It Works

1. The client submits a request containing certificate information and recipient details.
2. The API validates the request data.
3. A generation job is created and assigned a unique ID.
4. The application generates a certificate for each valid recipient.
5. The job and individual certificate statuses are recorded in the database.
6. The client checks job progress and retrieves successfully generated certificates.

## Failure Handling

A failure while generating one certificate should not prevent other valid recipients from being processed.

The application will track each recipient's generation result and record useful error information for failed certificates.

## Getting Started

### Prerequisites

- Python 3.10 or later
- pip
- Git

### Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/bulk-certificate-generator.git
cd bulk-certificate-generator
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

Install dependencies after creating `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Run the Application

Once the application entry point is implemented:

```bash
uvicorn app.main:app --reload
```

Open the interactive API documentation at:

`http://127.0.0.1:8000/docs`

### Run Tests

After implementing the test suite:

```bash
pytest
```

## Example Request

The planned `POST /jobs` endpoint will accept a request similar to:

```json
{
  "event_name": "Python Workshop",
  "date": "2026-10-10",
  "recipients": [
    {
      "name": "Arun Kumar",
      "email": "arun@example.com"
    },
    {
      "name": "Priya Kumar",
      "email": "priya@example.com"
    }
  ]
}
```

The actual request schema and response format will be documented alongside the implemented API.

## Project Structure

```text
bulk-certificate-generator/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routes/
│   ├── services/
│   └── templates/
├── tests/
├── generated_certificates/
├── requirements.txt
├── .gitignore
└── README.md
```

The structure may evolve as the implementation progresses.

## Design Decisions

- **FastAPI:** Provides request validation and interactive API documentation.
- **SQLite:** Keeps local development and evaluation straightforward while satisfying the relational database requirement.
- **PDF certificates:** Provide downloadable documents that can be shared or printed.
- **Per-recipient status tracking:** Makes it possible to identify individual successes and failures.
- **Bulk requests:** Avoid requiring the client to submit a separate API request for every certificate.

The processing strategy will be documented based on the final implementation. For a production system with large workloads, a durable background task queue may be appropriate.

## Testing

The test suite will cover:

- Creating a generation job
- Input validation
- Certificate generation
- Job status and progress
- Individual certificate generation failures
- Retrieving generated certificates

## Future Improvements

- Configurable certificate styling
- ZIP downloads for completed jobs
- Persistent background workers
- Improved logging and monitoring
- Authentication and authorization

These improvements are optional and will be considered only after the core requirements are complete.

## License

This project is intended as a backend development assignment and learning project. Add a license if you intend to permit others to reuse or distribute the code.
