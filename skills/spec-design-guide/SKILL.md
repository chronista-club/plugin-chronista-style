---
name: spec-design-guide
description: spec（What & Why）・design（How）・guide（Usage）を docs/ に書き、コードと同じ PR で育てる Living Documentation の規律。設計に触れる変更のときに使う。
metadata:
  version: "2.0.1"
  tags: "documentation, spec, design, guide, living-documentation"
---

# Spec-Design-Guide (SDG)

> **ドキュメントは死んだテキストではなく、生きたコードベースの鏡である。**

文書の起動手順は [sdg スキル](../sdg/SKILL.md)。Claude Code では `/sdg`、Codex では `$sdg` で呼び出す。

## 目的 — 3 つを分ける

| 層 | 答える問い | 読み手 |
|----|-----------|--------|
| **spec** | What & Why — 何を、なぜ | 決める人、後から経緯を知りたい人 |
| **design** | How — どう作るか | 実装する人、変更する人 |
| **guide** | Usage — どう使うか | 使う人 |

本文は **`docs/spec|design|guide/NN-kebab.md`** に置き、番号で呼ぶ（「spec 25」「design 39」）。Creo Memories には本文を置かない — memory は起票・裁定・却下した案（Why の経緯）、docs は本文（What / How）。

## 何を書くか — 骨格

「この 4 つが読めれば成立する」という意味の骨格。順番と見出し名は強制しない。

**spec**: Abstract（3 秒で分かる要約）→ Motivation（なぜ必要か）→ Scope（In / Out）→ Requirements

**design**: Abstract（どの spec を実装するか）→ Architecture（構成。図が要るなら Mermaid）→ Data Model → Implementation

**guide**: Overview → Prerequisites → Usage（手順）→ Troubleshooting

design には「関連」（spec・memory・コードパスへの入口）と「やってはいけない」（実装で踏んだ地雷）がよく足される。歓迎する。

要件にトレーサビリティが要るなら `REQ-{NAME}-{NNN}` で番号を振り、テストのコメントから指す。任意の道具で、必須ではない。

```markdown
### REQ-SESSION-001: マルチセッション管理

**Acceptance Criteria:**
- [ ] 最大10セッションを同時管理
```

## ヘッダ — git が知らないことだけ

```markdown
# 39. 記憶の分類の構造

> **Status**: Draft | Active | Deprecated（Status log 参照）
> **Related**: spec 25、`mem_xxx`（起票 / 裁定）
> **対象**: `src/memory/classify.rs`, `migrations/0012_*.surql`
```

Author・作成日・更新日は書かない。git が知っている。**対象**のコードパスが「このコードを触るとき、どの文書を見るか」の索引になる。

## どう生かすか — Living Documentation

- **コードと同じ PR で触る。** design に関わる変更は、diff に design も載る。「後で docs を直す」は直らない
- **書き換えより追記。** 末尾の `## Status log` に日付と何が変わったかを積む。大きく変わったら Supersedes で新しい番号を切る（旧文書の Status を Deprecated に、Related で新番号を指す）
- **古くなったら消さない。** Status を Deprecated に。消すと「無かったこと」になる
- **地雷は文書に戻す。** 実装で踏んだ落とし穴は「やってはいけない」に追記する。コードから文書へ学びが還流するのが Living の証拠
- **What は文書、Why は memory。** 裁定と却下した案は memory に原文で。文書は Related から memory ID を指し、memory は文書のパスを指す

## どこで触るか — codeflow との対応

| ステップ | 動き |
|---|---|
| Conception の「調べる」 | 触るコードのパスで `docs/` を grep し、既存の design を読んでから話す。無ければ無いと分かる — 無理に作らない |
| GO | ユーザーが選ぶべき分岐があった変更は、その答えを design に書く価値がある。分岐が無かった変更に design は書かない |
| SDG | spec / design を Draft で置く |
| Implementation | 対象パスを変えたら同じブランチで design に追記（Status log / やってはいけない） |
| PR の前 | `verification`: 設計に触れた変更なら design が同じ PR にあること |
| Release | Status を Draft から Active に。Status log に出荷を一行 |

## 見つけ方

```bash
grep -rl 'src/memory/classify' docs/design   # 対象パスで引く
ls docs/design | tail -3                      # 次の番号
```

## 設計思想

→ `chronista-style` ルートの「設計哲学: Simplicity & Straightforward」に従う。文書自体も同じ — 必要な情報だけ、冗長さを排除、骨格どおりの直線的構成。
