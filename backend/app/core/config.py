"""
Central application configuration.
Reads from environment variables (.env) with sane local defaults so the
service runs out-of-the-box during development.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/

# Load backend/.env before reading environment variables
load_dotenv(BASE_DIR / ".env")


class Settings:
    # Project
    PROJECT_NAME: str = (
        "Infosys_Agentic AI for Smart Facility Operations and Optimization"
    )
    API_V1_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'data' / 'facilityops.db'}"
    )

    # Data ingestion source
    ENERGY_RAW_CSV: Path = (
        BASE_DIR / "data" / "raw" / "energy_readings_raw.csv"
    )

    # Analytics tuning
    ANOMALY_ZSCORE_THRESHOLD: float = 2.5
    OFF_HOURS_START: int = 20
    OFF_HOURS_END: int = 6
    BASELINE_WASTE_THRESHOLD_PCT: float = 15.0

    # CORS
    # Allows both local development and deployed Render frontend
    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,"
            "http://localhost:3000,"
            "https://infosys-ai-frontend.onrender.com"
        ).split(",")
        if origin.strip()
    ]

    # AI Provider
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")

    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "dev-only-insecure-secret-change-me"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_EXPIRE_MINUTES", "120")
    )

    # Admin credentials
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "Aryan")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Aryan@2k4")


settings = Settings()