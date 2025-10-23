import os, json, jinja2

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="canonical" href="{{ canonical_url }}">
<title>{{ title }} — {{ log_id }}</title>
<style>
  body{font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; background:#000; color:#e6e6e6; margin:40px;}
  a{color:#e6e6e6; text-decoration:underline;}
  .accent{border-top:2px solid #7A3A3A; margin:24px 0;}
  .meta{opacity:.8; font-size:.9rem; line-height:1.4;}
  .content{white-space:pre-wrap; line-height:1.6; font-size:1rem; margin-top:16px;}
  .artifacts{margin-top:24px;}
  .artifacts h2{font-size:1rem; margin:0 0 8px 0;}
  .table{border-collapse:collapse; width:100%;}
  .table td,.table th{border-top:1px solid #333; padding:8px; vertical-align:top;}
  .muted{opacity:.7;}
</style>
<h1>{{ title }}</h1>
<div class="meta">
  <div><strong>{{ log_id }}</strong> · {{ date }}</div>
  <div class="muted">Source: <a href="{{ source_url }}">{{ source_url }}</a></div>
</div>
<div class="accent"></div>
<div class="content">{{ body_md }}</div>

{% if artifacts %}
<div class="artifacts">
  <h2>Artifacts</h2>
  <table class="table">
    <tr><th>File</th><th>SHA-256</th><th class="muted">Info</th></tr>
    {% for f in artifacts %}
    <tr>
      <td><a href="/{{ f.relpath }}">{{ f.name }}</a></td>
      <td><code>{{ f.sha256 }}</code></td>
      <td class="muted">
        size {{ f.size }} bytes
        {% if f.duration_seconds %} · duration {{ "%.2f"|format(f.duration_seconds) }}s{% endif %}
        {% if f.bit_rate %} · bitrate {{ f.bit_rate }}{% endif %}
      </td>
    </tr>
    {% endfor %}
  </table>
</div>
{% endif %}
</html>
"""

REDIRECT_TEMPLATE = """<!doctype html>
<meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="{{ to }}">
<meta http-equiv="refresh" content="0; url={{ to }}">
<a href="{{ to }}">Redirecting to {{ to }}</a>
<script>location.href={{ to|tojson }};</script>
"""

def build(log_folder, meta, body_md, artifacts_manifest_path=None, canonical_url="#"):
    artifacts = []
    if artifacts_manifest_path and os.path.isfile(artifacts_manifest_path):
        with open(artifacts_manifest_path, "r", encoding="utf-8") as f:
            mf = json.load(f)
            artifacts = mf.get("files", [])

    html = jinja2.Template(PAGE_TEMPLATE).render(
        title = meta["title"],
        log_id = meta["log_id"],
        date = meta["date"],
        source_url = meta["source_url"],
        body_md = body_md,
        artifacts = artifacts,
        canonical_url = canonical_url
    )
    os.makedirs(log_folder, exist_ok=True)
    with open(os.path.join(log_folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

def build_redirect(alias_folder, to_url):
    os.makedirs(alias_folder, exist_ok=True)
    html = jinja2.Template(REDIRECT_TEMPLATE).render(to=to_url)
    with open(os.path.join(alias_folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
