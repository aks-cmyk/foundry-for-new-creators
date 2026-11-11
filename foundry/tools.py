"""Tool handlers — the code that runs when the LLM calls each tool.

Rules from the official guide: signature def handler(args: dict, **kwargs) -> str;
always return a JSON string, success and errors alike; never raise.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import bots, ledger, storage

# Ledger location (fixed 2026-11-06): the durable store
# plugin_db("foundry") -> <hermes home>/plugin-data/foundry/data.db,
# via foundry.storage — never a file inside the plugin folder (update /
# remove would delete it). The storage module owns the resolution, so
# tool handlers and the dashboard backend can never drift apart.
_DB_PATH = None  # kept for introspection; set_db_path() writes storage.

# PluginContext bound by register() in __init__.py. None outside Hermes
# (smoke tests, make demo) — Scribe then uses the rule-based rewrite.
_CTX = None


def bind_ctx(ctx) -> None:
    global _CTX
    _CTX = ctx


def _llm_complete(messages: list) -> str | None:
    """One host-LLM completion via ctx.llm (verified shape, Hermes
    v0.23.0: PluginLlm.complete(messages, temperature, max_tokens,
    timeout, purpose=...) -> result.text). No provider/model override,
    so the default trust gate passes. Returns None on any failure —
    the caller falls back to the rule-based rewrite."""
    if _CTX is None:
        return None
    try:
        result = _CTX.llm.complete(
            messages, temperature=0.7, max_tokens=800, timeout=120,
            purpose="foundry.scribe_revise")
        text = result.text.strip()
        return text or None
    except Exception:
        return None


def set_db_path(path) -> None:
    global _DB_PATH
    _DB_PATH = Path(path)
    storage.set_db_path(path)


def _conn():
    return storage.connect()


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


# Cartographer interview — the questions foundry_start asks, in order.
# Keys match cartographer_interview's answers dict; only who_you_help
# is required. Lists arrive as arrays or comma-separated strings.
INTERVIEW_QUESTIONS = [
    {"key": "who_you_help", "question": "Who do you help, and with what?", "required": True},
    {"key": "audience", "question": "Who exactly is your audience — describe them in a sentence.", "required": False},
    {"key": "story", "question": "Your story in a sentence or two: what did you build, and what did you learn?", "required": False},
    {"key": "pillars", "question": "Three topics you will write about most (your pillars)?", "required": False},
    {"key": "beliefs", "question": "What do you believe that most people in your niche get wrong?", "required": False},
    {"key": "against", "question": "What kind of advice will you never give?", "required": False},
    {"key": "voice_examples", "question": "Paste 2–3 lines you have written that sound like you.", "required": False},
    {"key": "voice_donts", "question": "Words or phrases you never want to see in your posts?", "required": False},
    {"key": "mission", "question": "Your mission in one line?", "required": False},
]


@_handler
def foundry_start(args, **kwargs):
    """Cartographer onboarding — the front door. Two steps, one tool:
    step 'begin' returns the interview questions (the agent asks them
    one at a time, in order); step 'complete' with answers writes the
    Identity Card. Only who_you_help is required. A bare call (no step)
    is 'begin'. Re-running after onboarding creates a new Identity
    version — the old one is never mutated."""
    step = args.get("step", "begin") or "begin"
    with _conn() as conn:
        if step == "begin":
            return _ok({"onboarded": bots.is_onboarded(conn),
                        "identity": bots.latest_identity(conn),
                        "questions": INTERVIEW_QUESTIONS,
                        "instruction": "Ask these questions one at a time, in order. "
                        "Only who_you_help is required. When the user has answered, "
                        "call foundry_start again with step 'complete' and the answers."})
        if step == "complete":
            answers = args.get("answers") or {}
            if not isinstance(answers, dict):
                return _err("answers must be an object keyed by interview question")
            for key in ("pillars", "beliefs", "voice_examples", "voice_donts"):
                v = answers.get(key)
                if isinstance(v, str):
                    answers[key] = [s.strip() for s in v.replace("\n", ",").split(",") if s.strip()]
            card = bots.cartographer_interview(conn, answers)
            return _ok({"identity": card, "onboarded": True,
                        "note": "Brand set. Scribe now drafts in this brand's voice; "
                        "see it on the Brand tab."})
        return _err("step must be 'begin' or 'complete'")


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
        identity = ledger.get_card(conn, args["identity_id"])
        if (identity is not None and identity["kind"] == "identity"
                and identity["payload"].get("origin") not in ("interview", "dashboard-edit")):
            return _err("identity-001 is Foundry's demo brand, not yours. "
                        "Run foundry_start first — a short interview sets up "
                        "your own brand — then draft with the new Identity Card.")
        card = bots.scribe_draft(conn, evidence_id=args["evidence_id"],
                                 identity_id=args["identity_id"],
                                 hook=args["hook"], body=args["body"])
    return _ok({"card": card})


@_handler
def foundry_draft_feedback(args, **kwargs):
    draft_id = args["draft_id"]
    ftype = args["feedback_type"]
    if ftype == "approve":
        return _err("Approval requires a trusted human review channel; approval is disabled until that channel is verified.")
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
                     "note": note, "author": "unverified", "applied_in": None},
            created_by="unverified")
        ledger.add_link(conn, rev["id"], draft_id, "revises")
        if ftype == "tweak":
            new_draft = bots.scribe_revise(
                conn, draft_id=draft_id, note=note,
                llm_complete=_llm_complete if _CTX is not None else None)
            ledger.add_event(conn, rev["id"], "applied", {"applied_in": new_draft["id"]})
            return _ok({"revision": ledger.get_card(conn, rev["id"]),
                        "revised_draft": new_draft})
        conn.execute("UPDATE cards SET status='rejected' WHERE id=?", (draft_id,))
        conn.commit()
        return _ok({"revision": ledger.get_card(conn, rev["id"]),
                    "draft": ledger.get_card(conn, draft_id)})


@_handler
def foundry_draft_approve(args, **kwargs):
    # Neither model arguments nor caller-supplied kwargs establish human origin.
    return _err("Approval requires a trusted human review channel; approval is disabled until that channel is verified.")


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


# NOTE (2026-11-06): the old foundry_dashboard_render tool was dropped.
# It did `from scripts.render_dashboard import render`, but scripts/ lives
# at the repo root, not inside an installed ~/.hermes/plugins/foundry/,
# so the tool failed in a live install. The static render still exists
# for demos via scripts/render_dashboard.py (make demo); the real
# dashboard surface is foundry/dashboard/ (web) and foundry/desktop/
# (Desktop GUI), served by plugin_api.py.
HANDLERS = {
    "foundry_start": foundry_start,
    "foundry_ledger_list": foundry_ledger_list,
    "foundry_ledger_get": foundry_ledger_get,
    "foundry_draft_create": foundry_draft_create,
    "foundry_draft_feedback": foundry_draft_feedback,
    "foundry_draft_approve": foundry_draft_approve,
    "foundry_scorecard": foundry_scorecard,
    "foundry_money_summary": foundry_money_summary,
}
