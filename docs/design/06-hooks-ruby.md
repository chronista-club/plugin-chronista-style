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

黙ったままでよいもの（異常ではない）:

- 違反なし、`stop_hook_active` の再入、`TRIPWIRE-ACK`
- cwd が git リポジトリでない（Branch 等は `-`）
- Codex の `transcript_path: null`（契約上 `string | null`。無ければ検査できない）
- Codex が暗号化して保存したツール出力（`function_call_output.output` の `encrypted_content` ブロック）。読めない証拠がある間は判定しない — 「本文なし」扱いにすると、ツールを使っていても証拠が無いと見なして誤 block する
- 本文を持たない正規のブロック（ToolSearch の `tool_reference`）は既知型として読み飛ばす。実データで Claude の 36% のセッションに含まれ、未知のままだと Stop のたびに hook error が出る（Moody Blues レビューの指摘）

逆に、知らない型のブロック・オブジェクトでない行・読めないファイルは「異常」として exit 1 で知らせる。新しい型が出てきたら、本文を持つかどうかを確かめて既知型に足す。

## 互換

- Ruby 2.6 で動く書き方（パターンマッチ、`filter_map`、endless method を使わない）。先頭で `Encoding.default_external = Encoding::UTF_8`（LANG=C の環境で日本語の commit message が落ちない）
- `ruby` が無い環境: shell の `command not found` が non-zero で返り、ホストが hook error を出す。セッションは続く
- `hooks.json` は `ruby "${CLAUDE_PLUGIN_ROOT}/hooks/…rb"` で直接呼ぶ（zip 配布で実行ビットが落ちても動く）。`--disable-gems` は使わない（json が default gem でなくなる版に備える）
- テストは Python の harness のまま。`HOOKS_RUBY=/usr/bin/ruby` で別の ruby を指して回せる。CI は ubuntu の Ruby 3.3 に加えて、**macOS ランナー同梱の `/usr/bin/ruby`（2.6）で hooks のテストを回す**ジョブを持つ。`ruby -c` は 2.7 以降の構文を見逃す（`filter_map` は実行して初めて落ちる）ので、実行で守る
- `Encoding.default_external` の代入は `$VERBOSE` を一時的に落として行う（`-w` の警告が stderr の先頭行を汚す）。ENV / `Dir.pwd` から来たパスは `force_encoding(UTF_8)`（LANG=C では locale の encoding で来る）、stdin と例外メッセージは `scrub`
- 通知に載る stderr は一行・160 文字まで（Ruby 2.6 の json は壊れた行を丸ごとメッセージに入れる）

## やってはいけない

- 失敗を `|| exit 0` / `rescue nil` で黙らせない。fail-open は「block しない」の意味で、「知らせない」ではない
- tripwire の内部エラーで exit 2 を返さない（block になる）
- hooks に Ruby 2.7 以降の構文を入れない。system ruby で動くことが前提
- pre-push（branch-step の git hook）を Ruby にしない。配った先の repo に ruby を要求することになる

## Status log

- 2026-10-30: Conception（mako「hooks を ruby に統一して、コケたらきちんとエラー」「ruby じゃなくても。sh は読みづらい、python は得意じゃない」→ Ruby を提案）、GO。`wip/hooks-ruby`。
- 2026-10-30: Moody Blues レビュー（PR #10、NEEDS WORK）。実 transcript 391 本で旧新の判定は全件一致したが、`tool_reference` を未知型として拒否するため Stop のたびに hook error が出ることを指摘。既知型に追加、Codex の暗号化ツール出力と `transcript_path: null` は静かに通す、session-start は cwd が無くても規律エッセンスを出す、LANG=C の日本語パス、stderr の長さ上限、macOS system ruby の CI ジョブ、verification / bin/setup / design 01 の古い記述を直した。
