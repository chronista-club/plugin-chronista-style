---
name: tdd
description: 機能追加・バグ修正の前に使用。テストファーストで実装する規律スキル。
metadata:
  version: "1.3.1"
  tags: "discipline, testing, tdd, red-green-refactor"
---

# Test-Driven Development (TDD)

> **テストを先に書く。失敗を見る。最小限のコードで通す。**

**Core principle:** 失敗を見ていないテストは、正しいものをテストしているか分からない。

## いつ使うか

新機能の実装、バグ修正、リファクタリング、振る舞いの変更。

**省略してよいもの:** 使い捨てプロトタイプ、自動生成コード、設定ファイル。該当すれば聞かずに省略してよい。省略したことは最終報告に書く。

## The Iron Law

```
テストが先に失敗しない限り、プロダクションコードを書かない
```

テストより先にコードを書いてしまったら、一旦退避し、テストが**実際に失敗する**ことを確認してから戻す。

## RED-GREEN-REFACTOR サイクル

```
RED（失敗するテストを書く）→ 失敗を確認 → GREEN（最小限のコード）→ 通過を確認 → REFACTOR（きれいにする）→ 次のテスト
```

### RED - 失敗するテストを書く

1つの振る舞いを表す最小限のテストを書く。

```typescript
// 良い例: 明確な名前、実際の振る舞いをテスト
test("3回リトライして成功する", async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error("fail");
    return "success";
  };

  const result = await retryOperation(operation);

  expect(result).toBe("success");
  expect(attempts).toBe(3);
});
```

**要件:** 1つの振る舞い、明確な名前、本物のコード（モックは最終手段）

### RED確認 - 失敗を見る

そのプロジェクトのテストランナーで対象テストを実行し、確認する:

- テストが**失敗する**（エラーではなく失敗）
- 失敗メッセージが期待通り
- 機能未実装が原因で失敗（タイポではなく）

テストが通る場合は既存の振る舞いをテストしている。テストを直す。

### GREEN - 最小限のコード

テストを通す最もシンプルなコードを書く。

```typescript
// 良い例: テストを通すのに十分なだけ
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 3; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === 2) throw e;
    }
  }
  throw new Error("unreachable");
}
```

テスト以上の機能追加、他コードのリファクタ、「改善」はここではしない。

### GREEN確認 - 通過を見る

テストランナーで実行し、確認する: テスト通過、他テストも通過、出力がクリーン。

### REFACTOR - きれいにする

GREENの後のみ: 重複除去、命名改善、ヘルパー抽出。テストは常にGREEN。振る舞いは足さない。

## Red Flags - 止まる合図

- テストより先にコードを書いた
- テストが即座に通った
- なぜ失敗したか説明できない

いずれかに該当したら、失敗を観測できる状態に戻してからやり直す。

## バグ修正の例

**バグ:** 空メールが受け入れられる

**RED:**
```typescript
test("空メールを拒否する", async () => {
  const result = await submitForm({ email: "" });
  expect(result.error).toBe("メールアドレスは必須です");
});
```

**RED確認:** `FAIL: expected 'メールアドレスは必須です', got undefined`

**GREEN:**
```typescript
function submitForm(data: FormData) {
  if (!data.email?.trim()) {
    return { error: "メールアドレスは必須です" };
  }
  // ...
}
```

**GREEN確認:** `PASS`

**REFACTOR:** 複数フィールドのバリデーション抽出（必要なら）。

## テストリストの 3 層 SSOT

TDD のテストリストは**変化速度で層を分ける**。

| 層 | 責務 | 寿命 | 場所 |
|----|------|------|------|
| **memory（creo-memories）** | ユーザー観測可能な成功基準（不変） | todo 完了まで | memory 本文 |
| **PR description** | テストリスト（S/M/L ラベル付き、☐→☑） | PR マージまで | GitHub PR body |
| **テストファイル** | テストの構造（describe / context / it 等）= リストの実装形 | コードの寿命 | テストファイル |

判定ルール:
- 「このフィーチャは何を達成する？」 → **memory** を見る
- 「今どこまで進んだ？」 → **PR description** のチェックリスト
- 「何がコードで保証されているか？」 → **テストファイルの実行結果**

紐付け: memory ID を PR description 冒頭に記載。テストファイルの先頭コメントに memory ID を入れる。

### 連携テスト（Medium）の粒度

「**モック不要で繋がる範囲**」が Medium の上限。外部 SDK / API / Network / DB / DOM の境界を越えない、自分たちのコードが素のまま動く部分のみ対象にする。モックを書きたくなったら Large 層（E2E）へ移行するか、単体テスト側に分解する合図。

## 完了チェックリスト

- [ ] すべての新機能/メソッドにテストがある
- [ ] 各テストの失敗を目視で確認した
- [ ] 各テストが期待通りの理由で失敗した
- [ ] 各テストに最小限のコードで通した
- [ ] 全テスト通過
- [ ] 出力がクリーン（エラー・警告なし）
- [ ] エッジケース・エラーケースもカバー
- [ ] テストの量は述べられた振る舞い 1 つにつき 1 本が目安。隣接するテストファイルと同じ粒度。使い捨ての確認スクリプトは残していない

チェックできない項目があれば、完了を宣言せず埋めてから進む。

> **t-wadaに突っ込まれないテストを書く。**
> テストの価値は「通ること」ではなく「失敗で問題を教えてくれること」。
