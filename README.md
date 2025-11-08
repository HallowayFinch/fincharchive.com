
# Finch Archive

Recovered notes from incomplete transmissions.

This repository is the canonical archive for **Halloway Finch** and deploys **https://fincharchive.com**.  
It stores public logs, sidecar artifacts (audio/images/docs), integrity metadata, and the static Jekyll site used for publishing.

[![RSS → Repo](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/rss.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/rss.yml)
[![Import Field Notes](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/import-field-notes.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/import-field-notes.yml)
[![Hash & Index Artifacts](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/hash-artifacts.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/hash-artifacts.yml)
[![Verify Artifacts](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/verify-artifacts.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/verify-artifacts.yml)
[![Pages build & deploy](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/pages.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/pages.yml)

---

## Repository layout

```
.github/workflows/    # GitHub Actions (importers, pages build, artifact hashing/verify)
_includes/            # Shared partials (head, footer, social-meta, etc.)
_layouts/             # Jekyll layouts (default, log, fieldnote, logs index)
assets/               # CSS, JS, static images
_logs/                # ✳️ Source Markdown for Logs (Jekyll collection)
_field-notes/         # ✳️ Field Notes (Jekyll collection)
artifacts/            # ✳️ Per-log folders with media & metadata
  └─ <slug>/          #    e.g. the-voice-in-the-static/
     ├─ *.wav|*.mp3|*.pdf|*.jpg|*.png|*.webp …
     └─ metadata.json   # machine-readable inventory (hashes, sizes)

.finch/state.json     # Importer state (stable IDs & slug mapping)
_config.yml           # Jekyll configuration (collections, meta, plugins)
```

**Pretty URLs**
- Each Log lives at `_logs/<slug>.md` → published at `/logs/<slug>/`.
- Artifacts for that log live under `/artifacts/<slug>/`.

---

## Automation

### 1) RSS → Jekyll (Logs)
- Workflow: **`.github/workflows/rss.yml`**
- Runs hourly at **:22** and on demand.
- Pulls the latest Substack entry and writes `_logs/<slug>.md` with front matter:
  - `title`, `date`, `log_id`, `source_url`, `guid`, `permalink`, optional `hero_image`.
- Ensures an **empty** `artifacts/<slug>/` folder exists so assets can be attached later.
- **Auth & attribution:** commits are authored as **HallowayFinch** using the verified noreply email so contributions appear on the profile activity chart.

**Secrets**
- `SUBSTACK_RSS_URL` (e.g., `https://www.hallowayfinch.com/feed`)
- `RSS_PROXY_URL` *(optional)*
- `HF_PAT` *(fine‑grained token for this repo, Contents: Read/Write)*
- `HF_NOREPLY_EMAIL` *(e.g., `239624912+HallowayFinch@users.noreply.github.com`)*

---

### 2) Import Field Notes (Substack Notes)
- Workflow: **`.github/workflows/import-field-notes.yml`**
- Runs every **30 minutes** and on demand.
- Converts Substack Notes to `_field-notes/*.md` and maintains a small ledger file.
- Commits are authored as **HallowayFinch** and pushed with `HF_PAT`.

**Secrets**
- `SUBSTACK_NOTES_RSS`

---

### 3) Hash & Index Artifacts
- Workflow: **`.github/workflows/hash-artifacts.yml`**
- Trigger: **on push** of files in `artifacts/**/*.{wav,flac,mp3,mp4,mov,png,jpg,jpeg,gif,webp,tif,tiff,pdf,txt}` and on demand.
- Rewrites **`metadata.json`** and (optionally) `SHA256SUMS.txt` per folder; commits only on change.
- Authored as **HallowayFinch**, pushed with `HF_PAT`.

---

### 4) Verify Artifacts & Publish Badge
- Workflow: **`.github/workflows/verify-artifacts.yml`**
- Nightly + on changes; scans `artifacts/**`, validates/derives hashes, then writes **`badges/artifacts.json`** for a status badge.
- Commits the badge only when content changes.

---

### 5) GitHub Pages (build & deploy)
- Workflow: **`.github/workflows/pages.yml`**
- **Triggers:** `on: push` (to `main`) for site-relevant paths and manual dispatch.
- **Guards:** uses `dorny/paths-filter` to skip builds when nothing site-visible changed.
- **Pre-build step:** generates paginated `/logs/page/N/` files (GitHub Pages–friendly).
- **Build:** `actions/jekyll-build-pages` → uploads `_site` artifact → deploys with `actions/deploy-pages`.

**What causes a deploy?**  
- A new/updated log (`_logs/**`) or field note (`_field-notes/**`), layout/asset changes, or any file matched by the `paths:` list.
- No deploy occurs when importers find **no** changes.

---

## Meta & SEO

Open Graph, Twitter, and iMessage unfurls are handled via includes:

- `_includes/head.html` provides titles, descriptions, canonical URLs.
- `_includes/social-meta.html` injects per-page images (`image`, `og_image`, `hero_image`) with a global fallback from `_config.yml`.
- Logs and Notes unfurl cleanly (Slack, Discord, iMessage).

---

## Integrity & verification

Each `artifacts/<slug>/metadata.json` contains SHA‑256 hashes and sizes.

**Verify a single file**
```bash
cd artifacts/the-voice-in-the-static
EXPECTED=$(jq -r '.files[] | select(.file=="reversed-audio.mp3") | .sha256' metadata.json)
sha256sum reversed-audio.mp3 | awk '{print $1}' | grep -qi "^$EXPECTED$" && echo "✓ OK" || echo "✗ MISMATCH"
```

`metadata.json` is the canonical source of truth. A `badges/artifacts.json` shield is generated nightly.

---

## Conventions

- **Slugs:** derived from Substack permalinks (e.g., `the-voice-in-the-static`).
- **Stable IDs:** `1022A`, `1022B`, … (`log_id` in front matter).
- **Dates:** ISO‑8601 with timezone.
- **Artifacts:** concise kebab‑case filenames.

Typical log front matter:

```yaml
---
layout: log
title: "The Voice in the Static"
log_id: "1022A"
date: "2025-10-23T03:22:15-05:00"
source_url: "https://www.hallowayfinch.com/p/the-voice-in-the-static"
guid: "https://www.hallowayfinch.com/p/the-voice-in-the-static"
permalink: "/logs/the-voice-in-the-static/"
hero_image: "https://substack-post-media.../header.png"
---
```

---

## Local development

```bash
# Serve locally
bundle install
bundle exec jekyll serve

# Run the RSS importer manually (example)
SUBSTACK_RSS_URL="https://www.hallowayfinch.com/feed" python scripts/rss_to_repo.py
```

---

## Secrets (summary)

| Secret | Used by | Notes |
|---|---|---|
| `SUBSTACK_RSS_URL` | rss.yml | Substack site feed |
| `RSS_PROXY_URL` | rss.yml | Optional proxy (can be empty) |
| `SUBSTACK_NOTES_RSS` | import-field-notes.yml | Notes feed (when available) |
| `HF_PAT` | all committing workflows | Fine‑grained PAT (Contents: RW) |
| `HF_NOREPLY_EMAIL` | all committing workflows | `239624912+HallowayFinch@users.noreply.github.com` |

> Ensure the PAT is scoped to this repo and belongs to the **HallowayFinch** account so contributions are attributed correctly.

---

## Troubleshooting

- **New Substack post not on site**
  1. Check **Actions → RSS → latest run**; confirm “Commit (if changes)” step shows `changed=true`.
  2. Check **Actions → github-pages**; you should see a build started by the push.  
     - If not, confirm importers push with `HF_PAT` and Pages `on.push.paths` include `_logs/**`.
  3. Hard refresh the site; optionally purge Cloudflare cache.

- **Two Pages builds for one change**  
  Remove any remaining `workflow_run` triggers in `pages.yml` (imports already push).

- **Front matter errors**  
  The Pages workflow validates required keys (`title`, `date`) and will fail with a descriptive message.

---

## License

All written and audio materials © Halloway Finch.  
Distributed under **CC BY‑NC‑ND 4.0** (Attribution – NonCommercial – NoDerivatives).  
See [`LICENSE`](LICENSE).

---

## Contact

**Halloway Finch** — <h@hallowayfinch.com>  
*Recovered notes from incomplete transmissions.*
