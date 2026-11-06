"""Foundry plugin — registration.

Wires schemas to handlers via ctx.register_tool(), and registers the
bundled skill via ctx.register_skill(). Follows the official guide:
https://hermes-agent.nousresearch.com/docs/developer-guide/plugins

UNVERIFIED: register_tool / register_skill kwarg shapes are as shown in
the guide's examples; they have not been executed against a live Hermes.
"""
import logging
from pathlib import Path

from . import schemas, tools

logger = logging.getLogger(__name__)


def register(ctx):
    for schema in schemas.ALL_SCHEMAS:
        handler = tools.HANDLERS[schema["name"]]
        try:
            ctx.register_tool(name=schema["name"], schema=schema, handler=handler)
        except TypeError:
            # Older/alternate ctx signature: register_tool(schema, handler)
            ctx.register_tool(schema, handler)
    skill_md = Path(__file__).parent / "skills" / "foundry-creator" / "SKILL.md"
    if skill_md.exists():
        try:
            ctx.register_skill("foundry-creator", skill_md)
        except Exception as exc:  # skill registration must not break loading
            logger.warning("Foundry: could not register skill: %s", exc)
    logger.info("Foundry: registered %d tools", len(schemas.ALL_SCHEMAS))
