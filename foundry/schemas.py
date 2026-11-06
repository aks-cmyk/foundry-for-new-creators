"""Tool schemas — what the LLM sees. Names must match plugin.yaml provides_tools."""

def _obj(props, required):
    return {"type": "object", "properties": props, "required": required}


def _str(desc):
    return {"type": "string", "description": desc}


FOUNDRY_LEDGER_LIST = {
    "name": "foundry_ledger_list",
    "description": "List Foundry ledger cards, optionally filtered by kind (identity, evidence, draft, revision, performance, money) or status.",
    "parameters": _obj({"kind": _str("Card kind to filter by (optional)."),
                        "status": _str("Card status to filter by (optional).")}, []),
}

FOUNDRY_LEDGER_GET = {
    "name": "foundry_ledger_get",
    "description": "Get one Foundry ledger card by id, with its links to other cards.",
    "parameters": _obj({"card_id": _str("Card id, e.g. draft-002.")}, ["card_id"]),
}

FOUNDRY_DRAFT_CREATE = {
    "name": "foundry_draft_create",
    "description": "Scribe: create a Draft Card (X thread) from an Evidence Card and an Identity Card. Refuses if the evidence does not exist — Scribe cannot draft without cited evidence.",
    "parameters": _obj({"evidence_id": _str("Evidence Card id to cite."),
                        "identity_id": _str("Identity Card id to write in voice of."),
                        "hook": _str("First line of the thread."),
                        "body": {"type": "array", "items": {"type": "string"},
                                 "description": "Thread posts after the hook."}},
                       ["evidence_id", "identity_id", "hook", "body"]),
}

FOUNDRY_DRAFT_FEEDBACK = {
    "name": "foundry_draft_feedback",
    "description": "Record human feedback on a draft (approve / tweak / reject with a one-line note). On tweak, Scribe returns a revised draft as a new version; the original is never changed.",
    "parameters": _obj({"draft_id": _str("Draft Card id."),
                        "feedback_type": _str("approve, tweak, or reject."),
                        "note": _str("One-line note, e.g. 'sharper hook'. Required for tweak/reject.")},
                       ["draft_id", "feedback_type"]),
}

FOUNDRY_DRAFT_APPROVE = {
    "name": "foundry_draft_approve",
    "description": "Human approval gate: mark a Draft Card approved. Nothing posts until a human approves it.",
    "parameters": _obj({"draft_id": _str("Draft Card id.")}, ["draft_id"]),
}

FOUNDRY_SCORECARD = {
    "name": "foundry_scorecard",
    "description": "Scorekeeper: performance summary for a draft, with a repeat / drop / retry verdict.",
    "parameters": _obj({"draft_id": _str("Draft Card id.")}, ["draft_id"]),
}

FOUNDRY_MONEY_SUMMARY = {
    "name": "foundry_money_summary",
    "description": "Bursar: profit summary (costs, revenue, profit in cents) for a draft, client, or period. Tax figures are tracking estimates only.",
    "parameters": _obj({"draft_id": _str("Draft Card id (optional)."),
                        "client": _str("Client name, default 'self'.")}, []),
}

FOUNDRY_DASHBOARD_RENDER = {
    "name": "foundry_dashboard_render",
    "description": "Render the Foundry three-tab dashboard (Proofing Table / Scorekeeper / Bursar) as HTML from the ledger.",
    "parameters": _obj({}, []),
}

ALL_SCHEMAS = [FOUNDRY_LEDGER_LIST, FOUNDRY_LEDGER_GET, FOUNDRY_DRAFT_CREATE,
               FOUNDRY_DRAFT_FEEDBACK, FOUNDRY_DRAFT_APPROVE, FOUNDRY_SCORECARD,
               FOUNDRY_MONEY_SUMMARY, FOUNDRY_DASHBOARD_RENDER]
