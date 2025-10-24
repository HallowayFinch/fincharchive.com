# Artifacts

Each recovered log may include one or more **artifacts** — supporting materials such as audio, images, or documents — stored in a dedicated subfolder named after the log’s permalink slug.

---

## Structure

```
/artifacts/
  └─ the-voice-in-the-static/
       ├─ reversed-audio.mp3
       ├─ transcript.pdf
       └─ metadata.json
```

- **Folder name** → matches the Substack permalink slug (`the-voice-in-the-static`)
- **Allowed types** → `.wav`, `.flac`, `.mp3`, `.pdf`, `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- **Metadata** → auto-generated `metadata.json` includes filename, size (bytes), and SHA-256 hash for every artifact

---

## Metadata

Artifacts are automatically hashed and indexed by the **Hash & Index Artifacts** GitHub Action  
(`.github/workflows/hash-artifacts.yml`).

That workflow:
- Monitors this `/artifacts/**` directory for new or changed files
- Rebuilds `metadata.json` for each folder
- Commits the updated metadata automatically

Each `metadata.json` looks like this:

```json
{
  "files": [
    {
      "file": "reversed-audio.mp3",
      "bytes": 102400,
      "sha256": "ab13e6c52d0f8f27eac1c6c8a5e7f8b1d3c2a0..."
    },
    {
      "file": "transcript.pdf",
      "bytes": 204800,
      "sha256": "9f1a4c3b72d8e9d6c1e7c8f9a4d6b5c2e0f1..."
    }
  ],
  "generated_at": "2025-10-24T03:22:00-05:00"
}
```

---

## Verification

To manually verify a file’s integrity:

```bash
cd artifacts/the-voice-in-the-static
jq -r '.files[] | select(.file=="reversed-audio.mp3") | .sha256' metadata.json
sha256sum reversed-audio.mp3
```

If the hashes match, the artifact is verified authentic.

---

## Notes

- Artifacts are never modified after publication.
- The `metadata.json` is the canonical source of integrity data (replaces older `SHA256SUMS.txt`).
- All artifacts are referenced in their parent log’s front matter and rendered on the corresponding `/logs/<slug>/` page.

---

## Example (from `_logs/the-voice-in-the-static.md`)

```yaml
artifacts:
  - path: "/artifacts/the-voice-in-the-static/reversed-audio.mp3"
    label: "Reversed audio (MP3)"
  - path: "/artifacts/the-voice-in-the-static/transcript.pdf"
    label: "Transcript (PDF)"
```

---

**Maintained by**  
**Halloway Finch** · h@hallowayfinch.com  
Recovered notes from incomplete transmissions.
