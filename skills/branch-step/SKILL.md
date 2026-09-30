---
name: branch-step
description: ブランチ名は「今どの段にいるか」だけを語る。段 = prefix（spike / exp / wip / review）、slug は不変。git next / keep / drop で段を進め、spike はローカル専用。枝を切る・進める・畳むとき、枝名で迷ったときに使う。
metadata:
  version: "1.0.0"
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
| 4 | nightly に積まれた | 枝は消える | nightly（`git branch --contains`） |
| 5 | main に出た | `vX.Y.Z` | main + tag（`git describe`） |
| 6 | 学びを残した | 枝なし | memory |

別列: `exp/<slug>` = 生かしておく実験。掃除と停滞検知の対象外、閉じるのは本人だけ。
例外: `hotfix/<slug>` = main 起点の一列。main へ PR、tag、main を nightly へ back-merge。

slug は起票 memory の Branch slug と同じ（`[a-z0-9-]+`）。worktree のディレクトリ名も slug。
起点は全列 nightly なので名前に載せない。type（feat / fix）は commit message の仕事で、枝名には載せない。

## 操作は三つ

```bash
git next [<slug>] [--memory mem_xxx] [--title "…"] [--no-pr] [--dry-run]
git keep [<slug>]
git drop [<slug>]
```

- **`git next` = 昇格**。`spike/` → `wip/`、`exp/` → `wip/`（どちらも GO の瞬間）、`wip/` → `review/`。
  review に入る時だけ **push して PR を開く**（base は trunk = `nightly`、無ければ `main`。body 冒頭に `--memory` の ID）。
  `wip/` の backup push があれば消して `review/` で押し直す。`review/` から先は rename しない — 直しは PR の中で回す
- **`git keep`**: `spike/` → `exp/`。ここで初めて外に出る（初 push）
- **`git drop`**: `spike/` を削除。無言でよい。`wip/` 以降は消さない
- slug を省くと今いる枝。trunk 上や別の枝からは slug を指定する

### wip → review の門

- `git config branch-step.test '<cmd>'` があればそれを走らせ、exit 0 でなければ進めない。未設定なら「未設定」と告げて通す
- trunk との diff に `docs/` 以外の変更があり `docs/design/` に変更が無ければ**警告**（止めない。設計に触れたかは機械では決めきれない）。`verification` の「設計に触れた変更なら design が同じ枝」はここで思い出す

## 導入

```bash
# 一度だけ（global alias）。--local なら今の repo だけ
bash "$CLAUDE_PLUGIN_ROOT/skills/branch-step/scripts/branch-step" install
```

- `git next` / `keep` / `drop` の alias を書く
- 今いる repo の `.git/hooks/pre-push` に [hook](hooks/pre-push) を置く。`refs/heads/spike/*` の push を拒否する（別名で押すのも、削除は通す）。別の pre-push が既にあれば上書きせず止まる。repo ごとに一度 `install` を走らせる

## 一覧が board

```bash
branch-step board
```

`git for-each-ref` を段の列で並べるだけ。`origin/review/*` = レビュー担当の受信箱、`wip/*` で committerdate が古いもの = 停滞、`spike/*` は月次で気兼ねなく `git branch --list 'spike/*' | xargs git branch -D`（`exp/*` は対象外）。VP はこの一覧を描くだけ。

## やらないこと

- `review/` → `wip/` の rename（PR を draft に戻す）
- `train/<epic>`、expand / migrate / contract の三拍、VP lane 名の変更 — 案のまま design の「未決」に
- release の背骨（nightly → main の merge commit と tag）— `release` スキルが固定点

## 言語について

bash で書いた（style の既定は Ruby）。git subcommand と pre-push hook は runtime 依存を持ち込まないことが要件で、CI も `bash -n` を既に回している。
