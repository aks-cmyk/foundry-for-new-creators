/* Foundry dashboard UI — IIFE, React from the Hermes SDK only.
 * Live-load status: the first live run (Mac Studio, Nov 10, 2026) loaded a
 * blank page — root cause found in the host source: the host's Tabs is a
 * render-prop component, children(active, setActive); elements-as-children
 * threw on first render and unmounted the app. Fixed 2026-11-10 (render-prop
 * form below). Live re-test still pending.
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
    var latest = drafts[drafts.length - 1];
    function setTab(t) { setState({ tab: t, cards: cards, error: error }); }
    // Human feedback — POST /feedback writes a real Revision Card (and,
    // for tweaks, a revised draft). Fixed 2026-11-06: these were
    // alert(...) placeholders. Tweak asks for a one-line note via
    // prompt(); Reject requires a reason the same way.
    function sendFeedback(type, note) {
      if (!latest) { return; }
      SDK.fetchJSON("/api/plugins/foundry/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ draft_id: latest.id, feedback_type: type, note: note || "" })
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
    // the button below stays inert instead of erroring.
    function doTweak() {
      var note = window.prompt("Tweak — one-line note for Scribe:", "sharper hook");
      if (note === null) { return; } // cancelled
      sendFeedback("tweak", note);
    }
    function doReject() {
      var note = window.prompt("Reject — reason required:", "");
      if (note === null || !note.trim()) { return; }
      sendFeedback("reject", note);
    }
    var body;
    if (tab === "proofing") {
      body = latest ? React.createElement(Card, null,
        React.createElement(CardHeader, null,
          React.createElement(CardTitle, null, latest.title + " — v" + latest.version + " (" + latest.status + ")")),
        React.createElement(CardContent, null,
          React.createElement("pre", null, latest.payload.text),
          React.createElement("p", { className: "muted" }, "Evidence: " + (latest.payload.evidence_ids || []).join(", ")),
          React.createElement(Button, { disabled: true, title: "Approval unavailable — trusted human review not wired" }, "Approval unavailable — trusted human review not wired"),
          React.createElement(Button, { onClick: doTweak }, "Tweak"),
          React.createElement(Button, { onClick: doReject }, "Reject")
        )) : React.createElement("p", null, "No drafts yet.");
    } else if (tab === "score") {
      body = React.createElement("div", null, perf.map(function (p) {
        return React.createElement(Card, { key: p.id },
          React.createElement(CardContent, null,
            React.createElement("p", null, p.payload.draft_id + ": " + p.payload.views + " views, " + p.payload.reposts + " reposts"),
            React.createElement(Badge, null, p.payload.verdict),
            React.createElement("p", { className: "muted" }, p.payload.verdict_reason + " (seeded, estimated)")));
      }));
    } else {
      body = React.createElement("div", null, moneyCards.map(function (m) {
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
    return React.createElement("div", { className: "foundry" },
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
