import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/rpl_assist.db")
    DEMO_MODE = os.getenv("DEMO_MODE", "True").lower() in ("true", "1", "yes")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    EVIDENCE_DIR = BASE_DIR / "evidence"
    REPORTS_DIR = BASE_DIR / "reports"
    QP_DIR = BASE_DIR / "data" / "qualification_packs"
    
    # Create directories if they don't exist
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    QP_DIR.mkdir(parents=True, exist_ok=True)

config = Config()
