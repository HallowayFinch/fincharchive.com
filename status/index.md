---
layout: default
title: System Status
permalink: /status/
---

<section class="container">
  <header class="page-header">
    <h1 class="page-title">System Status</h1>
    <p class="page-lead">Build, imports, and archive inventory.</p>
  </header>

  {%- assign logs  = site.logs | sort: "date" | reverse -%}
  {%- assign notes = site.field-notes | sort: "date" | reverse -%}

  {%- assign art_count = 0 -%}
  {%- for f in site.static_files -%}
    {%- if f.path contains '/artifacts/' -%}
      {%- assign art_count = art_count | plus: 1 -%}
    {%- endif -%}
  {%- endfor -%}

  <div class="status-grid" style="display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));align-items:start;">
    <div class="card">
      <h3>Build</h3>
      <!-- We'll rewrite this in JS to Central -->
      <p>
        <strong>Built (Central):</strong>
        <code class="ts-central" data-iso="{{ site.time | date_to_xmlschema }}">—</code>
      </p>
      {%- if site.github.build_revision -%}
      <p><strong>Commit:</strong> <code>{{ site.github.build_revision | slice: 0, 10 }}</code></p>
      {%- endif -%}
      <p><strong>Env:</strong> {{ jekyll.environment | default: "development" }}</p>
    </div>

    <div class="card">
      <h3>Heartbeat</h3>
      <p><strong>Updated (Central):</strong> <code id="hb-ts">—</code></p>
      <p><strong>Env (declared):</strong> <code>status.json</code></p>
    </div>

    <div class="card">
      <h3>Inventory</h3>
      <p><strong>Logs:</strong> {{ logs | size }}</p>
      <p><strong>Field Notes:</strong> {{ notes | size }}</p>
      <p><strong>Artifacts (files):</strong> {{ art_count }}</p>
    </div>

    <div class="card">
      <h3>Latest Log</h3>
      {%- if logs and logs.size > 0 -%}
        {%- assign L = logs | first -%}
        <p><a href="{{ L.url | relative_url }}">{{ L.title }}</a></p>
        <p>
          <strong>Published (Central):</strong>
          <time class="ts-central" datetime="{{ L.date | date_to_xmlschema }}" data-iso="{{ L.date | date_to_xmlschema }}">—</time>
        </p>
        {%- if L.log_id %}<p>ID: <code>{{ L.log_id }}</code></p>{% endif %}
      {%- else -%}
        <p>No logs found.</p>
      {%- endif -%}
    </div>

    <div class="card">
      <h3>Latest Field Note</h3>
      {%- if notes and notes.size > 0 -%}
        {%- assign N = notes | first -%}
        <p><a href="{{ N.url | relative_url }}">{{ N.title }}</a></p>
        <p>
          <strong>Published (Central):</strong>
          <time class="ts-central" datetime="{{ N.date | date_to_xmlschema }}" data-iso="{{ N.date | date_to_xmlschema }}">—</time>
        </p>
      {%- else -%}
        <p>No field notes found.</p>
      {%- endif -%}
    </div>

    <div class="card">
      <h3>Feeds</h3>
      <p><strong>Checked (Central):</strong> <code id="feeds-ts">—</code></p>
      <div id="feeds-list" class="chip-grid"></div>
    </div>
  </div>

  <hr>
  <p><strong>Quick links:</strong>
    <a href="{{ '/logs/' | relative_url }}">Logs</a> ·
    <a href="{{ '/feeds/' | relative_url }}">Feeds</a> ·
    <a href="{{ '/status/status.json' | relative_url }}">Status JSON</a> ·
    <a href="{{ '/status/feeds.json'  | relative_url }}">Feeds JSON</a> ·
    <a href="{{ '/healthz.txt' | relative_url }}">healthz</a>
  </p>
</section>

