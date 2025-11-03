import os
from datetime import timedelta
from typing import List

from dotenv import load_dotenv

# Load .env if present
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    APP_NAME: str = "DSP Backend API"
    APP_DESCRIPTION: str = "Handles API requests, user authentication logic, connects to SQLite database, and relays queries to the internal DSP endpoint."
    APP_VERSION: str = "0.1.0"

    # Database file (path to SQLite file)
    DB_FILE: str = os.getenv("DB_FILE", "dsp.db")

    # JWT configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-env")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    # expiration in minutes
    JWT_EXPIRES_MIN: int = int(os.getenv("JWT_EXPIRES_MIN", "60"))

    # DSP internal base URL and timeout
    DSP_INTERNAL_BASE: str = os.getenv("DSP_INTERNAL_BASE", "http://10.45.30.64")
    DSP_TIMEOUT_SEC: int = int(os.getenv("DSP_TIMEOUT_SEC", "30"))

    # CORS allow origins: comma-separated list
    CORS_ALLOW_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
        if origin.strip()
    ]

    @property
    def jwt_exp_delta(self) -> timedelta:
        return timedelta(minutes=self.JWT_EXPIRES_MIN)


settings = Settings()
