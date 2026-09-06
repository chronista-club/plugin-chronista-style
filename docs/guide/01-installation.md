# 01. インストールと更新

> **Status**: Draft
> **Related**: [両環境の共有構成](../design/01-claude-codex-shared-skills.md)
> **対象**: プラグイン配布・MCP 接続・ローカル検証

## 配布状況

本体の正本は [plugin-chronista-style](https://github.com/chronista-club/plugin-chronista-style)、配布カタログは [chronista-plugins](https://github.com/chronista-club/chronista-plugins)。本体 v0.32.0 は GitHub Release の ZIP として配布する。marketplace 経由の導入は準備中。以下の marketplace 導入・更新コマンドは、新カタログへの掲載と導入確認が済んでから使う。

旧 `claude-plugin-chronista-style` は現状のまま残し、新しい変更は新 repo で行う。旧 marketplace を更新しても新 repo の変更は受け取れない。

## 前提

Claude Code または Codex のプラグイン対応環境を使う。hooks には bash、git、jq、Python 3 が必要。Windows では Git Bash 上でこれらが PATH にあることを確認する。hooks を有効にしない場合もスキルは利用できるが、起動時の情報注入と Stop の検査は行われない。

## Claude Code

新規導入は、新 marketplace と本体の公開後に行う。旧 marketplace を登録済みの場合は、後述の「既存環境からの切替」を先に確認する。

```bash
claude plugin marketplace add chronista-club/chronista-plugins
claude plugin install chronista-style@chronista-plugins
```

開発中の checkout を試す場合は、リポジトリのルートで実行する。

```bash
claude --plugin-dir .
```

コマンドの名前空間は `/chronista-style:spark`、`/chronista-style:codeflow`、`/chronista-style:sdg`、`/chronista-style:release`。短縮名の解決が競合する場合も、この形式で指定できる。

公開版の更新:

```bash
claude plugin marketplace update chronista-plugins
claude plugin update chronista-style@chronista-plugins
```

更新後に Claude Code を再起動する。

## Codex：公開 GitHub marketplace

新カタログの Codex 定義から `chronista-club/plugin-chronista-style` のリリース済み `main` を配布する。次のコマンドはカタログとプラグインの両方が公開された後に利用できる。

```bash
codex plugin marketplace add chronista-club/chronista-plugins --ref main
codex plugin add chronista-style@chronista-plugins
```

新しいスレッドで `$spark`、`$codeflow`、`$sdg`、`$release` を呼ぶ。名前が競合するときはスキル選択 UI で Chronista Style のものを選ぶ。hooks は定義を確認して信頼した後に動作する。

公開版の更新:

```bash
codex plugin marketplace upgrade chronista-plugins
codex plugin add chronista-style@chronista-plugins
```

更新後は新しいスレッドを使う。ローカル開発で即座に変更を試す場合は `plugin-creator` で個人用 marketplace と配布用コピーを用意する。`+codex.<timestamp>` cachebuster はそのコピーにだけ付け、公開ソースの両 manifest は一致させる。

### 公開範囲

- 個人用 marketplace は自分の端末のカタログ。登録だけでは他の人に公開されない。
- GitHub の公開 marketplace は、リポジトリを知っている人が登録・導入できる配布方法。プラグインのライセンスは MIT。
- OpenAI の公式 Plugins Directory に検索・掲載されるには、別途提出・審査が必要。GitHub に公開しただけでは公式ディレクトリには掲載されない。

## 既存環境からの切替

旧カタログと新カタログの名前はどちらも `chronista-plugins`。旧登録が残った環境では、上の新規導入コマンドだけで切替が完了するとは扱わない。

新配布先の導入確認後に、登録元・導入済みプラグイン・設定を記録し、旧登録から新登録への切替と再導入を行う。Codex の `chronista-style@personal` を利用中なら、公開版との二重読込も確認する。切替後は新 repo の版が読み込まれ、更新できることを確認する。具体的な切替コマンドは実機検証後に追記する。

## Grok Build

Claude 互換を基本として確認する。専用構成は差分が必要になった場合に追加する。現在の Stop hook は Claude/Codex のログ形式を対象としており、Grok での動作は確認していない。スキルの発見・呼出し、plugin の有効化・信頼、hooks とログ形式を検証した後に導入手順を追加する。

## MCP 接続

creo-memories は別途接続する。プラグインのインストールだけで接続・認証・Context Engine の自動注入が成立するとは扱わない。

- Claude Code: creo-memories 側のセットアップ手順に従う。
- Codex: 既存接続を `codex mcp list` で確認し、接続元が指定した起動コマンドまたは URL で `codex mcp add` を使う。URL や認証情報をこのリポジトリに埋め込まない。
- 本リポジトリの `.mcp.json.example` は開発用 gitnexus の例。creo-memories の設定ではなく、`bin/setup*` も Codex の接続は作成しない。

接続後に検索ツールの利用を確認する。保存確認はユーザーが指定した内容で行い、実際の memory ID を確認する。未接続時の動作は [記憶接続ガイド](../../skills/chronista-style/reference/memory-connection.md) を参照。

## 検証と配布 ZIP

リポジトリのルートで実行する。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/sync-manifests.py --check
.venv/bin/python scripts/validate.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/package.py
```

Windows の Git Bash では `.venv/bin/python` を `.venv/Scripts/python.exe` に読み替える。

`dist/chronista-style.zip` に両 manifest と共有スキル・hooks をまとめる。ユーザー固有の `.mcp.json`、`.git/`、開発環境は含めない。ZIP はローカル導入用の配布物であり、公開カタログへの掲載は別手順。

版の正本は `.claude-plugin/plugin.json`。版を変更したら `python3 scripts/sync-manifests.py` で Codex 側へ同期し、検証する。CI も同期・スキル・hooks を確認し ZIP を artifact として作成する。tag、GitHub Release、marketplace 公開は自動では行わない。

## 実アプリでの確認

導入後、新しいセッションで次を確認する。

1. 11スキルが見つかり、codeflow と sdg の参照先が読める。
2. hook を信頼した環境で、SessionStart の branch / Atlas 候補が対象 repo と一致する。
3. creo-memories が未接続なら spark が「未保存」と返し、接続済みなら指定した原文が保存される。
4. Stop の差し戻し後も会話が継続できる。

合成ログによる自動テストの通過と、実アプリでの確認結果は区別して記録する。

## 参照

- [Claude Code plugins](https://code.claude.com/docs/en/plugins)
- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
