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

  {%- comment -%} Count artifacts by scanning /artifacts/ static files {%- endcomment -%}
  {%- assign art_count = 0 -%}
  {%- for f in site.static_files -%}
    {%- if f.path contains '/artifacts/' -%}
      {%- assign art_count = art_count | plus: 1 -%}
    {%- endif -%}
  {%- endfor -%}

  <div class="status-grid">
    <div class="card">
      <h3>Build</h3>
      <p><strong>Built:</strong> {{ site.time | date: "%Y-%m-%d %H:%M:%S %Z" }}</p>
      {%- if site.github.build_revision -%}
      <p><strong>Commit:</strong> <code>{{ site.github.build_revision | slice: 0, 12 }}</code></p>
      {%- endif -%}
      <p><strong>Env:</strong> {{ jekyll.environment | default: "development" }}</p>
    </div>

    <div class="card">
      <h3>Heartbeat</h3>
      {%- assign hb = site.static_files | where: "path", "/status/status.json" | first -%}
      {%- if hb -%}
        <p><strong>Updated (UTC):</strong> {{ hb.modified_time | date: "%Y-%m-%dT%H:%M:%SZ" }}</p>
        <p><strong>Env (declared):</strong> production</p>
        <p><code>status.json</code></p>
      {%- else -%}
        <p>Pending (no <code>status.json</code> yet)</p>
      {%- endif -%}
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
      {%- assign fs = site.data["feeds-status"] -%}
      {%- if fs and fs.endpoints -%}
        <p><strong>Checked (UTC):</strong> {{ fs.updated_utc }}</p>
        <ul class="feed-list">
          {%- for ep in fs.endpoints -%}
            {%- assign ok = ep.status | plus: 0 -%}
            <li>
              <a href="{{ ep.url }}">{{ ep.name }}</a>
              <code class="feed-code {% if ok >= 200 and ok < 300 %}is-ok{% else %}is-bad{% endif %}">
                {{ ep.status }}{% if ok >= 200 and ok < 300 %} ✓{% endif %}
              </code>
            </li>
          {%- endfor -%}
        </ul>
      {%- else -%}
        <p>Status file not generated yet.</p>
        <ul>
          <li><a href="{{ '/feed/' | relative_url }}">All (RSS)</a></li>
          <li><a href="{{ '/feed.json' | relative_url }}">All (JSON)</a></li>
          <li><a href="{{ '/logs/feed.xml' | relative_url }}">Logs (RSS)</a></li>
          <li><a href="{{ '/field-notes/feed.xml' | relative_url }}">Field Notes (RSS)</a></li>
          <li><a href="https://substack.com/api/v1/notes/rss?publication_id=6660929">Substack Field Notes (external)</a></li>
        </ul>
      {%- endif -%}
    </div>
  </div>

  <hr>

  <p><strong>Quick links:</strong>
    <a href="{{ '/logs/' | relative_url }}">Logs</a> ·
    <a href="{{ '/feeds/' | relative_url }}">Feeds</a> ·
    <a href="{{ '/status/status.json' | relative_url }}">Status JSON</a> ·
    <a href="{{ '/status/feeds.json' | relative_url }}">Feeds JSON</a> ·
    <a href="{{ '/healthz.txt' | relative_url }}">healthz</a>
  </p>
</section>

<style>
  /* status-specific layout polish (scoped to this page) */
  .status-grid{
    display:grid;
    gap:14px;
    grid-template-columns: 1fr;
  }
  @media (min-width: 960px){
    .status-grid{ grid-template-columns: 1fr 1fr; }
  }
  .card{
    border:1px solid var(--badge-border);
    background:var(--card-bg);
    border-radius:12px;
    padding:14px 16px;
    box-shadow: var(--shadow-soft);
  }
  .feed-list{
    list-style:none; padding:0; margin:.6rem 0 0;
    display:grid; gap:.45rem;
  }
  .feed-list li{
    display:flex; justify-content:space-between; align-items:center; gap:.6rem;
    border:1px solid var(--badge-border); border-radius:8px;
    padding:.45rem .6rem; background:var(--badge-bg);
  }
  .feed-code{ opacity:.95; }
  .feed-code.is-ok{
    border:1px solid rgba(60,160,90,.5);
    padding:.1rem .35rem; border-radius:6px;
    background:rgba(60,160,90,.12);
  }
  .feed-code.is-bad{
    border:1px solid rgba(160,60,60,.5);
    padding:.1rem .35rem; border-radius:6px;
    background:rgba(160,60,60,.10);
  }
</style>
