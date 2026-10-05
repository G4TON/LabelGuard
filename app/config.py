import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Load .env for local development.
# On Streamlit Cloud, secrets are provided through st.secrets.
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def get_setting(name, default=None):
    """Get a setting from Streamlit Secrets, falling back to .env/environment variables."""
    if name in st.secrets:
        return st.secrets[name]
    return os.getenv(name, default)


class Config:
    DATABASE_URL = get_setting(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR}/data/rpl_assist.db"
    )

    DEMO_MODE = str(
        get_setting("DEMO_MODE", "True")
    ).lower() in ("true", "1", "yes")

    GEMINI_API_KEY = get_setting("GEMINI_API_KEY")

    EVIDENCE_DIR = BASE_DIR / "evidence"
    REPORTS_DIR = BASE_DIR / "reports"
    QP_DIR = BASE_DIR / "data" / "qualification_packs"

    # Create directories if they don't exist
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    QP_DIR.mkdir(parents=True, exist_ok=True)


config = Config()
