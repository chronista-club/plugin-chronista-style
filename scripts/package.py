#!/usr/bin/env python3
"""Build a plugin-only ZIP from an explicit file list, never local MCP settings."""
import argparse
from pathlib import Path
import zipfile

from validate import ROOT, validate

FILES = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", "README.md", "LICENSE", "CHANGELOG.md", "requirements-dev.txt", ".mcp.json.example")
TREES = ("skills", "commands", "hooks", "docs", "scripts", "tests", "bin")


def package(root, destination):
    validate(root)
    paths = [root / name for name in FILES]
    for tree in TREES:
        paths.extend(p for p in (root / tree).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    for path in paths:
        assert not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), f"Nonportable package path: {path}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path, Path("chronista-style") / path.relative_to(root))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/chronista-style.zip")
    args = parser.parse_args()
    package(ROOT, args.output)
    print(args.output)
