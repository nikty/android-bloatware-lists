#!/usr/bin/env python3
"""Migrate bloatware/*.yaml entries from old removal scale to new scale,
and drop the `list:` field.

Old -> new mapping:
  recommended -> safe
  advanced    -> caution
  expert      -> risky
  unsafe      -> critical
  unknown     -> unknown (unchanged)

The `list:` field is dropped entirely.

Usage: python3 scripts/migrate_removal_scale.py [--dry-run]
"""
import glob
import os
import re
import sys

BLOATWARE_DIR = "bloatware"

REMOVAL_MAP = {
    "recommended": "safe",
    "advanced": "caution",
    "expert": "risky",
    "unsafe": "critical",
    "unknown": "unknown",
}


def migrate_file(path, dry_run=False):
    with open(path) as f:
        lines = f.readlines()

    new_lines = []
    changed = False
    stats = {"removal_renamed": 0, "list_dropped": 0}

    for line in lines:
        m = re.match(r"^  removal:\s*(\S+)\s*$", line)
        if m:
            old_val = m.group(1)
            new_val = REMOVAL_MAP.get(old_val, old_val)
            if new_val != old_val:
                new_lines.append(f"  removal: {new_val}\n")
                changed = True
                stats["removal_renamed"] += 1
            else:
                new_lines.append(line)
            continue

        if re.match(r"^  list:\s*\S+\s*$", line):
            changed = True
            stats["list_dropped"] += 1
            continue

        new_lines.append(line)

    if changed and not dry_run:
        with open(path, "w") as f:
            f.writelines(new_lines)

    return changed, stats


def main():
    dry_run = "--dry-run" in sys.argv

    files = sorted(glob.glob(os.path.join(BLOATWARE_DIR, "*.yaml")))
    total_files = 0
    total_renamed = 0
    total_dropped = 0

    for path in files:
        changed, stats = migrate_file(path, dry_run)
        if changed:
            total_files += 1
            total_renamed += stats["removal_renamed"]
            total_dropped += stats["list_dropped"]

    mode = "[DRY RUN] " if dry_run else ""
    print(f"{mode}Would modify {total_files} files:")
    print(f"  removal values renamed: {total_renamed}")
    print(f"  list: fields dropped:   {total_dropped}")

    if dry_run:
        print("\nNo files written.")


if __name__ == "__main__":
    main()