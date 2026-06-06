"""
Telemetry & Analytics Database
==============================
Lightweight SQLite database for tracking system usage, response times,
and user feedback.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/telemetry.db")


def _get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize the telemetry database schema."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_query TEXT NOT NULL,
                domain TEXT,
                response_time_ms INTEGER,
                provider_name TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER,
                timestamp TEXT NOT NULL,
                feedback_type TEXT NOT NULL, -- 'up' or 'down'
                FOREIGN KEY(query_id) REFERENCES queries(id)
            )
            """
        )
        conn.commit()


def log_query(user_query: str, domain: str, response_time_ms: int, provider_name: str) -> int:
    """Log a user query and return the query ID."""
    init_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO queries (timestamp, user_query, domain, response_time_ms, provider_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (datetime.now().isoformat(), user_query, domain, response_time_ms, provider_name),
        )
        conn.commit()
        return cursor.lastrowid


def log_feedback(query_id: int, feedback_type: str):
    """Log user feedback for a specific query."""
    init_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO feedback (query_id, timestamp, feedback_type)
            VALUES (?, ?, ?)
            """,
            (query_id, datetime.now().isoformat(), feedback_type),
        )
        conn.commit()


def get_telemetry_stats() -> dict:
    """Return high-level analytics from the SQLite database."""
    init_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM queries")
        total_queries = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(response_time_ms) FROM queries")
        avg_response_time = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type = 'up'")
        thumbs_up = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type = 'down'")
        thumbs_down = cursor.fetchone()[0]
        
    return {
        "total_queries": total_queries,
        "avg_response_time_ms": round(avg_response_time, 2),
        "thumbs_up": thumbs_up,
        "thumbs_down": thumbs_down,
    }
