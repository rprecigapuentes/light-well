# LightWell — Backend

FastAPI backend for the LightWell circadian lighting assessment system. Fetches melanopic EDI measurements from Supabase, computes statistical features, evaluates WELL v2 L04 compliance per local day, and serves AI-powered insights via Groq.

## Setup

**Prerequisites:** Python 3.10+

```bash
cd backend/myapp
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your credentials
uvicorn app.main:app --reload
# http://127.0.0.1:8000
```

## Environment Variables

Create `backend/myapp/.env` from `.env.example`:

| Variable | Description |
|---|---|
| `SUPABASE_URL` | `https://YOUR_PROJECT_ID.supabase.co` |
| `SUPABASE_KEY` | Supabase anon or service role key |
| `GROQ_API_KEY` | Groq API key |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` |
| `GROQ_MODEL` | Model name, e.g. `llama-3.3-70b-versatile` |

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

## API Endpoints

### `GET /health`

Validates that all required environment variables are set.

```bash
curl "http://127.0.0.1:8000/health" | jq
```

**Response:**
```json
{
  "SUPABASE_URL_set": true,
  "SUPABASE_KEY_set": true,
  "GROQ_API_KEY_set": true,
  "GROQ_MODEL_set": true
}
```

---

### `GET /data`

Returns raw EDI rows, statistical features, and WELL v2 L04 compliance for the requested time range.

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `start` | ISO 8601 string | Range start (UTC) |
| `end` | ISO 8601 string | Range end (UTC) |

```bash
curl "http://127.0.0.1:8000/data?start=2025-12-14T00:00:00Z&end=2025-12-14T23:59:59Z" | jq
```

**Response fields:**

| Field | Description |
|---|---|
| `count` | Number of rows retrieved |
| `features_global` | Statistical summary over the full range |
| `l04_global` | L04 compliance evaluated over the full range |
| `features_by_day` | Statistical summary per local day (UTC-5) |
| `l04_by_day` | L04 compliance per local day (UTC-5) |
| `rows` | Raw measurements (for debugging) |

**`features_*` object:**
```json
{
  "count": 101,
  "duration_s": 36060,
  "edi_min": 45.2,
  "edi_max": 312.8,
  "edi_mean": 178.4,
  "edi_median": 182.1,
  "edi_std": 54.3,
  "edi_p10": 98.2,
  "edi_p90": 270.1,
  "edi_last": 155.6,
  "edi_delta_vs_median": -26.5
}
```

**`l04_*` object (per tier):**
```json
{
  "tier1": {
    "compliant": true,
    "threshold": 136,
    "window_start": "2025-12-14T07:00:00+00:00",
    "window_end": "2025-12-14T11:00:00+00:00"
  },
  "tier2": {
    "compliant": false,
    "threshold": 250,
    "window_start": null,
    "window_end": null
  }
}
```

---

### `GET /insight`

Returns an LLM-generated summary and three actionable recommendations for the requested time range.

**Query parameters:** same as `/data`

```bash
curl "http://127.0.0.1:8000/insight?start=2025-12-14T00:00:00Z&end=2025-12-14T23:59:59Z" | jq
```

**Response:**
```json
{
  "llm": {
    "summary": "...",
    "recommendations": ["...", "...", "..."]
  }
}
```

---

### `GET /ask`

Answers a natural-language question about the data for the requested time range.

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `start` | ISO 8601 string | Range start (UTC) |
| `end` | ISO 8601 string | Range end (UTC) |
| `question` | string | User question |

```bash
curl -sG "http://127.0.0.1:8000/ask" \
  --data-urlencode "start=2025-12-14T00:00:00Z" \
  --data-urlencode "end=2025-12-14T23:59:59Z" \
  --data-urlencode "question=Why did I fail Tier 1 today?" | jq
```

**Response:**
```json
{
  "llm": {
    "answer": "...",
    "notes": "..."
  }
}
```

---

## Service Architecture

```
app/
├── main.py                  # FastAPI routes and CORS config
└── services/
    ├── supabase_client.py   # Singleton Supabase client (initialized once, reused)
    ├── data_service.py      # Supabase query — fetches (created_at, edi) rows by time range
    ├── preprocess.py        # Computes 11 statistical features from raw EDI time series
    ├── well_l04.py          # WELL v2 L04 compliance logic (continuous window detection)
    ├── daily_analysis.py    # Orchestrates L04 evaluation + features per local day (UTC-5)
    └── llm_groq.py          # Groq API integration (context injection, JSON parsing, rate limiting)
```

## WELL v2 L04 Compliance Logic

Compliance is determined using **explicit temporal logic**, not statistical averages.

**Algorithm per day:**
1. Rows are grouped by local day (Colombia timezone, UTC-5).
2. Readings after local noon are excluded (L04 requires the window to end before noon).
3. A forward scan checks for a continuous block of readings above the threshold.
4. A gap greater than **10 minutes** between consecutive readings resets the streak.
5. A valid block of **4 continuous hours** marks the day as compliant.

| Tier | Threshold | WELL Points |
|---|---|---|
| Tier 1 | ≥ 136 melanopic EDI | 1 |
| Tier 2 | ≥ 250 melanopic EDI | 3 |

When compliant, `window_start` and `window_end` serve as auditable evidence. When non-compliant, both fields are `null`.

## LLM Integration

- **Provider:** Groq (`llama-3.3-70b-versatile` by default)
- **Role:** the LLM explains and interprets deterministic compliance results — it does not decide compliance.
- **Context injected per request:** WELL L04 requirements, computed statistical features, per-day L04 results.
- **Rate limiting:** HTTP 429 responses are handled with exponential backoff.
- **Response parsing:** handles raw JSON and JSON wrapped in ` ```json ``` ` code fences.

## Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Health check
curl http://127.0.0.1:8000/health

# Validate Supabase connection directly (outside FastAPI)
python test_query.py
```
