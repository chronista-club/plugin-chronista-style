# 01. Claude Code / Codex の共有スキル構成

> **Status**: Draft
> **Related**: Claude Code / Codex 対応・第1〜3段階、`mem_1Cen9MQ4eFA5AQPL4qF4hT`（新 repo を正本にする裁定）
> **対象**: `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `commands/`, `skills/`, `hooks/`, `tests/test_hooks.py`

## Architecture

同じプラグイン内の `skills/` を両環境で共有する。Codex manifest を追加し、既存の Claude manifest と同じ名前・版を持たせる。開発の正本は新設した `chronista-club/plugin-chronista-style`。旧 `claude-plugin-chronista-style` は現状のまま残し、改名・同期更新は行わない。利用時のプラグイン名 `chronista-style` は維持する。

Claude の `commands/` は入力を共有スキルに渡す薄い入口とする。spark・sdg・release をスキル化し、codeflow の起動手順は既存スキルに統合する。sdg は文書生成の入口、spec-design-guide は文書の規約を担う。

## Implementation

- スキルの追加情報は `metadata` 配下に置く。版は `metadata.version`、タグと出典も文字列として保持する。既存の版番号は移行時に維持し、リリース時に変更分を更新する。
- 質問・worktree・subagent は環境で利用可能な機能を使う。council は会話履歴を継承しない独立した視点を要求し、実行できない voice を結果として報告しない。
- コマンドの相対リンクはコマンドファイルを、スキル内の相対リンクはスキルファイルを基準に解決する。
- 第2段階で hooks と記憶接続の前提を整備。第3段階で公開 GitHub marketplace・版同期・更新手順を整備。実際の両アプリによる起動・信頼設定・MCP 認証は配布時に確認する。

## Hooks と記憶接続

- SessionStart は stdin の `cwd` を優先し、省略時のみ `CLAUDE_PROJECT_DIR` / `PWD` にフォールバックする。移動できなければコンテキストを出さない。JSON の入出力には jq を使う。
- `hooks/hooks.json` は両環境で共有する。Codex が互換用の `CLAUDE_PLUGIN_ROOT` を設定するため、既存のコマンドパスを維持する。Codex では hook 定義の信頼が別途必要。
- Stop は Python 3 の標準ライブラリで実装する。`transcript.py` が Claude の `message.content` と Codex の `response_item.payload` を読み替える。証拠はセッション全体の tool_result / function_call_output / custom_tool_call_output のテキストだけとする。ユーザーの引用やツール呼び出し引数は証拠にしない。
- 検査対象は hook 入力の `last_assistant_message` を優先し、省略時はログ中の現在ターンの最終メッセージを使う。Codex の commentary は除外する。欠損・解析失敗・未対応の出力形式では fail-open。`stop_hook_active` の再実行は通し、同一ターンの差し戻しを一回に抑える。
- 既存の正規表現パターンを保持する。この検査は出力パターンの有無の照合であり、数値や成功状態の一致までは保証しない。
- 記憶接続は `skills/chronista-style/reference/memory-connection.md` に集約。実際のツール名とスキーマを使い、Atlas 名から ID を捏造しない。未接続でも記憶に依存しない作業を続け、未保存・結果未確認を報告する。

Codex の [公式 Hooks 仕様](https://learn.chatgpt.com/docs/hooks) と手元の rollout の構造を確認した。ログは安定 API ではないため、テストには実データを含まない合成レコードを使う。

## 配布と版同期

- 公開カタログは `chronista-club/chronista-plugins` に置く。Claude 用 `.claude-plugin/marketplace.json` と Codex 用 `.agents/plugins/marketplace.json` は新本体 `chronista-club/plugin-chronista-style` のリリース済み `main` を参照する方針。カタログの参照更新・公開・導入確認は後続作業であり、現時点では新配布先からの導入はできない。旧カタログへの同期更新は行わない。
- 個人用 marketplace はローカル開発用。公開経路の既定にはしない。公式 Plugins Directory の掲載は GitHub 配布とは別の提出・審査手順。
- `.claude-plugin/plugin.json` を版・共有 metadata の正本とし、`scripts/sync-manifests.py` で Codex 側へ同期する。`--check` と CI がずれを検出し、Codex 固有の表示設定は保持する。
- `scripts/validate.py` はリポジトリ固有の整合性検査。ホストの公式 validator を置き換えるものではない。
- `scripts/package.py` は明示したファイル・ディレクトリだけで ZIP を作る。個人の `.mcp.json` を含めない。CI は検証と ZIP 作成まで行い、公開や tag の操作は行わない。

## 対応範囲

基本構成は Claude Code / Codex の2系統とする。Grok Build は Claude 互換を基本として扱い、専用構成は先に増やさない。manifest の読込・スキル呼出し・hooks の入力とログ形式を実機で確認し、差が出た部分だけ対応する。Stop のログ読み替えは現状 Claude/Codex のみ。Gemini 対応は今回の対象外。

## 検証

`python3 -m unittest discover -s tests -v` で両形式の検出・証拠照合・例外時の通過・作業ディレクトリ選択を検証する。全スキルの frontmatter、Codex manifest、ローカル参照先を検証する。両環境でのコマンド発見と呼び出しは配布段階の実機確認に含める。

## Status log

- 2026-09-06: 第1段階の共有構成を実装。
- 2026-09-06: 第2段階の hooks と記憶接続ガイドを実装。
- 2026-09-06: 第3段階の公開カタログ、同期・検証・パッケージ作成と CI を整備。公開・実アプリ確認は未実施。
- 2026-09-06: 公開先は改名せず新設する方針に変更。まず Codex personal への導入と Claude ローカル hook 起動を確認。公開カタログはローカルひな形まで。
- 2026-09-06: 本体を plugin-chronista-style に新設して正本化。履歴と未コミット作業を引継ぎ、両 manifest の URL と導入文書を新配布先へ更新。Grok は未検証。カタログ更新・commit/push・新配布先での実機確認は未実施。
