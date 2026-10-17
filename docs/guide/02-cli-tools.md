# 02. sem と mbx の使い分け

## 入口

実行する環境の `sem --version` / `mbx --version` と各 `--help` を確認する。
以下は sem 0.27.0 / mbx 1.11.1 で確認した手順。新しい版の引数を古い版に持ち込まない。

グローバル CLI は Homebrew を優先する。sem の formula は **sem-cli**（Semgrep とは別物）。
Rust toolchain は rustup、mise はタスクとプロジェクト固有ランタイムに使う。
mbx の公式手順にある mise のグローバル Rust 登録を、この環境へそのままコピーしない。

## sem: 調査とレビューの補助

```bash
sem find parseConfig --context --json
sem impact --diff HEAD --tests --json
sem certify main..HEAD --json
sem history --blame src/config.ts --json
```

名前・ファイル・比較対象のブランチは対象プロジェクトに合わせる。
文字列検索は `rg`、呼び出し関係や変更単位の調査に sem を使う。
MCP では接続中の `tools/list` の名前と引数に従う。

`sem check` を使う場合も、プロジェクト指定の検証を網羅するか checker と対象範囲を読む。
終了コード 2 は判定不能。独自の `mise run check` / CI を省略する根拠にはしない。
`--promises` は一時的なコード変更を伴うので、読み取り専用レビューでは使わない。

## mbx: 普段は Cargo、確認は mbx

mbx が導入済みなら、普段のビルドはプロジェクト指定の `cargo` / `mise run` を使う。
既存 wrapper の上にさらに wrapper を重ねたり、全コマンドへ機械的に `mbx` を付けたりしない。

```bash
command -v cargo
command -v mbx
mbx setup --status
mbx doctor
mbx stats
mbx explain --last
mbx gc --dry-run
```

- `setup --status` は導入状態、`command -v cargo` はそのプロセスの入口。設定が存在するだけで有効と判断しない。
- mise wrapper 経由の場合、doctor が Cargo shim の PATH 警告を出すことがある。
  すぐ PATH を書き換えず、既存 wrapper の設定と通常のビルド出力で実際の経路を確認する。
- `stats` は累積の推定節約値。現在の実ディスク空き容量や今回の待ち時間と区別する。
- `explain --last` は最後の記録を読む。`explain <cargo command>` はビルドを再実行する。
- `gc --dry-run` は削除候補の確認。実際の `gc` / `clean` は必要な作業範囲で別途判断する。
- 新規の `mbx setup` は Cargo 経路を変える。既存の sccache / RUSTC_WRAPPER 等を確認し、
  導入作業として実施する。プラグイン利用時に自動設定しない。

## 公式資料

- [sem](https://github.com/Ataraxy-Labs/sem#using-sem-with-agents)
- [mbx](https://github.com/jdx/mr-boxington#readme)

公式の最新版と手元の版が異なる場合は、まず手元の help に合わせる。
