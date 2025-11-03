import os
from datetime import timedelta
from typing import List

from dotenv import load_dotenv

# Load .env if present (non-fatal if missing)
load_dotenv()


class Settings:
    """Application settings loaded from environment variables.

    Defaults are development-friendly and container/Rancher-safe.
    """
    APP_NAME: str = "DSP Backend API"
    APP_DESCRIPTION: str = "Handles API requests, user authentication logic, connects to SQLite database, and relays queries to the internal DSP endpoint."
    APP_VERSION: str = "0.1.0"

    # Database file (path to SQLite file). Default under container-local dsp_db volume/folder.
    # This keeps DB_FILE container-local and writable in Rancher/Docker setups.
    DB_FILE: str = os.getenv("DB_FILE", os.path.join("dsp_db", "dsp.db"))

    # JWT configuration - development default secret, algorithm HS256 and 120 min expiration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-only-change-me")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    # expiration in minutes
    JWT_EXPIRES_MIN: int = int(os.getenv("JWT_EXPIRES_MIN", "120"))

    # DSP internal base URL and timeout
    DSP_INTERNAL_BASE: str = os.getenv("DSP_INTERNAL_BASE", "http://10.45.30.64")
    DSP_TIMEOUT_SEC: int = int(os.getenv("DSP_TIMEOUT_SEC", "30"))

    # CORS allow origins: comma-separated list. Default to local frontend dev server.
    CORS_ALLOW_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]

    @property
    def jwt_exp_delta(self) -> timedelta:
        return timedelta(minutes=self.JWT_EXPIRES_MIN)


settings = Settings()
