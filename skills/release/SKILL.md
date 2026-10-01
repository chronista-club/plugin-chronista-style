---
name: release
description: リリースの背骨 — 版の検出・CHANGELOG・release commit・nightly → main・tag・GitHub Release。尻尾（CI / publish / 署名 / 配置）はプロジェクト側に委譲
metadata:
  version: "1.0.1"
---

# Release

記憶操作の前に [creo-memories の接続と未接続時の扱い](../chronista-style/reference/memory-connection.md) を読む。以下の記憶手順は、対応ツールが利用できる場合に実行する。

リリースの**背骨**だけを担う。tag や main への push の**後に起きること**（CI、image、publish、署名、配置）は**尻尾**としてプロジェクト側に委譲する。背骨は全プロジェクト共通、尻尾は全部違う。

## 背骨

### 1. 現在地と形式を読む

聞かずに全部読む。

- **版の正本**: `.claude-plugin/plugin.json` / `.codex-plugin/plugin.json`（プラグイン。両方あればリポジトリの同期規約を読み、同じ版を維持）/ `Cargo.toml`（`workspace.package.version` か `package.version`）/ `package.json`（monorepo なら package ごと）/ Swift アプリは tag が正本（`git describe --tags` で読む設計なら、tag を打つこと自体が版付け）
- **trunk モデル**: `nightly` ブランチがあり今そこにいるなら **nightly モデル**（nightly → main を merge して main で tag）。無ければ **main モデル**（今のブランチで tag）
- **前提**: working tree が clean、trunk の最新（`git pull`）。満たさなければ止まって報告
- **前提（worktree）**: `git worktree list --porcelain` で、trunk と main を**どの worktree が checkout しているか**を見る。**今いる worktree が trunk を持っていなければ止まる** — 「release は trunk を checkout している worktree（lead）で行う」と案内して終える。lane（linked worktree）から release すると、lead が持つ枝の checkout を git が拒む。その回避に **`core.bare` を触る / `--ignore-other-worktrees` / `--force` / `git worktree remove` を使わない**（共有 config の `core.bare = true` は lead の作業ツリーを取り残し、status / diff / pull が全部壊れる。creo-memories 2026-10-01 の事故）
- **直前のリリース**: `git tag --sort=-creatordate | head -1`、差分は `git log <tag>..HEAD --oneline`。release commit の流儀も直前のものに合わせる（`release: vX.Y.Z — 要約` が既定。`chore(release): X.Y.Z — 要約` の流儀ならそれに）
- **CI の起点**: `.github/workflows/*.yml` の `on:` を読む。`tags: ['v*']` があれば tag の push が尻尾を起動する。`branches: [main]` で tag を打つ workflow（`release-tag.yml` 等）があれば **自分では tag を打たない**
- **尻尾の有無**: 下記「尻尾の検出」

### 2. 版を決め、一度だけ確認する

- 呼び出し時にユーザーが指定した版があればそれ。無ければ差分 commit から semver を提案 — `feat:` → MINOR、`fix:` / `chore:` のみ → PATCH、`BREAKING` / `!:` → MAJOR。pre-release（`-alpha` / `-beta` / `-rc`）も可
- プラグイン形式なら、`git diff <tag>..HEAD --name-only -- 'skills/*/SKILL.md'` で変更のあったスキルを列挙し、frontmatter の `metadata.version`（旧形式では `version`） が上がっていないものを patch bump の提案に含める
- **確認は 1 回**。提案版、変更スキル、release commit の文言、nightly → main の merge と push、tag、GitHub Release、起動される CI と尻尾 — この全部を一つの提示にまとめて GO をもらう。GO の後は最後まで聞かない

### 3. 書く

- **CHANGELOG**: `CHANGELOG.md` があれば `[Unreleased]` を `[X.Y.Z] - YYYY-MM-DD` に切り替え、新しい空の `[Unreleased]` を上に置く。**無ければ作らない** — プロジェクトが持たない流儀に押し付けない。その場合は GitHub Release の notes に差分 commit の要約を書く
- **版の書き換え**: 正本のファイル。Rust なら `Cargo.lock` も追随させる（`cargo update -w` か build）。プラグインなら変更スキルの `metadata.version`（旧形式では `version`） も
- **両環境対応プラグイン**: `scripts/sync-manifests.py` があれば実行し、`scripts/validate.py` と hook テストを通す。公開版にはローカル用の `+codex.*` cachebuster を含めない。
- **release commit**: `release: vX.Y.Z — <主要変更の 1 行要約>`（流儀が違えば合わせる）

### 4. main に載せて tag を打つ

