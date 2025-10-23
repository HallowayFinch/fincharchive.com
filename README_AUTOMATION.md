# Finch Automation Package

This bundle turns **Substack** into your single publish point and keeps **fincharchive.com** updated automatically with:

- Pretty permalinks matching Substack slugs (e.g., `/logs/the-voice-in-the-static/`)
- Stable **Log IDs** for indexing/aliasing (e.g., `Log 1022A`) with a redirect `/logs/log-1022a/ → /logs/the-voice-in-the-static/`
- Full‑text capture (for timestamped copyright evidence)
- Artifact hashing (SHA‑256) and optional audio metadata via ffprobe
- Auto‑generated `/logs/index.html`

## Install

1. Copy the contents of this folder **into the root of your repo** (merge/overwrite).
2. Commit and push.
3. In GitHub → **Actions**, run **RSS → Repo (Substack sync)** once manually to seed.

## Configure

- **`SUBSTACK_RSS_URL`** is set in `.github/workflows/rss-sync.yml`. Change if your feed differs.
- **`SITE_BASE_URL`** is used for canonical URLs (default `https://fincharchive.com`).

## Usage

- Publish on Substack → the action imports new posts, assigns the next Log ID, creates
  `/logs/<substack-slug>/` + alias redirect `/logs/log-1022x/`, and updates `/logs/index.html`.
- Drop any files into `artifacts/log-1022x/` → on push, **Hash & Index Artifacts** builds an `artifacts.json` manifest.
- The pretty page will display artifact details on the next RSS sync run (or you can re-run it anytime).

## Notes

- Log IDs increment A, B, … Z, AA, AB, … in `.finch/state.json`.
- If a Substack slug already exists, a suffix `-2`, `-3`, … is added automatically.
- Pages are static—ideal for GitHub Pages. No server rewrites required.
- Styling is intentionally minimal and aligned to the Black‑Box Archive vibe.

_Last generated: 2025-10-23T14:33:41.879884Z_
