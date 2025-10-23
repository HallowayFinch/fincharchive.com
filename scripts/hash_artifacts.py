# scripts/hash_artifacts.py
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    for folder in sorted([d for d in ART.glob("*") if d.is_dir()]):
        meta = []
        for f in sorted(folder.iterdir()):
            if f.is_file():
                meta.append({
                    "file": f.name,
                    "bytes": f.stat().st_size,
                    "sha256": sha256_file(f),
                })
        if meta:
            (folder / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
            print(f"[hash-artifacts] wrote {folder/'metadata.json'}")

if __name__ == "__main__":
    main()
