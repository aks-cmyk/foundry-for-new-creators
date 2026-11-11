// Foundry — Desktop GUI half (Hermes Desktop, @hermes/plugin-sdk).
//
// One package, both SDKs: this file is the Desktop half of the same
// agent package (see the Desktop Plugin SDK page, "One package, both
// SDKs"). When the package lands in ~/.hermes/plugins/foundry/, Electron
// copies desktop/ into $HERMES_HOME/desktop-plugins/foundry/ beside a
// .hermes-package.json marker and hot-reloads it.
//
// It mirrors the web-dashboard board (foundry/dashboard/dist/index.js):
// Proofing Table / Scorekeeper / Bursar over the SAME backend,
// reached via ctx.rest('/cards'), ctx.rest('/summary') and the POST
// /feedback endpoint in foundry/dashboard/plugin_api.py — that backend
// namespace is the one piece shared between the two SDKs.
//
// Verified against: the Desktop Plugin SDK docs (2026-11-06), the
// installed Hermes v0.23.0 source (hermes_cli/desktop_plugin_halves.py:
// desktop/plugin.js is the loadable entrypoint; plugin_validate_desktop.py
// surface lint), and the in-tree disk-plugin precedent
// apps/desktop/src/plugins/radio/plugin.js (imports, jsx/jsxs, ctx.rest
// POST shape { method: 'POST', body: {...} } from the kanban plugin).
//
// UNVERIFIED: never loaded in a live `hermes desktop` — no Desktop app
// runs in this workspace. Ships opt-in (defaultEnabled: false): it
// inventories in Capabilities -> Plugins until the user flips it on,
// and the backend only imports when the plugin is in the
// plugins.enabled allow-list in config.yaml.
//
// Imports are limited to the three allowed specifiers:
// @hermes/plugin-sdk, react, react/jsx-runtime. No JSX (the file loads
// uncompiled), no document access, no eval, no dynamic imports.
import { host, PALETTE_AREA, ROUTES_AREA, SIDEBAR_NAV_AREA } from '@hermes/plugin-sdk'
import { useEffect, useState } from 'react'
import { jsx, jsxs } from 'react/jsx-runtime'

function money(cents) { return '$' + ((cents || 0) / 100).toFixed(2) }

const pad = { padding: '16px', maxWidth: '900px' }
const cardStyle = { border: '1px solid var(--ui-border, #444)', borderRadius: '8px', padding: '12px', margin: '12px 0' }
const mutedStyle = { color: 'var(--ui-text-tertiary, #999)', fontSize: '0.85em' }
const btnStyle = { marginRight: '8px', padding: '6px 12px', cursor: 'pointer' }
const tabBtnStyle = { marginRight: '8px', padding: '6px 12px', cursor: 'pointer' }

