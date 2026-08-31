# InvestmentAI

InvestmentAI is a modular FinTech platform for market analysis, simulation, quantitative research, portfolio optimization, ML forecasting and controlled future trade execution.

## Safety model

Trading environments are strictly separated: `simulation -> paper -> demo -> live`. Live trading is disabled by default and requires explicit promotion gates, risk checks and live credentials.

## Stack

- Python 3.12
- FastAPI + Pydantic
- pandas, NumPy, SciPy
- yfinance adapter
- scikit-learn / XGBoost-ready ML layer
- Firebase Realtime Database
- HTML/CSS/JavaScript PWA frontend
- GitHub Actions
- GitHub Pages for the static frontend

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Swagger: `/docs` and ReDoc: `/redoc`.

## Firebase

Set `FIREBASE_DATABASE_URL` and provide the Firebase Admin service-account JSON through `FIREBASE_SERVICE_ACCOUNT` only in a secure environment. Never commit credentials.

## Project state

See `PROJECT_CONTEXT.md`, `DEVELOPMENT_STATUS.md`, `ROADMAP.md` and `DECISIONS.md`. These files are the persistent handoff context for future development conversations.
