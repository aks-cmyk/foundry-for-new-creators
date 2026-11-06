"""Foundry bots — deterministic MVP implementations.

Bots are pure functions over the ledger. They never talk to each other
directly; they only read/write ledger cards (see docs/ARCHITECTURE.md).

MVP honesty: Scribe's revision is a rule-based rewrite of the seeded
draft, NOT a live LLM call. Lookout does not fetch the web — Evidence
Cards come from seed data or user-supplied sources. Live wiring
(Scribe via ctx.llm, Lookout via search) is the next build step and
its exact ctx.llm call shape is UNVERIFIED (docs/RESEARCH.md).
"""
from __future__ import annotations

import json

from . import ledger


def cartographer_interview(conn, answers: dict) -> dict:
    """Build an Identity Card from interview answers. Version 1 unless
    a previous Identity Card exists, in which case version + 1."""
    existing = ledger.list_cards(conn, kind="identity")
    version = (max(c["version"] for c in existing) + 1) if existing else 1
    card_id = f"identity-{version:03d}"
    payload = {
        "who_you_help": answers["who_you_help"],
        "audience": answers.get("audience", ""),
        "story": answers.get("story", ""),
        "pillars": answers.get("pillars", [])[:3],
        "beliefs": answers.get("beliefs", []),
        "against": answers.get("against", ""),
        "voice_examples": answers.get("voice_examples", [])[:5],
        "voice_donts": answers.get("voice_donts", []),
        "mission": answers.get("mission", ""),
    }
    supersedes = existing[-1]["id"] if existing else None
    return ledger.create_card(
        conn, id=card_id, kind="identity", version=version,
        lineage="identity-001", title="Identity Card",
        status="active", payload=payload, created_by="cartographer",
        supersedes_id=supersedes)


def lookout_evidence(conn, *, topic: str, sources: list[dict],
                     confirmed: list[str], niche: str) -> dict:
    """Create an Evidence Card. Requires >= 2 sources — a draft may
    only cite evidence that meets this bar."""
    if len(sources) < 2:
        raise ValueError("Evidence Card needs at least 2 sources")
    existing = ledger.list_cards(conn, kind="evidence")
    n = len(existing) + 1
    return ledger.create_card(
        conn, id=f"evidence-{n:03d}", kind="evidence", version=1,
        lineage=f"evidence-{n:03d}", title=f"Evidence: {topic}",
        status="active",
        payload={"topic": topic, "sources": sources,
                 "confirmed": confirmed, "unconfirmed": [], "niche": niche},
        created_by="lookout")


def scribe_draft(conn, *, evidence_id: str, identity_id: str,
                 hook: str, body: list[str]) -> dict:
    """Create a Draft Card. Refuses if the Evidence Card does not exist
    — Scribe cannot draft without citing evidence."""
    evidence = ledger.get_card(conn, evidence_id)
    if evidence is None:
        raise ValueError(f"no Evidence Card {evidence_id}: Scribe cannot draft without evidence")
    identity = ledger.get_card(conn, identity_id)
    if identity is None:
        raise ValueError(f"no Identity Card {identity_id}")
    existing = ledger.list_cards(conn, kind="draft")
    n = len(existing) + 1
    text = "\n\n".join([hook] + body)
    card = ledger.create_card(
        conn, id=f"draft-{n:03d}", kind="draft", version=1,
        lineage=f"draft-{n:03d}", title="X thread draft",
        status="in_review",
        payload={"platform": "x", "format": "thread", "text": text,
                 "evidence_ids": [evidence_id], "hook": hook,
                 "word_count": len(text.split()), "cost_cents": 0},
        created_by="scribe")
    ledger.add_link(conn, card["id"], evidence_id, "cites")
    ledger.add_link(conn, card["id"], identity_id, "derived_from")
    return ledger.get_card(conn, card["id"])


def _sharpen_hook(hook: str) -> str:
    """MVP rule-based revision for a 'sharper hook' note. A live Scribe
    would rewrite via the model; this deterministic rule keeps the
    demo loop working without an API key."""
    if hook.endswith(":"):
        return hook
    return hook.rstrip(".") + ": " + "here is the fix, in one thread."


