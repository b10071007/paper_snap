import os
from pathlib import Path

# Load .env file using standard library
BASE_DIR = Path(__file__).resolve().parent.parent
env_file = BASE_DIR / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

class Settings:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    FB_PAGE_ID: str = os.getenv("FB_PAGE_ID", "")
    FB_PAGE_ACCESS_TOKEN: str = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    
    DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "t", "yes")
    
    DB_PATH: Path = BASE_DIR / os.getenv("DB_PATH", "data/paper_snap.db")
    CLASSIC_SEED_PATH: Path = BASE_DIR / os.getenv("CLASSIC_SEED_PATH", "data/seed_classic_papers.json")

settings = Settings()

