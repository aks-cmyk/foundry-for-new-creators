/* Foundry dashboard UI — IIFE, React from the Hermes SDK only.
 * Live-load status: first live run (Mac Studio, Nov 10, 2026) loaded a
 * blank page — root cause: the host's Tabs is a render-prop component,
 * children(active, setActive); elements-as-children threw on first
 * render and unmounted the app. Fixed 2026-11-10 (render-prop form
 * below); live re-test Nov 10, 11:15 PM: renders, three tabs show.
 * Redesign 2026-11-11 (Amit's call): Proofing Table lists ALL drafts
 * as a vertical card stack, newest first — a phone-like feed in a
 * narrow centered column; each card has its own laid-out buttons.
 * Component names are copied from the official dashboard guide.
 * Fallback: if /api/plugins/foundry/cards is unreachable, the page
 * shows the seeded demo cards embedded by render_dashboard.py.
 */
(function () {
  "use strict";
  var SDK = window.__HERMES_PLUGIN_SDK__;
  if (!SDK) { return; } // loaded outside the dashboard: static render handles it
  var React = SDK.React;
  var useState = SDK.hooks.useState;
  var useEffect = SDK.hooks.useEffect;
  var Card = SDK.components.Card;
  var CardHeader = SDK.components.CardHeader;
  var CardTitle = SDK.components.CardTitle;
  var CardContent = SDK.components.CardContent;
  var Button = SDK.components.Button;
  var Badge = SDK.components.Badge;
  var Tabs = SDK.components.Tabs;
  var TabsList = SDK.components.TabsList;
  var TabsTrigger = SDK.components.TabsTrigger;

  function money(cents) { return "$" + (cents / 100).toFixed(2); }

  function FoundryPage() {
    var state = useState({ tab: "proofing", cards: [], error: null });
    var tab = state[0].tab, cards = state[0].cards, error = state[0].error;
    var setState = state[1];
    useEffect(function () {
      SDK.fetchJSON("/api/plugins/foundry/cards")
        .then(function (d) { setState({ tab: "proofing", cards: d.cards || [], error: null }); })
        .catch(function (e) {
          var seed = window.__FOUNDRY_SEED__ || [];
          setState({ tab: "proofing", cards: seed, error: "Live API unreachable — showing seeded demo data." });
        });
    }, []);
    var drafts = cards.filter(function (c) { return c.kind === "draft"; });
    var perf = cards.filter(function (c) { return c.kind === "performance"; });
    var moneyCards = cards.filter(function (c) { return c.kind === "money"; });
    function setTab(t) { setState({ tab: t, cards: cards, error: error }); }
    // Human feedback — POST /feedback writes a real Revision Card (and,
    // for tweaks, a revised draft). Fixed 2026-11-06: these were
    // alert(...) placeholders. Tweak asks for a one-line note via
    // prompt(); Reject requires a reason the same way.
    // Each draft card sends its own feedback (draftId), so every version
    // in the stack is reviewable, not just the latest.
    function sendFeedback(draftId, type, note) {
      if (!draftId) { return; }
      SDK.fetchJSON("/api/plugins/foundry/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ draft_id: draftId, feedback_type: type, note: note || "" })
      }).then(function (d) {
        if (!d || d.ok === false) { throw new Error((d && d.error) || "feedback failed"); }
        return SDK.fetchJSON("/api/plugins/foundry/cards");
      }).then(function (d) {
        setState({ tab: tab, cards: d.cards || [], error: null });
      }).catch(function (e) {
        setState({ tab: tab, cards: cards, error: "Feedback failed: " + (e.message || e) });
      });
    }
    // Approval is disabled (2026-11-11): no trusted human review
    // channel exists yet, so there is no approve action to send —
    // the button below stays inert instead of erroring. Its visible
    // label is short ("Approval unavailable"); the full reason stays
    // in the title tooltip: "Approval unavailable — trusted human
    // review not wired".
    function doTweak(draftId) {
      var note = window.prompt("Tweak — one-line note for Scribe:", "sharper hook");
      if (note === null) { return; } // cancelled
      sendFeedback(draftId, "tweak", note);
    }
    function doReject(draftId) {
      var note = window.prompt("Reject — reason required:", "");
      if (note === null || !note.trim()) { return; }
      sendFeedback(draftId, "reject", note);
    }
    // One draft card: title/version/status, text (wraps in the narrow
    // column), evidence, and its own buttons in a laid-out row.
    function draftCard(d) {
      return React.createElement(Card, { key: d.id },
        React.createElement(CardHeader, null,
          React.createElement(CardTitle, null, d.title + " — v" + d.version + " (" + d.status + ")")),
        React.createElement(CardContent, null,
          React.createElement("pre", { style: { whiteSpace: "pre-wrap", wordBreak: "break-word" } }, d.payload.text),
          React.createElement("p", { className: "muted" }, "Evidence: " + (d.payload.evidence_ids || []).join(", ")),
          React.createElement("div", { style: { display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "12px" } },
            React.createElement(Button, { disabled: true, title: "Approval unavailable — trusted human review not wired" }, "Approval unavailable"),
            React.createElement(Button, { onClick: function () { doTweak(d.id); } }, "Tweak"),
            React.createElement(Button, { onClick: function () { doReject(d.id); } }, "Reject")
          )));
    }
    // Vertical stack, newest first — a phone-like feed.
    var stackStyle = { display: "flex", flexDirection: "column", gap: "12px" };
    var body;
    if (tab === "proofing") {
      // All drafts, newest on top (oldest first in the ledger, reversed).
      var ordered = drafts.slice().reverse();
      body = ordered.length ? React.createElement("div", { style: stackStyle },
        ordered.map(draftCard)) : React.createElement("p", null, "No drafts yet.");
    } else if (tab === "score") {
      body = React.createElement("div", { style: stackStyle }, perf.map(function (p) {
        return React.createElement(Card, { key: p.id },
          React.createElement(CardContent, null,
            React.createElement("p", null, p.payload.draft_id + ": " + p.payload.views + " views, " + p.payload.reposts + " reposts"),
            React.createElement(Badge, null, p.payload.verdict),
            React.createElement("p", { className: "muted" }, p.payload.verdict_reason + " (seeded, estimated)")));
      }));
    } else {
      body = React.createElement("div", { style: stackStyle }, moneyCards.map(function (m) {
        return React.createElement(Card, { key: m.id },
          React.createElement(CardContent, null,
            React.createElement("p", null, m.title + ": cost " + money(m.payload.cost_cents || 0) +
              " · revenue " + money(m.payload.revenue_cents || 0) +
              " · profit " + money(m.payload.profit_cents || 0))));
      }));
    }
    // The host's Tabs is a render-prop component: children(active, setActive).
    // Passing elements as children throws "children is not a function" on
    // first render and unmounts the whole dashboard (blank page, empty
    // #root). Fixed 2026-11-10: render-prop form; triggers get active + value.
    // (The official dashboard guide lists the component names but shows no
    // Tabs usage example — the Radix-style shape was assumed, wrongly.)
    // Phone-like feed: narrow centered column, cards stacked vertically.
    return React.createElement("div", { className: "foundry", style: { maxWidth: "560px", margin: "0 auto", padding: "0 4px" } },
      React.createElement("h2", null, "Foundry — five bots, one ledger"),
      error ? React.createElement("p", { className: "muted" }, error) : null,
      React.createElement(Tabs, { defaultValue: "proofing" }, function (active, setActive) {
        return React.createElement("div", null,
          React.createElement(TabsList, null,
            React.createElement(TabsTrigger, { active: tab === "proofing", value: "proofing", onClick: function () { setTab("proofing"); } }, "Proofing Table"),
            React.createElement(TabsTrigger, { active: tab === "score", value: "score", onClick: function () { setTab("score"); } }, "Scorekeeper"),
            React.createElement(TabsTrigger, { active: tab === "money", value: "money", onClick: function () { setTab("money"); } }, "Bursar")),
          body);
      }));
  }
  window.__HERMES_PLUGINS__.register("foundry", FoundryPage);
})();
