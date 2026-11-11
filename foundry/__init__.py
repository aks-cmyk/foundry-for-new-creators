"""Foundry plugin — registration.

Wires schemas to handlers via ctx.register_tool(), and registers the
bundled skill via ctx.register_skill(). Follows the official guide:
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

VERIFIED 2026-11-06 against installed Hermes v0.23.0
(hermes_cli/plugins.py:463): PluginContext.register_tool() requires
``register_tool(name, toolset, schema, handler)`` — the ``toolset``
argument is mandatory (bundled google_meet plugin uses
``toolset="google_meet"``). A call without ``toolset`` raises TypeError
and registration fails entirely — this is what
``hermes plugins doctor`` caught (validate's stub accepts anything).
"""
import logging
from pathlib import Path

from . import schemas, tools

logger = logging.getLogger(__name__)


def register(ctx):
    # Bind ctx so tool handlers can reach the host LLM (ctx.llm) for
    # live Smith revisions; unbound outside Hermes, Smith falls back
    # to the rule-based rewrite.
    tools.bind_ctx(ctx)
    for schema in schemas.ALL_SCHEMAS:
        handler = tools.HANDLERS[schema["name"]]
        ctx.register_tool(name=schema["name"], toolset="foundry",
                          schema=schema, handler=handler)
    skill_md = Path(__file__).parent / "skills" / "foundry-creator" / "SKILL.md"
    if skill_md.exists():
        try:
            ctx.register_skill("foundry-creator", skill_md)
        except Exception as exc:  # skill registration must not break loading
            logger.warning("Foundry: could not register skill: %s", exc)
    logger.info("Foundry: registered %d tools", len(schemas.ALL_SCHEMAS))
