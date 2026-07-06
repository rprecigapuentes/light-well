# LightWell

<p align="center">
  <img src="https://img.shields.io/badge/ESP32--C3_Mini-WiFi_Wearable-blue?logo=espressif&logoColor=white"/>
  <img src="https://img.shields.io/badge/Sensor-AS7262_Multispectral-purple"/>
  <img src="https://img.shields.io/badge/Sensor-BH1750_Lux-orange"/>
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Frontend-Next.js_16-000000?logo=next.js&logoColor=white"/>
  <img src="https://img.shields.io/badge/Database-Supabase-3ECF8E?logo=supabase&logoColor=white"/>
  <img src="https://img.shields.io/badge/LLM-Groq_(Llama_3.3)-F55036"/>
  <img src="https://img.shields.io/badge/Standard-WELL_v2_L04-brightgreen"/>
</p>

An AI-driven **circadian lighting assessment** wearable system. LightWell measures melanopic EDI (Equivalent Daylight Illuminance, per CIE S 026) using an ESP32-C3 Mini with AS7262 multispectral + BH1750 lux sensors, stores readings in Supabase, evaluates WELL v2 L04 compliance, and surfaces AI-powered insights through a Next.js dashboard.

> **Assessment only** — LightWell measures and evaluates. It does not control lighting.

---

## How It Works

```
ESP32-C3 Wearable          Supabase (PostgreSQL)
  AS7262 + BH1750    →    mediciones table (edi, created_at, ...)
  computes EDI                     ↓
                          FastAPI Backend
                          • fetches time range
                          • computes statistical features
                          • evaluates WELL v2 L04 (Tier 1 & 2)
                          • groups by local day (Bogotá, UTC-5)
                          • calls Groq LLM for insights
                                   ↓
                          Next.js Dashboard
                          • date picker → daily view
                          • EDI statistics + compliance cards
                          • AI insight + Q&A
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Hardware | ESP32-C3 Mini, AS7262 (multispectral), BH1750 (lux) |
| Firmware | Arduino IDE / PlatformIO (C++) |
| Data logging | Python (serial reader → CSV) |
| Backend | FastAPI, Python 3.10+, uvicorn |
| Database | Supabase (PostgreSQL) |
| LLM | Groq API — `llama-3.3-70b-versatile` |
| Frontend | Next.js 16, React 19, TypeScript 5 |

---

## WELL v2 L04 Compliance

The core evaluation checks whether the wearable received at least **4 continuous hours** of melanopic EDI above threshold *before local noon* (Bogotá time, UTC-5):

| Tier | Threshold | Points |
|---|---|---|
| Tier 1 | ≥ 136 melanopic EDI | 1 |
| Tier 2 | ≥ 250 melanopic EDI | 3 |

A gap greater than **10 minutes** between consecutive sensor readings resets the continuous streak.

---

## Database Schema

Table: **`mediciones`** (Supabase / PostgreSQL)

| Column | Type | Description |
|---|---|---|
| `id` | `int8` | Auto-increment primary key |
| `created_at` | `timestamptz` | UTC timestamp of the reading |
| `edi` | `float8` | Melanopic EDI value (CIE S 026) |
| `violet` | `int4` | AS7262 violet channel (raw counts) |
| `blue` | `int4` | AS7262 blue channel (raw counts) |
| `green` | `int4` | AS7262 green channel (raw counts) |
| `yellow` | `int4` | AS7262 yellow channel (raw counts) |
| `orange` | `int4` | AS7262 orange channel (raw counts) |
| `red` | `int4` | AS7262 red channel (raw counts) |
| `lux` | `float8` | Illuminance from BH1750 (lux) |

---

## Project Structure

```
light-well/
├── frontend/                    # Next.js dashboard
│   ├── src/
│   │   ├── app/                 # page.tsx (main orchestrator), layout.tsx, CSS
│   │   ├── components/          # InsightBox, AskBox, Card, DaySelector
│   │   └── lib/
│   │       ├── time.ts          # bogotaDayRange() — date → UTC ISO range (UTC-5)
│   │       └── api/             # API client + TypeScript types
│   ├── .env.example
│   └── README.md
├── backend/myapp/
│   ├── app/
│   │   ├── main.py              # FastAPI app, routes, CORS
│   │   └── services/
│   │       ├── data_service.py  # Supabase query
│   │       ├── preprocess.py    # Statistical features
│   │       ├── well_l04.py      # WELL L04 compliance logic
│   │       ├── daily_analysis.py # Per-day orchestration (UTC-5)
│   │       └── llm_groq.py      # Groq API integration
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
└── hardware/data_acquisition/
    ├── arduino_sensor_v01/      # PlatformIO firmware (Serial → CSV)
    ├── arduino_sensor_v02/      # Arduino IDE firmware (WiFi → Supabase)
    └── python/                  # Serial data logger → CSV
```

---

## Quick Start

### Backend

```bash
cd backend/myapp
cp .env.example .env          # fill in your credentials
pip install -r requirements.txt
uvicorn app.main:app --reload  # http://127.0.0.1:8000
```

Verify with:
```bash
curl http://127.0.0.1:8000/health
```

### Frontend

```bash
cd frontend
cp .env.example .env.local    # set NEXT_PUBLIC_API_URL if needed
npm install
npm run dev                   # http://localhost:3000
```

### Hardware

**v02 — WiFi uploader (recommended):**
1. Open `hardware/data_acquisition/arduino_sensor_v02/enviardatosasuperbase.ino` in Arduino IDE.
2. Fill in `WIFI_SSID`, `WIFI_PASS`, `SUPABASE_URL`, and `SUPABASE_ANON_KEY` at the top of the file.
3. Flash to ESP32-C3 Mini.

**v01 — Serial CSV logger:**
```bash
# PlatformIO
cd hardware/data_acquisition/arduino_sensor_v01
platformio run --target upload

# Capture data with the Python logger
cd hardware/data_acquisition/python
python log_spectro_bh1750.py   # auto-detects Arduino port, writes to ./data/mediciones.csv
```

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Validates all required env vars are set |
| `GET /data?start=&end=` | Raw rows + statistical features + WELL L04 compliance (global and per local day) |
| `GET /insight?start=&end=` | Groq-generated summary + 3 actionable recommendations |
| `GET /ask?start=&end=&question=` | Groq answer to a user question about the data |

All timestamps use ISO 8601. The frontend sends UTC timestamps bracketing the selected day in Bogotá time (UTC-5).

---

## Environment Variables

**Backend** — create `backend/myapp/.env`:

| Variable | Description |
|---|---|
| `SUPABASE_URL` | `https://YOUR_PROJECT_ID.supabase.co` |
| `SUPABASE_KEY` | Supabase anon or service role key |
| `GROQ_API_KEY` | Groq API key |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` |
| `GROQ_MODEL` | e.g. `llama-3.3-70b-versatile` |

**Frontend** — create `frontend/.env.local`:

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend base URL | `http://127.0.0.1:8000` |

---

## Author

Rosemberth Steeven Preciga Puentes

Luis Guillermo Vaca Rincon
