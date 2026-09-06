---
name: codeflow
description: Spark（想起）から Conception（構想）を経て GO で作業に切り替え、SDG で仕様・設計を記録する開発フロー
metadata:
  tags: "development, workflow, sdg, spark, conception, second-opinion"
  version: "4.3.0"
---

# Code Flow Skill

記憶操作の前に [creo-memories の接続と未接続時の扱い](../chronista-style/reference/memory-connection.md) を読む。以下の記憶手順は、対応ツールが利用できる場合に実行する。

**Code Flow**は、Spark（想起）から Conception（構想）を経て GO で作業に切り替え、仕様・設計を体系的に記録する開発ワークフロー。態度は `chronista-style` ルートの「基本姿勢」に従う — 穏やかに、真面目に、ユーモアを忘れずに。

## セッションの起動

開発セッションの開始を依頼されたときに使う。継続中の作業では現在のステップから進み、起動手順を繰り返さない。固定メニューで選ばせない。

1. **対象** — メッセージに「何を作る / 何を改善する」があればそれを採用。なければ地の文で聞く
2. **現在地** — 注入済みの記憶コンテキストと現ブランチの `git log` で状態を拾い、不足する記憶だけ接続済みの `search` で補う。既存タスクの続きなら `list_todos` から該当 memory を引く
3. **理解の提示** — 分かったこと、これからやること、置いた仮定、迷っている点を短く書く。Conception のどの手（調べる / 話す / 理解を書く）から入るか、それとも GO 済みで作業に入るかは、この提示の中で自分の判断として述べる
4. **ズレと分岐** — 理解がズレていそうな所と、ユーザーが選ぶべき分岐だけ聞く。GO で走る（`codeflow` の「実装前の合意」）

## 概要

Code Flow は **ステップ名で管理** します（番号は使いません）。依存関係は矢印のみで表現します。

```
Spark → Conception → GO → SDG → Branch & PR → Implementation → Release（条件付き）→ Learning
```

硬い線は **GO** の一本だけ。GO の前は一つの自由な空間（Conception）、GO の後は作業のパイプライン。「何かが先」という順番は無い。

### Spark（想起）

アイデア、相談したいこと、気持ち悪さが、どちらかの中に浮かぶ。「ちと相談なんだけど」「…について議論したい」がその瞬間。ユーザーからでも AI からでも起きる — AI が「気になることがある」と会話を開いてよい。長く残したい火花は memory に `spark` として置く。入口は `spark` スキル（Claude Code: `/spark <言葉>`、Codex: `$spark <言葉>`） — 解釈ゼロで原文のまま pack し、一行で返す。「ちと相談なんだけど」が来たら作業の手を止め、Conception の構えに切り替える。

### Conception（構想）

Spark が形になるまでの会話。**順番は無い。** 必要な手を必要なときに打つ。

- **調べる（Discovery）** — コードベース、既存実装、類似事例、過去の記憶（`search`）。触るコードのパスで `docs/` を grep し、既存の design があれば読んでから話す。同じ領域の `spark` も `search` で拾い、繋がるものがあれば会話に出す（忘れられた火花を持ってくるのも AI の役目）。会話の途中で何度でも
- **話す（Discussion）** — 方向性を一緒に決める。**ここが一番楽しい。** 選択肢を並べる（「A案、B案、あと禁断のC案」）、雑談も脱線も歓迎、「それ、本当に必要？」は最高の質問。完璧な案を出そうとしない、決まらなくても焦らない
- **理解を書く** — 質問票ではなく、理解の提示と差分。自分の理解を短く書く（何を / なぜ / やらないこと / 置いた仮定 / 迷っている点）。聞くのは、理解がズレていそうな所と、ユーザーが選ぶべき分岐だけ。推測できることは仮定として明示する。分岐が 2〜4 個に離散的に絞れたときだけ利用可能な質問ツールを使い、使えない場合や開いた問いは地の文で聞く。「わからない」「後で決める」も回答 — 仮定を置いて進み、仮定を書き残す
- **合議（council）** — 判断軸が複数あって明確な勝者がいない分岐は `council` で 4 voice にかけ、trade-off と最強の dissent を表に出す

合意した理解は起票 memory の「AI の理解」節に書き戻す。ユーザーの裁定は原文のまま引用して不変に、理解はその上に積む。

### GO（実装前の合意）

設計判断を伴う変更は、方針を短く提示して合意を得てから実装に入る（数行の設計メモで十分）。typo 修正や明白な小修正はそのまま進めてよい。判断軸は「この変更に、ユーザーが選ぶべき分岐があるか」。

合意の粒度は軽くてよい — 短い方針提示に「いいね」「進めて」の GO で走り出せる状態を保つ。重い設計文書を待たず、GO なしで走らない。GO の後は合意した範囲を走り切り、途中の質問は回答に依存しない部分を済ませてからターン末尾でまとめて聞く。

GO の瞬間に memory を `spark` から `todo` に進める（Issue-first）。GO が要った変更 — ユーザーが選ぶべき分岐があった変更 — は、その分岐の答えを design に書く価値がある。分岐が無かった変更に design は書かない。

### SDG（Spec-Design-Guide）

spec / design を Draft で `docs/` に置く（何を書くか・どう生かすかは `spec-design-guide`）。実装タスクは 1 振る舞い 1 単位に割る。手順は `tdd`。

#### Issue 連携 — memory-as-issue

タスクは creo-memories の memory として起票し、進捗も同じ memory に積む（Issue / Todo / Decision が一つの層）。起票の中身（成功基準・非対象・AI の理解・Branch slug）は `chronista-style` ルートの「Issue-first の原則」、API の作法（status / tags / supersedes / 追記の仕方）は `creo-memories` スキルに従う。ここには複写しない。

### Branch & PR（ブランチ & PR フロー）

trunk は `nightly`、ブランチ名は `{type}/{slug}`、PR body 冒頭に memory ID。規約の本体は `chronista-style` ルートの「ブランチ運用（nightly trunk）」と「Branch slug の規約」。PR を出す前に `verification` を通す（設計に触れた変更なら design が同じ PR にあること、もそこで確かめる）。レビューで GO が出るまでマージしない。

### Implementation（実装・TDD）

`tdd` スキルの RED-GREEN-REFACTOR サイクルに従う。テストファーストで書き、失敗を確認し、最小限のコードで通す。

対象パスのコードを変えたら同じブランチで design を触る — 変わったことは Status log に、踏んだ地雷は「やってはいけない」に追記する（`spec-design-guide`）。進捗は起票した memory に追記する。

### Release（リリース & 配布・条件付き）

**トリガー条件**: 以下のいずれかに該当する場合のみ実行する。該当しなければスキップ。

- PR マージ → リリースが必要な場合
- デプロイが必要な場合

手順は [release スキル](../release/SKILL.md) — 背骨（版の検出 → CHANGELOG → release commit → nightly → main → tag → GitHub Release）は共通、尻尾（CI / publish / 署名 / 配置）はプロジェクト側に委譲。出荷した design の Status を Draft から Active に進め、Status log に一行。マージ後は起票した memory の todo を閉じる。

### Learning（学習）

セッションの知見を記録し、将来の開発に活用。

- **決定事項の記録**: 設計判断、学んだこと。文書には What、memory には Why
- **裁定は原文引用で記録**: ユーザーの裁定は「> 裁定: …」と原文のまま引用して memory に残す。要約は解釈が混ざる
- **タグ付け**: 機能名、技術名などで検索しやすく
- **失敗からも学ぶ**: うまくいかなかったアプローチも記録
