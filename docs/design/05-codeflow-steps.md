# 05. codeflow のステップ構成

> **Status**: Active
> **Related**: `mem_1CgYPcydRMs1DE88VjS4FL`（アクションと裁定）、design 02（ブランチのステージ）、design 04（PR のマージ判断）
> **対象**: `skills/codeflow/SKILL.md`, `skills/spec-design-guide/SKILL.md`, `skills/branch-step/SKILL.md`, `skills/chronista-style/SKILL.md`

## Abstract

codeflow の流れを、文書と操作が**実際に起きる時点**に並べ直す。

```
Spark → Conception → GO → Spec → Design → Implementation → Guide → PR → Release（条件付き）→ Learning
```

branch-step のステージ（0 思いついた → 1 spike → 2 wip → 3 review → 4 nightly → 5 main → 6 学び）と対応する。GO = spike → wip の瞬間、PR = wip → review → nightly、Release = nightly → main。

## 何を動かしたか

| 前 | 後 | 理由 |
|---|---|---|
| `SDG → Branch & PR → Implementation` | `Spec → Design → Implementation → Guide → PR` | 「Branch & PR」は時点の違う二つ（ブランチは実装の前、PR は後）を一つにしていた。guide には流れ上の居場所が無かった |
| Branch が独立のステップ | GO に吸収 | spike は Conception 中に切られ、GO で wip に昇格する。ブランチの誕生はステップではなく GO の瞬間の一手 |
| SDG 一つ | Spec / Design / Guide | 書ける時点が違う。spec / design はコードの前、guide は動いたものを見てから |
| アクションを閉じる・design を Active にするのは Release | PR のマージ時 | Release は条件付き。release しないプロジェクトでは閉じる手順と Active 化が消えていた。Release は Status log にバージョンを一行 |
| slug は生まれてから不変 | wip 以降不変 | spike の名前は仮。GO で実装内容と合わなければ付け替える（mako 裁定） |
| 「Issue 連携」が SDG 配下 | GO 配下 | 起票の瞬間は GO |
| 「1 振る舞い 1 単位」が SDG | Implementation の頭 | それはテストリストの話 |

## 語彙

同じ PR で揃えた語: 版 → **バージョン**、背骨 / 尻尾 → **共通手順 / 後工程**（release）、段 → **ステージ**（`<stage>/<slug>`）、起票 memory → **アクション**（creo-memories の todo。ツール名は `create_todo` / `complete_todo` のまま）。設計哲学の **actions**（Grokking Simplicity）とは別の語なので、タスクの方はカタカナで書く。

## やってはいけない

- ステップに番号を振らない。流れは依存の矢印だけで語る（番号は過去に全廃した）
- 「PR のマージ条件」の見出しを変えない。design 04 がアンカーで参照している
- 閉じる手順を条件付きのステップ（Release）に置かない。必ず通るステップ（PR）に置く
- Spec と Design を一つに戻さない。同じ一座りで書くことは多いが、How は What の後という依存を名前で残す

## Status log

- 2026-10-30: Conception（mako「Implementation ってここでいいの？」「PR のあとってこと？」「Spec → Design → Implementation → Guide でもいいかもね」）と GO「今までの観点盛り込んで GO」を受けて Draft。codeflow / spec-design-guide / branch-step / chronista-style / README / design 02 を `wip/codeflow-steps` で同じ PR に。
- 2026-10-30: PR #9 を squash merge（nightly `2db47ea`）。mako「マージして」。Status を Active に。
