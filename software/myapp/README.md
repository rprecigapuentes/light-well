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