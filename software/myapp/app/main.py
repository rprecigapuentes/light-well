from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any
import os

from app.services.data_service import fetch_rows
from app.services.preprocess import compute_features

load_dotenv()

app = FastAPI(title="LightWell API")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "SUPABASE_URL_set": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_KEY_set": bool(os.getenv("SUPABASE_KEY")),
        "GROQ_API_KEY_set": bool(os.getenv("GROQ_API_KEY")),
        "GROQ_MODEL_set": bool(os.getenv("GROQ_MODEL")),
    }


def _parse_iso8601(s: str) -> str:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        datetime.fromisoformat(s)
        return s
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ISO 8601 datetime: {s}",
        )


@app.get("/data")
def get_data(start: str, end: str) -> Dict[str, Any]:
    start = _parse_iso8601(start)
    end = _parse_iso8601(end)

    try:
        count, rows = fetch_rows(start=start, end=end)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Data service failed",
        ) from exc

    features = compute_features(rows)

    return {
        "count": count,
        "features": features,
        "rows": rows,  # se mantiene para debug / trazabilidad
    }

