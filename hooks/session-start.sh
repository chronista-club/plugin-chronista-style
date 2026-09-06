#!/usr/bin/env bash
# chronista-style SessionStart hook
# Outputs JSON with additionalContext to inject git project context into Claude Code / Codex initial context.
# Fail-open: on any error, emit empty context and exit 0 (never block the session).

set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0
input="$(cat 2>/dev/null)" || exit 0
# stdin.cwd is the host contract; environment is a legacy fallback.
input_dir="$(printf '%s' "$input" | jq -er '.cwd | select(type == "string" and length > 0)' 2>/dev/null)" || input_dir=""
project_dir="${input_dir:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$project_dir" 2>/dev/null || exit 0

# --- Git context ---
branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || git rev-parse --verify --short HEAD 2>/dev/null || echo "-")
last_commit=$(git log -1 --oneline 2>/dev/null || echo "-")
status_summary=$(git status --porcelain=v1 2>/dev/null | wc -l | tr -d ' ') || status_summary="-"
project_name=$(basename "$project_dir" 2>/dev/null || echo "-")

# --- Atlas candidate detection (convention + git remote hybrid) ---
# Candidate 1: directory basename (as-is)
atlas_candidate_dir="$project_name"

# Candidate 2: directory basename with common prefix stripped
# (e.g., "claude-plugin-chronista-style" → "chronista-style")
atlas_candidate_stripped=$(printf '%s' "$project_name" | sed -E 's/^(claude-plugin-|codex-plugin-|skillset-?|plugin-)//')
if [ "$atlas_candidate_stripped" = "$atlas_candidate_dir" ]; then
  atlas_candidate_stripped=""
fi

# Candidate 3: git remote URL → repo name
remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "")
atlas_candidate_remote=""
if [ -n "$remote_url" ]; then
  # Handle both https://github.com/org/repo(.git) and git@github.com:org/repo(.git)
  # BSD sed compatible: strip .git first, then take last path segment
  atlas_candidate_remote=$(printf '%s' "$remote_url" 2>/dev/null \
    | sed -E 's#\.git$##' 2>/dev/null \
    | awk -F'[:/]' '{print $NF}' 2>/dev/null \
    | sed -E 's/^(claude-plugin-|codex-plugin-|skillset-?|plugin-)//' 2>/dev/null)
  if [ "$atlas_candidate_remote" = "$atlas_candidate_dir" ] || [ "$atlas_candidate_remote" = "$atlas_candidate_stripped" ]; then
    atlas_candidate_remote=""
  fi
fi

# Build candidate lists — primary (directory) takes precedence over fallback (remote)
primary_candidates="$atlas_candidate_dir"
[ -n "$atlas_candidate_stripped" ] && primary_candidates="$primary_candidates / $atlas_candidate_stripped"
fallback_candidates="$atlas_candidate_remote"

# --- Build additionalContext ---
context=$(cat <<EOF
## Chronista Session Context

- Project dir: \`${project_name}\`
- Branch: \`${branch}\`
- Last commit: ${last_commit}
- Uncommitted files: ${status_summary}
- Remote: \`${remote_url:-none}\`

### creo-memories

- Context Engine の記憶コンテキストが実際に届いていれば重複検索は不要。未注入なら、接続済みの creo-memories の \`search\` で必要な記憶だけ補う。未接続なら作業は続け、記憶の取得・保存は未実施と報告する
- \`remember\` / \`create_todo\` の Atlas 候補: \`${primary_candidates}\`（remote 由来: \`${fallback_candidates:-なし}\`）。exact match が無ければ、同じ repo の過去の todo がある Atlas に倣う。前例も無ければ Personal に置いて一言添える。置き場で止まらない、聞かない

### 規律エッセンス（詳細は各スキル）

- テストが先に失敗しない限り、プロダクションコードを書かない（\`tdd\`）
- 根本原因を特定してから修正する（\`systematic-debugging\`）
- 検証の証拠なしに完了を宣言しない。実機でしか確認できないものは「実機確認待ち」で止める（\`verification\`）
- GO の前は自由な構想（Conception）。ユーザーが選ぶべき分岐があるときだけ短い方針提示 → GO。GO の後はその範囲を最後まで走り切る（\`codeflow\`）
- 火花が降ったら \`spark\` スキル — 解釈ゼロで原文のまま pack。作業の範囲外の気づきも同じ
- 穏やかに、真面目に、ユーモアを忘れずに。きつい言葉を使わず、事実は伝える（\`chronista-style\` 基本姿勢）

その他の原則は \`chronista-style\` スキルを参照。
EOF
)

# jq handles quotes, control characters and multiline context for both hosts.
jq -n --arg context "$context" '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $context}}' || true
exit 0
