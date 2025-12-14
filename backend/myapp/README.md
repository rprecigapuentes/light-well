# Step 0 — Environment Setup and Variables

## Objective
Set up a minimal FastAPI project to connect to Supabase and call Groq API.

## Folder Structure
```

/project_root
│
├── app
│   ├── main.py       # FastAPI app
│   ├── config.py     # Configuration settings (env variables)
│
├── .env.example      # Example .env file
├── requirements.txt  # Project dependencies

````

## Dependencies (`requirements.txt`)
- `fastapi`
- `uvicorn`
- `supabase`
- `python-dotenv`
- `pydantic`
- `requests` (or `httpx`)

## Example `.env.example`
```dotenv
SUPABASE_URL=
SUPABASE_KEY=
GROQ_API_KEY=
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=
````

## Installation & Execution

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create and configure `.env` file by copying `.env.example` and filling the necessary API keys.

3. Run FastAPI server:

   ```bash
   uvicorn app.main:app --reload
   ```

Ensure your environment variables (`SUPABASE_URL`, `SUPABASE_KEY`, `GROQ_API_KEY`, `GROQ_MODEL`) are set in the `.env` file.

# Step 1 — Supabase Client

## Objective
Create a reusable Supabase client configured via environment variables.

## Description
A dedicated module (`supabase_client.py`) is added to initialize and provide access to a single Supabase client instance. The client is created only once and reused across the application.

## Key Points
- Environment variables are loaded from `.env`.
- Required variables: `SUPABASE_URL`, `SUPABASE_KEY`.
- Missing configuration raises clear runtime errors.
- A singleton pattern avoids recreating the client on each request.
- Type hints (`Optional[Client]`) document the client lifecycle (`None` → `Client`).

## Result
The Supabase client is ready to be imported and used by future endpoints without modifying `main.py`.

# Step 2 — Supabase Query Validation

## Objective
Validate a real `SELECT` query against Supabase to confirm data access, schema correctness, and time-based filtering.

## Description
A standalone script (`test_query.py`) is used to query the database directly (outside FastAPI). It connects using the Supabase client, filters rows by a time range on `created_at` (TIMESTAMPTZ), and retrieves only the required metric (`edi`).

## What It Does
- Uses `get_supabase()` to create/reuse the Supabase client.
- Filters rows with `created_at` between `START_ISO` and `END_ISO` (ISO 8601).
- Selects only `created_at` and `edi` columns.
- Prints:
  - Total row count.
  - First 3 rows in JSON format.

## Result
The query executed successfully, returning real data (`count = 101`) and confirming:
- Supabase credentials are correct.
- Table and column names match the schema.
- `created_at` TIMESTAMPTZ filtering works as expected.
- The data pipeline from Supabase to Python is functional.

This step confirms the database layer is ready for integration into FastAPI and further preprocessing.

# Step 3 — FastAPI Data Endpoint

## Objective
Expose a FastAPI GET endpoint that returns time-filtered EDI data from Supabase, matching the validated query used in `test_query.py`.

## Description
The existing `main.py` was updated to add a `/data` endpoint. This endpoint reads `start` and `end` as query parameters (ISO 8601), validates them, queries Supabase using the same logic as the standalone test script, and returns the results as JSON.

## Endpoint
**GET** `/data`

### Query parameters
- `start`: ISO 8601 datetime string  
- `end`: ISO 8601 datetime string  

