"""Application Configuration."""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server and pipeline settings."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    COLLEGE_SCORECARD_API_KEY: Optional[str] = None
    
    # Paths (relative to project root)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    KNOWLEDGE_DIR: Path = BASE_DIR / "knowledge"
    CLIENT_DIR: Path = BASE_DIR / "client"
    
    DATABASE_PATH: Path = DATA_DIR / "college_portfolio.db"
    SEED_DATA_PATH: Path = DATA_DIR / "colleges_seed.json"
    
    LEDGER_MD_PATH: Path = KNOWLEDGE_DIR / "college-knowledge.md"
    LEDGER_JSONL_PATH: Path = KNOWLEDGE_DIR / "college-knowledge.jsonl"
    
    # Cache settings
    SCORECARD_CACHE_TTL_DAYS: int = 7
    COOKIE_NAME: str = "college_portfolio_id"
    COOKIE_MAX_AGE: int = 60 * 60 * 24 * 365  # 1 year


settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
