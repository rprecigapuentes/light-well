from typing import List, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.well_l04 import evaluate_l04_daily
from app.services.preprocess import compute_features_daily


LOCAL_TZ = "America/Bogota"


def analyze_by_local_day(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Orchestrate daily analysis (local day in Bogotá):
      - L04 daily compliance (+ missing minutes / best streak)
      - Daily compact features

    Args:
        rows: list of dicts with 'created_at' (UTC ISO 8601) and 'edi'

    Returns:
        {
          "l04_by_day": { "YYYY-MM-DD": {...}, ... },
          "features_by_day": { "YYYY-MM-DD": {...}, ... }
        }
    """
    if not rows:
        return {
            "l04_by_day": {},
            "features_by_day": {},
        }

    # IMPORTANT:
    # - Do NOT pre-convert timestamps here and then call per-day grouping again.
    # - well_l04.evaluate_l04_daily and preprocess.compute_features_daily already group by local day.
    return {
        "l04_by_day": evaluate_l04_daily(rows, tz=LOCAL_TZ),
        "features_by_day": compute_features_daily(rows, tz=LOCAL_TZ),
    }


def _parse_utc(s: str) -> datetime:
    # Kept only if other parts of the codebase still import it.
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)
