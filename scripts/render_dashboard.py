"""Render the Foundry dashboard as a static, self-contained HTML file.

Reads the seeded ledger (data/foundry.db, seeding first if missing)
and writes dashboard/index.html with three tabs: Proofing Table /
Scorekeeper / Bursar. Feedback (Approve / Tweak / Reject) works
client-side: Tweak sharpens the hook and shows v2, mirroring the
Scribe revision rule in foundry/bots.py. This is a demo artifact —
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
    latest = drafts[-1] if drafts else None
    perf = by_kind.get("performance", [])
    money = by_kind.get("money", [])
    identity = by_kind.get("identity", [{}])[0]
    evidence = by_kind.get("evidence", [{}])[0]

    def card_html(c):
        return f"<div class='card'><b>{html.escape(c['title'])}</b> <span class='muted'>v{c['version']} · {html.escape(c['status'])} · by {html.escape(c['created_by'])}</span></div>"

    proof = ""
    if latest:
        p = latest["payload"]
        sources = "".join(
            f"<li><a href='{html.escape(s['url'])}'>{html.escape(s['title'])}</a></li>"
            for s in evidence.get("payload", {}).get("sources", []))
        proof = f"""
        <div class='card'><h3>{html.escape(latest['title'])} — v{latest['version']} ({html.escape(latest['status'])})</h3>
        <pre id='draft-text'>{html.escape(p['text'])}</pre>
        <p class='muted'>Evidence: {', '.join(p.get('evidence_ids', []))} · cost so far {_money(p.get('cost_cents', 0))}</p>
        <p><b>Sources</b></p><ul>{sources}</ul>
        <button onclick="feedback('approve')">Approve</button>
        <button onclick="feedback('tweak')">Tweak — sharper hook</button>
        <button onclick="feedback('reject')">Reject</button>
        <p id='feedback-msg' class='muted'></p>
        <p class='muted'>Version history: v1 → v2 (Revision Card: tweak — sharper hook). Originals are never mutated.</p></div>"""
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
    identity_html = "".join(card_html(c) for c in by_kind.get("identity", []))

    doc = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<title>Foundry — Proofing Table / Scorekeeper / Bursar</title>
<style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;background:#0f0f0f;color:#eee}}
.card{{border:1px solid #444;border-radius:8px;padding:12px;margin:12px 0;background:#161616}}
.muted{{color:#999;font-size:.85em}}button{{margin-right:8px;padding:6px 12px;cursor:pointer}}
pre{{white-space:pre-wrap}}.tab{{display:none}}.tab.active{{display:block}}
.tabbtn{{background:#222;color:#eee;border:1px solid #555}}</style></head><body>
<h1>Foundry — five bots, one ledger</h1>
<p class='muted'>Seeded demo data — performance numbers are estimated, not real metrics. Human approval on anything public; nothing auto-posts.</p>
<p><button class='tabbtn' onclick="show('proofing')">Proofing Table</button>
<button class='tabbtn' onclick="show('score')">Scorekeeper</button>
<button class='tabbtn' onclick="show('money')">Bursar</button></p>
<div id='proofing' class='tab active'><h2>Proofing Table</h2>{identity_html}{proof}</div>
<div id='score' class='tab'><h2>Scorekeeper</h2>{score or '<p>No performance cards yet.</p>'}</div>
<div id='money' class='tab'><h2>Bursar</h2>{bursar or '<p>No money cards yet.</p>'}
<p class='muted'>Tax figures are tracking estimates only — no advice, no filing.</p></div>
<script>
function show(id){{document.querySelectorAll('.tab').forEach(function(t){{t.classList.remove('active')}});document.getElementById(id).classList.add('active');}}
function feedback(kind){{
  var msg=document.getElementById('feedback-msg'); var el=document.getElementById('draft-text');
  if(kind==='approve'){{msg.textContent='Approved — Revision Card recorded. Nothing posts until a human approves it (already done here).';}}
  else if(kind==='tweak'){{
    var t=el.textContent; var first=t.split('\\n\\n')[0];
    var sharp=first.replace(/\\.$/,'')+': here is the fix, in one thread.';
    el.textContent=t.replace(first, sharp);
    msg.textContent='Revision Card recorded (tweak — sharper hook). Scribe returned v2 — see the sharpened hook above.';}}
  else {{msg.textContent='Rejected — reason required. Revision Card recorded; Scribe will not re-draft without a new note.';}}
}}
</script></body></html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    print(f"Rendered {render()}")
