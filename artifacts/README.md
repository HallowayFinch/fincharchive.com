# Artifacts

Each log may include one or more artifacts (audio, images, etc.) stored under a subfolder with the same log identifier.

- Example: `/artifacts/log-1022a/`
- Integrity: each folder includes `SHA256SUMS.txt`.
- Sidecar metadata: `metadata.json` for reproducibility and discovery.

Consumers may programmatically discover artifacts by scanning `/artifacts/*/metadata.json`.
