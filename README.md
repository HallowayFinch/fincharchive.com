# Finch Archive

Recovered notes from incomplete transmissions.

This repository is the canonical archive for **Halloway Finch**.  
It hosts public logs, recovered media artifacts, and integrity data that together form the public record at **fincharchive.com**.

---

## Structure
```
/logs/         → individual recovered logs (one file per log)
/artifacts/    → supporting media & metadata (audio, images, hashes)
index.md       → site home
.nojekyll      → disable Jekyll so raw files serve unchanged
```

---

## How to Browse
- **Logs:** see `/logs/` (e.g., `log-1022a.md`)  
- **Artifacts:** see `/artifacts/` with per-log folders (e.g., `/artifacts/log-1022a/`)  
- **Integrity:** each artifact folder includes a `SHA256SUMS.txt` for verification  

---

## Conventions
- **Log file names:** `log-<id>.md` (e.g., `log-1022a.md`)  
- **Timestamps:** 24-hour format `HH:MM:SS.mmm` when relevant  
- **Artifact naming:** concise kebab-case (e.g., `you-heard-it_rev_10m22s.mp3`)  
- **Checksum algorithm:** SHA-256 recorded in `SHA256SUMS.txt`  
- **Metadata:** Each artifact folder includes a `metadata.json` for machine-readable context  

---

## Integrity and Verification
To verify an artifact’s integrity:

```bash
cd artifacts/log-1022a
shasum -a 256 -c SHA256SUMS.txt
```

A “✓ OK” result confirms the file matches the official archive hash.

---

## License
All written and audio materials © Halloway Finch.  
Distributed under the Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License (CC BY-NC-ND 4.0).  
See [`LICENSE`](LICENSE) for details.

---

## Contact
**Halloway Finch**  
📧 h@hallowayfinch.com

Recovered notes from incomplete transmissions.
