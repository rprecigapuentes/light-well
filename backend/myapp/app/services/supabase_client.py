# app/services/supabase_client.py
import os
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client


# Carga variables desde .env (si existe). No rompe si no existe, pero luego validamos.
load_dotenv()


_supabase: Optional[Client] = None


def get_supabase() -> Client:
    """
    Returns a singleton Supabase client configured from environment variables.

    Required env vars:
      - SUPABASE_URL
      - SUPABASE_KEY

    Raises:
      RuntimeError: if required variables are missing or client creation fails.
    """
    global _supabase

    if _supabase is not None:
        return _supabase

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()

    missing = []
    if not url:
        missing.append("SUPABASE_URL")
    if not key:
        missing.append("SUPABASE_KEY")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Create a .env file (copy from .env.example) and set them."
        )

    try:
        _supabase = create_client(url, key)
    except Exception as exc:
        raise RuntimeError(
            "Failed to create Supabase client. Check SUPABASE_URL/SUPABASE_KEY values."
        ) from exc

    return _supabase
