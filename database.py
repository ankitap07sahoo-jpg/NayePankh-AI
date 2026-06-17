import json
import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = BASE_DIR / "exports"
DB_PATH = DATA_DIR / "app.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            name TEXT,
            interests TEXT,
            skills TEXT,
            education TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_name TEXT,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            response TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS generated_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_name TEXT,
            content_type TEXT NOT NULL,
            topic TEXT,
            audience TEXT,
            tone TEXT,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_name TEXT,
            campaign_name TEXT NOT NULL,
            goal TEXT,
            target_audience TEXT,
            duration TEXT,
            budget TEXT,
            report_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS volunteer_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_name TEXT,
            request_json TEXT NOT NULL,
            response_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            memory_key TEXT NOT NULL,
            memory_value TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, memory_key)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS app_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def record_app_event(session_id: str, event_type: str, payload: Any) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO app_events (session_id, event_type, payload) VALUES (?, ?, ?)",
        (session_id, event_type, json.dumps(payload, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def save_chat_message(session_id: str, user_name: str, role: str, message: str, response: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_history (session_id, user_name, role, message, response) VALUES (?, ?, ?, ?, ?)",
        (session_id, user_name, role, message, response),
    )
    conn.commit()
    conn.close()


def get_chat_history(session_id: str, limit: int = 100) -> list[dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT role, message, response, timestamp
        FROM chat_history
        WHERE session_id = ?
        ORDER BY id ASC
        LIMIT ?
        """,
        (session_id, limit),
    ).fetchall()
    conn.close()
    transcript: list[dict[str, Any]] = []
    for row in rows:
        content = row["message"] if row["role"] == "user" else (row["response"] or row["message"])
        transcript.append(
            {
                "role": row["role"],
                "content": content,
                "timestamp": row["timestamp"],
            }
        )
    return transcript


def save_content(session_id: str, user_name: str, content_type: str, topic: str, audience: str, tone: str, content: str) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO generated_content (session_id, user_name, content_type, topic, audience, tone, content)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (session_id, user_name, content_type, topic, audience, tone, content),
    )
    conn.commit()
    conn.close()


def save_campaign_plan(session_id: str, user_name: str, campaign_name: str, goal: str, target_audience: str, duration: str, budget: str, report_json: dict) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO campaigns (session_id, user_name, campaign_name, goal, target_audience, duration, budget, report_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (session_id, user_name, campaign_name, goal, target_audience, duration, budget, json.dumps(report_json, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def save_volunteer_recommendation(session_id: str, user_name: str, request_json: dict, response_json: dict) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO volunteer_recommendations (session_id, user_name, request_json, response_json)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, user_name, json.dumps(request_json, ensure_ascii=False), json.dumps(response_json, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def set_memory_value(session_id: str, memory_key: str, memory_value: str) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO user_memory (session_id, memory_key, memory_value, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(session_id, memory_key) DO UPDATE SET
            memory_value = excluded.memory_value,
            updated_at = CURRENT_TIMESTAMP
        """,
        (session_id, memory_key, memory_value),
    )
    conn.commit()
    conn.close()


def get_memory(session_id: str) -> dict[str, str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT memory_key, memory_value FROM user_memory WHERE session_id = ?",
        (session_id,),
    ).fetchall()
    conn.close()
    return {row["memory_key"]: row["memory_value"] for row in rows}


def get_user_profile(session_id: str) -> dict[str, str]:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT name, interests, skills, education
        FROM users
        WHERE session_id = ? AND COALESCE(name, '') != ''
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """,
        (session_id,),
    ).fetchone()
    conn.close()
    if not row:
        return {}
    return dict(row)


def upsert_user_profile(session_id: str, name: str = "", interests: str = "", skills: str = "", education: str = "") -> None:
    if not name.strip():
        return
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE session_id = ? AND name = ?", (session_id, name)).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE users
            SET interests = ?, skills = ?, education = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (interests, skills, education, existing["id"]),
        )
    else:
        conn.execute(
            """
            INSERT INTO users (session_id, name, interests, skills, education)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, name, interests, skills, education),
        )
    conn.commit()
    conn.close()


def _fetch_recent(table: str, limit: int = 10) -> list[dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_recent_content(limit: int = 10) -> list[dict[str, Any]]:
    return _fetch_recent("generated_content", limit)


def get_recent_campaigns(limit: int = 10) -> list[dict[str, Any]]:
    return _fetch_recent("campaigns", limit)


def get_recent_volunteer_recommendations(limit: int = 10) -> list[dict[str, Any]]:
    return _fetch_recent("volunteer_recommendations", limit)


def get_statistics() -> dict[str, int]:
    conn = get_connection()
    stats = {
        "total_users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "total_chat_interactions": conn.execute("SELECT COUNT(*) FROM chat_history").fetchone()[0],
        "total_campaigns": conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0],
        "total_content": conn.execute("SELECT COUNT(*) FROM generated_content").fetchone()[0],
        "total_recommendations": conn.execute("SELECT COUNT(*) FROM volunteer_recommendations").fetchone()[0],
    }
    conn.close()
    return stats
