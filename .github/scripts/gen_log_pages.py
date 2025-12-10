#!/usr/bin/env python3
# .github/scripts/gen_log_pages.py
"""
Generate paginated /logs/page/N/ index files before Jekyll build.
- Computes total logs by counting files in _logs/
- Creates /logs/page/2..N/index.md with correct front matter
- Removes stale pages beyond N
This runs in the GitHub Pages CI workspace only (no commits needed).
"""

import os, math, pathlib, shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "_logs"
PAGES_ROOT = ROOT / "logs" / "page"

PER_PAGE = int(os.environ.get("LOGS_PER_PAGE", "12"))

def count_logs():
    if not LOG_DIR.exists():
        return 0
    return sum(1 for p in LOG_DIR.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".markdown"})

def write_page(n: int):
    d = PAGES_ROOT / str(n)
    d.mkdir(parents=True, exist_ok=True)
    out = d / "index.md"
    fm = f"""---
layout: logs
title: Logs · Page {n}
permalink: /logs/page/{n}/
page_num: {n}
per_page: {PER_PAGE}
---
"""
    out.write_text(fm, encoding="utf-8")

def cleanup_extra(from_n_plus_one: int):
    if not PAGES_ROOT.exists():
        return
    for child in PAGES_ROOT.iterdir():
        if child.is_dir():
            try:
                pn = int(child.name)
            except ValueError:
                continue
            if pn >= from_n_plus_one:
                shutil.rmtree(child, ignore_errors=True)

def main():
    total_logs = count_logs()
    total_pages = math.ceil(total_logs / PER_PAGE) if total_logs else 1
    # ensure pages 2..N exist (page 1 is /logs/)
    for n in range(2, total_pages + 1):
        write_page(n)
    # remove stale pages beyond N
    cleanup_extra(total_pages + 1)
    print(f"[gen_log_pages] logs={total_logs}, per_page={PER_PAGE}, pages={total_pages}")

if __name__ == "__main__":
    main()