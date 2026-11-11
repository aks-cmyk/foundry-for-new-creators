// Foundry — Desktop GUI half (Hermes Desktop, @hermes/plugin-sdk).
//
// One package, both SDKs: this file is the Desktop half of the same
// agent package (see the Desktop Plugin SDK page, "One package, both
// SDKs"). When the package lands in ~/.hermes/plugins/foundry/, Electron
// copies desktop/ into $HERMES_HOME/desktop-plugins/foundry/ beside a
// .hermes-package.json marker and hot-reloads it.
//
// It mirrors the web-dashboard board (foundry/dashboard/dist/index.js):
// Proofing Table / Brand / Inspector / Paymaster over the SAME backend,
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
  const [notes, setNotes] = useState({}) // per-draft one-line note
  const [busy, setBusy] = useState(false)
  const [brandForm, setBrandForm] = useState(null) // null = viewing, values = editing
  const [brandBusy, setBrandBusy] = useState(false)

  function load() {
    return rest('/cards').then(function (d) {
      setCards((d && d.cards) || [])
      setError(null)
    }).catch(function (e) {
      setError('Could not load the Foundry ledger: ' + (e && e.message ? e.message : e))
    })
  }
  useEffect(function () { load() }, [])

  function draftNote(draftId) { return notes[draftId] === undefined ? 'sharper hook' : notes[draftId] }
  function setDraftNote(draftId, value) {
    var next = {}; next[draftId] = value
    setNotes(Object.assign({}, notes, next))
  }
  function sendFeedback(draftId, type) {
    if (!draftId || busy) { return }
    var note = draftNote(draftId)
    if (type === 'reject' && !note.trim()) {
      setError('Reject needs a reason — type one in the note box first.')
      return
    }
    setBusy(true)
    setError(null)
    rest('/feedback', {
      method: 'POST',
      body: { draft_id: draftId, feedback_type: type, note: type === 'approve' ? '' : note }
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
  var identities = cards.filter(function (c) { return c.kind === 'identity' })
  var identity = identities[identities.length - 1]

  // Brand tab — view + edit. Lists are comma-separated in the form.
  var BRAND_FIELDS = [
    ['who_you_help', 'Who you help', 'input'],
    ['audience', 'Audience', 'input'],
    ['mission', 'Mission', 'input'],
    ['story', 'Story', 'textarea'],
    ['pillars', 'Pillars (comma-separated)', 'input'],
    ['beliefs', 'Beliefs (comma-separated)', 'input'],
    ['against', 'Never say', 'input'],
    ['voice_examples', 'Voice examples (one per line)', 'textarea'],
    ['voice_donts', 'Never use (comma-separated)', 'input']
  ]
  var BRAND_LIST_KEYS = ['pillars', 'beliefs', 'voice_examples', 'voice_donts']
  function splitList(s) { return (s || '').split(/[\n,]+/).map(function (x) { return x.trim() }).filter(Boolean) }
  function joinList(v) { return (v || []).join(', ') }
  function startBrandEdit() {
    if (!identity) { return }
    var p = identity.payload, values = {}
    BRAND_FIELDS.forEach(function (f) {
      values[f[0]] = Array.isArray(p[f[0]]) ? p[f[0]].join('\n') : (p[f[0]] || '')
    })
    setBrandForm(values)
  }
  function saveBrand() {
    if (!brandForm || brandBusy || !identity) { return }
    var payload = {}
    BRAND_FIELDS.forEach(function (f) {
      var key = f[0]
      payload[key] = BRAND_LIST_KEYS.indexOf(key) !== -1 ? splitList(brandForm[key]) : brandForm[key]
    })
    setBrandBusy(true)
    setError(null)
    rest('/brand', {
      method: 'POST',
      body: { identity_id: identity.id, payload: payload }
    }).then(function (d) {
      if (!d || d.ok === false) { throw new Error((d && d.error) || 'brand save failed') }
      setBrandForm(null)
      return load()
    }).catch(function (e) {
      setError('Brand save failed: ' + (e && e.message ? e.message : e))
    }).then(function () { setBrandBusy(false) })
  }
  function setBrandField(key, value) {
    var next = {}; next[key] = value
    setBrandForm(Object.assign({}, brandForm, next))
  }

  var body
  if (tab === 'proofing') {
    // All drafts, newest first — a vertical card stack; each card has
    // its own note box and buttons.
    var ordered = drafts.slice().reverse()
    body = ordered.length ? jsxs('div', { children: ordered.map(function (d) {
      return jsxs('div', { key: d.id, style: cardStyle, children: [
        jsx('h3', { children: d.title + ' — v' + d.version + ' (' + d.status + ')' }),
        jsx('pre', { style: { whiteSpace: 'pre-wrap' }, children: d.payload.text }),
        jsx('p', { style: mutedStyle, children: 'Evidence: ' + (d.payload.evidence_ids || []).join(', ') }),
        jsx('input', {
          type: 'text', value: draftNote(d.id), 'aria-label': 'One-line note for Smith',
          placeholder: 'One-line note, e.g. sharper hook',
          style: { width: '100%', padding: '6px', marginBottom: '8px' },
          onChange: function (e) { setDraftNote(d.id, e.target.value) }
        }),
        jsxs('div', { children: [
          // Approval is disabled (2026-11-11): no trusted human review
          // channel exists yet — the button stays inert, not an error.
          jsx('button', { style: btnStyle, disabled: true, title: 'Approval unavailable — trusted human review not wired', children: 'Approval unavailable' }),
          jsx('button', { style: btnStyle, disabled: busy, onClick: function () { sendFeedback(d.id, 'tweak') }, children: 'Tweak' }),
          jsx('button', { style: btnStyle, disabled: busy, onClick: function () { sendFeedback(d.id, 'reject') }, children: 'Reject' })
        ] }),
        jsx('p', { style: mutedStyle, children: 'Approval is disabled — no trusted human review channel yet. Nothing auto-posts. Tweak sends the note to Smith and returns a new draft version — the original is never changed; feedback is recorded as unverified.' })
      ] })
    }) }) : jsx('p', { children: 'No drafts yet.' })
  } else if (tab === 'brand') {
    if (!identity) {
      body = jsx('p', { children: "No brand yet. Say 'foundry start' in chat — a short interview sets up your brand." })
    } else if (brandForm) {
      body = jsxs('div', { style: cardStyle, children: [
        jsx('h3', { children: 'Edit brand' }),
        jsxs('div', { children: BRAND_FIELDS.map(function (f) {
          var key = f[0], label = f[1], kind = f[2]
          return jsxs('div', { key: key, style: { marginBottom: '10px' }, children: [
            jsx('label', { style: { display: 'block', fontSize: '0.85em', marginBottom: '4px' }, children: label }),
            kind === 'textarea'
              ? jsx('textarea', { value: brandForm[key], rows: 3, style: { width: '100%', padding: '6px' }, onChange: function (e) { setBrandField(key, e.target.value) } })
              : jsx('input', { type: 'text', value: brandForm[key], style: { width: '100%', padding: '6px' }, onChange: function (e) { setBrandField(key, e.target.value) } })
          ] })
        }) }),
        jsxs('div', { children: [
          jsx('button', { style: btnStyle, disabled: brandBusy, onClick: saveBrand, children: brandBusy ? 'Saving…' : 'Save brand' }),
          jsx('button', { style: btnStyle, onClick: function () { setBrandForm(null) }, children: 'Cancel' })
        ] })
      ] })
    } else {
      var p = identity.payload
      var rows = [
        ['Who you help', p.who_you_help],
        ['Audience', p.audience],
        ['Mission', p.mission],
        ['Story', p.story],
        ['Pillars', joinList(p.pillars)],
        ['Beliefs', joinList(p.beliefs)],
        ['Never say', p.against],
        ['Voice examples', (p.voice_examples || []).join(' / ')],
        ['Never use', joinList(p.voice_donts)]
      ]
      body = jsxs('div', { style: cardStyle, children: [
        jsx('h3', { children: 'Brand — v' + identity.version + ' (' + (p.origin || 'demo') + ')' }),
        (p.origin === 'seed' || !p.origin) ? jsx('p', { style: mutedStyle, children: "This is Foundry's demo brand. Say 'foundry start' in chat to set up your own — or edit it here." }) : null,
        jsxs('div', { children: rows.map(function (r) {
          return jsx('p', { key: r[0], children: [jsx('strong', { key: 'l', children: r[0] + ': ' }), r[1] || '—'] })
        }) }),
        jsx('button', { style: btnStyle, onClick: startBrandEdit, children: 'Edit brand' })
      ] })
    }
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
      jsx('button', { style: tabBtnStyle, onClick: function () { setTab('proofing'); setBrandForm(null) }, children: 'Proofing Table' }),
      jsx('button', { style: tabBtnStyle, onClick: function () { setTab('brand'); setBrandForm(null) }, children: 'Brand' }),
      jsx('button', { style: tabBtnStyle, onClick: function () { setTab('score'); setBrandForm(null) }, children: 'Inspector' }),
      jsx('button', { style: tabBtnStyle, onClick: function () { setTab('money'); setBrandForm(null) }, children: 'Paymaster' })
    ] }),
    body
  ] })
}

export default {
  id: 'foundry',
  name: 'Foundry',
  description: 'Creator plugin: Proofing Table, Brand tab, Inspector and Paymaster over one shared ledger. Say "foundry start" to set up your brand.',
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
          keywords: ['foundry', 'proofing', 'drafts', 'brand', 'onboarding'],
          run: function () { host.navigate('/foundry') }
        }
      }
    ])
  }
}
