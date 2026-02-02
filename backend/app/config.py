# Fresas Standalone App Configuration
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Excel file path (source of truth)
    EXCEL_PATH: str = "/app/data/Control FRESAS.xls"
    
    # Pending writes log (fallback when Excel locked)
    PENDING_LOG_PATH: str = "/app/data/pending_consumos.csv"
    
    # SQLite cache (optional, for fast queries)
    CACHE_DB_PATH: str = "/app/data/cache.db"
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Auth (simple for standalone)
    ADMIN_PIN: str = "1234"
    JWT_SECRET: str = "fresas-standalone-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


def get_excel_path() -> Path:
    """Get resolved Excel file path."""
    return Path(settings.EXCEL_PATH)


def get_pending_log_path() -> Path:
    """Get pending consumos log path."""
    return Path(settings.PENDING_LOG_PATH)