<style>
:root{
  --chip-ok-bg:    rgba( 46,120, 86,.14);
  --chip-ok-bd:    rgba( 46,120, 86,.45);
  --chip-bad-bg:   rgba(160, 60, 60,.14);
  --chip-bad-bd:   rgba(160, 60, 60,.45);
  --chip-code-bg:  rgba(255,255,255,.08);
  --chip-fg:       currentColor;
}
[data-theme="light"],
:root.light {
  --chip-ok-bg:    rgba( 26,120, 86,.16);
  --chip-ok-bd:    rgba( 26,120, 86,.40);
  --chip-bad-bg:   rgba(200, 70, 70,.16);
  --chip-bad-bd:   rgba(200, 70, 70,.38);
  --chip-code-bg:  rgba(0,0,0,.06);
  --chip-fg:       #222;
}

/* Two-column chip grid to keep the card compact without inner scrollbars */
.chip-grid{
  display:grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap:.5rem;
}
@media (max-width: 560px){
  .chip-grid{ grid-template-columns: 1fr; }
}

.chip{
  display:flex;align-items:center;justify-content:space-between;gap:.5rem;
  padding:.35rem .5rem;border-radius:.4rem;text-decoration:none;
  border:1px solid var(--chip-ok-bd); background:var(--chip-ok-bg); color:var(--chip-fg);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  font-size: .92rem;
  line-height: 1.2;
}
.chip.bad{ border-color:var(--chip-bad-bd); background:var(--chip-bad-bg); }
.chip .label{white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.chip .code{
  margin-left:.35rem; padding:.05rem .32rem; border-radius:.25rem;
  background:var(--chip-code-bg); font-size:.85em; opacity:.9;
}
</style>

<script>
(function(){
  // Central Time formatter: 2025-11-08 14:03:27 CST/CDT
  const centralFmt = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Chicago',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false, timeZoneName: 'short'
  });

  const toCentral = (iso) => {
    try {
      const d = new Date(iso);
      // Intl returns e.g. "11/08/2025, 14:03:27 CST"
      const parts = centralFmt.formatToParts(d);
      const map = Object.fromEntries(parts.map(p => [p.type, p.value]));
      return `${map.year}-${map.month}-${map.day} ${map.hour}:${map.minute}:${map.second} ${map.timeZoneName}`;
    } catch { return '—'; }
  };

  // 1) Convert any server-rendered timestamps marked with .ts-central
  document.querySelectorAll('.ts-central[data-iso], time.ts-central[data-iso]').forEach(el => {
    const iso = el.getAttribute('data-iso') || el.getAttribute('datetime');
    if (iso) el.textContent = toCentral(iso);
  });

  // 2) Heartbeat timestamp (from status.json)
  fetch('{{ "/status/status.json" | relative_url }}', { cache: 'no-store' })
    .then(r => r.json())
    .then(hb => { document.getElementById('hb-ts').textContent = hb.updated_utc ? toCentral(hb.updated_utc) : '—'; })
    .catch(() => { document.getElementById('hb-ts').textContent = '—'; });

  // 3) Feeds grid + checked time
  fetch('{{ "/status/feeds.json" | relative_url }}', { cache: 'no-store' })
    .then(r => r.json())
    .then(data => {
      const ts = data.updated_utc ? toCentral(data.updated_utc) : '—';
      document.getElementById('feeds-ts').textContent = ts;

      const grid = document.getElementById('feeds-list');
      grid.innerHTML = '';

      (data.endpoints || []).forEach(ep => {
        const ok   = Number(ep.status) === 200;
        const name = (ep.name || 'Feed').replace(/\s*\(external\)\s*/i, ''); // remove "(external)" from the label only

        const a = document.createElement('a');
        a.className = 'chip' + (ok ? '' : ' bad');
        a.href = ep.url; a.target = '_blank'; a.rel = 'noopener';
        a.title = ep.name || name; // keep full name for tooltip

        const label = document.createElement('span');
        label.className = 'label';
        label.textContent = name;

        const code = document.createElement('span');
        code.className = 'code';
        code.textContent = String(ep.status ?? '—');

        a.appendChild(label);
        a.appendChild(code);
        grid.appendChild(a);
      });
    })
    .catch(() => { document.getElementById('feeds-ts').textContent = '—'; });
})();
</script>