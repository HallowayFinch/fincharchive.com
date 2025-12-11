# Finch Archive

Recovered notes from incomplete transmissions.

This repository is the canonical archive for **Halloway Finch** and deploys **https://fincharchive.com**.  
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