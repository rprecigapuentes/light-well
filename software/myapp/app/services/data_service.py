from typing import Dict, Any, List, Tuple

from app.services.supabase_client import get_supabase


def fetch_rows(start: str, end: str) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Fetch EDI rows from Supabase filtered by time range.

    Args:
        start: ISO 8601 datetime string (inclusive).
        end: ISO 8601 datetime string (inclusive).

    Returns:
        Tuple with:
        - count: total number of rows
        - rows: list of dicts with created_at and edi
    """
    TABLE_NAME = "mediciones"
    TIME_COLUMN = "created_at"
    EDI_COLUMN = "edi"

    sb = get_supabase()

    query = (
        sb.table(TABLE_NAME)
        .select(f"{TIME_COLUMN},{EDI_COLUMN}", count="exact")
        .gte(TIME_COLUMN, start)
        .lte(TIME_COLUMN, end)
        .order(TIME_COLUMN, desc=True)
    )

    res = query.execute()

    count = res.count if res.count is not None else len(res.data or [])
    rows: List[Dict[str, Any]] = res.data or []

    return count, rows
