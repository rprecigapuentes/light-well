import json
import os
import time
from typing import Any, Dict, List, Optional

import httpx


class GroqError(RuntimeError):
    """Raised when Groq API call fails."""


def _get_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise GroqError(f"Missing required env var: {name}")
    return v


def _compact_daily_l04(l04_by_day: Any, top_k: int = 7) -> Dict[str, Any]:
    """
    Reduce daily L04 payload to avoid token bloat.
    Expects l04_by_day like:
      {"YYYY-MM-DD": {"tier_1": {...}, "tier_2": {...}, "notes": ...}, ...}
    Keeps:
      - closest days to compliance by missing minutes (tier_1)
      - most recent days
    """
    if not isinstance(l04_by_day, dict) or not l04_by_day:
        return {
            "days": {},
            "closest_tier_1": [],
            "closest_tier_2": [],
        }

    # Sort days (ISO date sorts lexicographically)
    all_days = sorted(l04_by_day.keys())
    most_recent_days = all_days[-top_k:]

    def _missing(day_data: dict, tier_key: str) -> int:
        try:
            return int(day_data[tier_key].get("missing_minutes", 999999))
        except Exception:
            return 999999

    # Compute closest days by missing minutes (smaller is better)
    scored_t1 = [(d, _missing(l04_by_day[d], "tier_1")) for d in all_days]
    scored_t2 = [(d, _missing(l04_by_day[d], "tier_2")) for d in all_days]

    scored_t1.sort(key=lambda x: x[1])
    scored_t2.sort(key=lambda x: x[1])

    closest_t1 = [d for d, m in scored_t1[:top_k] if m < 999999]
    closest_t2 = [d for d, m in scored_t2[:top_k] if m < 999999]

    # Keep only union of (most recent) U (closest)
    keep_days = sorted(set(most_recent_days + closest_t1 + closest_t2))

    days_compact: Dict[str, Any] = {}
    for d in keep_days:
        day_data = l04_by_day.get(d, {})
        # Keep only the essentials needed for "missing minutes" explanations
        def _tier_compact(tier: dict) -> dict:
            return {
                "compliant": tier.get("compliant"),
                "threshold": tier.get("threshold"),
                "best_continuous_minutes": tier.get("best_continuous_minutes"),
                "missing_minutes": tier.get("missing_minutes"),
                "best_window_start": tier.get("best_window_start"),
                "best_window_end": tier.get("best_window_end"),
                "required_minutes": tier.get("required_minutes"),
                "max_gap_min": tier.get("max_gap_min"),
            }

        days_compact[d] = {
            "tier_1": _tier_compact(day_data.get("tier_1", {})),
            "tier_2": _tier_compact(day_data.get("tier_2", {})),
            "notes": day_data.get("notes"),
        }

    return {
        "days": days_compact,
        "closest_tier_1": closest_t1,
        "closest_tier_2": closest_t2,
        "most_recent_days": most_recent_days,
    }


