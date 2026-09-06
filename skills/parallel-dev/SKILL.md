---
name: parallel-dev
description: 並列開発の作業単位を決めるとき、スコープが混ざったとき、worktree / VP lane / stacked PR のどれを使うか迷ったときに使用。「隔離・出荷」2層モデルで道具を選ぶ判断スキル。
metadata:
  version: "0.2.1"
  tags: "parallel, worktree, vantage-point, stacked-pr, workflow"
---

# 隔離・出荷 — 並列開発2層モデル

## Core principle

**並列開発で本当に要るのは「実行の隔離」だけ。**

ビルド・テストが互いを壊さずに走ること — これが並列性の本体で、worktree が解く。
書き込みの帰属（どの変更がどの branch か）は、専用ブランチ + ハンク単位のコミットで足りる。

## 2層モデル

| 層 | 道具 | 解く問題 |
|---|---|---|
| **隔離** | worktree（小タスク = session worktree / 大タスク = **VP lane**） | テスト・ビルドが独立に走る |
| **出荷** | GitHub native stack（`gh stack`） | 依存 PR の列車。bottom merge で server-side cascading rebase |

worktree は「作業ディレクトリごと分ける」ので、隔離は構造的に保証される。
1つの作業コピーに複数スコープを同居させる方式は、テストが混合状態に対して走るため採らない。

## 判断ルール

1. **小タスク（1セッションで完結）**
   → session worktree（Claude Code では利用可能なら `EnterWorktree`、Codex では提供されている worktree 機能か `git worktree add`）。lane には紐づけない。

2. **大タスク（並列 orchestration・独立したビルド/テストが必要）**
   → 最初から VP lane（`vp flow handoff <name> --task-spec <file|->`）。
   VP が worktree を native 所有する（B方針）。

3. **メイン作業中に別スコープの修正が混ざった**（「ここでこのバグ直しちゃえ」）
   → 手は止めない。そのまま直し、コミット時に `git add -p` でハンク単位に割って
   別ブランチへ。混ざりを咎めず、後から割る。

4. **修正の検証・出荷を委譲したい**
   → ブランチを push → `vp flow handoff` で performer へ。performer は自分の
   worktree で test → PR。自分は主線タスクに留まる。

5. **依存関係のある複数 PR を出す**
   → native stack で積む。bottom merge 後の rebase はサーバー側が面倒を見る。

## アンチパターン

- ❌ 小タスクを VP lane で起こす（Stand 二重起動・port 消費・`.vp/lanes/` 肥大）
- ❌ 大タスクを単一作業コピーで並列化する（実行隔離がない）
- ❌ 1つの作業コピーに複数スコープを同居させ、そこでのテスト結果を
  スコープ単体の正しさの根拠にする（単体の保証は worktree か CI の per-PR ビルドで取る）
- ❌ worktree を切ったまま放置して乱立させる（gitnexus / sem のインデックスが増える。
  完了したら畳む）
