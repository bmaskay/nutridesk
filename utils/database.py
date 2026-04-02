"""
database.py — SQLite persistence layer for NutriDesk
Tables: clients, client_sessions, meal_plans, biomarkers
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

# Store DB in home dir — mounted filesystems (FUSE) don't support SQLite locking
DB_PATH = Path.home() / ".nutridesk" / "clients.db"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT,
            phone       TEXT,
            dob         TEXT,
            gender      TEXT,
            height_cm   REAL,
            weight_kg   REAL,
            goal        TEXT,
            activity_level TEXT,
            -- Section 2: Lifestyle
            occupation  TEXT,
            sleep_hrs   REAL,
            stress_level TEXT,
            water_intake_L REAL,
            -- Section 3: Food preferences
            diet_type   TEXT,          -- vegetarian / non-vegetarian / eggetarian / vegan
            cuisine_pref TEXT,         -- JSON list
            allergies   TEXT,          -- JSON list
            dislikes    TEXT,          -- JSON list
            meal_frequency INTEGER,    -- meals per day
            veg_choices TEXT,          -- JSON list of preferred vegetables
            meat_choices TEXT,         -- JSON list of preferred meats
            -- Section 4: Snacks
            snack_frequency INTEGER,
            snack_types TEXT,          -- JSON list
            -- Medical
            medical_conditions TEXT,   -- JSON list
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            updated_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS client_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id   INTEGER NOT NULL,
            session_date TEXT DEFAULT (date('now','localtime')),
            weight_kg   REAL,
            notes       TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );

        CREATE TABLE IF NOT EXISTS meal_plans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id   INTEGER NOT NULL,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            plan_json   TEXT NOT NULL,   -- serialised 7-day plan dict
            calorie_target REAL,
            protein_target REAL,
            carb_target REAL,
            fat_target  REAL,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );

        CREATE TABLE IF NOT EXISTS biomarkers (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id       INTEGER NOT NULL,
            recorded_date   TEXT DEFAULT (date('now','localtime')),
            fasting_glucose REAL,
            hba1c           REAL,
            total_cholesterol REAL,
            hdl             REAL,
            ldl             REAL,
            triglycerides   REAL,
            tsh             REAL,
            vitamin_d       REAL,
            b12             REAL,
            ferritin        REAL,
            notes           TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );
    """)
    conn.commit()
    conn.close()


# ── Clients ────────────────────────────────────────────────────────────────

def create_client(data: dict) -> int:
    """Insert a new client, return new id."""
    conn = get_conn()
    c = conn.cursor()
    # JSON-encode list fields
    for key in ("cuisine_pref", "allergies", "dislikes", "veg_choices",
                "meat_choices", "snack_types", "medical_conditions"):
        if key in data and isinstance(data[key], list):
            data[key] = json.dumps(data[key], ensure_ascii=False)
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    c.execute(f"INSERT INTO clients ({cols}) VALUES ({placeholders})",
              list(data.values()))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id


def update_client(client_id: int, data: dict):
    for key in ("cuisine_pref", "allergies", "dislikes", "veg_choices",
                "meat_choices", "snack_types", "medical_conditions"):
        if key in data and isinstance(data[key], list):
            data[key] = json.dumps(data[key], ensure_ascii=False)
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    set_clause = ", ".join(f"{k} = ?" for k in data)
    conn.execute(
        f"UPDATE clients SET {set_clause} WHERE id = ?",
        list(data.values()) + [client_id]
    )
    conn.commit()
    conn.close()


def get_all_clients() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, gender, weight_kg, goal, created_at FROM clients ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_client(client_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for key in ("cuisine_pref", "allergies", "dislikes", "veg_choices",
                "meat_choices", "snack_types", "medical_conditions"):
        if d.get(key):
            try:
                d[key] = json.loads(d[key])
            except Exception:
                d[key] = []
        else:
            d[key] = []
    return d


def delete_client(client_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.execute("DELETE FROM client_sessions WHERE client_id = ?", (client_id,))
    conn.execute("DELETE FROM meal_plans WHERE client_id = ?", (client_id,))
    conn.execute("DELETE FROM biomarkers WHERE client_id = ?", (client_id,))
    conn.commit()
    conn.close()


# ── Sessions (weight check-ins) ─────────────────────────────────────────────

def add_session(client_id: int, weight_kg: float, notes: str = "") -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO client_sessions (client_id, weight_kg, notes) VALUES (?, ?, ?)",
        (client_id, weight_kg, notes)
    )
    conn.commit()
    sid = c.lastrowid
    conn.close()
    return sid


def get_sessions(client_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM client_sessions WHERE client_id = ? ORDER BY session_date",
        (client_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Meal Plans ──────────────────────────────────────────────────────────────

def save_meal_plan(client_id: int, plan: dict, targets: dict) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """INSERT INTO meal_plans
           (client_id, plan_json, calorie_target, protein_target, carb_target, fat_target)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (client_id, json.dumps(plan, ensure_ascii=False),
         targets.get("calories"), targets.get("protein"),
         targets.get("carbs"), targets.get("fat"))
    )
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return pid


def get_latest_meal_plan(client_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM meal_plans WHERE client_id = ? ORDER BY created_at DESC LIMIT 1",
        (client_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["plan"] = json.loads(d["plan_json"])
    return d


def get_all_meal_plans(client_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, created_at, calorie_target FROM meal_plans WHERE client_id = ? ORDER BY created_at DESC",
        (client_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Biomarkers ──────────────────────────────────────────────────────────────

def add_biomarkers(client_id: int, data: dict) -> int:
    conn = get_conn()
    c = conn.cursor()
    data["client_id"] = client_id
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    c.execute(f"INSERT INTO biomarkers ({cols}) VALUES ({placeholders})",
              list(data.values()))
    conn.commit()
    bid = c.lastrowid
    conn.close()
    return bid


def get_biomarkers(client_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM biomarkers WHERE client_id = ? ORDER BY recorded_date",
        (client_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Initialise on import
init_db()