Example:
```

/data?start=2025-12-14T00:00:00Z&end=2025-12-14T23:59:59Z

````

## Behavior
- Validates ISO 8601 timestamps (supports `Z` and `+00:00`).
- Queries table `mediciones`.
- Filters by `created_at` (TIMESTAMPTZ) between `start` and `end`.
- Selects only `created_at` and `edi`.
- Returns:
  ```json
  {
    "count": <int>,
    "rows": [ ... ]
  }
    ```

## Result

The endpoint successfully returns real data (same results as `test_query.py`), confirming:

* FastAPI routing and query parameters work correctly.
* Supabase client integration is correct.
* The backend HTTP layer is ready for preprocessing and downstream analysis.

## Run

```bash
uvicorn app.main:app --reload
```

# Step 4 — Data Service Layer

## Objective
Separate database access logic from the FastAPI endpoint by moving it into a dedicated service module.

## Description
The Supabase query logic was refactored into a new service file (`data_service.py`). The `/data` endpoint now delegates data retrieval to this service, keeping the API layer thin and focused on request handling.

## Changes
- Created `app/services/data_service.py`.
- Implemented `fetch_rows(start, end)`:
  - Queries Supabase table `mediciones`.
  - Filters by `created_at` (ISO 8601 range).
  - Selects only `created_at` and `edi`.
  - Returns `(count, rows)`.

- Updated `/data` endpoint in `main.py`:
  - Validates input timestamps.
  - Calls `fetch_rows`.
  - Returns `{count, rows}` as JSON.

## Result
- Clean separation of concerns:
  - **API layer**: HTTP + validation.
  - **Service layer**: data access.
- Logic is reusable and easier to extend (preprocessing, caching, ML input).
- Endpoint behavior remains identical and fully functional.

This step prepares the backend for adding preprocessing and downstream analytics without modifying the API interface.

# Step 5 — Preprocessing (Compact Numerical Features)

## Objective
Generate a compact, robust numerical summary of the melanopic EDI time series to support downstream analysis (LLM input and normative evaluation).

## Description
A new preprocessing service was added to compute descriptive statistics from the raw time series (`created_at`, `edi`). This step condenses multiple measurements into a stable, interpretable feature set without embedding regulatory logic.

## Implementation
- Created `app/services/preprocess.py`.
- Implemented `compute_features(rows)`:
  - Input: list of rows with `created_at` (ISO 8601) and `edi`.
  - Output: a consistent dictionary of numerical features.
  - Handles empty input (`rows = []`) gracefully.

## Computed Features
- `count`: number of samples
- `duration_s`: total duration of the window (seconds)
- `edi_min`, `edi_max`
- `edi_mean`, `edi_median`
- `edi_std`
- `edi_p10`, `edi_p90`
- `edi_last`
- `edi_delta_vs_median`

## API Update
The `/data` endpoint was updated to:
- Fetch raw rows via the data service.
- Compute preprocessing features.
- Return both raw data and the compact feature summary.

Response structure:
```json
{
  "count": <int>,
  "features": { ... },
  "rows": [ ... ]
}
````

## Result

* Preprocessing works correctly with real data.
* Features are robust, interpretable, and LLM-ready.
* The system is now prepared for a higher-level compliance check (e.g., WELL v2 L04) without mixing concerns.

This step completes the numerical preprocessing layer of the backend.

# Step 6 — WELL v2 Circadian Compliance (L04 / L05)

## Objective
Evaluate automatic compliance with WELL v2 circadian lighting requirements using the estimated melanopic EDI time series.

---

## WELL v2 – L04: Circadian Lighting Design

### Core Requirement
WELL v2 **L04** requires that occupants receive:

- **Sufficient melanopic illuminance (melanopic EDI, CIE S 026)**
- **For at least 4 continuous hours**
- **Ending before local solar noon**

The requirement is **continuous**, not averaged:
- Any drop below the threshold breaks compliance.
- A valid sub-window must exist within the measured data.

---

### Tiers and Thresholds

| Tier | Requirement | Melanopic EDI |
|-----:|-------------|----------------|
| Tier 1 | 1 point | ≥ **136 melanopic EDI** (≈150 EML) |
| Tier 2 | 3 points | ≥ **250 melanopic EDI** (≈275 EML) |

Each tier is evaluated independently.

---

### Interpretation of Results

For each tier, the system reports:
- `compliant`: whether a valid 4 h window exists
- `window_start`: start timestamp of the first compliant window
- `window_end`: end timestamp of the first compliant window
- `threshold`: melanopic EDI threshold used

If no valid window exists:
- `compliant = false`
- `window_start = null`
- `window_end = null`

This behavior indicates **non-compliance**, not missing data.

---

## WELL v2 – L05: Enhanced Circadian Lighting (Context)

- **L05** builds on L04.
- It introduces **higher thresholds, longer durations, or additional temporal constraints**.
- L05 is **optional and more stringent**.
- The current implementation focuses on **L04**, but the architecture supports extension to L05.

---

## Design Rationale

- Compliance is evaluated using **explicit temporal logic**, not statistical averages.
- The detected `window` represents **evidence of compliance**, not the full data range.
- Statistical features (mean, std, percentiles) are used for diagnostics, not as compliance criteria.

---

## Result
The backend now provides:
- Automated WELL v2 L04 Tier 1 / Tier 2 compliance evaluation.
- Explicit evidence windows for auditing.
- A clean separation between data acquisition, preprocessing, and normative logic.

This completes the normative evaluation layer of the system.

# Step 7 — Daily Analysis & Time Zones (Short Explanation)

## Objective
Evaluate WELL L04 **per local day (Colombia)** even though the data is stored in UTC.

---

## Key Concepts

