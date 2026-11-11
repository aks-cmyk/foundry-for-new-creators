"""Tool schemas — what the LLM sees. Names must match plugin.yaml provides_tools."""

def _obj(props, required):
    return {"type": "object", "properties": props, "required": required}


def _str(desc):
    return {"type": "string", "description": desc}


FOUNDRY_START = {
    "name": "foundry_start",
    "description": "Patternmaker: start Foundry — the onboarding interview that sets up the creator's brand. Say 'foundry start' to run this. Call with step 'begin' (or no arguments) to get the interview questions; ask them one at a time, in order. Then call again with step 'complete' and the answers to write the Identity Card. Only who_you_help is required. Until a brand exists, Smith cannot draft in the user's voice — drafting with the demo brand is refused.",
    "parameters": _obj({"step": _str("begin: get the interview questions. complete: write the Identity Card from answers."),
                        "answers": {"type": "object",
                                    "description": "Interview answers keyed by question: who_you_help (required), audience, story, pillars (up to 3), beliefs, against, voice_examples (up to 5), voice_donts, mission. Lists may be given as arrays or comma-separated strings."}},
                       []),
}

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
    "description": "Smith: create a Draft Card (X thread) from an Evidence Card and an Identity Card. Refuses if the evidence does not exist — Smith cannot draft without cited evidence.",
    "parameters": _obj({"evidence_id": _str("Evidence Card id to cite."),
                        "identity_id": _str("Identity Card id to write in voice of."),
                        "hook": _str("First line of the thread."),
                        "body": {"type": "array", "items": {"type": "string"},
                                 "description": "Thread posts after the hook."}},
                       ["evidence_id", "identity_id", "hook", "body"]),
}

FOUNDRY_DRAFT_FEEDBACK = {
    "name": "foundry_draft_feedback",
    "description": "Record feedback on a draft (tweak / reject with a one-line note; approve is disabled — no trusted human review channel yet). On tweak, Smith returns a revised draft as a new version; the original is never changed. Feedback is recorded as unverified, never as human authorship.",
    "parameters": _obj({"draft_id": _str("Draft Card id."),
                        "feedback_type": _str("approve, tweak, or reject."),
                        "note": _str("One-line note, e.g. 'sharper hook'. Required for tweak/reject.")},
                       ["draft_id", "feedback_type"]),
}

FOUNDRY_DRAFT_APPROVE = {
    "name": "foundry_draft_approve",
    "description": "Approval is currently disabled — no trusted human review channel exists yet, so this tool always returns an error. Nothing auto-posts.",
    "parameters": _obj({"draft_id": _str("Draft Card id.")}, ["draft_id"]),
}

FOUNDRY_SCORECARD = {
    "name": "foundry_scorecard",
    "description": "Inspector: performance summary for a draft, with a repeat / drop / retry verdict.",
    "parameters": _obj({"draft_id": _str("Draft Card id.")}, ["draft_id"]),
}

FOUNDRY_MONEY_SUMMARY = {
    "name": "foundry_money_summary",
    "description": "Paymaster: profit summary (costs, revenue, profit in cents) for a draft, client, or period. Tax figures are tracking estimates only.",
    "parameters": _obj({"draft_id": _str("Draft Card id (optional)."),
                        "client": _str("Client name, default 'self'.")}, []),
}

# NOTE (2026-11-06): foundry_dashboard_render was dropped — it imported
# scripts/render_dashboard, which is not inside an installed plugin folder,
# so the tool failed in a live install. Static rendering for demos lives in
# scripts/render_dashboard.py (make demo); the live dashboards are served
# by foundry/dashboard/plugin_api.py.
ALL_SCHEMAS = [FOUNDRY_START, FOUNDRY_LEDGER_LIST, FOUNDRY_LEDGER_GET, FOUNDRY_DRAFT_CREATE,
               FOUNDRY_DRAFT_FEEDBACK, FOUNDRY_DRAFT_APPROVE, FOUNDRY_SCORECARD,
               FOUNDRY_MONEY_SUMMARY]
