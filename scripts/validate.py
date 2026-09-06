#!/usr/bin/env python3
"""Repository invariants; complements each host's plugin validator."""
import json
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?")


def validate(root):
    manifests = [json.loads((root / folder / "plugin.json").read_text())
                 for folder in (".claude-plugin", ".codex-plugin")]
    for manifest in manifests:
        assert manifest["name"] == "chronista-style", "Unexpected plugin name"
        assert SEMVER.fullmatch(manifest["version"]), "Invalid plugin version"
    for key in ("name", "version", "description", "author", "repository", "homepage", "keywords", "license"):
        assert manifests[0].get(key) == manifests[1].get(key), f"Manifest mismatch: {key}; run scripts/sync-manifests.py"
    assert manifests[1]["skills"] == "./skills/", "Codex must use shared skills"
    for manifest in manifests:
        assert not manifest.get("mcpServers"), "Personal MCP config must not be bundled"
    skills = sorted((root / "skills").glob("*/SKILL.md"))
    assert len(skills) == 11, "Expected 11 shared skills"
    for path in skills:
        parts = path.read_text().split("---", 2)
        assert len(parts) == 3 and not parts[0], f"Missing frontmatter: {path}"
        fm = yaml.safe_load(parts[1])
        assert fm["name"] == path.parent.name, f"Skill name mismatch: {path}"
        assert isinstance(fm["description"], str) and fm["description"].strip(), path
        assert set(fm) <= {"name", "description", "metadata", "license", "allowed-tools"}, path
        assert SEMVER.fullmatch(fm["metadata"]["version"]), path
        assert all(isinstance(v, str) for v in fm["metadata"].values()), path
    markdown = [root / "README.md", *skills, *(root / "skills").rglob("reference/*.md"),
                *(root / "commands").glob("*.md"), *(root / "docs").rglob("*.md")]
    for path in markdown:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if "://" in target or target.startswith("#"):
                continue
            resolved = (path.parent / target.split("#")[0]).resolve()
            assert resolved.is_relative_to(root.resolve()) and resolved.exists(), f"Broken local reference: {path}: {target}"
    hooks = json.loads((root / "hooks/hooks.json").read_text())["hooks"]
    for event in ("SessionStart", "Stop"):
        for group in hooks[event]:
            for handler in group["hooks"]:
                assert handler["type"] == "command", "Only shared command hooks supported"
                for target in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"]+)", handler["command"]):
                    assert (root / target).is_file(), target


if __name__ == "__main__":
    validate(ROOT)
    print("Manifests, 11 skills, hook paths and local references validated.")
