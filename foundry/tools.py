"""Tool handlers — the code that runs when the LLM calls each tool.

Rules from the official guide: signature def handler(args: dict, **kwargs) -> str;
always return a JSON string, success and errors alike; never raise.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import bots, ledger

# Standalone demo path. In Hermes, replace with plugin_db("foundry")
# (see docs/ARCHITECTURE.md). The path is overridable for tests.
_DEFAULT_DB = Path(__file__).parent / "data" / "foundry.db"
_DB_PATH = _DEFAULT_DB


def set_db_path(path) -> None:
    global _DB_PATH
    _DB_PATH = Path(path)


def _conn():
    return ledger.connect(_DB_PATH)


def _ok(data) -> str:
    return json.dumps({"ok": True, **data})


def _err(message: str) -> str:
    return json.dumps({"ok": False, "error": message})


def _handler(fn):
    def wrapper(args: dict, **kwargs) -> str:
        try:
            return fn(args, **kwargs)
        except Exception as exc:  # never raise from a handler
            return _err(str(exc))
    return wrapper


@_handler
def foundry_ledger_list(args, **kwargs):
    with _conn() as conn:
        cards = ledger.list_cards(conn, kind=args.get("kind"), status=args.get("status"))
    return _ok({"cards": [{k: c[k] for k in ("id", "kind", "version", "title", "status", "created_by")} for c in cards]})


@_handler
def foundry_ledger_get(args, **kwargs):
    with _conn() as conn:
        card = ledger.get_card(conn, args["card_id"])
    if card is None:
        return _err(f"no card {args['card_id']}")
    return _ok({"card": card})


@_handler
def foundry_draft_create(args, **kwargs):
    with _conn() as conn:
        card = bots.scribe_draft(conn, evidence_id=args["evidence_id"],
                                 identity_id=args["identity_id"],
                                 hook=args["hook"], body=args["body"])
    return _ok({"card": card})


@_handler
def foundry_draft_feedback(args, **kwargs):
    draft_id = args["draft_id"]
    ftype = args["feedback_type"]
    note = args.get("note", "")
    if ftype not in ("approve", "tweak", "reject"):
        return _err("feedback_type must be approve, tweak, or reject")
    if ftype in ("tweak", "reject") and not note:
        return _err("tweak/reject needs a one-line note")
    with _conn() as conn:
        draft = ledger.get_card(conn, draft_id)
        if draft is None:
            return _err(f"no Draft Card {draft_id}")
        existing = ledger.list_cards(conn, kind="revision")
        rev = ledger.create_card(
            conn, id=f"revision-{len(existing) + 1:03d}", kind="revision",
            version=1, lineage=f"revision-{len(existing) + 1:03d}",
            title=f"Feedback on {draft_id}", status="open",
            payload={"draft_id": draft_id, "feedback_type": ftype,
                     "note": note, "author": "human", "applied_in": None},
            created_by="human")
        ledger.add_link(conn, rev["id"], draft_id, "revises")
        if ftype == "tweak":
            new_draft = bots.scribe_revise(conn, draft_id=draft_id, note=note)
            ledger.add_event(conn, rev["id"], "applied", {"applied_in": new_draft["id"]})
            return _ok({"revision": ledger.get_card(conn, rev["id"]),
                        "revised_draft": new_draft})
        if ftype == "approve":
            conn.execute("UPDATE cards SET status='approved' WHERE id=?", (draft_id,))
            conn.commit()
            return _ok({"revision": ledger.get_card(conn, rev["id"]),
                        "draft": ledger.get_card(conn, draft_id)})
        conn.execute("UPDATE cards SET status='rejected' WHERE id=?", (draft_id,))
        conn.commit()
        return _ok({"revision": ledger.get_card(conn, rev["id"]),
                    "draft": ledger.get_card(conn, draft_id)})


@_handler
def foundry_draft_approve(args, **kwargs):
    with _conn() as conn:
        draft = ledger.get_card(conn, args["draft_id"])
        if draft is None:
            return _err(f"no Draft Card {args['draft_id']}")
        conn.execute("UPDATE cards SET status='approved' WHERE id=?", (args["draft_id"],))
        conn.commit()
        ledger.add_event(conn, args["draft_id"], "approved", {"by": "human"})
        return _ok({"draft": ledger.get_card(conn, args["draft_id"])})


@_handler
def foundry_scorecard(args, **kwargs):
    with _conn() as conn:
        cards = ledger.list_cards(conn, kind="performance")
    perf = [c for c in cards if c["payload"].get("draft_id") == args.get("draft_id")]
    if not perf:
        return _err(f"no Performance Card for {args.get('draft_id')}")
    return _ok({"performance": perf[-1]})


@_handler
def foundry_money_summary(args, **kwargs):
    with _conn() as conn:
        cards = ledger.list_cards(conn, kind="money")
    money = [c for c in cards if c["payload"].get("record_type") != "partnership"
             and c["payload"].get("record_type") != "tax"]
    if args.get("draft_id"):
        money = [c for c in money if c["payload"].get("draft_id") == args["draft_id"]]
    if not money:
        return _err("no Money Card found")
    total_profit = sum(c["payload"].get("profit_cents", 0) for c in money)
    return _ok({"money": money, "total_profit_cents": total_profit,
                "note": "Tax figures, where present, are tracking estimates only."})


@_handler
def foundry_dashboard_render(args, **kwargs):
    from scripts.render_dashboard import render
    out = render()
    return _ok({"dashboard": str(out)})


HANDLERS = {
    "foundry_ledger_list": foundry_ledger_list,
    "foundry_ledger_get": foundry_ledger_get,
    "foundry_draft_create": foundry_draft_create,
    "foundry_draft_feedback": foundry_draft_feedback,
    "foundry_draft_approve": foundry_draft_approve,
    "foundry_scorecard": foundry_scorecard,
    "foundry_money_summary": foundry_money_summary,
    "foundry_dashboard_render": foundry_dashboard_render,
}
