# Finch Archive

Recovered notes from incomplete transmissions.

This repository is the canonical archive for **Halloway Finch** and deploys **https://fincharchive.com**.  
It stores public logs, sidecar artifacts (audio/images/docs), integrity metadata, and the static Jekyll site used for publishing.

[![RSS → Repo](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/rss.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/rss.yml)
[![Hash & Index Artifacts](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/hash-artifacts.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/hash-artifacts.yml)
[![Pages build & deploy](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/pages.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/pages.yml)

---

## Repository layout

```
.github/workflows/   # GitHub Actions (RSS import, pages build, artifact hashing)
_includes/           # Shared partials (head, footer, social-meta, etc.)
_layouts/            # Jekyll layouts (default, log, fieldnote)
assets/              # CSS, JS, static images
logs/                # ✳️ Source markdown for logs (Jekyll collection)
field-notes/         # ✳️ Secondary collection (Field Notes)
artifacts/           # ✳️ Per-log folders with media & metadata
  └─ <slug>/         #    e.g. the-voice-in-the-static/
     ├─ *.wav|*.mp3|*.pdf|*.jpg|*.png|*.webp …
     └─ metadata.json  # machine-readable inventory (hashes, sizes)

.finch/state.json     # Importer state (stable IDs & slug mapping)
_config.yml           # Jekyll configuration (collections, meta, plugins)
```

**Pretty URLs**
- Each log is authored in `_logs/<slug>.md` and published at `/logs/<slug>/`.
- Artifacts for that log live under `/artifacts/<slug>/`.

---

## Automation

### 1) RSS → Jekyll import
- Workflow: **`.github/workflows/rss.yml`**
- Pulls the latest Substack entry and writes `_logs/<slug>.md`.
- Extracts hero image (RSS enclosure) when present.
- Normalizes the body (strips duplicate title/author/share blocks and keeps content from the first `<p>` onward).
- Ensures an **empty folder** exists at `artifacts/<slug>/` for sidecar files.

**Secrets used**
- `SUBSTACK_RSS_URL` (e.g. `https://www.hallowayfinch.com/feed`)
- `RSS_PROXY_URL` (optional; e.g. `https://rss.fincharchive.com`)

Runs automatically every hour at 22 minutes past and also supports manual “Run workflow”.

---

### 2) Hash & Index Artifacts
- Workflow: **`.github/workflows/hash-artifacts.yml`**
- Trigger: **on push** to anything under `artifacts/**`.
- Reads each `/artifacts/<slug>/` folder and (re)writes a canonical `metadata.json` with:
  - `file`, `bytes`, `sha256` for each artifact
  - Optional audio/image dimensions where available
- Commits only when metadata actually changes.

---

### 3) GitHub Pages
- Workflow: **`.github/workflows/pages.yml`**
- Builds the Jekyll site and publishes it to **fincharchive.com** using GitHub Pages.

---

## Meta & SEO

Open Graph, Twitter, and iMessage unfurls are handled automatically:

- `_includes/head.html` defines titles, descriptions, and canonical URLs.
- `_includes/social-meta.html` injects per-page images (using `image`, `og_image`, `hero_image`, or a site-wide fallback).
- `_config.yml` declares a `social_image` fallback and optional `twitter_username`.
- Logs and Field Notes unfurl cleanly on Slack, Discord, and iMessage with their hero or share image.

---

## How to add a new artifact

1. Identify the log slug (e.g. `_logs/the-voice-in-the-static.md` → slug is `the-voice-in-the-static`).
2. Place new files into `artifacts/the-voice-in-the-static/` (supported types: `.wav .flac .mp3 .pdf .jpg .jpeg .png .gif .webp`).
3. Commit and push.  
   The **Hash & Index Artifacts** workflow will regenerate `metadata.json`.

Artifacts appear automatically on the corresponding log page.

---

## Integrity & verification

Each artifact folder has a machine-readable inventory (`metadata.json`) including SHA-256 hashes.

**Example: verify a single file**
```bash
cd artifacts/the-voice-in-the-static
# Read expected hash from metadata.json (requires jq)
EXPECTED=$(jq -r '.files[] | select(.file=="reversed-audio.mp3") | .sha256' metadata.json)
# Compute actual and compare
sha256sum reversed-audio.mp3 | awk '{print $1}' | grep -qi "^$EXPECTED$"   && echo "✓ OK" || echo "✗ MISMATCH"
```

No `SHA256SUMS.txt` is required — `metadata.json` is the canonical source of truth.

---

## Conventions

- **Slugs / folder names:** derived from the Substack permalink (`the-voice-in-the-static`).
- **Stable log IDs:** sequential identifiers (`1022A`, `1022B`, …).
- **Dates:** ISO-8601 with timezone in front matter.
- **Artifact filenames:** concise kebab-case; descriptive when relevant.  
  Example: `voice-in-static_reversed.mp3`, `cassette-label.jpg`.

Typical front matter:

```yaml
---
layout: log
title: "The Voice in the Static"
log_id: "1022A"
date: "2025-10-23T03:22:15-05:00"
source_url: "https://www.hallowayfinch.com/p/the-voice-in-the-static"
guid: "https://www.hallowayfinch.com/p/the-voice-in-the-static"
permalink: "/logs/the-voice-in-the-static/"
hero_image: "https://.../header.png"
artifacts:
  - path: "/artifacts/the-voice-in-the-static/reversed-audio.mp3"
    label: "Reversed audio (MP3)"
---
```

---

## Local development

Preview the site locally:

```bash
bundle install
bundle exec jekyll serve
```

To test the importer manually:

```bash
SUBSTACK_RSS_URL="https://www.hallowayfinch.com/feed" python scripts/rss_to_repo.py
```

---

## Validation tools

- [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
- [Twitter Card Validator](https://cards-dev.twitter.com/validator)
- [Slack Block Kit URL Preview Tester](https://api.slack.com/tools/block-kit-builder)

Use these to confirm your Open Graph tags and image unfurls.

---

## License

All written and audio materials © Halloway Finch.  
Distributed under **CC BY-NC-ND 4.0** (Attribution – NonCommercial – NoDerivatives).  
See [`LICENSE`](LICENSE).

---

## Contact

**Halloway Finch** — h@hallowayfinch.com  
Recovered notes from incomplete transmissions.
