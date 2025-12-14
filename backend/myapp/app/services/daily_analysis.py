from typing import List, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.well_l04 import evaluate_l04


LOCAL_TZ = ZoneInfo("America/Bogota")


def analyze_by_local_day(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Group rows by local day (Colombia time) and evaluate WELL L04 per day.

    Args:
        rows: list of dicts with 'created_at' (UTC ISO 8601) and 'edi'

    Returns:
        Dict keyed by local date (YYYY-MM-DD) with L04 evaluation.
    """

    if not rows:
        return {}

    # Parse timestamps and convert to local time
    parsed = []
    for r in rows:
        ts = _parse_utc(r["created_at"]).astimezone(LOCAL_TZ)
        parsed.append({
            "created_at": ts,
            "edi": float(r["edi"]),
        })

    # Group by local date
    days: Dict[str, List[Dict[str, Any]]] = {}
    for r in parsed:
        day_key = r["created_at"].date().isoformat()
        days.setdefault(day_key, []).append(r)

    # Evaluate L04 per day
    results: Dict[str, Any] = {}
    for day, day_rows in days.items():
        # Convert back to ISO strings (local time preserved)
        rows_for_eval = [
            {
                "created_at": r["created_at"].isoformat(),
                "edi": r["edi"],
            }
            for r in day_rows
        ]
        results[day] = evaluate_l04(rows_for_eval)

    return results


def _parse_utc(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)
