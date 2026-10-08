"""Load backend settings from environment variables and backend/.env."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

raw_database_url = os.getenv("DATABASE_URL", "").strip()
if raw_database_url.startswith("postgresql://"):
    # Explicitly select Psycopg 3; SQLAlchemy's short URL otherwise uses psycopg2.
    DATABASE_URL: str | None = raw_database_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )
elif raw_database_url.startswith("postgresql+psycopg://"):
    DATABASE_URL = raw_database_url
else:
    DATABASE_URL = None

if raw_database_url and DATABASE_URL is None:
    DATABASE_CONFIG_ERROR = "DATABASE_URL must use PostgreSQL with the Psycopg 3 driver."
elif not raw_database_url:
    DATABASE_CONFIG_ERROR = "DATABASE_URL is not configured. Copy backend/.env.example to backend/.env and set it."
else:
    DATABASE_CONFIG_ERROR = None

# Authentication settings are environment-only. Startup of auth operations fails
# closed when a real secret has not been configured.
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
ALGORITHM = os.getenv("ALGORITHM", "HS256").strip().upper()
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
except ValueError:
    ACCESS_TOKEN_EXPIRE_MINUTES = 0


def validate_auth_config() -> None:
    """Reject unsafe or unusable JWT configuration before issuing/verifying tokens."""
    if len(SECRET_KEY.encode("utf-8")) < 32 or SECRET_KEY.lower().startswith(
        ("replace-", "generate-", "your-")
    ):
        raise RuntimeError("SECRET_KEY must be set to a random value of at least 32 bytes.")
    if ALGORITHM != "HS256":
        raise RuntimeError("ALGORITHM must be HS256 for the configured JWT implementation.")
    if not 1 <= ACCESS_TOKEN_EXPIRE_MINUTES <= 1440:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 1440.")
