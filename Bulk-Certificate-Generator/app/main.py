"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401
from app.database import Base, engine
from app.routes import certificates, jobs

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Bulk Certificate Generator",
    description="Generate PDF certificates in bulk from a predefined template.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(jobs.router)
app.include_router(certificates.router)

# --- Website: serve the HTML at "/" ---
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(str(STATIC_DIR / "index.html"))
else:
    @app.get("/", tags=["meta"])
    def home():
        return {"message": "API is running", "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health_check():
    return {"status": "healthy"}