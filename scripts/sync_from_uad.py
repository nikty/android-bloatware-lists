#!/usr/bin/env python3
"""Convert UAD-ng uad_lists.json entries missing from our YAML catalog
into our YAML format, grouped by the first two elements of the package ID.

Usage: python3 scripts/sync_from_uad.py [--dry-run]
"""
import json
import glob
import re
import os
import sys
from collections import defaultdict

UAD_PATH = "uad_lists.json"
BLOATWARE_DIR = "bloatware"

REMOVAL_MAP = {
    "Recommended": "safe",
    "Advanced": "caution",
    "Expert": "risky",
    "Unsafe": "critical",
}


def load_ours():
    ours = {}
    for path in glob.glob(os.path.join(BLOATWARE_DIR, "*.yaml")):
        with open(path) as f:
            content = f.read()
        for block in re.split(r"(?m)^- ", content):
            m = re.search(r"(?m)^  id:\s*(\S+)", block)
            if m:
                ours[m.group(1)] = path
    return ours


def load_uad():
    with open(UAD_PATH) as f:
        return json.load(f)


def make_filename(pid):
    parts = pid.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}.yaml"
    return f"{parts[0]}.yaml"


def main():
    dry_run = "--dry-run" in sys.argv

    ours = load_ours()
    uad = load_uad()

    missing = {pid: uad[pid] for pid in uad if pid not in ours}
    if not missing:
        print("No missing entries. Nothing to do.")
        return

    grouped = defaultdict(list)
    for pid, entry in missing.items():
        grouped[make_filename(pid)].append((pid, entry))

    for fname in grouped:
        grouped[fname].sort(key=lambda x: x[0])

    total = len(missing)
    files = len(grouped)
    print(f"Would add {total} entries across {files} files:")

    new_files = []
    for fname in sorted(grouped):
        entries = grouped[fname]
        target = os.path.join(BLOATWARE_DIR, fname)
        exists = os.path.exists(target)
        status = "append" if exists else "new"
        print(f"  {fname}: {len(entries)} entries ({status})")
        if not exists:
            new_files.append(fname)

    if new_files:
        print(f"\nNew files ({len(new_files)}):")
        for f in new_files:
            print(f"  {f}")

    if dry_run:
        print("\n[Dry run] No files written.")
        return

    for fname, entries in grouped.items():
        target = os.path.join(BLOATWARE_DIR, fname)
        mode = "a" if os.path.exists(target) else "w"

        if mode == "a":
            with open(target) as f:
                content = f.read()
            if content and not content.endswith("\n"):
                with open(target, "a") as f:
                    f.write("\n")

        with open(target, mode) as f:
            for pid, entry in entries:
                removal = REMOVAL_MAP.get(entry.get("removal", ""), "unknown")
                desc = entry.get("description", "").strip()
                lst = entry.get("list", "")

                f.write(f"- description: |-\n")
                for line in desc.split("\n"):
                    f.write(f"    {line}\n")
                f.write(f"  id: {pid}\n")
                f.write(f"  removal: {removal}\n")
                f.write(f"  list: {lst}\n")
                f.write("\n")

    print(f"\nDone. Added {total} entries to {files} files.")


if __name__ == "__main__":
    main()