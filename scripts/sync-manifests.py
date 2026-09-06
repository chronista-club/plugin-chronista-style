#!/usr/bin/env python3
"""Sync shared metadata from the Claude manifest; preserve Codex-only fields."""
import argparse
import json
from pathlib import Path

SHARED = ("name", "version", "description", "author", "repository", "homepage", "keywords", "license")


def sync(root, check=False):
    source = json.loads((root / ".claude-plugin/plugin.json").read_text())
    path = root / ".codex-plugin/plugin.json"
    target = json.loads(path.read_text())
    changed = [key for key in SHARED if source.get(key) != target.get(key)]
    if check:
        if changed:
            raise ValueError("Manifest mismatch: " + ", ".join(changed))
        return
    for key in SHARED:
        if key in source:
            target[key] = source[key]
        else:
            target.pop(key, None)
    path.write_text(json.dumps(target, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        sync(Path(__file__).resolve().parents[1], args.check)
    except (OSError, ValueError) as error:
        parser.exit(1, str(error) + "\n")
    print("Manifest metadata matched." if args.check else "Manifest metadata synchronized.")
