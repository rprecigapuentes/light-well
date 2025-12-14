from typing import Dict, List, Any
from datetime import datetime
import statistics


def compute_features(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute compact numerical features from EDI time series.

    Assumes each row has:
      - 'created_at': ISO 8601 string (TIMESTAMPTZ)
      - 'edi': float

    Returns a consistent dict even if rows is empty.
    """

    # Caso vacío (muy importante para robustez)
    if not rows:
        return {
            "count": 0,
            "duration_s": 0.0,
            "edi_min": None,
            "edi_max": None,
            "edi_mean": None,
            "edi_median": None,
            "edi_std": None,
            "edi_p10": None,
            "edi_p90": None,
            "edi_last": None,
            "edi_delta_vs_median": None,
        }

    # Extraer valores
    edis = [float(r["edi"]) for r in rows]
    timestamps = [
        _parse_iso8601(r["created_at"]) for r in rows
    ]

    edis_sorted = sorted(edis)
    timestamps_sorted = sorted(timestamps)

    count = len(edis)

    # Estadísticos básicos
    edi_min = edis_sorted[0]
    edi_max = edis_sorted[-1]
    edi_mean = statistics.mean(edis_sorted)
    edi_median = statistics.median(edis_sorted)
    edi_std = statistics.stdev(edis_sorted) if count > 1 else 0.0

    # Percentiles (robustos)
    edi_p10 = _percentile(edis_sorted, 10)
    edi_p90 = _percentile(edis_sorted, 90)

    # Último valor (estado actual)
    edi_last = edis[-1]
    edi_delta_vs_median = edi_last - edi_median

    # Duración total de la ventana
    duration_s = (timestamps_sorted[-1] - timestamps_sorted[0]).total_seconds()

    return {
        "count": count,
        "duration_s": duration_s,
        "edi_min": edi_min,
        "edi_max": edi_max,
        "edi_mean": edi_mean,
        "edi_median": edi_median,
        "edi_std": edi_std,
        "edi_p10": edi_p10,
        "edi_p90": edi_p90,
        "edi_last": edi_last,
        "edi_delta_vs_median": edi_delta_vs_median,
    }


def _parse_iso8601(s: str) -> datetime:
    """
    Parse ISO 8601 datetime string into datetime.
    Accepts 'Z' and '+00:00'.
    """
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _percentile(sorted_values: List[float], p: float) -> float:
    """
    Compute percentile p (0–100) from a sorted list.
    """
    if not sorted_values:
        return None

    k = (len(sorted_values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)

    if f == c:
        return sorted_values[int(k)]

    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)
