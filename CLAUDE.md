# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

**light-well** is an AI-driven circadian-light wearable assessment system. It measures melanopic EDI (Equivalent Daylight Illuminance, per CIE S 026) via ESP32-C3 + AS7262/BH1750 sensors, stores data in Supabase, and evaluates WELL v2 L04/L05 compliance. It is assessment-only — it does not control lighting.

The system has three components: `frontend/` (Next.js), `backend/myapp/` (FastAPI), and `hardware/` (Arduino/ESP32 firmware).

## Commands

### Backend
```bash
cd backend/myapp
pip install -r requirements.txt
uvicorn app.main:app --reload          # Starts on http://127.0.0.1:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev       # Starts on http://localhost:3000
npm run build
npm run lint
```

### Hardware
- **v01 (PlatformIO):** `platformio run -e esp32-c3-mini --target upload`
- **v02 (Arduino IDE):** Flash `enviardatosasuperbase.ino` directly
- **Python logger:** `python hardware/data\ acquisition/python/log_spectro_bh1750.py`

## Architecture

### Data Flow
```
Hardware (AS7262 + BH1750 → ESP32-C3) → Supabase PostgreSQL (mediciones table)
                                                ↓
                              Backend FastAPI fetches, preprocesses, evaluates
                                                ↓
                              Frontend fetches /data, /insight, /ask endpoints
```

### Backend (`backend/myapp/app/`)
- `main.py` — FastAPI app, CORS config, route definitions
- `services/supabase_client.py` — singleton Supabase client
- `services/data_service.py` — queries `mediciones` table (columns: `created_at`, `edi`)
- `services/preprocess.py` — computes 10 statistical features (min/max/mean/median/std/p10/p90/count/duration)
- `services/well_l04.py` — WELL v2 L04 compliance: checks for 4 continuous hours ≥136 (Tier 1) or ≥250 (Tier 2) melanopic EDI before local noon; max 10-minute gap allowed before resetting streak
- `services/daily_analysis.py` — groups results by local day (Colombia timezone, UTC-5)
- `services/llm_groq.py` — Groq API calls for `/insight` (auto-summary + 3 recommendations) and `/ask` (Q&A)

### Frontend (`frontend/src/`)
- `app/page.tsx` — main orchestrator; fetches all endpoints, manages state
- `components/DaySelector.tsx` — date picker; converts selected date to Bogotá UTC-5 ISO range
- `components/InsightBox.tsx` — displays LLM-generated insight
- `components/AskBox.tsx` — user Q&A interface
- `components/Card.tsx` — generic card wrapper
- No external UI framework; plain CSS with CSS variables (light theme)

### Required Environment Variables (backend `.env`)
```
SUPABASE_URL=
SUPABASE_KEY=
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
```

### API Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /health` | Validates env vars |
| `GET /data?start=...&end=...` | Raw rows + statistical features + L04 compliance (global and per-day) |
| `GET /insight?start=...&end=...` | Groq-generated summary of compliance data |
| `GET /ask?start=...&end=...&question=...` | Groq answer to user question about data |

All timestamps are ISO 8601. Frontend sends Bogotá-local day boundaries as UTC timestamps.

### WELL v2 L04 Compliance Logic
The key rule: find the longest continuous window of readings above threshold (Tier 1: 136 melanopic EDI, Tier 2: 250) that ends before local noon. A gap >10 minutes between consecutive samples resets the streak. Compliance requires ≥240 continuous minutes (4 hours). Results include `best_continuous_minutes`, `missing_minutes`, and the window start/end.
