# 02. ブランチの段 — 段 = prefix、slug は不変

> **Status**: Draft
> **Related**: `mem_1CfZvzMGQyyyQJLqyZMyR8`（Conception と裁定の原文）、`mem_1CfZz3aDDKfmVm7uRs6w9Z`（Mermaid 図 5 枚）、`mem_1Cfa1hzGjo7uen8XuchVQg`（起票）
> **対象**: `skills/branch-step/`, `skills/chronista-style/SKILL.md`（ブランチ運用）, `skills/parallel-dev/SKILL.md`, `skills/codeflow/SKILL.md`, `tests/test_branch_step.py`

## Abstract

ブランチ名は「今どの段にいるか」だけを語る。一つの仕事に一つの slug（起票 memory と同じ、不変）、prefix が段。段が進んだら `git branch -m` で rename する。段ごとに語り手は一人 — PR 以前はブランチ、PR 以後は PR、merge 以後は trunk と tag。起点は全列 nightly なので名前に載せず、名前に載せるのは例外（hotfix）だけ。

固定点は `release` スキルの規約（trunk = `nightly`、`main` は出荷済みだけ、nightly → main は merge commit、lightweight tag）。ここは触らない。

## なぜ（memory から要点だけ）

規約は `{type}/{slug}` だったのに、実態は `{type}/{slug}` / `mako/{slug}`（VP lane）/ `worktree-{name}`（Claude Code worktree）/ `lane/{name}` が混在し、**どこから切ってどこへ帰るブランチかが名前から読めなかった**。`--base nightly` の付け忘れ事故はその症状。裁定の原文は Related の memory に。

## Architecture

### 段

| 段 | 名前 | 語り手 | 起点 | 一括削除 | 閉じ方 |
|---|---|---|---|---|---|
| 探る | `spike/<slug>` | ブランチ | nightly | **対象**（月次） | `wip/` へ昇格 / `exp/` へ / 削除 |
| 育てる | `exp/<slug>` | ブランチ | nightly | 対象外 | 本人だけが閉じる。学びを memory へ |
| 作る | `wip/<slug>` | ブランチ | nightly | 対象外（古いものは停滞） | `review/` へ |
| 見せる | `review/<slug>` | ブランチ + PR | nightly | 対象外 | squash merge で消える |
| 緊急 | `hotfix/<slug>` | ブランチ + PR | **main** | 対象外 | main へ PR、tag、back-merge |

`spike/` は**ローカル専用**。pre-push hook が `refs/heads/spike/*` を拒否する（別名で押すのも拒否、削除は通す）。

### 遷移

```mermaid
flowchart LR
  spike["spike/*<br/>ローカルだけ"] -->|git next| wip["wip/*"]
  spike -->|git keep| exp["exp/*"]
  spike -.->|git drop| x(( ))
  exp -->|git next| wip
  wip -->|"git next: 門 → push + PR"| review["review/*"]
  review -->|"PR(squash), delete-branch"| nightly
  nightly -->|release| main
  main -->|切る| hotfix["hotfix/*"]
  hotfix -->|PR + tag| main
  main -.->|back-merge| nightly
```

nightly 宛て PR の merge は **squash**（裁定 2026-10-01）。`train/` の出発だけは merge commit で部品を残す（未決）。nightly → main は `release` スキルどおり `--no-ff`。

下へ戻る遷移は無い。rename は最大 2 回で、どちらも PR が存在する前。`review/` に入ってからの直しは PR の中で回す（draft に戻すだけ）。

### 操作

| コマンド | 前 → 後 | 副作用 |
|---|---|---|
| `git next` | `spike/` → `wip/` | rename だけ（spike は local） |
| `git next` | `exp/` → `wip/` | push（`exp/x:refs/heads/wip/x`）→ rename → upstream を `origin/wip/x` に → `origin/exp/x` 削除 |
| `git next --memory <id>` | `wip/` → `review/` | gh の存在と認証 → 門 → push（`wip/x:refs/heads/review/x`）→ rename → upstream → `origin/wip/*` 削除 → `gh pr create --base <trunk>`（body 冒頭に memory ID）。PR 作成に失敗したらブランチは残し、次の `git next --memory` が PR 作成だけやり直す |
| `git next` | `review/`（PR あり） | 何もしない。語り手は PR |
| `git keep` | `spike/` → `exp/` | rename → 初 push（spike の ref は hook が拒否するので rename が先。push に失敗したら名前を戻す） |
| `git drop` | `spike/` → 削除 | 未 commit があれば止まる。checkout 中なら trunk へ移ってから `branch -D`。trunk が別 worktree で使われていれば detached にする |

