"""Application configuration read from environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Where generated PDFs are written.
OUTPUT_DIR = Path(os.getenv("CERT_OUTPUT_DIR", str(BASE_DIR / "generated_certificates")))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Maximum recipients accepted in a single job.
MAX_RECIPIENTS = int(os.getenv("MAX_RECIPIENTS", "1000"))


def is_inline_mode() -> bool:
    """
    Read at call time (not import time) so tests can flip it.

    "background" -> processing is dispatched via FastAPI BackgroundTasks (default).
    "inline"     -> processing runs inside the POST /jobs request (used by tests
                    so assertions are deterministic without polling).
    """
    return os.getenv("CERT_PROCESSING_MODE", "background").lower() == "inline"