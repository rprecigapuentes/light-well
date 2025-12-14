from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


# WELL v2 – L04 thresholds (melanopic EDI)
TIER_1_THRESHOLD = 136.0  # ≈ 150 EML
TIER_2_THRESHOLD = 250.0  # ≈ 275 EML

REQUIRED_DURATION = timedelta(hours=4)


def evaluate_l04(
    rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Evaluate WELL v2 L04 compliance on a time series of melanopic EDI.

    Args:
        rows: list of dicts with:
              - 'created_at': ISO 8601 string (TIMESTAMPTZ)
              - 'edi': float

    Returns:
        Dict with compliance results for Tier 1 and Tier 2.
    """

    if not rows:
        return _empty_result()

    # Parse and sort by time
    series = [
        (_parse_iso8601(r["created_at"]), float(r["edi"]))
        for r in rows
    ]
    series.sort(key=lambda x: x[0])

    # Keep only samples before 12:00 (UTC proxy for noon)
    series = [
        (t, edi)
        for (t, edi) in series
        if t.time() < datetime.strptime("12:00", "%H:%M").time()
    ]

    if len(series) < 2:
        return _empty_result()

    tier1 = _check_threshold(series, TIER_1_THRESHOLD)
    tier2 = _check_threshold(series, TIER_2_THRESHOLD)

    return {
        "tier_1": tier1,
        "tier_2": tier2,
    }


def _check_threshold(
    series: List[tuple[datetime, float]],
    threshold: float,
) -> Dict[str, Any]:
    """
    Check if there exists a continuous window >= 4h
    where edi >= threshold at all times.
    """
    start_idx = 0

    for end_idx in range(len(series)):
        _, edi = series[end_idx]

        # If value drops below threshold, reset window
        if edi < threshold:
            start_idx = end_idx + 1
            continue

        # Check duration of current window
        start_time = series[start_idx][0]
        end_time = series[end_idx][0]

        if end_time - start_time >= REQUIRED_DURATION:
            return {
                "compliant": True,
                "window_start": start_time.isoformat(),
                "window_end": end_time.isoformat(),
                "threshold": threshold,
            }

    return {
        "compliant": False,
        "window_start": None,
        "window_end": None,
        "threshold": threshold,
    }


def _parse_iso8601(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _empty_result() -> Dict[str, Any]:
    return {
        "tier_1": {
            "compliant": False,
            "window_start": None,
            "window_end": None,
            "threshold": TIER_1_THRESHOLD,
        },
        "tier_2": {
            "compliant": False,
            "window_start": None,
            "window_end": None,
            "threshold": TIER_2_THRESHOLD,
        },
    }
