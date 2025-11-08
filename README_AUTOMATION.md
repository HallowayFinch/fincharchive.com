# Finch Archive Automation Workflows

This document explains how the Finch Archive automations work together to keep the Substack feed, Jekyll site, icons, and artifact system in sync.

---

## 🧠 Overview

The Finch Archive repository runs a coordinated set of GitHub Actions that automatically:
- Pull new posts from Substack via RSS.
- Convert them into Markdown (`_logs/`) and generate the Jekyll site (`/logs/`).
- Manage, hash, and verify supporting files in `/artifacts/`.
- Generate and maintain favicon and PWA icon assets.
- Validate content structure, metadata, and links to ensure archival integrity.

---

## ⚙️ Workflow Summary

### **1. RSS → Repo (Substack Sync)**
**Purpose:** Imports new Substack posts into the Finch Archive.

**Runs:**
- Every hour at `:22` past the hour.
- On manual trigger (`Run workflow`).

**Steps:**
1. Fetches Substack RSS feed (`https://www.hallowayfinch.com/feed`).
2. Converts new posts into `_logs/{slug}.md` files.
3. Creates matching `/logs/{slug}/` pages for Jekyll.
4. Sets up `/artifacts/{slug}/` directories for attachments.
5. Updates `.finch/state.json` to record imported posts.
6. Triggers the site rebuild workflow **only if** new content was imported (to avoid redundant builds).

**Safe to delete before running:**
- `_logs/*`
- `/artifacts/*`
- `.finch/state.json`
*(All will be regenerated automatically.)*

---

### **2. Hash & Index Artifacts**
**Purpose:** Verifies integrity of archived media and ensures all metadata is up to date.

**Triggers:**
- When any file within `/artifacts/` changes.

**Steps:**
1. Scans `/artifacts/` for all supported formats (`.wav`, `.flac`, `.mp3`, `.png`, `.pdf`, `.txt`, etc.).
2. Computes SHA‑256 hashes for every artifact.
3. Writes or updates `metadata.json` with file size, hash, and modification time.
4. Updates `SHA256SUMS.txt` and the `/logs/index.json` machine‑readable manifest.

**When to run manually:**
- After adding or replacing artifacts.
- After performing a cleanup or manual reorganization.

---

### **3. Build Icons**
**Purpose:** Automatically regenerates raster icons, webmanifest, and favicon sets from the canonical Finch SVG.

**Triggers:**
- When `assets/icons/finch.svg` changes.
- On manual trigger (`Run workflow`).

**Steps:**
1. Uses ImageMagick to generate:
   - `favicon-16/32/48/180/192/256/384/512.png`
   - `apple-touch-icon.png`
   - `android-chrome-192x192.png`, `android-chrome-512x512.png`
   - `favicon.ico`
2. Updates `site.webmanifest` automatically with correct references.
3. Commits and pushes the new icons to `main`.
4. Optionally creates or updates `safari-pinned-tab.svg` if a `finch-pinned.svg` file exists.

**Notes:**
- The workflow runs under the `HallowayFinch` user to show daily GitHub activity.
- All generated assets are version‑busted automatically via `?v={ site.time | date: '%s' }` to avoid browser cache issues.

---

### **4. Verify & Publish Badge**
**Purpose:** Validates site integrity and updates repository status badge.

**Runs:**
- Automatically after each content or artifact change.

**Checks performed:**
- Confirms every `_logs/*.md` file includes header metadata and required separators.
- Verifies every artifact referenced in logs exists and hashes correctly.
- Updates the `/status/` badge and commits any resulting changes.

---

## 🧩 Environment Variables (Secrets)

| Secret | Description | Example |
|--------|--------------|----------|
| `SUBSTACK_RSS_URL` | Full Substack RSS feed URL | `https://www.hallowayfinch.com/feed` |
| `RSS_PROXY_URL` | Optional proxy or caching endpoint | `https://rss.fincharchive.com` |
| `HF_PAT` | Personal access token for commits from the Finch automation user | `ghp_••••••••••••` |
| `HF_NOREPLY_EMAIL` | Email address for Finch automation commits | `actions@fincharchive.com` |

Secrets are stored under:  
**Settings → Secrets and Variables → Actions → Secrets**

---

## 🧼 Safe‑Delete Rules

| File/Folder | Safe to Delete? | Auto‑Recreated? | Purpose |
|--------------|----------------|-----------------|----------|
| `_logs/*` | ✅ | ✅ | Markdown source logs |
| `/artifacts/*` | ✅ | ✅ | Attachment folders and metadata |
| `.finch/state.json` | ✅ | ✅ | Importer state tracking |
| `/assets/icons/*` | ⚠️ | ✅ (via Build Icons) | Favicons and app icons |
| `.github/workflows/*` | ❌ | ❌ | Core automation logic |
| `/scripts/*` | ❌ | ❌ | Python utilities for import/validation |

---

## 🔄 Recommended Maintenance Flow

1. **Run “RSS → Repo (Substack Sync)”** → imports new logs from Substack.
2. **Confirm `_logs/` and `/artifacts/` updates.**
3. **Run “Hash & Index Artifacts”** → updates checksums and metadata.
4. **Verify “Build Icons”** (if logo changes) → regenerates favicon set and webmanifest.
5. **Allow “Verify & Publish Badge”** → ensures repo integrity and updates status indicators.
6. **Review `Actions` tab** → confirm all workflows succeeded.

---

## 🧰 Future Enhancements

- Automatic Cloudflare cache purge on new deploys.
- Combined “Full Sync” workflow to run RSS + Hash + Deploy sequentially.
- Archive mirror and checksum verification endpoint (`/verify.json`).
- Optional Slack/Matrix notifications when new logs are imported.

---

_Last updated: November 2025_
