"""Durable ledger location — the fix for the ledger-location bug.

The scaffold stored the ledger at ``foundry/data/foundry.db`` *inside* the
plugin folder. The official plugin guide is explicit: never write runtime
state into the plugin directory — ``hermes plugins update`` / ``remove``
delete it. The durable store is ``plugins.plugin_storage``:

    from plugins.plugin_storage import plugin_data_dir, plugin_db

``plugin_db("foundry")`` opens ``<hermes home>/plugin-data/foundry/data.db``
(WAL-safe via Hermes's shared ``open_db`` helper; survives update/remove;
follows the active profile). ``db_path()`` below returns that same file,
so every part of Foundry — tool handlers, the dashboard backend, the
Desktop half's backend — reads and writes ONE database.

Standalone fallback: outside Hermes (smoke tests, ``make demo``) the
``plugins`` package is not importable, so the local demo file
``foundry/data/foundry.db`` is used instead. Tool handlers can also be
pointed at an explicit path with ``tools.set_db_path()`` (tests do this).

First-use seeding: a brand-new durable database is empty, so ``connect()``
seeds it from ``foundry/data/seed.json`` (9 cards) the first time — and
only then. ``load_seed`` is never called on a non-empty database, so live
user data is never wiped by a re-seed.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import ledger

PLUGIN_NAME = "foundry"
_FALLBACK_DB = Path(__file__).parent / "data" / "foundry.db"
_SEED = Path(__file__).parent / "data" / "seed.json"

# Explicit override (tests / dev only). When set, every caller — tool
# handlers AND the dashboard backend — uses this file, so they can never
# drift apart. tools.set_db_path() sets it.
_OVERRIDE: Path | None = None


def set_db_path(path) -> None:
    global _OVERRIDE
    _OVERRIDE = Path(path)


def db_path() -> Path:
    """Path of the durable ledger file — the same file ``plugin_db("foundry")``
    opens (default filename ``data.db``). Falls back to the local demo file
    outside Hermes. An explicit override (tests) wins."""
    if _OVERRIDE is not None:
        return _OVERRIDE
    try:
        from plugins.plugin_storage import plugin_data_dir
        return plugin_data_dir(PLUGIN_NAME) / "data.db"
    except Exception:
        return _FALLBACK_DB


def _ensure_seed(conn) -> None:
    if ledger.counts(conn):
        return
    if _SEED.exists():
        ledger.load_seed(conn, _SEED)


def connect():
    """Open the ledger on the durable store, creating + seeding it on
    first use. Uses Hermes's ``plugin_db`` (safe SQLite handling) when
    available, else the local demo file via ``ledger.connect``. An
    explicit override (tests) is a plain ``ledger.connect`` on that file."""
    if _OVERRIDE is not None:
        conn = ledger.connect(_OVERRIDE)
        _ensure_seed(conn)
        return conn
    try:
        from plugins.plugin_storage import plugin_db
        conn = plugin_db(PLUGIN_NAME)
        conn.row_factory = sqlite3.Row
        conn.executescript(ledger.SCHEMA)
        _ensure_seed(conn)
        return conn
    except Exception:
        conn = ledger.connect(_FALLBACK_DB)
        _ensure_seed(conn)
        return conn
