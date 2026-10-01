---
name: branch-step
description: ブランチ名は「今どの段にいるか」だけを語る。段 = prefix（spike / exp / wip / review）、slug は不変。git next / keep / drop で段を進め、spike はローカル専用。枝を切る・進める・PR を開く・畳むとき、枝名で迷ったときに使う。
metadata:
  version: "1.0.2"
  tags: "git, branch, workflow, parallel-dev, kanban"
  source: "mem_1CfZvzMGQyyyQJLqyZMyR8 (設計と裁定), mem_1CfZz3aDDKfmVm7uRs6w9Z (図)"
---

# Branch Step — 段 = prefix、slug は不変

> **名前は看板ではなくカンバンの列。** 一つの仕事に一つの slug。変わるのは今いる段だけ。

設計の本文は [design 02](../../docs/design/02-branch-step-naming.md)。ここは使い方。

## 段と語り手

| 段 | 何をしている | 名前 | 語り手 |
|---|---|---|---|
| 0 | 思いついた。コード無し | 枝なし | memory |
| 1 | 探っている。捨ててよい | `spike/<slug>` | 枝（**ローカル専用**） |
| 2 | 作っている | `wip/<slug>` | 枝 |
| 3 | 見せている。PR が開いている | `review/<slug>` | 枝 + PR |
| 4 | nightly に積まれた | 枝は消える | nightly（`git branch --contains`）。`gh pr merge --squash --delete-branch` → worktree を畳む → `git worktree prune` |
| 5 | main に出た | `vX.Y.Z` | main + tag（`git describe`）。nightly → main は `release` スキル（merge commit `--no-ff`）。**release は trunk を checkout している lead で行う**。lane からは出さない |
| 6 | 学びを残した | 枝なし | memory |

別列: `exp/<slug>` = 生かしておく実験。掃除と停滞検知の対象外、閉じるのは本人だけ。
例外: `hotfix/<slug>` = main 起点の一列。main へ PR、tag、main を nightly へ back-merge。

slug は起票 memory の Branch slug と同じ（`[a-z0-9-]+`、完全一致で探す）。worktree のディレクトリ名も slug。stack 形（`<段>/<epic>/<part>`）は未決なので script は扱わない。
起点は全列 nightly なので名前に載せない。type（feat / fix）は commit message の仕事で、枝名には載せない。

## 操作は三つ

```bash
git next [<slug>] [--memory mem_xxx] [--title "…"] [--no-pr] [--print-pr]
git keep [<slug>]
git drop [<slug>]
git board
```

- **`git next` = 昇格**。`spike/` → `wip/`、`exp/` → `wip/`（どちらも GO の瞬間）、`wip/` → `review/`。
  review に入る時だけ **push して PR を開く**（base は trunk = `nightly`。local に無くても origin にあれば nightly、どちらにも無ければ `main`。body 冒頭に `--memory` の ID）。
  順序は **push が先、rename が後**。push が失敗しても local の名前は変わらない。`wip/` の backup push があれば消して `review/` で押し直す。`review/` から先は rename しない — 直しは PR の中で回す。
  `--print-pr` は `gh` を呼ばず PR コマンドを印字する（push と rename は行う。本物の dry-run ではない）。
  `gh pr create` に失敗しても枝は `review/` のまま残り、手で打つコマンドが出る。もう一度 `git next --memory` すれば PR 作成だけやり直す
- **`git keep`**: `spike/` → `exp/`。ここで初めて外に出る（初 push。失敗したら `spike/` に名前を戻す）
- **`git drop`**: `spike/` を削除。無言でよい。`wip/` 以降は消さない。未 commit の変更があれば止まる（捨てるなら stash、残すなら commit して `git keep`）
- slug を省くと今いる枝。trunk 上や別の枝からは slug を指定する。`git drop` を linked worktree の中で使うと、その worktree は detached になる（あとで `git worktree remove`）

### wip → review の門

- `git config branch-step.test '<cmd>'` があればそれを走らせ、exit 0 でなければ進めない。未設定なら「未設定」と告げて通す。テストは**その枝が checkout されている worktree の中**で走る。どこにも checkout されていない、または未 commit の変更があれば止まる（検査した中身と push する中身を同じにする）。git が `!` alias の子に渡す `GIT_DIR` / `GIT_PREFIX` 等は script の先頭で剥がすので、テストが一時 repo を作って git を呼んでも本物の repo には触れない
- PR を開くなら `gh` の存在と認証を push より前に確かめる（PR の無い `review/` を残さない）
- trunk との diff に `docs/` 以外の変更があり `docs/design/` に変更が無ければ**警告**（止めない。設計に触れたかは機械では決めきれない）。`verification` の「設計に触れた変更なら design が同じ枝」はここで思い出す

## 導入

```bash
# repo ごとに一度（alias も hook も今の repo だけ）
bash "${CLAUDE_PLUGIN_ROOT}/skills/branch-step/scripts/branch-step" install
# alias だけ入れる（hook は repo 側で管理する repo）
bash "${CLAUDE_PLUGIN_ROOT}/skills/branch-step/scripts/branch-step" install --no-hook
```

- `git next` / `keep` / `drop` / `board` の alias を今の repo に書く。alias は script の絶対パス（plugin の版ごとのディレクトリ）を指すので、**plugin を更新したら `install` をやり直す**。`--global` は全 repo に効き、更新で全 repo が壊れうるので、agent は mako に確認してから
- 今いる repo の pre-push（`git rev-parse --git-path hooks`。`core.hooksPath` を尊重）に [hook](hooks/pre-push) を置く。`refs/heads/spike/*` の push を拒否する（`spike/x:wip/x` や `HEAD:wip/x` の別名も拒否、削除は通す）。`<sha>:refs/heads/…` のように sha を直に指す push は止められない（仕様。`spike/x~0:` のような revision 式は止める）。repo ごとに一度 `install` を走らせる
- **既存の別 pre-push がある repo**（`core.hooksPath = .githooks` で dispatcher を持つ等）では、hook は上書きせず案内だけ出して exit 0（alias は入る）。spike の拒否が要るなら `hooks/pre-push` を dispatcher に vendor する（例: `.githooks/pre-push.d/10-branch-step`）。vendor した hook は plugin の更新で自動では追従しない

## 一覧が board

```bash
git board
```

`git for-each-ref` を段の列で並べるだけ。`origin/review/*` = レビュー担当の受信箱、`wip/*` で committerdate が古いもの = 停滞、`spike/*` は月次で気兼ねなく消す（`exp/*` は対象外）:

```bash
git for-each-ref --format='%(refname:short)' refs/heads/spike/ | xargs -r git branch -D
```

`git push --all` は spike が 1 本でもあると hook が push 全体を止める。押すなら枝を指定する。VP はこの一覧を描くだけ。

## やらないこと

- `review/` → `wip/` の rename（PR を draft に戻す）
- `train/<epic>`、expand / migrate / contract の三拍、VP lane 名の変更 — 案のまま design の「未決」に
- release の背骨（nightly → main の merge commit と tag）— `release` スキルが固定点

## 言語について

bash で書いた（style の既定は Ruby）。git subcommand と pre-push hook は runtime 依存を持ち込まないことが要件。構文は `tests/test_branch_step.py` の `test_scripts_parse` が見る。
