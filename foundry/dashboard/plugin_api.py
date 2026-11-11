"""Foundry dashboard backend — FastAPI routes.

Mounted by Hermes at /api/plugins/foundry/ (see the official dashboard
guide, and the Desktop SDK page: the same namespace is shared with the
Desktop half, which reaches it via ctx.rest). Serves ledger cards as
JSON; POST /feedback writes a real Revision Card and, for tweaks, a
revised draft (rule-based rewrite here — the dashboard process has no
ctx.llm bound; the live-LLM path runs in tool handlers, see tools.py).

Ledger location (fixed 2026-11-06): the durable store
plugin_db("foundry") via foundry.storage — the SAME database the tool
handlers use. Never a file inside the plugin folder.

UNVERIFIED: this file has not been loaded by a live `hermes dashboard`
or a live Desktop app. The import below (adding the plugin root's parent
to sys.path so `foundry.storage` resolves) is the scaffold's approach;
verify against the live dashboard loader before the catalog PR.
"""
import json
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


def _conn():
    """Ledger connection on the durable store (foundry.storage). Falls
    back to a direct read of the local demo DB if that import fails."""
    try:
        from foundry import storage
        return storage.connect()
    except Exception:
        from foundry import ledger
        return ledger.connect(_PLUGIN_ROOT / "data" / "foundry.db")


def _read_cards():
    from foundry import ledger
    conn = _conn()
    try:
        return ledger.list_cards(conn)
    finally:
        conn.close()


def _feedback(draft_id: str, feedback_type: str, note: str = "") -> dict:
    """Shared with the tool handler: record feedback on a draft.
    Returns the handler's parsed JSON dict."""
    from foundry import tools
    out = json.loads(tools.foundry_draft_feedback(
        {"draft_id": draft_id, "feedback_type": feedback_type, "note": note}))
    return out


# Endpoint functions are plain module-level functions so they are
# testable without FastAPI (the smoke test runs on system Python, which
# has no FastAPI; the gateway process does). They are registered onto
# the router only when FastAPI imported successfully.
def list_cards():
    return {"ok": True, "cards": _read_cards()}


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


def feedback(body: dict):
    """Human feedback from the Proofing Table (web or Desktop).
    Body: {"draft_id": ..., "feedback_type": "approve"|"tweak"|"reject",
    "note": "..."} — note required for tweak/reject. On tweak, Scribe
    returns a revised draft as a new version; the original is never
    changed. Returns {"ok": true, "revision": ..., "revised_draft"|"draft": ...}
    or {"ok": false, "error": ...}."""
    draft_id = (body or {}).get("draft_id")
    feedback_type = (body or {}).get("feedback_type")
    note = (body or {}).get("note", "") or ""
    if not draft_id or feedback_type not in ("approve", "tweak", "reject"):
        return {"ok": False,
                "error": "feedback needs draft_id and feedback_type approve|tweak|reject"}
    if feedback_type in ("tweak", "reject") and not note:
        return {"ok": False, "error": "tweak/reject needs a one-line note"}
    return _feedback(draft_id, feedback_type, note)


BRAND_FIELDS = ("who_you_help", "audience", "story", "pillars", "beliefs",
                "against", "voice_examples", "voice_donts", "mission")
BRAND_LIST_FIELDS = ("pillars", "beliefs", "voice_examples", "voice_donts")


def brand(body: dict):
    """Save the brand from the Brand tab (web or Desktop).
    Body: {"identity_id": ..., "payload": {...}} — identity_id is
    optional and defaults to the latest Identity Card. Merges the
    given fields over the current brand and writes a NEW Identity
    version (cards are never mutated); the old version is untouched.
    Lists may be arrays or comma-separated strings. Created by
    'dashboard' with origin 'dashboard-edit' — the dashboard has no
    auth channel, so the edit is recorded as a dashboard edit, never
    as human authorship. Returns {"ok": true, "identity": ...}."""
    from foundry import bots, ledger
    payload = (body or {}).get("payload") or {}
    if not isinstance(payload, dict):
        return {"ok": False, "error": "brand needs a payload object"}
    unknown = sorted(set(payload) - set(BRAND_FIELDS))
    if unknown:
        return {"ok": False, "error": "unknown brand fields: " + ", ".join(unknown)}
    conn = _conn()
    try:
        identity_id = (body or {}).get("identity_id")
        if identity_id:
            current = ledger.get_card(conn, identity_id)
            if current is None or current["kind"] != "identity":
                return {"ok": False, "error": f"no Identity Card {identity_id}"}
        else:
            current = bots.latest_identity(conn)
            if current is None:
                return {"ok": False, "error": "no Identity Card yet — run foundry_start first"}
        answers = dict(current["payload"])
        for key, value in payload.items():
            if key in BRAND_LIST_FIELDS and isinstance(value, str):
                value = [s.strip() for s in value.replace("\n", ",").split(",") if s.strip()]
            answers[key] = value
        answers.pop("origin", None)
        if not (answers.get("who_you_help") or "").strip():
            return {"ok": False, "error": "who_you_help is required"}
        card = bots.cartographer_interview(conn, answers,
                                           origin="dashboard-edit",
                                           created_by="dashboard")
        return {"ok": True, "identity": card}
    finally:
        conn.close()


if router is not None:
    router.get("/cards")(list_cards)
    router.get("/summary")(summary)
    router.post("/feedback")(feedback)
    router.post("/brand")(brand)
