"""Foundry dashboard backend — FastAPI routes.

Mounted by Hermes at /api/plugins/foundry/ (see the official
dashboard guide). Serves ledger cards as JSON; feedback posts a
Revision Card and returns the revised draft.

UNVERIFIED: this file has not been loaded by a live `hermes dashboard`.
The import path below (adding the plugin root to sys.path) is the
scaffold's best effort; verify against the live dashboard loader
before the catalog PR.
"""
import json
import sqlite3
import sys
from pathlib import Path

try:
    from fastapi import APIRouter
except ImportError:  # pragma: no cover - FastAPI is a Hermes dependency
    APIRouter = None

router = APIRouter() if APIRouter else None

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(_PLUGIN_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT.parent))

DB_PATH = _PLUGIN_ROOT / "data" / "foundry.db"


def _read_cards():
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM cards ORDER BY created_at, id").fetchall()
    conn.close()
    out = []
    for row in rows:
        card = dict(row)
        card["payload"] = json.loads(card["payload"])
        out.append(card)
    return out


if router is not None:
    @router.get("/cards")
    def list_cards():
        return {"ok": True, "cards": _read_cards()}

    @router.get("/summary")
    def summary():
        cards = _read_cards()
        return {"ok": True,
                "counts": {k: sum(1 for c in cards if c["kind"] == k)
                           for k in ("identity", "evidence", "draft",
                                     "revision", "performance", "money")},
                "total_profit_cents": sum(
                    c["payload"].get("profit_cents", 0) for c in cards
                    if c["kind"] == "money"
                    and c["payload"].get("record_type") != "partnership")}
