# 🎓 Bulk Certificate Generator

A Python backend API for generating certificates in bulk using a predefined certificate template. The application accepts recipient data, validates input, generates PDF certificates, tracks generation progress, and allows clients to retrieve generated certificates.

## 📌 Overview

Organizations often need to issue certificates to large numbers of participants after workshops, courses, training programs, and other events.

Generating each certificate individually is time-consuming. This project aims to automate the process through a REST API that accepts multiple recipients in a single request.

## ✨ Features

- 📦 Bulk certificate generation through a REST API
- ✅ Recipient data validation
- 📄 PDF certificate generation using a predefined template
- 📊 Generation job creation and status tracking
- ⚠️ Individual success and failure tracking
- 📥 Retrieval of generated certificates
- 🧪 Automated tests for core functionality

> Features will be marked as complete as they are implemented and tested.

## 🛠️ Tech Stack

- **Language:** Python
- **Web framework:** FastAPI
- **Database:** SQLite
- **ORM:** SQLAlchemy
- **PDF generation:** ReportLab
- **Testing:** Pytest
- **API documentation:** FastAPI Swagger UI


Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

**🪟 Windows:**

```bash
.venv\Scripts\activate
```

**🐧 macOS/Linux:**

```bash
source .venv/bin/activate
```

Install dependencies after creating `requirements.txt`:

```bash
pip install -r requirements.txt
```

### ▶️ Run the Application

Once the application entry point is implemented:

```bash
uvicorn app.main:app --reload
```

Open the interactive API documentation at:

`http://127.0.0.1:8000/docs`

### 🧪 Run Tests

After implementing the test suite:

```bash
pytest
```

## 📁 Project Structure

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

## 🔮 Future Improvements

- 🎨 Configurable certificate styling
- 📦 ZIP downloads for completed jobs
- ⚙️ Persistent background workers
- 📈 Improved logging and monitoring
- 🔐 Authentication and authorization

These improvements are optional and will be considered only after the core requirements are complete.
