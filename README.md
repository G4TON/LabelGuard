# RPL-Assist

AI-Assisted Skill Assessment Tool for Recognition of Prior Learning (RPL).

Built for SMART INDIA HACKATHON 2026 (Problem Statement ID: SIH26242).

## Features
- Worker self-declaration with text/evidence upload
- AI-driven Qualification Pack mapping (Gemini 2.5 Flash)
- AI-assisted evidence review
- Assessor-in-the-loop with override capability
- Anchored 1-4 competency rubric
- In-person assessment flagging
- PDF Competency Report Generation
- Cohen's Kappa analytics for assessor agreement
- Offline-first capable (Local SQLite)

## Installation

1. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY if not in DEMO mode
   ```

4. Run the application:
   ```bash
   python -m streamlit run app/main.py
   ```

## Demo Mode
By default, the application runs in DEMO mode. Set `DEMO_MODE=False` and provide `GEMINI_API_KEY` in `.env` for real AI mapping.

## Testing
```bash
pytest
```
