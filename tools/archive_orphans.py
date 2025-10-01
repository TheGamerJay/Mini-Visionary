#!/usr/bin/env python3
"""Archive orphan files detected by audit_project.py"""
import json, shutil, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORT = ROOT / "tools" / "_reports" / "audit.json"
ARCHIVE = ROOT / "backend" / "_archive"
ARCHIVE.mkdir(parents=True, exist_ok=True)

stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
batch_dir = ARCHIVE / f"orphans-{stamp}"
batch_dir.mkdir()

data = json.loads(REPORT.read_text(encoding="utf-8"))
orphans = data.get("orphans", [])

# Exclude files that are actually being used but scanner missed
EXCLUDE_PATTERNS = [
    "logo.png",  # Used in HTML <link rel="icon">
    "favicon",   # Favicons
    "categories/",  # Category images used in gallery
]

filtered_orphans = []
for rel in orphans:
    # Skip if matches exclude pattern
    if any(pattern in rel for pattern in EXCLUDE_PATTERNS):
        print(f"[SKIP] {rel} (likely in use)")
        continue
    filtered_orphans.append(rel)

moved = []
for rel in filtered_orphans:
    src = ROOT / rel
    if src.exists():
        dest = batch_dir / rel.replace("/", "_").replace("\\", "_")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        moved.append(rel)
        print(f"[MOVE] {rel}")

log = ARCHIVE / f"moved-orphans-{stamp}.txt"
log.write_text("\n".join(moved), encoding="utf-8")
print(f"\n[OK] Archived {len(moved)} orphan(s) into {batch_dir}")
print(f"[OK] Skipped {len(orphans) - len(moved)} files (likely in use)")
print(f"[OK] Log: {log}")
