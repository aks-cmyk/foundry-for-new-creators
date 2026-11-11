"""Render the Foundry dashboard as a static, self-contained HTML file.

Reads the seeded ledger (data/foundry.db, seeding first if missing)
and writes dashboard/index.html with four tabs: Proofing Table /
Brand / Inspector / Paymaster. The Proofing Table lists all drafts
newest-first, mirroring the live dashboard; the Brand tab shows the
Identity Card. Feedback (Tweak / Reject) works
client-side: Tweak sharpens the hook and shows v2, mirroring the
Smith revision rule in foundry/bots.py. Approve is disabled — no
trusted human review channel exists yet (see
docs/APPROVAL_CHECKPOINT.md). This is a demo artifact —
the real dashboard extension is foundry/dashboard/ (see ARCHITECTURE.md).
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry import ledger  # noqa: E402

DB = ROOT / "foundry" / "data" / "foundry.db"
SEED = ROOT / "foundry" / "data" / "seed.json"
OUT = ROOT / "dashboard" / "index.html"


def _money(cents):
    return f"${cents / 100:.2f}"


def render() -> Path:
    if not DB.exists():
        conn = ledger.connect(DB)
        ledger.load_seed(conn, SEED)
    conn = ledger.connect(DB)
    cards = ledger.list_cards(conn)
    by_kind = {}
    for c in cards:
        by_kind.setdefault(c["kind"], []).append(c)
    drafts = by_kind.get("draft", [])
    perf = by_kind.get("performance", [])
    money = by_kind.get("money", [])
    evidence = by_kind.get("evidence", [{}])[0]

    def draft_html(d):
        p = d["payload"]
        sources = "".join(
            f"<li><a href='{html.escape(s['url'])}'>{html.escape(s['title'])}</a></li>"
            for s in evidence.get("payload", {}).get("sources", []))
        sup = (f" · supersedes {html.escape(d['supersedes_id'])}"
               if d.get("supersedes_id") else "")
        return f"""
        <div class='card'><h3>{html.escape(d['title'])} — v{d['version']} ({html.escape(d['status'])}){sup}</h3>
        <pre id='draft-text-{html.escape(d['id'])}'>{html.escape(p['text'])}</pre>
        <p class='muted'>Evidence: {', '.join(p.get('evidence_ids', []))} · cost so far {_money(p.get('cost_cents', 0))}</p>
        <p><b>Sources</b></p><ul>{sources}</ul>
        <button disabled title="Approval unavailable — trusted human review not wired">Approval unavailable — trusted human review not wired</button>
        <button onclick="feedback('tweak', '{html.escape(d['id'])}')">Tweak — sharper hook</button>
        <button onclick="feedback('reject', '{html.escape(d['id'])}')">Reject</button>
        <p id='feedback-msg-{html.escape(d['id'])}' class='muted'></p>
        <p class='muted'>Originals are never mutated — feedback returns a new version.</p></div>"""

    # All drafts, newest-first (reversed ledger order), like the live board.
    proof = "".join(draft_html(d) for d in reversed(drafts))

    # Brand tab: the Identity Card, with the demo banner when the brand
    # is seeded demo data (origin "seed" or missing) — same rule as the
    # live dashboard.
    ident = by_kind.get("identity", [{}])[0]
    ip = ident.get("payload", {}) or {}
    is_demo = ip.get("origin") not in ("interview", "dashboard-edit")

    def _field(label, value):
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        return f"<p><b>{label}:</b> {html.escape(str(value))}</p>" if value else ""

    brand_html = (
        ("<p><b>This is Foundry's demo brand.</b> Say 'foundry start' in chat "
         "to set up your own — or edit it here.</p>" if is_demo else "")
        + f"<p class='muted'>Identity Card v{ident.get('version', '?')} · "
          f"{'demo' if is_demo else 'your brand'}</p>"
        + _field("Who you help", ip.get("who_you_help"))
        + _field("Audience", ip.get("audience"))
        + _field("Story", ip.get("story"))
        + _field("Topics", ip.get("pillars"))
        + _field("Beliefs", ip.get("beliefs"))
        + _field("Never", ip.get("against"))
        + _field("Sounds like me", ip.get("voice_examples"))
        + _field("Never say", ip.get("voice_donts"))
        + _field("Mission", ip.get("mission"))
    )
    score = "".join(
        f"<div class='card'><b>{html.escape(c['payload'].get('draft_id',''))}</b> — "
        f"{c['payload'].get('views')} views · {c['payload'].get('reposts')} reposts · "
        f"{c['payload'].get('replies')} replies · verdict: <b>{html.escape(c['payload'].get('verdict',''))}</b>"
        f"<p class='muted'>{html.escape(c['payload'].get('verdict_reason',''))} (seeded, estimated — not real metrics)</p></div>"
        for c in perf)
    bursar = "".join(
        (f"<div class='card'><b>{html.escape(c['title'])}</b> — cost {_money(c['payload'].get('cost_cents', 0))} · "
         f"revenue {_money(c['payload'].get('revenue_cents', 0))} · profit {_money(c['payload'].get('profit_cents', 0))}</div>"
         if c['payload'].get('record_type') not in ('partnership', 'tax') else
         f"<div class='card'><b>{html.escape(c['title'])}</b> <span class='muted'>{html.escape(str(c['payload']))}</span></div>")
        for c in money)

    doc = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<title>Foundry — Proofing Table / Brand / Inspector / Paymaster</title>
<style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;background:#0f0f0f;color:#eee}}
.card{{border:1px solid #444;border-radius:8px;padding:12px;margin:12px 0;background:#161616}}
.muted{{color:#999;font-size:.85em}}button{{margin-right:8px;padding:6px 12px;cursor:pointer}}
pre{{white-space:pre-wrap}}.tab{{display:none}}.tab.active{{display:block}}
.tabbtn{{background:#222;color:#eee;border:1px solid #555}}</style></head><body>
<h1>Foundry — five bots, one ledger</h1>
<p class='muted'>Seeded demo data — performance numbers are estimated, not real metrics. Approval is disabled — no trusted human review channel yet; nothing auto-posts.</p>
<p><button class='tabbtn' onclick="show('proofing')">Proofing Table</button>
<button class='tabbtn' onclick="show('brand')">Brand</button>
<button class='tabbtn' onclick="show('score')">Inspector</button>
<button class='tabbtn' onclick="show('money')">Paymaster</button></p>
<div id='proofing' class='tab active'><h2>Proofing Table</h2>{proof or '<p>No drafts yet.</p>'}</div>
<div id='brand' class='tab'><h2>Brand</h2>{brand_html or '<p>No brand yet. Say ‘foundry start’ in chat to set up your own.</p>'}</div>
<div id='score' class='tab'><h2>Inspector</h2>{score or '<p>No performance cards yet.</p>'}</div>
<div id='money' class='tab'><h2>Paymaster</h2>{bursar or '<p>No money cards yet.</p>'}
<p class='muted'>Tax figures are tracking estimates only — no advice, no filing.</p></div>
<script>
function show(id){{document.querySelectorAll('.tab').forEach(function(t){{t.classList.remove('active')}});document.getElementById(id).classList.add('active');}}
function feedback(kind, id){{
  var msg=document.getElementById('feedback-msg-'+id); var el=document.getElementById('draft-text-'+id);
  if(kind==='approve'){{msg.textContent='Approval unavailable — trusted human review not wired. Nothing auto-posts.';}}
  else if(kind==='tweak'){{
    var t=el.textContent; var first=t.split('\\n\\n')[0];
    var sharp=first.replace(/\\.$/,'')+': here is the fix, in one thread.';
    el.textContent=t.replace(first, sharp);
    msg.textContent='Revision Card recorded (tweak — sharper hook). Smith returned v2 — see the sharpened hook above.';}}
  else {{msg.textContent='Rejected — reason required. Revision Card recorded; Smith will not re-draft without a new note.';}}
}}
</script></body></html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    print(f"Rendered {render()}")
