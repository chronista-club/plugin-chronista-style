# 前提の再検証 — 行動評価

評価結果は [RESULTS.md](RESULTS.md)。

`cases.json` は実行前に固定した6件の依頼、合成fixture、判定基準。私的ログや実デバイスの実装は含まない。`run.py` はホストごとの新規セッションに本文を明示的に渡す。スキルの自動発見・パッケージ読込・実機挙動の評価ではない。

## 実行

認証済みの Claude Code / Codex CLI、git、Python 3 を使う。出力先はリポジトリ外の絶対パス。既存設定を変更せず、各実行は別ワークスペースを作る。Claude は safe mode と明示的なツール許可、Codex は独立した設定ディレクトリと workspace-write / approval never を使う。Codex の認証ファイルは既存ファイルへのシンボリックリンクとし、内容を出力・複製しない。自動承認レビューは使わない。

```bash
python3 evals/hypothesis-gates/run.py --host claude --model claude-opus-5-5 --skills /tmp/baseline-skills --output /tmp/eval-baseline-claude
python3 evals/hypothesis-gates/run.py --host codex --model gpt-6-astra --effort high --skills /tmp/baseline-skills --output /tmp/eval-baseline-codex
```

同じコマンドの `--skills` と出力先だけを変えて改訂版を試す。モデルはその時の比較対象を明示し、同一ホスト内で固定する。ホスト間の得点でモデルの優劣を論じない。`--case` で追加反復する。

## 判定

- 6ケース各1回を予備評価とし、差が出た/判定が揺れた重要ケースを追加反復する。
- 評価対象へ期待解や判定基準、版名を渡さない。採点時も匿名の実行IDで出力と成果物を読み、最後に版の対応を開く。
- 最終回答だけで採点しない。実際のツール結果と変更成果物を照合し、可能な場合はテストや故障注入を再実行する。
- 本文の文字数、ツール呼出し数、不要な確認質問も記録する。API内部の非公開処理や課金量は推定しない。
- 実行環境の失敗はスキルの失敗と分ける。設定変更が必要なら両版を同じ条件でやり直す。
- 改訂前から通る項目は改善に数えない。差が見えない場合は文面を増やさず、縮小・取り下げを検討する。

`metadata.json` はCLI引数、モデル、skill SHA-256、終了状態、時間を記録する。`events.jsonl` と `artifacts.json` が実行証拠。認証リンクを含む実行ディレクトリ全体を公開しない。共有する場合は匿名のfixture・結果要約だけにする。