### Parsing
**Parsing** means converting text into a usable object.
```python
datetime.fromisoformat("2025-12-14T10:30:00+00:00")
````

Converts a timestamp string into a `datetime` object.

---

### Time zone conversion

```python
dt.astimezone(ZoneInfo("America/Bogota"))
```

Transforms a UTC time into **local Colombia time (UTC−5)** without changing the actual moment.

---

### Grouping by local day

```python
day = dt.date().isoformat()
```

Extracts `"YYYY-MM-DD"` so measurements are grouped by **human calendar day**, not UTC day.

---

## Why this is needed for WELL

* WELL L04 is evaluated **per day**.
* “Before noon” refers to **local time**, not UTC.
* Each day must be checked independently for a valid 4-hour window.

---

## Processing Pipeline

```text
UTC timestamp (string)
→ parse to datetime
→ convert to Colombia time
→ group by local day
→ evaluate L04 per day
```

---

## Result

The backend can now:

* Distinguish different days correctly
* Handle Colombian local time
* Report WELL L04 compliance **day by day**

This prepares the data for clear reporting and LLM-based explanations.

## Step 8 — LLM Integration (Groq)

**Goal:** automatically interpret circadian lighting results (WELL v2 – L04) and allow user questions about the processed data.

### Model used
- **Model:** `llama-3.3-70b-versatile`
- **Provider:** Groq (OpenAI-compatible API)

### Why Groq
- Very low inference latency.
- Access to large models (70B) with no direct cost at this stage.
- OpenAI-compatible API → simple integration via `chat/completions`.
- No internet access required: all normative and project context is explicitly injected.

### What is sent to the LLM
- **LightWell project context** (wearable, assessment-only system).
- Explicit definition of **WELL v2 – L04** (4-hour window, thresholds, tiers).
- Backend-computed results:
  - statistical features
  - global L04 evaluation
  - per-day (local time, UTC-5) L04 evaluation

The LLM **does not decide compliance**. It only explains and interprets deterministic results.

### Test endpoints
- **Automatic summary:**

[http://localhost:8000/insight?start=YYYY-MM-DDT00:00:00Z&end=YYYY-MM-DDT23:59:59Z](http://localhost:8000/insight?start=YYYY-MM-DDT00:00:00Z&end=YYYY-MM-DDT23:59:59Z)

- **User question:**

[http://localhost:8000/ask?start=YYYY-MM-DDT00:00:00Z&end=YYYY-MM-DDT23:59:59Z&question=Your%20question%20here](http://localhost:8000/ask?start=YYYY-MM-DDT00:00:00Z&end=YYYY-MM-DDT23:59:59Z&question=Your%20question%20here)


### Technical note
Robust JSON parsing was added to handle raw JSON or JSON wrapped in ```json``` code fences returned by the LLM.

## Step 10 — API Testing with curl

**Goal:** validate the full backend pipeline without a frontend.

### Prerequisites
- Backend running locally:
  ```bash
  uvicorn app.main:app --reload
    ```

* Optional (recommended): install `jq` for readable JSON output

  ```bash
  sudo apt update && sudo apt install -y jq
  ```

---

### 1) Health check

Verify that the server is running and required environment variables are loaded.

```bash
curl -s "http://127.0.0.1:8000/health" | jq
```

Key fields:

* `SUPABASE_URL_set`
* `SUPABASE_KEY_set`
* `GROQ_API_KEY_set`
* `GROQ_MODEL_set`

All should be `true`.

---

### 2) Data endpoint

Fetch raw data, computed features, and WELL L04 evaluations.

```bash
curl -s "http://127.0.0.1:8000/data?start=2025-12-14T00:00:00Z&end=2025-12-14T23:59:59Z" | jq
```

Relevant fields:

* `count`: number of rows retrieved
* `features`: statistical summary of melanopic EDI
* `l04_global`: L04 compliance over the full range
* `l04_by_day`: L04 compliance per local day (UTC-5)
* `rows`: raw measurements (debugging only)

---

### 3) Insight endpoint (LLM summary)

Generate an automatic interpretation using the LLM.

```bash
curl -s "http://127.0.0.1:8000/insight?start=2025-12-14T00:00:00Z&end=2025-12-14T23:59:59Z" | jq
```

Relevant fields:

* `llm.summary`: concise textual summary (≤120 words)
* `llm.recommendations`: exactly 3 actionable recommendations

---

### 4) Ask endpoint (user question)

Ask a natural-language question about the same data range.

```bash
curl -sG "http://127.0.0.1:8000/ask" \
  --data-urlencode "start=2025-12-14T00:00:00Z" \
  --data-urlencode "end=2025-12-14T23:59:59Z" \
  --data-urlencode "question=Why did I fail Tier 1 today?" | jq
```

Relevant fields:

* `llm.answer`: direct answer based on computed results
* `llm.notes`: clarifications or data limitations, if applicable

---

With these commands, the backend can be fully validated end-to-end without any frontend.