function FoundryPage({ rest }) {
  const [tab, setTab] = useState('proofing')
  const [cards, setCards] = useState([])
  const [error, setError] = useState(null)
  const [note, setNote] = useState('sharper hook')
  const [busy, setBusy] = useState(false)

  function load() {
    return rest('/cards').then(function (d) {
      setCards((d && d.cards) || [])
      setError(null)
    }).catch(function (e) {
      setError('Could not load the Foundry ledger: ' + (e && e.message ? e.message : e))
    })
  }
  useEffect(function () { load() }, [])

  function sendFeedback(type) {
    var latest = cards.filter(function (c) { return c.kind === 'draft' }).slice(-1)[0]
    if (!latest || busy) { return }
    if (type === 'reject' && !note.trim()) {
      setError('Reject needs a reason — type one in the note box first.')
      return
    }
    setBusy(true)
    setError(null)
    rest('/feedback', {
      method: 'POST',
      body: { draft_id: latest.id, feedback_type: type, note: type === 'approve' ? '' : note }
    }).then(function (d) {
      if (!d || d.ok === false) { throw new Error((d && d.error) || 'feedback failed') }
      return load()
    }).catch(function (e) {
      setError('Feedback failed: ' + (e && e.message ? e.message : e))
    }).then(function () { setBusy(false) })
  }

  var drafts = cards.filter(function (c) { return c.kind === 'draft' })
  var perf = cards.filter(function (c) { return c.kind === 'performance' })
  var moneyCards = cards.filter(function (c) { return c.kind === 'money' })
  var latest = drafts[drafts.length - 1]

  var body
  if (tab === 'proofing') {
    body = latest ? jsxs('div', { style: cardStyle, children: [
      jsx('h3', { children: latest.title + ' — v' + latest.version + ' (' + latest.status + ')' }),
      jsx('pre', { style: { whiteSpace: 'pre-wrap' }, children: latest.payload.text }),
      jsx('p', { style: mutedStyle, children: 'Evidence: ' + (latest.payload.evidence_ids || []).join(', ') }),
      jsx('input', {
        type: 'text', value: note, 'aria-label': 'One-line note for Scribe',
        placeholder: 'One-line note, e.g. sharper hook',
        style: { width: '100%', padding: '6px', marginBottom: '8px' },
        onChange: function (e) { setNote(e.target.value) }
      }),
      jsxs('div', { children: [
        // Approval is disabled (2026-11-11): no trusted human review
        // channel exists yet — the button stays inert, not an error.
        jsx('button', { style: btnStyle, disabled: true, title: 'Approval unavailable — trusted human review not wired', children: 'Approval unavailable — trusted human review not wired' }),
        jsx('button', { style: btnStyle, disabled: busy, onClick: function () { sendFeedback('tweak') }, children: 'Tweak' }),
        jsx('button', { style: btnStyle, disabled: busy, onClick: function () { sendFeedback('reject') }, children: 'Reject' })
      ] }),
      jsx('p', { style: mutedStyle, children: 'Approval is disabled — no trusted human review channel yet. Nothing auto-posts. Tweak sends the note to Scribe and returns a new draft version — the original is never changed; feedback is recorded as unverified.' })
    ] }) : jsx('p', { children: 'No drafts yet.' })
  } else if (tab === 'score') {
    body = jsxs('div', { children: perf.map(function (p) {
      return jsxs('div', { key: p.id, style: cardStyle, children: [
        jsx('p', { children: p.payload.draft_id + ': ' + p.payload.views + ' views, ' + p.payload.reposts + ' reposts — ' + p.payload.verdict }),
        jsx('p', { style: mutedStyle, children: p.payload.verdict_reason + ' (seeded, estimated)' })
      ] })
    }) })
  } else {
    body = jsxs('div', { children: moneyCards.map(function (m) {
      return jsx('div', { key: m.id, style: cardStyle, children:
        m.title + ': cost ' + money(m.payload.cost_cents) +
        ' · revenue ' + money(m.payload.revenue_cents) +
        ' · profit ' + money(m.payload.profit_cents) })
    }) })
  }

  return jsxs('div', { style: pad, children: [
    jsx('h2', { children: 'Foundry — five bots, one ledger' }),
    error ? jsx('p', { style: { color: '#ff6b6b' }, children: error }) : null,
    jsxs('div', { children: [
      jsx('button', { style: tabBtnStyle, onClick: function () { setTab('proofing') }, children: 'Proofing Table' }),
      jsx('button', { style: tabBtnStyle, onClick: function () { setTab('score') }, children: 'Scorekeeper' }),
      jsx('button', { style: tabBtnStyle, onClick: function () { setTab('money') }, children: 'Bursar' })
    ] }),
    body
  ] })
}

export default {
  id: 'foundry',
  name: 'Foundry',
  description: 'Creator plugin: Proofing Table, Scorekeeper and Bursar over one shared ledger.',
  defaultEnabled: false,
  register(ctx) {
    var rest = ctx.rest
    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/foundry' },
        render: function () { return jsx(FoundryPage, { rest: rest }) }
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        data: { path: '/foundry', label: 'Foundry', codicon: 'project' }
      },
      {
        id: 'open',
        area: PALETTE_AREA,
        data: {
          id: 'foundry.open',
          label: 'Open Foundry',
          keywords: ['foundry', 'proofing', 'drafts'],
          run: function () { host.navigate('/foundry') }
        }
      }
    ])
  }
}
