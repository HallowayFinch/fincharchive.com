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

  {%- comment -%} Live artifact file count as a fallback {%- endcomment -%}
  {%- assign art_count = 0 -%}
  {%- for f in site.static_files -%}
    {%- if f.path contains '/artifacts/' -%}
      {%- assign art_count = art_count | plus: 1 -%}
    {%- endif -%}
  {%- endfor -%}

  {%- assign heartbeat = site.data.status -%}
  {%- assign hb_updated = heartbeat.updated_utc | default: site.time | date: "%Y-%m-%dT%H:%M:%SZ" -%}
  {%- assign hb_env     = heartbeat.environment | default: "production" -%}
  {%- assign hb_logs    = heartbeat.counts.logs | default: logs.size -%}
  {%- assign hb_notes   = heartbeat.counts.field_notes | default: site["field-notes"].size -%}
  {%- assign hb_files   = heartbeat.counts.artifacts | default: art_count -%}

  <div class="status-grid" style="display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));">
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
      <p><strong>Updated (UTC):</strong> {{ hb_updated }}</p>
      <p><strong>Env (declared):</strong> {{ hb_env }}</p>
      <p><a href="{{ '/status/status.json' | relative_url }}">status.json</a></p>
    </div>

    <div class="card">
      <h3>Inventory</h3>
      <p><strong>Logs:</strong> {{ hb_logs }}</p>
      <p><strong>Field Notes:</strong> {{ hb_notes }}</p>
      <p><strong>Artifacts (files):</strong> {{ hb_files }}</p>
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
      {%- assign notes_all = site["field-notes"] | sort: "date" | reverse -%}
      {%- if notes_all and notes_all.size > 0 -%}
        {%- assign N = notes_all | first -%}
        <p><a href="{{ N.url | relative_url }}">{{ N.title }}</a></p>
        <p><time datetime="{{ N.date | date_to_xmlschema }}">{{ N.date | date: "%b %-d, %Y %H:%M" }}</time></p>
      {%- else -%}
        <p>No field notes found.</p>
      {%- endif -%}
    </div>
  </div>

  <hr>

  <p><strong>Quick links:</strong>
    <a href="{{ '/logs/' | relative_url }}">Logs</a> ·
    <a href="{{ '/feeds/' | relative_url }}">Feeds</a> ·
    <a href="{{ '/status/status.json' | relative_url }}">Status JSON</a> ·
    <a href="{{ '/healthz.txt' | relative_url }}">healthz</a>
  </p>
</section>
