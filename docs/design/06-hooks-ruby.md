# 06. hooks の実装言語とエラー報告

> **Status**: Draft
> **Related**: `mem_1CgYRtErN8zMr1d34Jyrod`（アクションと裁定）、design 01（Hooks と記憶接続）
> **対象**: `hooks/`, `tests/test_hooks.py`, `.mise.toml`, `.github/workflows/validate.yml`

## Abstract

Claude Code / Codex 共用の hooks（SessionStart、Stop）を bash + jq + Python から **Ruby** に統一する。振る舞いは fail-open のまま、失敗を黙らせない。

## なぜ Ruby

- スタイルの既定（Ruby first）。sh は読みづらく、Python は書き手の得意でない
- hooks が動く場所に居る: macOS は system ruby 2.6、homebrew 4.x、CI の ubuntu。Codex は同じ `hooks.json` のコマンドをそのまま実行する
- JSON が標準ライブラリ。jq と python3 の依存が消え、要件は ruby と git だけになる
- 例外が一箇所に集まる。`rescue` 一つで「何がコケたか」を拾って見せられる

見送った候補: Node/JS（Claude Code のネイティブ版・Codex では保証されない）、Go/Rust の単体バイナリ（リポジトリにバイナリを置く）、Perl（読みやすさ）。

## エラー報告の形

ホストの仕様（Claude Code hooks リファレンス、Codex hooks）:

- exit 0 + JSON: フィールドが適用される。`systemMessage` はユーザーに警告として表示（両ホスト）
- exit 2: block（Stop）。SessionStart では stderr を hook error 通知として表示し、セッションは続く
- その他の non-zero: non-blocking error。transcript に `<hook> hook error` 通知と stderr の先頭行

| hook | 正常 | 判定・取得に失敗 |
|---|---|---|
| session-start | exit 0、`hookSpecificOutput.additionalContext` | exit 0。出せる context は出す（git だけ失敗なら git 抜き）。`systemMessage: "chronista-style session-start: …"` を添える。cwd が無い・stdin が壊れているときも同じ |
| fabrication-tripwire | 違反なしは無出力、違反は `decision: block` | **exit 1 + stderr 一行**（`chronista-style fabrication-tripwire: skipped — …`）、stdout 無し。block しない |

tripwire の内部エラーに systemMessage を使わないのは、Stop での systemMessage の扱いがリファレンスで確認できなかったため。non-zero exit の通知は全イベント共通で定義されている。

黙ったままでよいもの（異常ではない）: 違反なし、`stop_hook_active` の再入、`TRIPWIRE-ACK`、cwd が git リポジトリでない。

## 互換

- Ruby 2.6 で動く書き方（パターンマッチ、`filter_map`、endless method を使わない）。先頭で `Encoding.default_external = Encoding::UTF_8`（LANG=C の環境で日本語の commit message が落ちない）
- `ruby` が無い環境: shell の `command not found` が non-zero で返り、ホストが hook error を出す。セッションは続く
- `hooks.json` は `ruby "${CLAUDE_PLUGIN_ROOT}/hooks/…rb"` で直接呼ぶ（zip 配布で実行ビットが落ちても動く）。`--disable-gems` は使わない（json が default gem でなくなる版に備える）
- テストは Python の harness のまま。`HOOKS_RUBY=/usr/bin/ruby` で別の ruby を指して回せる

## やってはいけない

- 失敗を `|| exit 0` / `rescue nil` で黙らせない。fail-open は「block しない」の意味で、「知らせない」ではない
- tripwire の内部エラーで exit 2 を返さない（block になる）
- hooks に Ruby 2.7 以降の構文を入れない。system ruby で動くことが前提
- pre-push（branch-step の git hook）を Ruby にしない。配った先の repo に ruby を要求することになる

## Status log

- 2026-10-30: Conception（mako「hooks を ruby に統一して、コケたらきちんとエラー」「ruby じゃなくても。sh は読みづらい、python は得意じゃない」→ Ruby を提案）、GO。`wip/hooks-ruby`。
