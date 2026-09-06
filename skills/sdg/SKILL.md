---
name: sdg
description: spec / design / guide のひな形を docs/ に起こす。種類と対象は推測して提示し、聞くのは分岐だけ
metadata:
  version: "1.0.0"
---

# SDG 起動

記憶操作の前に [creo-memories の接続と未接続時の扱い](../chronista-style/reference/memory-connection.md) を読む。以下の記憶手順は、対応ツールが利用できる場合に実行する。

`spec-design-guide` スキルのエントリポイント。**ひな形生成までを 1 コマンドで**。質問票にしない — 種類と対象は推測して提示し、聞くのはズレと分岐だけ。

## 実行手順

### 1. 種類と対象を推測する

聞く前に読む。

- **対象**: メッセージにあればそれ。無ければ現ブランチ名 → 起票 memory（`search`）→ 直近 commit の順に推測する
- **種類**: 対象に spec が無ければ spec、spec があって design が無ければ design、実装済みで使い方が要るなら guide。判断がつかなければ spec から

推測した種類と対象、置く番号（`docs/<種類>/` の最大番号 + 1）を短く提示する。ズレていそうなら直してもらう。種類の分岐が本当に残るときだけ、利用可能な質問ツールか地の文で聞く。

### 2. ひな形を書く

| 種類 | 保存先 | 骨格 |
|------|--------|------|
| spec | `docs/spec/{NN}-{kebab-case}.md` | Abstract → Motivation → Scope → Requirements |
| design | `docs/design/{NN}-{kebab-case}.md` | Abstract → Architecture → Data Model → Implementation |
| guide | `docs/guide/{NN}-{kebab-case}.md` | Overview → Prerequisites → Usage → Troubleshooting |

本文は `docs/` のみに置く。Status は `Draft` から始め、コードと同じ PR で更新する。分かっていることは埋めて書く（空のひな形を渡さない）。

### 3. ヘッダと要件 ID

ヘッダは Status（Draft）と Related（spec 番号・起票 memory）と対象（コードパス）だけ。Author や日付は書かない。spec でトレーサビリティが要るなら `REQ-{NAME}-{NNN}` を振る（任意。NAME はドメインの短い語を提案して進める）。

### 4. 相互参照

生成したファイルのパスを提示する。対象に起票 memory があれば、ドキュメントのヘッダ（Related）に memory ID を書き、memory 側にはファイルパスを追記して往復を閉じる。

## Living Documentation

> 文書には What、memory には Why

生かし方（同じ PR で触る、書き換えより追記、消さず Deprecated）は [spec-design-guide](../spec-design-guide/SKILL.md) を参照。
