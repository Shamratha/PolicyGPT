from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, created_at TEXT NOT NULL, role TEXT NOT NULL,
                query TEXT NOT NULL, response_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, domain TEXT NOT NULL,
                agency TEXT NOT NULL, source_url TEXT NOT NULL, effective_date TEXT,
                version TEXT NOT NULL, text TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """)

    def save_session(self, role: str, query: str, response: dict[str, Any]) -> str:
        sid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as c:
            c.execute("INSERT INTO sessions VALUES (?,?,?,?,?)", (sid, now, role, query, json.dumps(response)))
        return sid

    def recent_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as c:
            rows = c.execute("SELECT id,created_at,role,query FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def save_document(self, doc: dict[str, Any]) -> str:
        did = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as c:
            c.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?)", (did, doc["title"], doc["domain"], doc["agency"], doc["source_url"], doc.get("effective_date"), doc.get("version", "1.0"), doc["text"], now))
        return did
