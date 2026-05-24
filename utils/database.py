"""
database.py — Supabase persistence layer for NutriDesk
Replaces SQLite. All function signatures remain identical so no pages need changes.
"""

import json
import os
from datetime import datetime
from supabase import create_client as _supabase_create_client, Client

# ── Supabase client ────────────────────────────────────────────────────────
# Reads from Streamlit secrets (cloud) or environment variables (local)
def _get_client() -> Client:
    try:
        import streamlit as st
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "Supabase credentials missing. "
            "Set SUPABASE_URL and SUPABASE_KEY in .streamlit/secrets.toml or as env vars."
        )
    return _supabase_create_client(url, key)


def init_db():
    """No-op — tables are created in Supabase directly. Kept for compatibility."""
    pass


# ── JSON helpers ───────────────────────────────────────────────────────────
_JSON_FIELDS = (
    "cuisine_pref", "allergies", "dislikes", "veg_choices",
    "meat_choices", "snack_types", "medical_conditions", "meal_slots"
)

# Column name aliases: SQLite used capital L, Supabase schema uses lowercase
_COLUMN_ALIASES = {"water_intake_L": "water_intake_l"}

def _normalize_columns(data: dict) -> dict:
    """Rename any SQLite legacy column names to match Supabase schema."""
    return {_COLUMN_ALIASES.get(k, k): v for k, v in data.items()}

def _encode_json_fields(data: dict) -> dict:
    """Encode list fields as JSON strings before sending to Supabase."""
    d = _normalize_columns(dict(data))
    for key in _JSON_FIELDS:
        if key in d and isinstance(d[key], list):
            d[key] = json.dumps(d[key], ensure_ascii=False)
    return d

def _decode_json_fields(d: dict) -> dict:
    """Decode JSON string fields back to lists after reading from Supabase."""
    for key in _JSON_FIELDS:
        if d.get(key):
            try:
                d[key] = json.loads(d[key])
            except Exception:
                d[key] = []
        else:
            d[key] = []
    return d


# ── Clients ────────────────────────────────────────────────────────────────

def create_client(data: dict) -> int:
    db = _get_client()
    payload = _encode_json_fields(data)
    res = db.table("clients").insert(payload).execute()
    return res.data[0]["id"]


def update_client(client_id: int, data: dict):
    db = _get_client()
    payload = _encode_json_fields(data)
    payload["updated_at"] = datetime.utcnow().isoformat()
    db.table("clients").update(payload).eq("id", client_id).execute()


def get_all_clients() -> list[dict]:
    db = _get_client()
    res = db.table("clients") \
        .select("id, name, gender, weight_kg, goal, created_at") \
        .order("created_at", desc=True) \
        .execute()
    return res.data or []


def get_client(client_id: int) -> dict | None:
    db = _get_client()
    res = db.table("clients").select("*").eq("id", client_id).execute()
    if not res.data:
        return None
    return _decode_json_fields(res.data[0])


def delete_client(client_id: int):
    db = _get_client()
    # ON DELETE CASCADE handles related rows automatically
    db.table("clients").delete().eq("id", client_id).execute()


# ── Sessions (weight check-ins) ────────────────────────────────────────────

def add_session(client_id: int, weight_kg: float, notes: str = "") -> int:
    db = _get_client()
    res = db.table("client_sessions").insert({
        "client_id": client_id,
        "weight_kg": weight_kg,
        "notes": notes,
    }).execute()
    return res.data[0]["id"]


def get_sessions(client_id: int) -> list[dict]:
    db = _get_client()
    res = db.table("client_sessions") \
        .select("*") \
        .eq("client_id", client_id) \
        .order("session_date") \
        .execute()
    return res.data or []


# ── Meal Plans ─────────────────────────────────────────────────────────────

def save_meal_plan(client_id: int, plan: dict, targets: dict) -> int:
    db = _get_client()
    res = db.table("meal_plans").insert({
        "client_id":      client_id,
        "plan_json":      json.dumps(plan, ensure_ascii=False),
        "calorie_target": targets.get("calories"),
        "protein_target": targets.get("protein"),
        "carb_target":    targets.get("carbs"),
        "fat_target":     targets.get("fat"),
    }).execute()
    return res.data[0]["id"]


def get_latest_meal_plan(client_id: int) -> dict | None:
    db = _get_client()
    res = db.table("meal_plans") \
        .select("*") \
        .eq("client_id", client_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()
    if not res.data:
        return None
    d = res.data[0]
    d["plan"] = json.loads(d["plan_json"])
    return d


def get_all_meal_plans(client_id: int) -> list[dict]:
    db = _get_client()
    res = db.table("meal_plans") \
        .select("id, created_at, calorie_target") \
        .eq("client_id", client_id) \
        .order("created_at", desc=True) \
        .execute()
    return res.data or []


# ── Biomarkers ─────────────────────────────────────────────────────────────

def add_biomarkers(client_id: int, data: dict) -> int:
    db = _get_client()
    payload = dict(data)
    payload["client_id"] = client_id
    res = db.table("biomarkers").insert(payload).execute()
    return res.data[0]["id"]


def get_biomarkers(client_id: int) -> list[dict]:
    db = _get_client()
    res = db.table("biomarkers") \
        .select("*") \
        .eq("client_id", client_id) \
        .order("recorded_date") \
        .execute()
    return res.data or []


# Kept for compatibility — no-op in Supabase version
init_db()


# ── Client Personalization ─────────────────────────────────────────────────

def get_personalization(client_id: int) -> dict | None:
    """Retrieve saved personalisation for a client. Returns None if not set or table missing."""
    try:
        db = _get_client()
        res = db.table("client_personalization") \
            .select("*") \
            .eq("client_id", client_id) \
            .limit(1) \
            .execute()
        if not res.data:
            return None
        row = res.data[0]
        return {
            "exercises":   json.loads(row.get("exercises_json")   or "[]"),
            "guidelines":  json.loads(row.get("guidelines_json")  or "[]"),
            "avoid_items": json.loads(row.get("avoid_json")       or "[]"),
            "snacks":      json.loads(row.get("snacks_json")       or "[]"),
        }
    except Exception:
        return None  # Table not yet created — falls back to auto-generated plan


def save_personalization(client_id: int, plan: dict):
    """Upsert personalised plan for a client. Silently fails if table not yet created."""
    try:
      db = _get_client()
    payload = {
        "client_id":      client_id,
        "exercises_json": json.dumps(plan.get("exercises",   []), ensure_ascii=False),
        "guidelines_json":json.dumps(plan.get("guidelines",  []), ensure_ascii=False),
        "avoid_json":     json.dumps(plan.get("avoid_items", []), ensure_ascii=False),
        "snacks_json":    json.dumps(plan.get("snacks",      []), ensure_ascii=False),
        "updated_at":     datetime.utcnow().isoformat(),
        }
        db.table("client_personalization").upsert(payload, on_conflict="client_id").execute()
    except Exception:
        pass  # Table not yet created
