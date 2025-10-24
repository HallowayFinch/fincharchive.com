# Finch Archive

Recovered notes from incomplete transmissions.

This repository is the canonical archive for **Halloway Finch** and deploys **https://fincharchive.com**.  
It stores public logs, sidecar artifacts (audio/images/docs), and integrity metadata.

---

## Repository layout

```
/.github/workflows/   # GitHub Actions (RSS import, pages build, artifact hashing)
/_layouts/            # Jekyll layouts (default, log, logs, fieldnote)
/_pages or /pages/    # Static pages (e.g., /logs/, /field-notes/)
/_assets or /assets/  # CSS, images, etc.

/_logs/               # ✳️ Source markdown for logs (Jekyll collection; one file per log)
/artifacts/           # ✳️ Per-log folders with media & metadata
  └─ <slug>/          #    e.g. the-voice-in-the-static/
     ├─ *.wav|*.mp3|*.pdf|*.jpg|*.png|*.webp …
     └─ metadata.json #    machine-readable inventory (hashes, sizes)

.finch/state.json     # Importer state (stable IDs & slug mapping)
_config.yml           # Jekyll site config
```

**Pretty URLs**
- Each log is authored in `_logs/<slug>.md` and is served at `/logs/<slug>/`.
- Artifacts for that log live in `/artifacts/<slug>/`.

---

## Automation

### 1) RSS → Jekyll import
- Workflow: **`.github/workflows/rss.yml`**
- Pulls the latest Substack entry and writes `_logs/<slug>.md`.
- Extracts hero image (RSS enclosure) when present.
- Normalizes the body (strips duplicate title/author/share blocks and keeps content from the first `<p>` onward).
- Ensures an **empty folder** exists at `artifacts/<slug>/` so you can drop sidecar files.

**Secrets used**
- `SUBSTACK_RSS_URL` (e.g., `https://hallowayfinch.substack.com/feed`)
- `RSS_PROXY_URL` (optional; e.g., `https://rss.fincharchive.com`)

Runs every 30 minutes and also supports manual “Run workflow”.

### 2) Hash & index artifacts
- Workflow: **`.github/workflows/hash-artifacts.yml`**
- Trigger: **on push** to anything under `artifacts/**`.
- Reads each `/artifacts/<slug>/` folder and (re)writes a canonical `metadata.json` with:
  - `file`, `bytes`, `sha256` for each artifact
  - optional audio/image dimensions where available
- Commits only when metadata actually changes.

### 3) GitHub Pages
- Workflow: **`.github/workflows/pages.yml`** (or your repo’s default pages flow)
- Builds the Jekyll site and publishes to `fincharchive.com`.

---

## How to add a new artifact

1. Find the slug of the target log (e.g., `_logs/the-voice-in-the-static.md` → slug is `the-voice-in-the-static`).
2. Place files into `artifacts/the-voice-in-the-static/` (any of: `.wav .flac .mp3 .pdf .jpg .jpeg .png .gif .webp`).
3. Push your commit.  
   The **Hash & Index Artifacts** workflow will regenerate `metadata.json`.

Artifacts are listed automatically on the log page (layout `log.html`).

---

## Integrity & verification

Each artifact folder has a machine-readable inventory in `metadata.json` including SHA-256 hashes.

**Example: verify a single file**
```bash
cd artifacts/the-voice-in-the-static
# read expected hash from metadata.json (with jq)
EXPECTED=$(jq -r '.files[] | select(.file=="reversed-audio.mp3") | .sha256' metadata.json)
# compute actual and compare
sha256sum reversed-audio.mp3 | awk '{print $1}' | grep -qi "^$EXPECTED$"   && echo "✓ OK" || echo "✗ MISMATCH"
```

No `SHA256SUMS.txt` is required—`metadata.json` is the source of truth.

---

## Conventions

- **Slugs / folder names**: derived from the Substack permalink, e.g. `the-voice-in-the-static`.
- **Stable log IDs**: sequential `1022A`, `1022B`, … (stored in front matter as `log_id`).
- **Dates**: ISO-8601 with timezone in front matter (Jekyll formats on render).
- **Artifact filenames**: concise kebab-case; include meaningful hints when useful  
  e.g. `voice-in-static_reversed.mp3`, `cassette-label.jpg`.

Front matter for a typical log:
```yaml
---
layout: log
title: "The Voice in the Static"
log_id: "1022A"
date: "2025-10-23T03:22:15-05:00"
source_url: "https://hallowayfinch.substack.com/p/the-voice-in-the-static"
guid: "https://hallowayfinch.substack.com/p/the-voice-in-the-static"
permalink: "/logs/the-voice-in-the-static/"
hero_image: "https://.../header.png" # when present in RSS
artifacts:
  - path: "/artifacts/the-voice-in-the-static/reversed-audio.mp3"
    label: "Reversed audio (MP3)"
---
```

---

## Local development

- This site is built by GitHub Pages, but you can preview locally:
  ```bash
  bundle install
  bundle exec jekyll serve
  ```
- The importer is Python 3.11:
  ```bash
  SUBSTACK_RSS_URL="https://hallowayfinch.substack.com/feed"   python scripts/rss_to_repo.py
  ```

---

## License

All written and audio materials © Halloway Finch.  
Distributed under **CC BY-NC-ND 4.0** (Attribution–NonCommercial–NoDerivatives).  
See [`LICENSE`](LICENSE).

---

## Contact

**Halloway Finch** — h@hallowayfinch.com  
Recovered notes from incomplete transmissions.
