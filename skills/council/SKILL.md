---
name: council
description: 多義的な意思決定・トレードオフ・go/no-go 判断のために、4 voice の合議を召集する。複数の妥当な path が存在し、選択前に構造化された反対意見が必要なときに使う。
metadata:
  version: "2.0.1"
  origin: "ECC (Everything Claude Code) — chronista 適合 fork"
  tags: "decision, council, ambiguity, multi-voice, second-opinion"
---

# Council 🏛️

記憶操作の前に [creo-memories の接続と未接続時の扱い](../chronista-style/reference/memory-connection.md) を読む。以下の記憶手順は、対応ツールが利用できる場合に実行する。

> **「不一致を可視化することが目的だ。一致は副産物にすぎない。」**

**Core principle:** 判断軸が複数ある decision を単一視点で決めない。**4 voice の合議**で trade-off を表に出してから選ぶ。「これしかない」と確信した瞬間こそ召集の合図 — 1 voice の確信は conversational anchoring の signal。

## いつ使うか

複数の妥当な path が存在し、明確な勝者がいない decision:

- 設計判断（アーキテクチャの分岐）、scope 判断（今 ship か polish 待ちか）
- migration / rollout の go/no-go（breaking change vs alias 維持、段階展開 vs 一気 cutover）
- ユーザーが「どれが良い？」「迷ってる」と表明したとき
- 自分の初期 position はあるが確信度が低いとき

| ❌ council を使うな | ✅ 代わりに |
|---|---|
| output が正しいか検証したい | `santa-method`（team-bucciarati） |
| バグの根本原因を特定したい | `systematic-debugging` |
| コードのレビュー | 利用環境のコードレビュー機能またはレビュー用スキル |
| 単純な事実確認・明白な実行タスク | 直接やる |

## 4 Voice

各 voice は**独立した視点**。**会話履歴を渡さない**ことが anti-anchoring の核。

| Voice | レンズ | 担い手 |
|---|---|---|
| **Architect** | 正しさ・保守性・長期影響 | 現在の会話を担当するモデル自身 |
| **Skeptic** | 前提への挑戦・より単純な代案 | 会話履歴を継承しない独立した subagent |
| **Pragmatist** | 出荷速度・user impact・運用の現実 | 会話履歴を継承しない独立した subagent |
| **Critic** | edge case・downside risk・failure mode | 会話履歴を継承しない独立した subagent |

4 voice 全部を in-context で演じない — anchoring が機能せず結局 1 視点になる。

## フロー

```
Extract → Gather → Position → Convene → Synthesize → Present
```

- **Extract**: decision を 1 文の explicit prompt に絞る（曖昧なら先に 1 つだけ clarifying question）
- **Gather**: 必要最小限の context を集める。subagent に渡しすぎると anti-anchoring が崩れる
- **Position**: 外部 voice を読む前に、Architect として自分の初期 position・3 つの理由・最大 risk を書き留める（外部 voice の mirror に堕ちないため）
- **Convene**: Skeptic / Pragmatist / Critic を**並列で**召集。渡すのは question + compact context + 役割定義 + 出力 format のみ
- **Synthesize**: bias guardrail 付きで統合（下記）
- **Present**: compact verdict（下記）

### 実行環境への対応

Claude Code では Agent ツール、Codex では利用可能な subagent ツールを使う。会話履歴の継承を無効にできる場合は無効にし（`spawn_agent` に `fork_turns` があれば `"none"`）、下記の入力だけを渡す。独立した subagent を作れない環境では、その制約を報告し、単独の分析として返す。未実施の voice を生成して合議結果にしない。

### Subagent prompt template

```text
You are the [ROLE] on a four-voice decision council.

Question: [decision question]
Context: [only the relevant snippets or constraints]

Respond with:
1. Position — 1-2 sentences
2. Reasoning — 3 concise bullets
3. Risk — biggest risk in your recommendation
4. Surprise — one thing the other voices may miss

Be direct. No hedging. Keep it under 300 words.
```

### Synthesize の bias guardrail

- 外部 voice を**理由なしに**否定しない
- 外部 voice で recommendation が変わったら**明示的に**そう書く
- 採用しなくても**最強の dissent** は必ず記載
- 2 voice が initial position に反対したら **real signal** として扱う
- raw position は verdict の前に必ず可視化する

### Present format

```markdown
## Council: [短い decision タイトル]

**Architect / Skeptic / Pragmatist / Critic:** [各 1-2 文 position + 1 行 why]

### Verdict
- **Consensus:** [一致点]
- **Strongest dissent:** [最重要の反対]
- **Recommendation:** [統合された path]
```

短く。

## creo-memories 連携

**実態を変える decision だけ** pin する（category: `design-decision`、tag: `[council, decision-log]`）。verdict だけでなく **4 voice の raw position と strongest dissent** も記録する — 将来 revert を検討するときの参考になる。council で initial position が変わった場合は、その理由も残す。
