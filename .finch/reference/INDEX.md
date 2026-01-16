# Reference Index
*Internal reference — not for publication*

This index is the “resume” of the Finch Archive production system.
Use it to find the right doc fast and keep the reference set from drifting.

---

## Core (read most often)

| Doc | Purpose | When to use | Update trigger |
|-----|---------|-------------|----------------|
| `story-bible.md` | High-level premise, pillars, and the Archive stance | When re-centering tone or adding new foundational concepts | Major canon decisions |
| `voice-style-guide.md` | How Finch sounds; stylistic guardrails | Before drafting any Log/Field Note | When voice evolves |
| `format-spec.md` | Required metadata and formatting rules | When publishing or changing layouts/automation expectations | Any format change |
| `continuity-checklist.md` | Preflight checklist for every Log | Immediately before publishing | Rare |

---

## Canon & continuity (update as the archive grows)

| Doc | Purpose | When to use | Update trigger |
|-----|---------|-------------|----------------|
| `canon-ledger.md` | Single source of truth: pillars, rules, motifs, established facts | After publishing/importing a Log | New canon fact / constraint |
| `lexicon.md` | Canon terminology and consistent usage | When introducing a new recurring term | New term becomes “repeatable” |
| `timeline.md` | Publication vs recovery chronology; contradictions register | When new provenance or conflicts appear | Any contradiction or “fixed point” |
| `continuity-log.md` | Changelog of canon decisions (retcons, standardizations) | When you correct or formalize a decision | Any canon/format decision |

---

## World scaffolding

| Doc | Purpose | When to use | Update trigger |
|-----|---------|-------------|----------------|
| `sites-and-recoveries.md` | Quick index of locations and recovered material | When adding a new site reference | New site introduced |
| `locations-dossier.md` | Deep “site sheets” (sensory anchors, failure modes) | When a site will recur or needs a signature | Second appearance of a site |
| `characters-and-entities.md` | Finch baseline + Archive/Daemon constraints | When tempted to “explain” or escalate | Any new systemic behavior |

---

## Meta layers

| Doc | Purpose | When to use | Update trigger |
|-----|---------|-------------|----------------|
| `puzzle-layer.md` | Diegetic puzzle architecture (optional layer) | When planning ARG-style discovery | When puzzle tier escalates |

---

## Templates

| Path | Purpose |
|------|---------|
| `templates/log-template.md` | Starter structure for Logs |
| `templates/field-note-template.md` | Starter structure for Field Notes |

---

## Planning (outside /reference)

| Path | Purpose |
|------|---------|
| `../planning/arc-map.md` | Phased escalation steering doc |

---

## Authority rule (prevents drift)

- If two docs appear to conflict:
  1. **Format conflicts:** `format-spec.md` wins.
  2. **Canon conflicts:** `canon-ledger.md` wins.
  3. **Voice conflicts:** `voice-style-guide.md` wins.
  4. Record the decision in `continuity-log.md`.

[End of recovered material]