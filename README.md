# Chronista Style Plugin

Chronista のプロダクト群を横断する**共通の開発スタイル基盤**。どのプロダクトでも同じ流儀で「強く美しいプロダクト」に育てていくために、Spark → Conception → GO の開発フロー・Living Documentation・規律スキル（TDD / デバッグ / 検証）を統合する。

> **バージョン**: プラグイン本体は `.claude-plugin/plugin.json` を、各スキルは個別の `SKILL.md` の `metadata.version` を参照。履歴は [CHANGELOG.md](./CHANGELOG.md) に記録。

## インストール

Claude Code / Codex で共通の `skills/` を使う。導入・更新・MCP 接続の手順は [インストールと更新](docs/guide/01-installation.md) を参照。

開発の正本は [plugin-chronista-style](https://github.com/chronista-club/plugin-chronista-style)。配布先は [chronista-plugins](https://github.com/chronista-club/chronista-plugins) marketplace とする。旧本体 repo は現状のまま残し、新しい変更はこの repo で行う。

本体 v0.32.0 は GitHub Release の ZIP として配布する。新 marketplace への掲載と、そこからの導入確認は準備中。

| 環境 | 対応状況 |
|---|---|
| Claude Code | 共有スキル・hooks の実装あり。新配布先での実機確認待ち。ローカル確認は `claude --plugin-dir .` |
| Codex | manifest・共有スキル・hooks の実装あり。新配布先での実機確認待ち |
| Grok Build | Claude 互換を基本として確認予定。専用構成は差分が必要になった場合に追加。実機では未検証 |

## スキル一覧

| スキル | 種別 | 説明 |
|--------|------|------|
| `chronista-style` | 入口 | North Star・設計哲学・基本姿勢・プロジェクト管理の規約。各スキルへ routing する |
| `codeflow` | プロセス | Spark（想起）→ Conception（構想）→ GO で作業に切り替え、SDG で仕様・設計を記録する開発フロー |
| `parallel-dev` | プロセス | 並列開発の道具選び。「隔離・出荷」2 層モデルで worktree / VP lane / stacked PR を判断 |
| `branch-step` | プロセス | ブランチの段。`<段>/<slug>`（spike / wip / review）を `git next` / `keep` / `drop` で進める。spike はローカル専用 |
| `spec-design-guide` | 文書 | spec（What & Why）・design（How）・guide（Usage）を `docs/` に書き、コードと同じ PR で育てる |
| `tdd` | 規律 | テストファーストで実装する RED-GREEN-REFACTOR サイクル |
| `systematic-debugging` | 規律 | 根本原因を特定してから修正する 4 ステップデバッグ |
| `verification` | 規律 | 証拠なき完了宣言を防ぐ。検証コマンド実行 → 出力確認 → 主張 |
| `spark` | 入口 | 原文のアイデアを記憶へ保存 |
| `sdg` | 入口 | spec / design / guide の文書生成 |
| `release` | 出荷 | 版・CHANGELOG・tag・リリース手順 |
| `council` | AI 協働 | 4 voice の合議で意思決定。多義的なトレードオフや go/no-go 判断に |

規律 3 スキルは該当場面で省略しない。それ以外の該当判断はモデルに委ねる。

## 呼び出し

| Claude Code / Codex | 説明 |
|----------|------|
| `/chronista-style:spark` / `$spark` | 降ってきたアイデアを解釈ゼロで memory に pack。一手で終わる |
| `/chronista-style:codeflow` / `$codeflow` | 開発セッションを開始。理解を提示してから該当ステップに入る |
| `/chronista-style:sdg` / `$sdg` | spec / design / guide のひな形を `docs/` に起こす |
| `/chronista-style:release` / `$release` | リリースの背骨（版・CHANGELOG・nightly → main・tag・GitHub Release）。尻尾はプロジェクト側に委譲 |

## 開発フロー

```
Spark（想起、どちらからでも）→ Conception（構想: 調べる・話す・理解を書く・合議、順不同）→ GO → SDG → Branch & PR → Implementation → Release → Learning
```

硬い線は GO の一本だけ。詳細は `codeflow` スキルを参照。

## hooks

- **SessionStart**: git コンテキストと Atlas 候補、規律エッセンスを注入
- **Stop**: `fabrication-tripwire.sh` — 観測していないツール出力を最終メッセージに書いたら差し戻す（fail-open、同一ターンの差し戻しは一回まで）

hooks は bash / git / jq / Python 3 が必要。Codex では hook 定義の信頼設定も必要。

## 関連プラグイン

| プラグイン | 説明 |
|-----------|------|
| [creo-memories](https://github.com/chronista-club/claude-plugin-creo-memories) | 永続記憶システム（MCP Server） |

## ライセンス

MIT
