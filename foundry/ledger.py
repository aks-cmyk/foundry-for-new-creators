"""Foundry shared ledger — SQLite cards + links + events.

In Hermes, the database lives at plugin_db("foundry") via
plugins.plugin_storage (see docs/ARCHITECTURE.md). In this scaffold,
callers pass an explicit path (tests use a temp file; the demo uses
data/foundry.db, regenerated from data/seed.json).

Invariants (see docs/LEDGER.md):
- Cards are never mutated in place; a new version is a new row with
  supersedes_id set.
- A Draft Card must cite >= 1 Evidence Card.
- Money is integer cents.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  version INTEGER NOT NULL,
  lineage TEXT NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  supersedes_id TEXT
);
CREATE TABLE IF NOT EXISTS links (
  from_id TEXT NOT NULL,
  to_id TEXT NOT NULL,
  relation TEXT NOT NULL,
  PRIMARY KEY (from_id, to_id, relation)
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id TEXT NOT NULL,
  event TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL
);
"""

KINDS = {"identity", "evidence", "draft", "revision", "performance", "money"}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str | Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def create_card(conn, *, id: str, kind: str, version: int, lineage: str,
                title: str, status: str, payload: dict,
                created_by: str, supersedes_id: str | None = None) -> dict:
    if kind not in KINDS:
        raise ValueError(f"unknown card kind: {kind}")
    row = {
        "id": id, "kind": kind, "version": version, "lineage": lineage,
        "title": title, "status": status,
        "payload": json.dumps(payload, sort_keys=True),
        "created_by": created_by, "created_at": utcnow(),
        "supersedes_id": supersedes_id,
    }
    conn.execute(
        "INSERT INTO cards VALUES (:id, :kind, :version, :lineage, :title,"
        " :status, :payload, :created_by, :created_at, :supersedes_id)", row)
    conn.execute("INSERT INTO events (card_id, event, detail, created_at)"
                 " VALUES (?, 'created', ?, ?)",
                 (id, json.dumps({"kind": kind, "version": version}), row["created_at"]))
    conn.commit()
    return get_card(conn, id)


def get_card(conn, card_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if row is None:
        return None
    card = dict(row)
    card["payload"] = json.loads(card["payload"])
    card["links"] = [dict(r) for r in conn.execute(
        "SELECT to_id, relation FROM links WHERE from_id = ?", (card_id,))]
    return card


def list_cards(conn, kind: str | None = None, status: str | None = None) -> list[dict]:
    sql, params = "SELECT * FROM cards", []
    where = []
    if kind:
        where.append("kind = ?")
        params.append(kind)
    if status:
        where.append("status = ?")
        params.append(status)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at, id"
    out = []
    for row in conn.execute(sql, params):
        card = dict(row)
        card["payload"] = json.loads(card["payload"])
        out.append(card)
    return out


def add_link(conn, from_id: str, to_id: str, relation: str) -> None:
    conn.execute("INSERT OR IGNORE INTO links VALUES (?, ?, ?)",
                 (from_id, to_id, relation))
    conn.commit()


def add_event(conn, card_id: str, event: str, detail: dict | None = None) -> None:
    conn.execute("INSERT INTO events (card_id, event, detail, created_at)"
                 " VALUES (?, ?, ?, ?)",
                 (card_id, event, json.dumps(detail or {}), utcnow()))
    conn.commit()


def load_seed(conn, seed_path: str | Path) -> dict[str, Any]:
    """Load seed.json: {"cards": [...], "links": [...]}. Idempotent-ish:
    clears existing cards first (demo DB only — never call on a live DB)."""
    seed = json.loads(Path(seed_path).read_text(encoding="utf-8"))
    conn.execute("DELETE FROM links")
    conn.execute("DELETE FROM events")
    conn.execute("DELETE FROM cards")
    for card in seed["cards"]:
        conn.execute(
            "INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (card["id"], card["kind"], card["version"], card["lineage"],
             card["title"], card["status"], json.dumps(card["payload"], sort_keys=True),
             card["created_by"], card.get("created_at", utcnow()),
             card.get("supersedes_id")))
    for link in seed.get("links", []):
        conn.execute("INSERT OR IGNORE INTO links VALUES (?, ?, ?)",
                     (link["from_id"], link["to_id"], link["relation"]))
    conn.commit()
    return {"cards_loaded": len(seed["cards"]), "links_loaded": len(seed.get("links", []))}


def counts(conn) -> dict[str, int]:
    return {row["kind"]: row["n"] for row in
            conn.execute("SELECT kind, COUNT(*) n FROM cards GROUP BY kind")}