**nightly モデル**。先に `git worktree list --porcelain` で main を持つ worktree を見る。別の worktree が main を持っていればそこで行う（lead でなければ止まる）。どこにも無ければ lead で `git checkout main` するか、lead の枝を動かさずに **main 専用の worktree を切る**（`git worktree add <tmp> main` → その中で merge / tag / push → `git worktree remove <tmp>`）。回避手段は前提と同じく使わない。

```bash
git worktree list --porcelain | grep -B2 'refs/heads/main$'   # main を持つ worktree が無いこと
git checkout main && git pull
git merge --no-ff nightly -m "Merge nightly into main — release vX.Y.Z"
git tag vX.Y.Z                  # lightweight。-a は使わない
git push origin main nightly vX.Y.Z
git checkout nightly
```

squash はしない。squash すると履歴が発散し、次回のリリースで全面コンフリクトする。

**main モデル**: 今のブランチで `git tag vX.Y.Z` → `git push origin <branch> vX.Y.Z`。

**CI が main への push で tag を打つプロジェクト**: merge と push で終わり。自分では打たない。

**Tag Verify Gate**（tag を打った直後、必ず）:

```bash
git tag -l vX.Y.Z          # 出力が vX.Y.Z であること
git rev-parse vX.Y.Z       # commit SHA が返ること
git branch --contains vX.Y.Z | grep -q main   # nightly モデルなら main 上にあること
```

失敗したら止まって報告する。`git tag` は既存 tag と衝突すると黙って失敗する。あわせて過去の release commit に tag が欠けていないかを一度見る:

```bash
for v in $(git log --oneline | grep -oE 'release: v[0-9]+\.[0-9]+\.[0-9]+' | awk '{print $2}'); do
  git rev-parse "$v" >/dev/null 2>&1 || echo "MISSING TAG: $v"
done
```

### 5. GitHub Release

```bash
gh release create vX.Y.Z --title "vX.Y.Z — <要約>" --notes-file <CHANGELOG の該当節を書き出したファイル>
```

CHANGELOG が無ければ `--generate-notes`。pre-release なら `--prerelease`。

push で CI が起動する形式なら `gh run list --limit 3` で起動を確認し、結果を待つ必要があるもの（image、publish）は `gh run watch` で見届けて報告する。

### 6. 尻尾へ委譲する

**尻尾の検出**（順に探し、最初に見つかったものを使う）:

1. `mise tasks` に `release` があれば `mise run release`
2. `scripts/release*` があればそれ
3. リポジトリの `AGENTS.md` / `CLAUDE.md` の「Release」節、`.agents/skills/release*/SKILL.md` / `.claude/skills/release*/SKILL.md` に手順があれば、実行環境に該当するものに従う。プラグインのこの共有スキル自身を再帰的に呼ばない

見つかれば実行する。実機を伴うもの（署名、公証、`/Applications` への配置、デバイスへの転送）は実行して結果を報告し、**完了は実機確認待ち**で止める（`verification`）。ユーザーの明示承認が要るもの（本番 deploy、破壊的 migration）は GO をもらった範囲に入っていなければ聞く。

見つからなければ、「push が起動した CI」と「手で残っていること」を報告して終わる。

**プラグイン形式の尻尾**: marketplace の source / ref / version を確認し、pin されていれば配布先の規約に従って更新する。Claude Code は `claude plugin update <name>@<marketplace>` 後に再起動。Codex は実際に登録された配布先から `codex plugin add <name>@<marketplace>` で再インストールし、新しいスレッドで確認する。ローカル開発の cachebuster は配布用コピーだけに付ける。本リポジトリの具体的な手順は [インストールと更新](../../docs/guide/01-installation.md) を参照。

### 7. 締め

- 起票 memory の todo を閉じる（`complete_todo`）。リリース内容は memory に一行
- 最終報告: 版、tag の SHA、GitHub Release の URL、起動した CI、尻尾の結果、実機確認待ちのもの

## 尻尾をプロジェクトに置くとき

背骨に分岐を足さない。プロジェクト側に、次のどれかで置く:

- `mise.toml` の `[tasks.release]` — 署名・配置・publish の手順をスクリプトに
- `scripts/release.sh` — 同上
- `.agents/skills/release/SKILL.md` または `.claude/skills/release/SKILL.md` — 手順が対話を伴うとき（実機確認の順番、デバイスの選択）

尻尾は「tag が打たれた後に何をするか」だけを書く。版の決定や CHANGELOG は背骨に任せる。

## やらないこと

- `cargo publish` / `npm publish` を自動で走らせない（尻尾に書かれていれば別）
- annotated tag（`-a`）を使わない
- CHANGELOG を持たないプロジェクトに CHANGELOG を作らない
- 確認を複数回に分けない。2 で一度だけ
