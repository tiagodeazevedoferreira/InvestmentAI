# Production Runtime Configuration

This document defines the provider-neutral environment contract for the Linux API container.

## Configuration versus secrets

The container receives configuration through environment variables. Secret values must be injected by the eventual hosting platform's secret facility and must never be committed to Git.

Potentially sensitive settings are:

- `FIREBASE_SERVICE_ACCOUNT`
- `TRADINGVIEW_WEBHOOK_SECRET`
- Any future provider credential, token or private key

The current DOTO/MT5 integration is different: the authenticated MT5 desktop terminal is a Windows execution boundary and is not part of the Linux production container.

## Runtime contract

| Variable | Purpose | Safe default / example |
|---|---|---|
| `APP_NAME` | API application name | `InvestmentAI` |
| `ENVIRONMENT` | Runtime environment identifier | `production` |
| `TRADING_MODE` | Application trading mode | `simulation` |
| `FIREBASE_DATABASE_URL` | Firebase endpoint | unset |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase service-account material | secret; unset unless required |
| `MARKET_DATA_TIMEOUT_SECONDS` | Market-data timeout | `20` |
| `MAX_FIREBASE_WRITE_BYTES` | Firebase write ceiling | `900000` |
| `MODEL_MIN_PROBABILITY` | Model probability threshold | `0.65` |
| `LIVE_TRADING_ENABLED` | LIVE execution safety switch | `false` |
| `MODEL_APPROVED` | Explicit model approval flag | `false` |
| `RISK_GATE_ENABLED` | Risk-gate control | `true` |
| `TRADINGVIEW_WEBHOOK_SECRET` | Webhook authentication secret | secret; unset unless required |
| `PAPER_INITIAL_CASH` | Paper starting cash | `100000` |
| `PAPER_FEE_BPS` | Paper fee assumption | `5` |
| `PAPER_SLIPPAGE_BPS` | Paper slippage assumption | `5` |
| `PAPER_ACCOUNT_PATH` | Paper account state path | `paper/account` |
| `PAPER_MAX_ORDER_NOTIONAL` | Paper order ceiling | `10000` |
| `XGBOOST_MODEL_DIR` | Model artifact directory | `models/xgboost` |
| `CORS_ALLOWED_ORIGINS` | Browser origins allowed by API | exact frontend origins recommended |
| `API_DOCS_ENABLED` | Interactive API documentation | `false` recommended |
| `LOG_LEVEL` | API logging level | `INFO` |
| `DOTO_MT5_TERMINAL_PATH` | Windows MT5 terminal path | unset in Linux container |
| `MT5_TERMINAL_PATH` | Legacy MT5 terminal path alias | unset in Linux container |
| `MT5_EXPECTED_LOGIN` | Expected MT5 account identity | unset in Linux container |
| `MT5_EXPECTED_SERVER` | Expected MT5 server | `DOTOGlobal-Real` |
| `MT5_DEMO_EXECUTION_ENABLED` | DEMO execution switch | `false` |
| `MT5_DEMO_EXPECTED_LOGIN` | Expected DEMO account identity | unset |
| `MT5_DEMO_EXPECTED_SERVER` | Expected DEMO server | unset |

## Production safety posture

The default production template deliberately uses:

- `TRADING_MODE=simulation`
- `LIVE_TRADING_ENABLED=false`
- `MODEL_APPROVED=false`
- `MT5_DEMO_EXECUTION_ENABLED=false`
- `API_DOCS_ENABLED=false`
- `LOG_LEVEL=INFO`

A future LIVE deployment requires a separate explicit approval and deployment task. Supplying environment variables alone is not a substitute for that approval.

## CORS

The application accepts a comma-separated list through `CORS_ALLOWED_ORIGINS`. The template retains the application's safe-compatible wildcard default so the configuration remains runnable without frontend provisioning, but an actual production deployment should replace `*` with the exact frontend origins before public exposure.

## Persistence

`PAPER_ACCOUNT_PATH` and model paths are application paths, not a persistence guarantee. Persistent volumes/storage must be designed and validated as a separate deployment task.

## Reference

Use `deploy/production.env.example` as the starting inventory. It contains placeholders only and must not receive real credentials.
