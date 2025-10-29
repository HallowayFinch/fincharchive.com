
# Finch Archive Automation Workflows

This document explains how the Finch Archive automations work together to keep the Substack feed, Jekyll site, and artifact system in sync.

---

## 🧠 Overview

The Finch Archive repo is built on a set of coordinated GitHub Actions that automatically:
- Pull new posts from Substack via RSS.
- Convert them into Markdown (`_logs/`) and build the Jekyll site (`/logs/`).
- Manage and checksum supporting files (`/artifacts/`).
- Validate that all content is properly formatted and linked.

---

## ⚙️ Workflows Summary

### **1. RSS → Repo (Substack Sync)**
**Purpose:** Fetches and imports new posts from the Substack RSS feed.

**Runs:**
- Every hour at `:22` past the hour (via cron).
- On manual trigger (`Run workflow`).

**What it does:**
1. Fetches the RSS feed from Substack (`https://www.hallowayfinch.com/feed`).
2. Converts new posts into `_logs/{slug}.md` files.
3. Generates matching `/logs/{slug}/` pages for the site.
4. Creates folders under `/artifacts/{slug}/` for attachments or sidecar files.
5. Updates `.finch/state.json` to track known posts and prevent duplicates.

**Safe to delete before running:**  
- `_logs/*`  
- `/artifacts/*`  
- `.finch/state.json`  

(All will be recreated automatically.)

---

### **2. Hash & Index Artifacts**
**Purpose:** Maintains the integrity of supporting assets and metadata.

**Runs:**
- Automatically when any file changes within `/artifacts/`.

**What it does:**
1. Scans `/artifacts/` for `.wav`, `.jpg`, `.png`, `.pdf`, and other supported types.
2. Computes and updates SHA‑256 checksums for each file.
3. Writes or updates `metadata.json` entries for artifact size and hash.
4. Generates `/logs/index.json` to serve as a machine-readable index of all artifacts.

**When to run manually:**
- After uploading or replacing any artifact files.
- After a bulk cleanup or reorganization.

---

### **3. Site Build & Deployment (Planned)**
**Purpose:** Automatically rebuild and deploy the Finch Archive site to GitHub Pages.

**Planned tasks:**
1. Regenerate site with Jekyll.
2. Deploy to `gh-pages` branch.
3. Optionally clear Cloudflare cache to ensure latest content appears immediately.

---

## 🧩 Environment Variables (Secrets)

| Secret | Description | Example |
|--------|--------------|----------|
| `SUBSTACK_RSS_URL` | Full RSS feed URL | `https://www.hallowayfinch.com/feed` |
| `RSS_PROXY_URL` | Optional proxy or caching endpoint | `https://rss.fincharchive.com` |

Secrets are stored under:  
**Settings → Secrets and Variables → Actions → Secrets**

---

## 🧼 Safe‑Delete Rules

| File/Folder | Safe to Delete? | Auto‑Recreated? | Purpose |
|--------------|----------------|-----------------|----------|
| `_logs/*` | ✅ | ✅ | Source Markdown posts |
| `/artifacts/*` | ✅ | ✅ | Attachment folders and metadata |
| `.finch/state.json` | ✅ | ✅ | RSS importer state memory |
| `.github/workflows/*` | ❌ | ❌ | Core automation logic |
| `/scripts/*` | ❌ | ❌ | Python utilities for import and validation |

---

## 🔄 Typical Maintenance Flow

1. **RSS → Repo (Substack Sync)**  
   → Imports new posts and updates folder structure.

2. **Verify** the new post appears under `_logs/` and `/artifacts/`.

3. **Hash & Index Artifacts**  
   → Updates hashes and metadata for all artifact files.

4. **Confirm** site deployment and index accuracy.

---

## 🧰 Future Enhancements

- Combine the RSS and Hash workflows into a single pipeline.
- Add `.mp4`, `.txt`, and `.json` artifact support.
- Add notification when new posts are imported (email or Slack).
- Automated `gh-pages` deployment and Cloudflare purge integration.

---

_Last updated: October 2025_
