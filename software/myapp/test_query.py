# test_query.py
"""
Step 2 — Supabase SELECT test (time range only)

- Filters by created_at (TIMESTAMPTZ) between START_ISO and END_ISO
- Selects only: created_at, edi
- Prints: count + first 3 rows as JSON

Run:
  python test_query.py

Edit placeholders:
  - TABLE_NAME
  - EDI_COLUMN (if your column name differs)
  - START_ISO / END_ISO (ISO 8601 strings)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from app.services.supabase_client import get_supabase


# -----------------------------
# EDIT THESE PLACEHOLDERS
# -----------------------------
TABLE_NAME = "mediciones"

# Column names (adjust if your schema uses different names)
TIME_COLUMN = "created_at"     # you said this exists (TIMESTAMPTZ)
EDI_COLUMN = "edi"             # change if your metric column has another name


START_ISO = "2025-12-14T00:00:00Z"
END_ISO   = "2025-12-14T23:59:59Z"


def _safe_preview(rows: List[Dict[str, Any]], n: int = 3) -> List[Dict[str, Any]]:
    return rows[:n] if rows else []


def _query_rows() -> Tuple[int, List[Dict[str, Any]]]:
    sb = get_supabase()

    # Select only the needed columns to keep payload small
    select_expr = f"{TIME_COLUMN},{EDI_COLUMN}"

    query = (
        sb.table(TABLE_NAME)
        .select(select_expr, count="exact")
        .gte(TIME_COLUMN, START_ISO)
        .lte(TIME_COLUMN, END_ISO)
        .order(TIME_COLUMN, desc=True)  # latest first
        .limit(1000)
    )

    res = query.execute()

    count = getattr(res, "count", None)
    if count is None:
        count = len(res.data) if getattr(res, "data", None) else 0

    rows = res.data or []
    return int(count), rows


def main() -> None:
    try:
        count, rows = _query_rows()
    except Exception as exc:
        print("Query failed.")
        print("Common causes:")
        print("- Missing/invalid SUPABASE_URL or SUPABASE_KEY in .env")
        print("- TABLE_NAME or column names don't match your schema")
        print("- START_ISO / END_ISO not valid ISO 8601 strings")
        print("- created_at is not a timestamp/datetime column in DB")
        raise

    print(f"count = {count}")
    print("preview (first 3 rows):")
    print(json.dumps(_safe_preview(rows, 3), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
