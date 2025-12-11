# Finch Archive

Recovered notes from incomplete transmissions.

This repository is the canonical archive for **Halloway Finch** and deploys **[fincharchive.com](https://fincharchive.com)**.

It stores public logs, sidecar artifacts (audio/images/docs), integrity metadata, and the static Jekyll site used for publishing.

[![RSS → Repo](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/rss.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/rss.yml)
[![Import Field Notes](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/import-field-notes.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/import-field-notes.yml)
[![Artifacts: Hash, Index & Verify](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/artifacts.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/artifacts.yml)
[![Status / Heartbeat](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/status.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/status.yml)
[![Pages build & deploy](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/pages.yml/badge.svg?branch=main)](https://github.com/HallowayFinch/fincharchive.com/actions/workflows/pages.yml)

---

## Repository layout

```text
.github/workflows/    # GitHub Actions (importers, pages build, artifacts, status, feeds, icons)
.github/scripts/      # CI-only helpers (e.g., gen_log_pages.py)
_includes/            # Shared partials (head, footer, social-meta, etc.)
_layouts/             # Jekyll layouts (default, log, fieldnote, logs index)
assets/               # CSS, icons, static images
_logs/                # ✳️ Source Markdown for Logs (Jekyll collection)
_field-notes/         # ✳️ Field Notes (Jekyll collection)
artifacts/            # ✳️ Per-log folders with media & metadata
  └─ <slug>/          #    e.g. the-voice-in-the-static/
     ├─ *.wav|*.mp3|*.pdf|*.jpg|*.png|*.webp …
     ├─ metadata.json   # machine-readable inventory (hashes, sizes)
     └─ SHA256SUMS.txt  # optional text summary of checksums

badges/               # Machine-generated JSON badges (e.g., artifacts integrity)
status/               # Machine-generated status payloads (heartbeat, feeds)

.finch/state.json     # Importer state (stable IDs & slug mapping)
_config.yml           # Jekyll configuration (collections, meta, plugins)
```

**Pretty URLs**

- Each Log lives at `_logs/<slug>.md` → published at `/logs/<slug>/`.
- Artifacts for that log live under `/artifacts/<slug>/`.
- Field Notes live at `_field-notes/<slug>.md` → `/field-notes/<slug>/`.

---

## Automation

### 1) RSS → Jekyll (Logs)

- Workflow: **`.github/workflows/rss.yml`**
- Runs hourly at **:25** (buffered after scheduled 10:22 Substack releases) and on demand.
- Pulls the latest Substack entry and writes `_logs/<slug>.md` with front matter:
  - `title`, `date`, `log_id`, `source_url`, `guid`, `permalink`, optional `hero_image`.
- Ensures a corresponding `artifacts/<slug>/` folder exists so assets can be attached later.
- Optionally runs light validation and artifact hashing as part of the import flow.
- **Auth & attribution:** commits are authored as **HallowayFinch** using the verified noreply email so contributions appear on the profile activity chart.

**Secrets**

- `SUBSTACK_RSS_URL` (e.g., `https://www.hallowayfinch.com/feed`)
- `RSS_PROXY_URL` *(optional; used when direct fetch is blocked)*
- `HF_PAT` *(fine-grained token for this repo, Contents: Read/Write)*
- `HF_NOREPLY_EMAIL` *(e.g., `239624912+HallowayFinch@users.noreply.github.com`)*

---

### 2) Import Field Notes (Substack Notes)

- Workflow: **`.github/workflows/import-field-notes.yml`**
- Runs every **30 minutes** and on demand (staggered away from other jobs).
- Converts Substack Notes into `_field-notes/*.md` and maintains a small ledger file (`.fieldnote-import-ledger.json`) to avoid duplicates.
- Commits are authored as **HallowayFinch** and pushed with `HF_PAT`.

**Secrets**

- `SUBSTACK_NOTES_RSS`
- `HF_PAT`
- `HF_NOREPLY_EMAIL`

---

### 3) Artifacts: Hash, Index & Verify

- Workflow: **`.github/workflows/artifacts.yml`**
- Triggers:
  - **On push** of files in `artifacts/**/*.{wav,flac,mp3,m4a,aiff,mp4,mov,png,jpg,jpeg,gif,webp,tif,tiff,pdf,txt,csv}`
  - **Nightly** cron
  - On manual dispatch
- Responsibilities:
  1. Run `scripts/hash_artifacts.py` to:
     - Rebuild each `artifacts/<slug>/metadata.json` (hashes, sizes, relative paths).
     - Maintain/refresh `SHA256SUMS.txt` where appropriate.
  2. Scan all artifact folders and derive a single **`badges/artifacts.json`** shield payload summarizing integrity state (e.g., *verified*, *mismatch*, *none*).
- Commits only when metadata or badge content actually changes.
- Authored as **HallowayFinch**, pushed with `HF_PAT`.

This workflow is the canonical source of artifact integrity; opportunistic hashing inside other jobs (e.g. RSS imports) is purely a convenience.

---

### 4) Status & Feeds

#### a) Status / Heartbeat

- Workflow: **`.github/workflows/status.yml`**
- Runs every few hours and on manual dispatch.
- Derives a minimal heartbeat payload with:
  - UTC timestamp
  - Counts for logs, field notes, and artifacts
- Writes to **`status/status.json`** and **`_data/status.json`** for use in templates and `/status/`.

#### b) Feeds Check & Publish

- Workflow: **`.github/workflows/feeds-check.yml`**
- Runs hourly at **:12** (staggered away from RSS/Field Notes).
- Probes the site’s feeds:
  - `/feed/`, `/feed.json`
  - `/logs/feed.xml`, `/field-notes/feed.xml`
  - Substack Notes RSS endpoint
- Writes current status (HTTP response codes, proxy usage) to **`status/feeds.json`**.

Both workflows commit only on change and use `HF_PAT` / `HF_NOREPLY_EMAIL` for authorship.

---

### 5) Icons

- Workflow: **`.github/workflows/icons.yml`**
- Triggered when `assets/icons/finch.svg` (or the workflow itself) changes.
- Uses `librsvg` + ImageMagick to generate:

  - A set of favicons: `favicon-16.png`, `favicon-32.png`, `favicon-48.png`, `favicon-180.png`, `favicon-192.png`, `favicon-256.png`, `favicon-384.png`, `favicon-512.png`
  - `apple-touch-icon.png`, Android Chrome icons, and **`favicon.ico`** (including a root-level copy)
  - `site.webmanifest` describing the app icons / theme

- Commits only when icon/manifest outputs change.

---

### 6) GitHub Pages (build & deploy)

- Workflow: **`.github/workflows/pages.yml`**
- Triggers:
  - `on: push` to `main` for site-relevant paths (layouts, includes, collections, assets, feeds, config)
  - `workflow_dispatch` for manual rebuilds
- Guard rails:
  - `on.push.paths` ensures only site-visible changes trigger a build.
  - Concurrency group `"pages"` cancels redundant builds when new commits land quickly.
- Pre-build step:
  - Runs `.github/scripts/gen_log_pages.py` which:
    - Counts `_logs/` entries
    - Generates ephemeral `/logs/page/N/` index files with the correct front matter
    - Cleans up stale page directories
  - This happens **inside the CI workspace only**; no commits are made.
- Build:
  - Uses `actions/jekyll-build-pages` to compile into `_site`
  - Uploads the artifact and deploys via `actions/deploy-pages` to the `github-pages` environment.

**What causes a deploy?**

- A new/updated log (`_logs/**`)
- A new/updated field note (`_field-notes/**`)
- Layout/include/theme changes, asset updates, feed/template changes, `_config.yml`, etc.

If the importers run but detect no changes, they will skip committing, which means Pages will not trigger.

---

## Meta & SEO

Open Graph, Twitter, and iMessage unfurls are handled via includes:

- `_includes/head.html` provides titles, descriptions, canonical URLs, language, and basic meta.
- `_includes/social-meta.html` injects per-page images (`image`, `og_image`, `hero_image`) with a global fallback specified in `_config.yml` (`social_image`).
- Logs and Field Notes unfurl cleanly in Slack, Discord, iMessage, and similar clients.

Feeds are hand-rolled:

- **All content RSS:** `/feed/` (`/feed/index.xml`)
- **All content JSON Feed:** `/feed.json`
- **Logs-only RSS:** `/logs/feed.xml`
- **Field Notes RSS:** `/field-notes/feed.xml`

---

## Integrity & verification

Each `artifacts/<slug>/metadata.json` is a small, machine-readable index describing:

- `file` / `path`
- `sha256` (full checksum)
- `size` (bytes)
- Any additional fields the hash script may add over time

`SHA256SUMS.txt` is an optional companion file with a more traditional checksum listing.

A nightly + on-change workflow aggregates this into **`badges/artifacts.json`** for a Shields.io-style badge (used above).

**Verify a single file**

```bash
cd artifacts/the-voice-in-the-static

EXPECTED=$(jq -r '.files[] | select(.file=="reversed-audio.mp3") | .sha256' metadata.json)

sha256sum reversed-audio.mp3   | awk '{print $1}'   | grep -qi "^$EXPECTED$"   && echo "✓ OK"   || echo "✗ MISMATCH"
```

`metadata.json` is the canonical record; if it conflicts with reality, the artifacts workflow will eventually mark this via the badge state.

---

## Conventions

- **Slugs**  
  Derived from Substack permalinks (e.g., `the-voice-in-the-static`).

- **Stable IDs**  
  `log_id` values such as `1022A`, `1022B`, … are treated as permanent identifiers, referenced in both the archive and external notes.

- **Dates**  
  ISO-8601 with timezone (UTC stored; rendered in US Central per `_config.yml`).

- **Artifacts**  
  Concise, descriptive kebab-case filenames. Grouped by log slug (or an explicitly configured `artifacts_folder` in front matter).

Typical log front matter:

```yaml
---
layout: log
title: "The Voice in the Static"
log_id: "1022A"
date: "2025-10-23T03:22:15+00:00"
source_url: "https://www.hallowayfinch.com/p/the-voice-in-the-static"
guid: "/p/the-voice-in-the-static"
permalink: "/logs/the-voice-in-the-static/"
hero_image: "https://substack-post-media.s3.amazonaws.com/public/images/.../header.png"
---
```

---

## Local development

```bash
# Install Ruby dependencies (once)
bundle install

# Serve locally
bundle exec jekyll serve
```

The importers (RSS / Field Notes) and artifact hashing are designed for CI, but can be run manually if needed:

```bash
# Example: run the RSS importer locally
SUBSTACK_RSS_URL="https://www.hallowayfinch.com/feed" python scripts/rss_to_repo.py

# Example: recompute artifact metadata & checksums
python scripts/hash_artifacts.py
```

You do **not** need to run `.github/scripts/gen_log_pages.py` locally unless you want to mirror CI pagination behavior exactly; Jekyll will happily render `/logs/` with the full list for development.

---

## Secrets (summary)

| Secret               | Used by                         | Notes                                                |
|----------------------|---------------------------------|------------------------------------------------------|
| `SUBSTACK_RSS_URL`   | `rss.yml`                       | Substack site feed                                   |
| `RSS_PROXY_URL`      | `rss.yml`, `feeds-check.yml`    | Optional proxy (may be blank)                        |
| `SUBSTACK_NOTES_RSS` | `import-field-notes.yml`        | Substack Notes feed (when available)                 |
| `HF_PAT`             | all committing workflows        | Fine-grained PAT (Contents: Read/Write)              |
| `HF_NOREPLY_EMAIL`   | all committing workflows        | `239624912+HallowayFinch@users.noreply.github.com`   |

> The PAT should belong to the **HallowayFinch** account and be scoped to this repository so commits and activity are correctly attributed.

---

## Troubleshooting

- **New Substack log not appearing on the site**

  1. Check **Actions → RSS → latest run** and confirm the importer created or updated a `_logs/<slug>.md` file and, if needed, committed changes.
  2. Confirm a subsequent **github-pages** workflow ran successfully.
  3. Hard refresh the site (and purge any external cache if applicable).

- **Artifacts not showing under a log**

  - Ensure the files live at `artifacts/<slug>/` or that the log front matter sets `artifacts_folder` correctly.
  - Confirm the extension is one of the allowed types (`wav`, `mp3`, `m4a`, `png`, `jpg`, `pdf`, `txt`, `csv`, etc.).
  - Check the **Artifacts: Hash, Index & Verify** workflow for recent runs; it will rebuild `metadata.json` and update the badge status.

- **Feed status looks stale**

  - Check **Feeds Check & Publish** in Actions.  
    If the run succeeded but a feed still returns an error code, the issue is likely upstream (Substack, DNS, or hosting), not the archive itself.

---

## License

All written and audio materials © Halloway Finch.  
Distributed under **CC BY-NC-ND 4.0** (Attribution – NonCommercial – NoDerivatives).  
See [`LICENSE`](LICENSE).

---

## Contact

**Halloway Finch** — <h@hallowayfinch.com>  
*Recovered notes from incomplete transmissions.*
