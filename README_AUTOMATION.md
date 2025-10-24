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
- Every 15 minutes (via cron).
- On manual trigger (`Run workflow`).

**What it does:**
1. Fetches the RSS feed from Substack (`https://hallowayfinch.substack.com/feed`).
2. Converts new posts into `_logs/{slug}.md` files.
3. Generates matching `/logs/{slug}/index.html` pages.
4. Creates folders under `/artifacts/{slug}/` if attachments exist.
5. Updates `.finch/state.json` to track known posts and avoid duplicates.

**Safe to delete before running:**  
- `_logs/*`  
- `/logs/*`  
- `/artifacts/*`  
- `.finch/state.json`

*(All will be recreated automatically.)*

---

### **2. RSS → Jekyll Import**
**Purpose:** Validates and cleans the site after import.

**Runs:**
- Every 15 minutes (after Substack sync).
- On manual trigger.

**What it does:**
1. Runs the same RSS importer to confirm structure.
2. Validates Markdown formatting and front matter.
3. Re-hashes artifacts (`hash_artifacts.py`).
4. Commits any metadata or structural corrections.

**When to run manually:**
- After confirming new posts pulled correctly.
- After making edits in `_logs/` or `/artifacts/`.

---

### **3. Hash & Index Artifacts**
**Purpose:** Maintains integrity of supporting assets.

**What it does:**
- Scans `/artifacts/` for `.wav`, `.jpg`, `.png`, `.pdf`, etc.
- Creates or updates `metadata.json` and `SHA256SUMS.txt` files.
- Ensures artifacts are discoverable and verifiable.

**When to run manually:**
- After uploading or replacing any artifact files.
- After a bulk cleanup or reorganization.

---

## 🧩 Environment Variables (Secrets)

| Secret | Description | Example |
|--------|--------------|----------|
| `SUBSTACK_RSS_URL` | Full RSS feed URL | `https://hallowayfinch.substack.com/feed` |
| `RSS_PROXY_URL` | Proxy URL for caching or rate limiting | `https://rss.fincharchive.com` |

Both are stored under:  
**Settings → Secrets and Variables → Actions → Secrets**

---

## 🧼 Safe-Delete Rules

| File/Folder | Safe to Delete? | Auto-Recreated? | Purpose |
|--------------|----------------|-----------------|----------|
| `_logs/*` | ✅ | ✅ | Source Markdown posts |
| `/logs/*` | ✅ | ✅ | Generated HTML pages |
| `/artifacts/*` | ✅ | ✅ | Attachment folders |
| `.finch/state.json` | ✅ | ✅ | RSS import state memory |
| `.github/workflows/rss.yml` | ❌ | ❌ | Main automation logic |
| `/scripts/*` | ❌ | ❌ | Python utilities for import/validation |

---

## 🔄 Typical Maintenance Flow

1. **Run → RSS → Repo (Substack Sync)**  
   → Imports new posts and updates folder structure.

2. **(Optional)** Verify new post appears under `_logs/` and `/logs/`.

3. **Run → RSS → Jekyll Import**  
   → Validates structure, hashes artifacts, commits any corrections.

4. **Run → Hash & Index Artifacts**  
   → (Only if you manually uploaded new files to `/artifacts/`.)

5. **Confirm** the site rebuilds successfully on GitHub Pages.

---

## 🧰 Future Improvements

- Merge RSS → Repo and Jekyll Import into a single chained workflow for efficiency.
- Extend artifact support for `.mp4`, `.txt`, and `.json`.
- Add Slack or email notification when new posts are imported.

---

_Last updated: October 2025_
