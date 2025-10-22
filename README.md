# Finch Archive

Minimal Jekyll site for **fincharchive.com** — the in‑character home for Halloway Finch.

## Aesthetic
Black background, off‑white text, muted red accent. Serif for titles; monospace body. Tagline:
> Recovered notes from incomplete transmissions.

## Content model
Two Jekyll collections:
- `_logs/` → documentary logs
- `_field-notes/` → field notes

Each item is a Markdown file with YAML front matter.

## Automation (Substack → GitHub)
Have your automation create Markdown files into `_logs/` with front matter like:

```yaml
---
title: Log 1022B — <Title>
date: 2025-10-29 22:22:00 -0500
source: Substack
canonical_url: https://hallowayfinch.substack.com/p/<slug>
---
```

Commit message suggestion:
```
Add {{title}} (via Substack RSS)
```

## GitHub Pages
- This repo is GitHub Pages–ready. No external theme.
- Custom domain is provided via `CNAME` (fincharchive.com).
- Enable Pages in **Settings → Pages** with build from `main` branch (`/root`).