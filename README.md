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
  AS7262 + BH1750    →    mediciones table (edi, created_at)
  computes EDI                     ↓
                          FastAPI Backend
                          • fetches time range
                          • computes statistics
                          • evaluates WELL v2 L04 (Tier 1 & 2)
                          • groups by local day (Bogotá UTC-5)
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

## Project Structure

```
light-well/
├── frontend/                    # Next.js dashboard
│   └── src/
│       ├── app/                 # page.tsx (main), layout.tsx, CSS
│       ├── components/          # InsightBox, AskBox, Card
│       └── lib/
│           ├── time.ts          # bogotaDayRange() — date → UTC range
│           └── api/             # API client + TypeScript types
├── backend/myapp/
│   ├── app/
│   │   ├── main.py              # FastAPI app, routes
│   │   └── services/
│   │       ├── data_service.py  # Supabase query
│   │       ├── preprocess.py    # Statistical features
│   │       ├── well_l04.py      # WELL L04 compliance logic
│   │       ├── daily_analysis.py
│   │       └── llm_groq.py      # Groq API integration
│   ├── requirements.txt
│   └── .env.example
└── hardware/data_acquisition/
    ├── arduino_sensor_v01/      # PlatformIO (CSV logger via Serial)
    ├── arduino_sensor_v02/      # Arduino IDE (WiFi → Supabase uploader)
    └── python/                  # Serial reader → CSV
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
npm install
npm run dev                    # http://localhost:3000
```

To point the frontend at a non-default backend URL, set `NEXT_PUBLIC_API_URL` in a `.env.local` file:
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### Hardware

**v02 — WiFi uploader (recommended):**
1. Open `hardware/data_acquisition/arduino_sensor_v02/enviardatosasuperbase.ino` in Arduino IDE.
2. Fill in your `WIFI_SSID`, `WIFI_PASS`, `SUPABASE_URL`, and `SUPABASE_ANON_KEY` at the top of the file.
3. Flash to ESP32-C3 Mini.

**v01 — Serial CSV logger:**
```bash
# PlatformIO
cd hardware/data_acquisition/arduino_sensor_v01
platformio run --target upload

# Then capture data with the Python logger
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

Create `backend/myapp/.env` (see `.env.example`):

```
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_key
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

---

## Author

Rosemberth Steeven Preciga Puentes
