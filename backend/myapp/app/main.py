from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any
import os
from fastapi import Response

from app.services.llm_groq import groq_generate
from app.services.daily_analysis import analyze_by_local_day
from app.services.preprocess import compute_features
from app.services.well_l04 import evaluate_l04
from app.services.data_service import fetch_rows


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

    daily = analyze_by_local_day(rows)

    return {
        "count": count,
        "features_global": compute_features(rows),
        "l04_global": evaluate_l04(rows),
        "features_by_day": daily["features_by_day"],
        "l04_by_day": daily["l04_by_day"],
        "rows": rows,
    }

@app.get("/insight")
def insight(start: str, end: str) -> Dict[str, Any]:
    start = _parse_iso8601(start)
    end = _parse_iso8601(end)

    count, rows = fetch_rows(start=start, end=end)
    daily = analyze_by_local_day(rows)

    context = {
        "range": {"start": start, "end": end},
        "features_global": compute_features(rows),
        "l04_global": evaluate_l04(rows),
        "features_by_day": daily["features_by_day"],
        "l04_by_day": daily["l04_by_day"],
    }

    llm = groq_generate(context=context, question=None)

    return {
        "count": count,
        "context": context,
        "llm": llm,
    }

@app.get("/ask")
def ask(start: str, end: str, question: str) -> Dict[str, Any]:
    start = _parse_iso8601(start)
    end = _parse_iso8601(end)

    count, rows = fetch_rows(start=start, end=end)
    daily = analyze_by_local_day(rows)

    context = {
        "range": {"start": start, "end": end},
        "features_global": compute_features(rows),
        "l04_global": evaluate_l04(rows),
        "features_by_day": daily["features_by_day"],
        "l04_by_day": daily["l04_by_day"],
    }

    llm = groq_generate(context=context, question=question)

    return {
        "count": count,
        "question": question,
        "context": context,
        "llm": llm,
    }
