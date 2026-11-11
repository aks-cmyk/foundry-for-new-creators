# Foundry creator skill

Run one Foundry cycle for a creator, in order. Use the Foundry tools;
never invent facts, numbers, quotes or sources.

1. **Cartographer (interview).** Say "foundry start" → begin. Then
   ask ONE question at a time, in order — never ask for all the
   answers up front. Save as you go: as soon as `who_you_help` is
   answered, call `foundry_start` complete with everything known so
   far (only `who_you_help` is required). That writes a real Identity
   Card immediately, so if the turn ends, nothing is lost. Keep
   asking the rest one at a time; each complete call writes a NEW
   version (never overwrite) and must include `who_you_help` plus
   every answer given so far — carry the earlier answers forward.
   If an Identity Card already exists, read it first and ask only
   for what is missing; the user can resume anytime by saying
   "foundry start" again. Never treat the seeded demo identity
   (origin `"seed"` — the "three small tools" story) as the user's
   voice: if the ledger only has the demo card, the interview must
   run before any drafting (the draft guard refuses the demo brand).
   Every seeded demo card is titled `Demo: …` and carries origin
   `"seed"` — treat all of them as sample data, never as the user's
   voice, numbers, or sources.
2. **Lookout (research).** Find sourced evidence in the niche.
   An Evidence Card needs at least 2 sources with links. Drop any
   claim you cannot confirm with a link.
3. **Scribe (draft).** Draft only from cited Evidence Cards, in the
   Identity Card's voice. One platform, one format (MVP: X thread).
4. **Proofing Table (human).** Show the draft on the dashboard.
   The human tweaks (one-line note) or rejects (reason) — approval
   is currently disabled, so never promise an approval step.
   A tweak writes a Revision Card; Scribe returns a new version.
   Nothing posts until a human approves it — and since approval is
   disabled, nothing posts from this flow at all right now.
5. **Scorekeeper.** After posting, record a Performance Card:
   views, likes, reposts, replies, saves, verdict repeat / drop /
   retry-differently, with one-line reason.
6. **Bursar.** Record a Money Card for the same draft: costs,
   revenue, profit (integer cents). Track partnerships
   (pitched → terms → delivered → paid) and tax as tracking only —
   no advice, no filing.

Rules: Scribe cannot draft without an Evidence Card. Feedback is a
Revision Card, not a chat message. Performance and money write back
to the ledger so the next cycle learns.
