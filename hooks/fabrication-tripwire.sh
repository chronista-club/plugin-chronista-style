#!/usr/bin/env bash
# Shared Claude Code / Codex Stop hook. Missing runtime or script: fail open.
set -uo pipefail
command -v python3 >/dev/null 2>&1 || exit 0
hook_dir="$(cd "$(dirname "$0")" && pwd)" || exit 0
PYTHONDONTWRITEBYTECODE=1 python3 "$hook_dir/fabrication-tripwire.py" || true
