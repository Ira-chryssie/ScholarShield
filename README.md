# ScholarShield AI
Streamlit + SQLite + Pandas prototype for the Ignite Your Future 2026 AI Innovation Challenge.

## Structure
app.py (UI) · engine.py (LLM + deterministic fallback) · db.py (SQLite) · demo_data.py (fictional DEMO DATA) · docs/PITCH.md, docs/SUBMISSION.md

## Run
    python3 -m venv venv
    source venv/bin/activate        # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    streamlit run app.py

## DEMO mode (no key)
Do nothing: with `LLM_API_KEY` empty the app uses regex/rule-based extraction, risk scoring and matching. On the Dashboard click **Load DEMO DATA**, or open *Analyze Opportunity* and pick a sample.

## Configure the AI API
    cp .env.example .env    # then set LLM_API_KEY=... (and optionally LLM_MODEL)
The key is read only from the environment. `engine._call_llm` uses the Anthropic Messages API; to use another provider, change that one function. If the call fails, the app falls back automatically. Eligibility percentage is always computed by transparent rules; the LLM extracts, assesses risk signals and adds checklist items.

## Disclaimer
Assessments are AI-assisted, not official. Providers confirm eligibility; risk levels are indicators, not proof of fraud.

## Guided demo
Click **🚀 Start Demo** (sidebar or Dashboard). 8 steps, no typing. Uses fictional DEMO DATA and a demo profile; your profile is not changed.

## Modes
`DEMO MODE — Rule-based AI analysis` (no key or API failure) · `AI MODE — LLM-assisted analysis` (key set). Keys are read only from the environment and never displayed.
