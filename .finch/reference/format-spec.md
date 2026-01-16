# Submission & Formatting Spec
*Internal reference — not for publication*

This spec defines the **canonical formatting rules** for Finch Archive materials.
It supports consistency across writing and automation.

---

## 1) Document types

### A) Logs
- Location: `_logs/<slug>.md`
- Published URL: `/logs/<slug>/`
- Target length: **950–1,100 words**
- Must end with: **`[End of recovered material]`**

### B) Field Notes
- Location: `_field-notes/<slug>.md`
- Published URL: `/field-notes/<slug>/`
- Target length: **250–450 words**
- Must end with: **`[End of recovered material]`**

---

## 2) Required front matter (Logs)

```yaml
---
layout: log
title: "TITLE"
log_id: "1022X"
date: "YYYY-MM-DDTHH:MM:SS+00:00"
source_url: "https://www.hallowayfinch.com/p/..."
guid: "/p/..."
permalink: "/logs/<slug>/"
---