trunk は `refs/heads/nightly` か `refs/remotes/origin/nightly` があれば nightly、どちらも無ければ main。比較（merge-base、PR 本文）には origin 側の ref を優先する。clone 直後で local に nightly が無くても main 宛てにならない。

## Implementation

- 実体は `skills/branch-step/scripts/branch-step`（bash、一つのファイル）。先頭で git が `!` alias の子に注入する `GIT_DIR` / `GIT_WORK_TREE` / `GIT_INDEX_FILE` / `GIT_PREFIX` / `GIT_COMMON_DIR` / `GIT_CONFIG_PARAMETERS` 等を剥がす（`GIT_AUTHOR_*` / `GIT_COMMITTER_*` / `GIT_CONFIG_GLOBAL` / `GIT_CONFIG_NOSYSTEM` / `GIT_SSH*` / `GIT_EDITOR` / `GIT_EXEC_PATH` は残す）。これが無いと別 worktree への `git -C` や門のテストが本物の repo を触る。`install` が `git config --local alias.next '!<path> next'` 等を書き（既定は今の repo だけ。`--global` は明示時のみ）、今いる repo の pre-push（`--git-path hooks`）に `skills/branch-step/hooks/pre-push` をコピーする。既存の別 hook があれば上書きせず案内だけで exit 0、`--no-hook` で alias だけ
- slug の解決: slug は `^[a-z0-9-]+$` に限る（stack 形は未決なので拒否）。引数無しなら今のブランチ（段の列でなければ失敗）。引数ありなら段ごとに `git show-ref --verify` で完全一致を探し、0 件と複数件は失敗。glob や前方一致は使わない（`drop epic` が `spike/epic/a` を消さない）
- wip → review の門: ブランチが checkout されている worktree（`git worktree list --porcelain`）の中で `git config branch-step.test` を実行して exit 0 を要求。どこにも checkout されていない、または worktree に未 commit の変更があれば止まる（検査した状態と push する状態を一致させる）。trunk との diff に `docs/` 以外の変更があり `docs/design/` が無ければ警告（block しない）。memory ID と `gh` の存在・認証は門より前に確認する（止まったら push も rename もしない）
- PR 作成は `gh`。`--print-pr` は `gh` を呼ばず PR コマンドを印字する（push と rename は行う。名前を dry-run にしなかったのは、副作用が無いと誤解させないため）
- pre-push hook: local ref が `HEAD` / `@` なら `git symbolic-ref` で実名に解決してから判定する。local sha が全部 0（SHA-1 / SHA-256 どちらも）は削除なので通す。`<sha>:refs/heads/…` は ref 名を経由しないので止められない（仕様として SKILL.md に明記）
- bash を選んだ理由: git subcommand と pre-push hook に runtime 依存を持ち込まない。構文は `tests/test_branch_step.py` の `test_scripts_parse` が見る（CI の `bash -n` 行はこの PR では触っていない）

## 未決（案のまま。実装しない）

- `train/<epic>` — 揃うまで待つ乗り物。部品の PR は train 宛て、全部乗ったら nightly へ PR 一本。取り込みは nightly → train の一方通行
- 同時デプロイをなくす三拍（expand / migrate / contract）と `wip/<slug>-contract` の別 loop
- stack `<段>/<epic>/<n>-<part>`（順番は名前に投影、強制は base 鎖）
- vendor した pre-push の版ズレ検出（hook 冒頭に version comment を置き、`install` が比較して警告する等）
- checkout を使わない release: `git fetch` → `git commit-tree -p origin/main -p origin/nightly <tree>` で merge commit を作り `git push origin <sha>:main` → tag。lane からでも安全に出せるが幅が大きい。まずは worktree の前提確認で止める
- VP lane のブランチ名（`mako/<name>` → `wip/<slug>`）は VP repo の別 loop。nexus / creo-memories / vantage-point の CLAUDE.md・AGENTS.md 追従も別 loop

## やってはいけない

