from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo


# WELL v2 – L04 thresholds (melanopic EDI)
TIER_1_THRESHOLD = 136.0  # ≈ 150 EML
TIER_2_THRESHOLD = 250.0  # ≈ 275 EML

REQUIRED_DURATION = timedelta(hours=4)
REQUIRED_MINUTES = int(REQUIRED_DURATION.total_seconds() // 60)

# Continuity rule: if the gap between consecutive samples exceeds this, the streak breaks.
MAX_GAP_MIN = 10


def evaluate_l04(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Legacy (single-bucket) evaluator.

    NOTE:
    - This function evaluates only one time series (as given), filtering to < 12:00
      based on the timestamp's own timezone.
    - For the correct WELL L04 interpretation "per day (local)", use evaluate_l04_daily().
    """
    if not rows:
        return _empty_result()

    series = [(_parse_iso8601(r["created_at"]), float(r["edi"])) for r in rows]
    series.sort(key=lambda x: x[0])

    # Keep only samples before 12:00 in the timestamp's timezone
    series = [(t, edi) for (t, edi) in series if t.time() < time(12, 0)]

    if len(series) < 2:
        return _empty_result()

    tier1 = _evaluate_threshold(series, TIER_1_THRESHOLD, max_gap_min=MAX_GAP_MIN)
    tier2 = _evaluate_threshold(series, TIER_2_THRESHOLD, max_gap_min=MAX_GAP_MIN)

    return {"tier_1": tier1, "tier_2": tier2}


def evaluate_l04_daily(
    rows: List[Dict[str, Any]],
    tz: str = "America/Bogota",
    max_gap_min: int = MAX_GAP_MIN,
) -> Dict[str, Any]:
    """
    Evaluate WELL v2 L04 compliance per local day (tz), restricted to 00:00–12:00 local.

    Returns:
      {
        "YYYY-MM-DD": {
          "tier_1": {...},
          "tier_2": {...},
          "notes": Optional[str]
        },
        ...
      }
    """
    if not rows:
        return {}

    tzinfo = ZoneInfo(tz)

    # Build local-time series
    series_local: List[Tuple[datetime, float]] = []
    for r in rows:
        t = _parse_iso8601(r["created_at"])
        if t.tzinfo is None:
            # Defensive: if upstream gives naive timestamps, assume UTC.
            t = t.replace(tzinfo=ZoneInfo("UTC"))
        t_local = t.astimezone(tzinfo)
        series_local.append((t_local, float(r["edi"])))

    series_local.sort(key=lambda x: x[0])

    # Group by local day
    by_day: Dict[str, List[Tuple[datetime, float]]] = {}
    for t_local, edi in series_local:
        day = t_local.date().isoformat()
        by_day.setdefault(day, []).append((t_local, edi))

    out: Dict[str, Any] = {}
    for day, day_series in by_day.items():
        # Morning window: before local noon
        morning = [(t, edi) for (t, edi) in day_series if t.time() < time(12, 0)]

        if len(morning) < 2:
            out[day] = {
                "tier_1": _empty_tier_result(TIER_1_THRESHOLD),
                "tier_2": _empty_tier_result(TIER_2_THRESHOLD),
                "notes": "insufficient_data_before_noon",
            }
            continue

        t1 = _evaluate_threshold(morning, TIER_1_THRESHOLD, max_gap_min=max_gap_min)
        t2 = _evaluate_threshold(morning, TIER_2_THRESHOLD, max_gap_min=max_gap_min)

        out[day] = {"tier_1": t1, "tier_2": t2, "notes": None}

    return out


def _evaluate_threshold(
    series: List[Tuple[datetime, float]],
    threshold: float,
    max_gap_min: int,
) -> Dict[str, Any]:
    """
    For a single (already time-sorted) series, find the best continuous streak
    where edi >= threshold, using a max-gap continuity rule.

    Returns:
      - compliant: True if best streak >= 4h
      - best_continuous_minutes
      - missing_minutes (gap to 240)
      - best_window_start/end (isoformat)
    """
    max_gap = timedelta(minutes=max_gap_min)

    best_start: Optional[datetime] = None
    best_end: Optional[datetime] = None
    best_dur = timedelta(0)

    cur_start: Optional[datetime] = None
    cur_end: Optional[datetime] = None

    for t, edi in series:
        if edi < threshold:
            cur_start = None
            cur_end = None
            continue

        if cur_start is None:
            cur_start = t
            cur_end = t
        else:
            gap = t - cur_end  # type: ignore[arg-type]
            if gap <= max_gap:
                cur_end = t
            else:
                # Break continuity due to missing samples / large gap
                cur_start = t
                cur_end = t

        dur = (cur_end - cur_start)  # type: ignore[operator]
        if dur > best_dur:
            best_dur = dur
            best_start = cur_start
            best_end = cur_end

    best_minutes = int(best_dur.total_seconds() // 60)
    missing_minutes = max(0, REQUIRED_MINUTES - best_minutes)

    return {
        "compliant": best_minutes >= REQUIRED_MINUTES,
        "threshold": threshold,
        "best_continuous_minutes": best_minutes,
        "missing_minutes": missing_minutes,
        "best_window_start": best_start.isoformat() if best_start else None,
        "best_window_end": best_end.isoformat() if best_end else None,
        "required_minutes": REQUIRED_MINUTES,
        "max_gap_min": max_gap_min,
    }


def _parse_iso8601(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _empty_tier_result(threshold: float) -> Dict[str, Any]:
    return {
        "compliant": False,
        "threshold": threshold,
        "best_continuous_minutes": 0,
        "missing_minutes": REQUIRED_MINUTES,
        "best_window_start": None,
        "best_window_end": None,
        "required_minutes": REQUIRED_MINUTES,
        "max_gap_min": MAX_GAP_MIN,
    }


def _empty_result() -> Dict[str, Any]:
    return {
        "tier_1": _empty_tier_result(TIER_1_THRESHOLD),
        "tier_2": _empty_tier_result(TIER_2_THRESHOLD),
    }
