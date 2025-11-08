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
      <p><strong>Built:</strong> {{ site.time | date: "%Y-%m-%d %H:%M:%S %Z" }}</p>
      {%- if site.github.build_revision -%}
      <p><strong>Commit:</strong> <code>{{ site.github.build_revision | slice: 0, 10 }}</code></p>
      {%- endif -%}
      <p><strong>Env:</strong> {{ jekyll.environment | default: "development" }}</p>
    </div>

    <div class="card">
      <h3>Heartbeat</h3>
      <p><strong>Updated (UTC):</strong>
        {%- capture hb -%}{%- include_relative status.json -%}{%- endcapture -%}
        {%- assign hb_json = hb | jsonify | replace:'\"','"' -%}
        <code id="hb-ts">{{ hb_json | split: '"updated_utc":"' | last | split: '"' | first }}</code>
      </p>
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
        <p><time datetime="{{ L.date | date_to_xmlschema }}">{{ L.date | date: "%b %-d, %Y %H:%M" }}</time></p>
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
        <p><time datetime="{{ N.date | date_to_xmlschema }}">{{ N.date | date: "%b %-d, %Y %H:%M" }}</time></p>
      {%- else -%}
        <p>No field notes found.</p>
      {%- endif -%}
    </div>

    <div class="card">
      <h3>Feeds</h3>
      <p><strong>Checked (UTC):</strong> <code id="feeds-ts">—</code></p>
      <div id="feeds-list" class="chip-list"></div>
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
/* Theme-aware chip colors (works in both dark & light) */
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

.chip-list{display:flex;flex-wrap:wrap;gap:.5rem;}
.chip{
  display:flex;align-items:center;gap:.5rem;
  padding:.45rem .6rem;border-radius:.4rem;text-decoration:none;
  border:1px solid var(--chip-ok-bd); background:var(--chip-ok-bg); color:var(--chip-fg);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
}
.chip.bad{ border-color:var(--chip-bad-bd); background:var(--chip-bad-bg); }
.chip .label{white-space:nowrap;}
.chip .badge{
  margin-left:.25rem; font-size:.85em; opacity:.82;
  padding:.05rem .35rem; border-radius:.25rem; background:var(--chip-code-bg);
}
.chip .code{
  margin-left:.35rem; padding:.12rem .4rem; border-radius:.25rem;
  background:var(--chip-code-bg);
}
</style>

<script>
(async () => {
  try {
    const res  = await fetch('{{ "/status/feeds.json" | relative_url }}', { cache: 'no-store' });
    const data = await res.json();

    // timestamp
    document.getElementById('feeds-ts').textContent = data.updated_utc || '—';

    // list
    const box = document.getElementById('feeds-list');
    box.innerHTML = '';

    (data.endpoints || []).forEach(ep => {
      const ok = Number(ep.status) === 200;

      const a = document.createElement('a');
      a.className = 'chip' + (ok ? '' : ' bad');
      a.href = ep.url; a.target = '_blank'; a.rel = 'noopener';

      // single label (no duplication)
      const name = document.createElement('span');
      name.className = 'label';
      name.textContent = ep.name || 'Feed';

      // optional “via …” badge
      if (ep.via) {
        const via = document.createElement('span');
        via.className = 'badge';
        via.textContent = `via ${ep.via}`;
        name.appendChild(document.createTextNode(' '));
        name.appendChild(via);
      }

      // status code pill
      const code = document.createElement('span');
      code.className = 'code';
      code.textContent = String(ep.status ?? '—');

      a.appendChild(name);
      a.appendChild(code);
      box.appendChild(a);
    });
  } catch (e) {
    document.getElementById('feeds-ts').textContent = 'error';
    console.error('feeds.json load failed', e);
  }
})();
</script>