def _build_messages(context: Dict[str, Any], question: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Build a 3-message chat payload:
      1) system rules
      2) system context (authoritative project + normative context + computed data)
      3) user instruction (summary mode or Q&A mode)
    """

    # ------------------------------------------------------------------
    # 1) SYSTEM RULES (fixed behavior constraints)
    # ------------------------------------------------------------------
    system_rules = (
        "You are a technical assistant specialized in circadian lighting and WELL v2 (L04/L05). "
        "Use ONLY the provided data and definitions. "
        "Do NOT invent measurements, timestamps, thresholds, standards, or compliance results. "
        "If information is missing or insufficient, state it explicitly and explain what would be needed.\n\n"
        "Output format rules:\n"
        '- If no user question is provided: return JSON with keys: "summary", "recommendations".\n'
        '- If a user question is provided: return JSON with keys: "answer", "notes".\n'
        '- "summary" must be <= 120 words.\n'
        '- "recommendations" must be an array of exactly 3 short items.\n'
        "- Never include raw rows, time series dumps, or unnecessary numerical detail.\n"
        "- When referencing WELL v2, focus on L04 and optionally mention L05 only as a stricter extension.\n"
        "- If daily L04 results are available, explicitly report the day closest to compliance and missing minutes."
    )

    # ------------------------------------------------------------------
    # 2) SYSTEM CONTEXT (authoritative knowledge for THIS project)
    # ------------------------------------------------------------------
    # Compact the daily L04 to avoid sending massive payloads
    context_for_llm = dict(context)

    l04_by_day = context_for_llm.get("l04_by_day")
    if isinstance(l04_by_day, dict):
        # Replace with compact version
        context_for_llm["l04_by_day_compact"] = _compact_daily_l04(l04_by_day, top_k=7)
        # Optionally remove the full daily block to save tokens
        context_for_llm.pop("l04_by_day", None)

    context_block = (
        "PROJECT CONTEXT (AUTHORITATIVE — DO NOT IGNORE):\n\n"
        "Project name: LightWell.\n"
        "LightWell is a wearable-based circadian lighting assessment system.\n"
        "It does NOT directly control luminaires.\n"
        "Lighting control logic is implemented separately at the firmware level (e.g., ESP32).\n\n"
        "This backend:\n"
        "- estimates melanopic EDI from calibrated sensors,\n"
        "- evaluates compliance with WELL v2 (L04),\n"
        "- summarizes results and explains them to the user.\n\n"
        "The LLM is used ONLY for interpretation and explanation.\n"
        "All compliance decisions are computed deterministically in software, not by the LLM.\n\n"
        "------------------------------------------------------------\n"
        "WELL v2 – L04 (Circadian Lighting Design) — DEFINITION:\n\n"
        "WELL L04 is a building and human health standard related to circadian lighting.\n"
        "It is NOT related to oil, gas, drilling, or industrial well control.\n\n"
        "Purpose:\n"
        "Support circadian entrainment by ensuring sufficient morning exposure to melanopic light.\n\n"
        "Metric:\n"
        "- melanopic EDI (CIE S 026).\n\n"
        "Core requirement:\n"
        "- A continuous 4-hour window before local noon.\n"
        "- The melanopic EDI threshold must be maintained continuously.\n"
        "- Averages or accumulated dose are NOT sufficient.\n\n"
        "Thresholds:\n"
        "- Tier 1: >= 136 melanopic EDI.\n"
        "- Tier 2: >= 250 melanopic EDI.\n\n"
        "Interpretation:\n"
        "- If no valid continuous 4-hour window exists, the day is non-compliant.\n"
        "- If daily results exist, report missing minutes and the closest day to compliance.\n"
        "- WELL L04 does NOT define night-time limits.\n"
        "- Night-time reduction is a design choice, not a direct L04 requirement.\n\n"
        "------------------------------------------------------------\n"
        "DATA CONTEXT:\n\n"
        "User timezone: America/Bogota (UTC-5).\n"
        'Data source: Supabase table "mediciones" with fields:\n'
        "- created_at (TIMESTAMPTZ, stored in UTC)\n"
        "- edi (melanopic EDI estimate)\n\n"
        "Computed outputs (authoritative, already validated):\n"
        f"{json.dumps(context_for_llm, ensure_ascii=False)}\n"
    )

    # ------------------------------------------------------------------
    # 3) USER TASK (summary or Q&A)
    # ------------------------------------------------------------------
    if question and question.strip():
        user_task = (
            "User question:\n"
            f"{question.strip()}\n\n"
            "Answer using ONLY the project and WELL L04 context above and the computed outputs. "
            "If the question cannot be answered from the data, state clearly what is missing.\n"
            'Return JSON with keys: "answer", "notes".\n'
            "If daily L04 is available, include: closest day to Tier 1 compliance and missing minutes."
        )
    else:
        user_task = (
            "Generate:\n"
            "1) A short summary (<= 120 words) describing the circadian lighting situation "
            "and WELL L04 compliance status.\n"
            "2) Exactly 3 actionable recommendations to improve or maintain WELL L04 compliance.\n"
            'Return JSON with keys: "summary", "recommendations".\n'
            "If daily L04 is available, mention the closest day to compliance and missing minutes."
        )

    return [
        {"role": "system", "content": system_rules},
        {"role": "system", "content": context_block},
        {"role": "user", "content": user_task},
    ]


def _post_chat_completions(messages: List[Dict[str, str]], timeout_s: float = 15.0) -> Dict[str, Any]:
    """
    Call Groq OpenAI-compatible /chat/completions.

    Retries:
      - 429: up to 3 retries with exponential backoff
    Errors:
      - 401/403: immediate failure
      - 5xx: immediate failure
    """
    api_key = _get_env("GROQ_API_KEY")
    base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
    model = _get_env("GROQ_MODEL")

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    max_retries_429 = 3
    backoff_s = 1.0

    with httpx.Client(timeout=timeout_s) as client:
        for attempt in range(max_retries_429 + 1):
            resp = client.post(url, headers=headers, json=payload)

            if resp.status_code in (401, 403):
                raise GroqError("Unauthorized (401/403). Check GROQ_API_KEY and project access.")

            if resp.status_code == 429:
                if attempt >= max_retries_429:
                    raise GroqError("Rate limited (429). Max retries reached.")
                time.sleep(backoff_s)
                backoff_s *= 2.0
                continue

            if 500 <= resp.status_code <= 599:
                raise GroqError(f"Groq server error ({resp.status_code}). Try again later.")

            if resp.status_code >= 400:
                raise GroqError(f"Groq request failed ({resp.status_code}): {resp.text}")

            return resp.json()

    raise GroqError("Groq request failed unexpectedly.")


def _extract_json_from_response(resp_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract assistant content and parse it as JSON.
    Accepts:
      - pure JSON
      - JSON wrapped in ```json ... ``` fences
    If parsing fails, return a fallback dict.
    """
    try:
        content = resp_json["choices"][0]["message"]["content"]
    except Exception:
        return {"error": "Invalid Groq response format", "raw": resp_json}

    s = (content or "").strip()

    # Remove Markdown code fences if present
    if s.startswith("```"):
        lines = s.splitlines()
        # drop first line: ``` or ```json
        if lines:
            lines = lines[1:]
        # drop last line if it's ```
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        s = "\n".join(lines).strip()

    # Now try strict JSON parse
    try:
        return json.loads(s)
    except Exception:
        return {
            "error": "LLM did not return valid JSON",
            "raw_text": (content or "").strip(),
        }


def groq_generate(context: Dict[str, Any], question: Optional[str] = None) -> Dict[str, Any]:
    """
    High-level helper:
      - Builds messages
      - Calls Groq
      - Returns parsed JSON (or a safe fallback)
    """
    messages = _build_messages(context=context, question=question)
    resp_json = _post_chat_completions(messages=messages)
    return _extract_json_from_response(resp_json)