- `review/` を `wip/` に戻す rename。PR が語り手になった後にブランチ名を変えると二重帳簿になる
- `spike/` を push する。pre-push hook が止めるが、hook は repo ごとに `install` しないと入らない
- `review/` への rename を push より先にやる。push が失敗すると local だけ `review/` になって語り手が二人になる。push（`wip/x:refs/heads/review/x`）が通ってから rename する
- 門のテストを「今いる作業ツリー」で走らせる。slug を指定して別の場所から `git next` すると、進めるブランチではなく手元の状態を検査してしまう。ブランチが checkout されている worktree を探してそこで走らせる
- trunk を local の ref だけで判定する。clone 直後は local に `main` しか無く、PR が main 宛てに開く（防ぎたかった事故そのもの）。origin 側も見る
- `--dry-run` という名前で push や rename を伴う操作を提供する。下見のつもりで実行される
- `.github/workflows` を触る commit を agent のブランチに混ぜる。OAuth の `workflow` scope が無い token では push が拒否される。CI の変更は mako の手か scope を足した後の別 PR で
- slug を glob や前方一致で探す。`drop epic` が `spike/epic/a` を消し、`drop '*'` が全部消す
- `install` の既定を global にする。alias は plugin の版付きパスを指すので、更新で全 repo の `git next` が壊れる
- git が `!` alias の子に渡す `GIT_DIR` 等をそのまま子プロセスへ流す。creo-memories で実際に起きた: 門のテストが一時 repo を作って git を呼び、`GIT_DIR` が本物を指していたので本物のブランチに commit が増え、`origin/nightly` が update-ref され、共有 config に `user.name` が書かれ、**テストの `git init` が本物の repo を bare として再初期化して `core.bare = true` が入った**（`git init` は GIT_DIR あり / GIT_WORK_TREE なし / cwd が親でないと bare 判定。lead の作業ツリーが取り残され status / diff / pull が壊れた。復旧済み）。script の先頭で剥がす（1.0.1）
- 門を dirty な worktree で通す。直したが commit し忘れた状態でテストが通り、FAIL の入った commit が push される
- lane（linked worktree）から release を実行する。lead が trunk を持っているので `git checkout` が拒まれる（二重 checkout）。詰まった時の回避に `core.bare` / `--ignore-other-worktrees` / `--force` / `git worktree remove` を使わない。release スキルは worktree を確かめて lead で行うよう止める（当初 creo-memories 2026-10-01 の `core.bare = true` をこの経路の回避と見たが、実際の原因は上の GIT_* 継承だった。慣習を止める理由は二重 checkout で詰まること）
- 門を機械で厳しくしすぎる。「設計に触れたか」は人が決める。警告に留める

## 検証

`python3 -m unittest tests.test_branch_step -v` — 一時 repo（bare origin 付き）で、spike → wip → review の rename、review での push と PR コマンド（`--print-pr`）、門（test コマンド / design 警告）、keep / drop、install、pre-push の拒否と削除の許可、slug の解決を検証する。`gh` は呼ばない。

## Status log

- 2026-10-01: Conception の裁定を受けて Draft。`branch-step` スキル、規約の書き換え（chronista-style / parallel-dev / codeflow）、テストを同じ PR で。
- 2026-10-01: dogfood の初回 push が token scope（`.github/workflows` の変更）で拒否され、local だけ `review/` になった。push を rename より先に変更し、CI の `bash -n` 追加はテスト側（`test_scripts_parse`）に置き換え。
- 2026-10-01: Moody Blues のレビュー（PR #1）で再現つきの指摘 8 件。門をブランチの worktree で走らせる、trunk 判定に origin を含める、hook の `HEAD:` 解決、exp→wip を push 先行に、`--dry-run` を `--print-pr` に改名、keep の push 失敗で名前を戻す、worktree 内の drop を detached で、`gh` の事前確認、`git board` alias。テスト 19 → 27 件。
- 2026-10-01: 再検証で残った 1 件（dirty worktree の門）を修正。hook は `spike/x~0:` の revision 式も止める。テスト 28 件。
- 2026-10-01: mako 裁定「GO」: nightly 宛て PR は squash、CI の `bash -n` 修正は別 PR（workflow scope が通った後）。
- 2026-10-01: nexus 側 deep review。`gh pr create` 失敗後に PR 作成だけやり直せる経路、slug の完全一致と stack 形の拒否、dirty な spike の drop 拒否、`install` の既定を `--local` に、merge → worktree 畳み → prune を規約本文に。exp→wip の push 先行は nexus が承認。テスト 32 件。
- 2026-10-01: v0.33.0 の実地（creo-memories）で門のテストが本物の repo を触る事故。script 先頭で git 注入の `GIT_*` を剥がす。linked worktree から alias 経由で再現する回帰テスト。`install` は既存 hook を skip して exit 0、`--no-hook` 追加。branch-step 1.0.1。
- 2026-10-01: creo-memories の `core.bare = true` を受け、release スキルに worktree の前提確認を足す（release 1.0.1、branch-step 1.0.2）。checkout を使わない release は未決へ。
- 2026-10-01: 訂正（creo-memories lane が scratch で再現）。`core.bare = true` の原因は lane からの release ではなく、門の GIT_* 継承で hook テストの `git init` が本物を bare 化したこと（1.0.1 で解消済み）。前提確認は二重 checkout を止める目的でそのまま有効。release 1.0.2 で文言を訂正
