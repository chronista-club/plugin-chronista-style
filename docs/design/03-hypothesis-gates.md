# 03. 前提の再検証と失敗を防ぐ仕組み

> **Status**: Active
> **Related**: `mem_1Cg7qNf32jB4JLHHGHfnYH`（方針と裁定）
> **対象**: `skills/codeflow/SKILL.md`, `evals/hypothesis-gates/`

## 判断と評価の結果

既存3スキルを改訂する候補を、匿名の合成fixtureで比較した。調査元は [pstack](https://github.com/cursor/plugins/tree/101b274dd991f694e1f7024be2157e5f3adf07de/pstack) の attack-the-premise / encode-lessons-in-structure / eval。新しい総合モード、常時のhook、自動的な並列レビューは増やさない。

systematic-debugging と verification は、前提の見直し・実行証拠・実機未確認の区別の多くは現行でもできていた。Claudeの一部ケースでは未確認の境界や承認済み制約の扱いに失敗も残った。候補に安定した追加効果を確認できなかったため、本文の変更を取り下げる。試した候補は `evals/hypothesis-gates/candidate-v1.patch` に保持する。

codeflow の Learning は、失敗を注意書きだけに残さず、まず正本・所有・型で失敗経路を減らす判断へ絞る。消せる説明の重複を残して語句照合の検査で監視し続けない。残る不変条件を既存検査・振る舞いのテストへ戻す。判断が必要な部分は短い理由と失敗例にとどめ、別repoの変更は別タスクとする。

## 評価の境界

ソースリポジトリの `evals/hypothesis-gates/README.md` と評価記録に、固定ケース・実行手順・結果を残す。評価用fixtureとrunnerは配布ZIPには含めない。私的ログを配布せず、必要な構造だけを合成した。これは開発に使った事例での予備評価であり、未知の実案件への一般化や自動発見・パッケージ読込を保証しない。

構造テスト、モデルの行動、実機の成功は別の結果とする。現行でも通る項目を改善実績に数えない。同一ホスト内でモデル・設定を固定し、環境で拒否された実行はスキルの失敗と分ける。独立した採点では方式を伏せた出力と実行証拠を渡す。

## やってはいけない

- 合成fixtureでの対照実験を実機での原因確定とする。
- スキルの語句の存在をテストして、判断が改善した証拠とする。
- 一回の通過やホスト間の得点差で、安定した改善・モデルの優劣を主張する。

## Status log

- 2026-10-17: 合意した6ケースで3スキルの候補を比較。systematic-debugging / verification の改訂は取り下げ、codeflow の Learning に絞って追加評価。未リリース。

- 2026-10-17: v0.34.0 で codeflow の採用差分と評価資料を出荷。