def scribe_revise(conn, *, draft_id: str, note: str) -> dict:
    """Apply a Revision Card to a draft and return a new Draft Card (v+1).
    The original is never mutated."""
    draft = ledger.get_card(conn, draft_id)
    if draft is None:
        raise ValueError(f"no Draft Card {draft_id}")
    payload = dict(draft["payload"])
    lowered = note.lower()
    if "hook" in lowered:
        payload["hook"] = _sharpen_hook(payload["hook"])
        first, *rest = payload["text"].split("\n\n", 1)
        payload["text"] = payload["hook"] + ("\n\n" + rest[0] if rest else "")
    elif "short" in lowered:
        payload["text"] = payload["text"][:600]
    payload["word_count"] = len(payload["text"].split())
    existing = ledger.list_cards(conn, kind="draft")
    n = len(existing) + 1
    new = ledger.create_card(
        conn, id=f"draft-{n:03d}", kind="draft",
        version=draft["version"] + 1, lineage=draft["lineage"],
        title=draft["title"], status="in_review", payload=payload,
        created_by="scribe", supersedes_id=draft_id)
    for link in draft["links"]:
        ledger.add_link(conn, new["id"], link["to_id"], link["relation"])
    ledger.add_link(conn, new["id"], draft_id, "supersedes")
    return ledger.get_card(conn, new["id"])


def scorekeeper_verdict(conn, *, draft_id: str, metrics: dict) -> dict:
    """Write a Performance Card. Verdict rule (MVP, documented):
    repeat if reposts+replies beat the seeded baseline, else retry."""
    draft = ledger.get_card(conn, draft_id)
    if draft is None:
        raise ValueError(f"no Draft Card {draft_id}")
    engagement = metrics.get("reposts", 0) + metrics.get("replies", 0)
    verdict = "repeat" if engagement >= 50 else "retry_differently"
    existing = ledger.list_cards(conn, kind="performance")
    n = len(existing) + 1
    card = ledger.create_card(
        conn, id=f"performance-{n:03d}", kind="performance", version=1,
        lineage=f"performance-{n:03d}",
        title=f"Performance: {draft_id}", status="measured",
        payload={"draft_id": draft_id, "platform": "x",
                 **{k: metrics.get(k) for k in
                    ("views", "likes", "reposts", "replies", "saves")},
                 "verdict": verdict,
                 "verdict_reason": ("Hook format outperformed the last "
                                    "threads" if verdict == "repeat"
                                    else "Low replies — retry with a sharper hook"),
                 "measured_at": ledger.utcnow()},
        created_by="scorekeeper")
    ledger.add_link(conn, card["id"], draft_id, "measures")
    return ledger.get_card(conn, card["id"])


def bursar_money(conn, *, draft_id: str | None, cost_cents: int,
                 revenue_cents: int, client: str = "self",
                 partnership_id: str | None = None) -> dict:
    """Write a Money Card. Profit is computed, not asserted."""
    existing = ledger.list_cards(conn, kind="money")
    n = len(existing) + 1
    card = ledger.create_card(
        conn, id=f"money-{n:03d}", kind="money", version=1,
        lineage=f"money-{n:03d}",
        title=f"Money: {draft_id or 'period'}", status="final",
        payload={"draft_id": draft_id, "client": client,
                 "period": "2026-11", "cost_cents": cost_cents,
                 "revenue_cents": revenue_cents,
                 "profit_cents": revenue_cents - cost_cents,
                 "currency": "USD",
                 "cost_breakdown": {"model_cents": cost_cents // 2,
                                    "tools_cents": 0,
                                    "time_cents": cost_cents - cost_cents // 2},
                 "partnership_id": partnership_id},
        created_by="bursar")
    if draft_id:
        ledger.add_link(conn, card["id"], draft_id, "prices")
    return ledger.get_card(conn, card["id"])


def ledger_summary(conn) -> dict:
    cards = ledger.list_cards(conn)
    return {
        "counts": ledger.counts(conn),
        "drafts": [{"id": c["id"], "version": c["version"], "status": c["status"],
                    "title": c["title"]} for c in cards if c["kind"] == "draft"],
        "total_profit_cents": sum(
            c["payload"].get("profit_cents", 0) for c in cards
            if c["kind"] == "money" and c["payload"].get("record_type") != "partnership"),
    }
