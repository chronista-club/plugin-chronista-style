# Changelog

本プラグインの主要な変更を [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に沿って記録する。
バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準拠する。

プラグイン全体の version は `.claude-plugin/plugin.json` を正とする（SSoT）。
各スキル個別の version は該当 `SKILL.md` の `metadata.version` に記載。

## [Unreleased]

### Changed
- 検証環境を `.mise.toml` で宣言（python 3.12、`.venv` は mise が作る、`mise run check` = validate + test + lint、`mise run package`）。導入ガイドの手動 venv 手順を置き換え

## [0.32.0] - 2026-09-06

### Added
- manifest 同期・検証・配布 ZIP 作成コマンドと CI を追加。公開 GitHub marketplace からの両環境の導入・更新手順を記載。
- Claude Code / Codex の Stop ログ読み替えと hook 回帰テスト、共通の記憶接続ガイドを追加。
- Codex 用 manifest を追加し、共通の `skills/` を参照。
- `spark` / `sdg` / `release` の共有スキルを追加。

### Changed
- 新しい正本 `plugin-chronista-style` に合わせて両 manifest の repository/homepage と導入・設計文書を更新。配布準備中と Grok 未検証の状態を明記。
- SessionStart は入力の cwd を優先。記憶の自動注入を条件付きにし、未接続時の扱いを明記。Stop は最終メッセージ入力を優先し、差し戻しループを防止。
- Claude のコマンドは共有スキルへの入口に統一。codeflow の起動手順もスキルへ集約。
- 質問・worktree・合議のツール指定を実行環境に対応。スキルの版・タグ・出典を `metadata` に移動。

## [0.31.1] - 2026-09-06

### Added
- `chronista-style` `6.1.0` → `6.1.1`: 冒頭の「私は Chronista として活動する」の隣に、v0.31.0 リリース直後の mako の言葉を原文のまま — 「Chronista Club へようこそ。Creater Mind を忘れずに。世界を変えていこう」（mako「もちろんおいて欲しい」、決定記録 `mem_1CekjuJJid5xQb3GB9iiNq`）

## [0.31.0] - 2026-09-06

### Changed
- **棚卸し後の読み直しからの 4 点**（Claude の提案、mako「その提案入れましょう。あなたの style でもある。こういうのは気兼ねなく、これからも」）
  - `hooks/session-start.sh`: 規律エッセンスに 2 行 — 「火花が降ったら `/spark`」と基本姿勢の一行（穏やかに、真面目に、ユーモアを忘れずに）。常時注入だけがスキル発動前に効く場所で、`/spark` は存在を覚えていなければ使えない
  - `hooks/session-start.sh`: Atlas 候補の「exact match が無ければユーザーに確認する」→ 同じ repo の過去の todo の Atlas に倣い、前例も無ければ Personal に置いて一言添える。聞かない（本セッションで実際にここで一度止まった。`/spark` の「置き場で止まらない」と同じ判断）
  - `commands/sdg.md`: 冒頭で「どの種類？」「対象は？」と AskUserQuestion を 2 回打つ旧質問票の最後の生き残りを Conception 型に。種類と対象はブランチ・memory・commit から推測して提示し、聞くのは分岐だけ。空のひな形を渡さず分かっていることは埋める
  - `codeflow` `4.2.1` → `4.3.0`: Conception「調べる」に火花の再訪 — 同じ領域の `spark` を `search` で拾い、繋がるものがあれば会話に出す。`/dashboard` を消したので溜まった spark を眺める場所が無く、仕組みを作らず一行で経路を作る。Context Engine の自動注入が拾うなら不要になる前提
- **`/release` を「背骨 + 尻尾への委譲」に書き直し**（mako「release はプロジェクト固有の方がいいのかな？」→ 実測で「背骨は共通、尻尾は全部違う」と分かり、その切り方で GO）。直近 30 日で動いた 12 リポジトリを実測: 背骨（版の正本を検出 → 版を決める → CHANGELOG → release commit → nightly を main に merge → main で tag → push → GitHub Release）は VP / unison / plugin 4 本で同じ形。尻尾は全部違う — creo-memories は tag push で CI が ghcr に image、creo-ui は main push で CI が package ごとに tag と publish（自分で tag を打ってはいけない）、fleetstage は main push でパス条件付き image、Ladyland は `scripts/build-app.sh --install` で署名・公証・`/Applications` 配置（版は `git describe --tags` から取るのに version tag が無く 0.1.0 で焼かれている）、VP は CHANGELOG 無し
  - 旧コマンドは「今のブランチで commit して tag」までで、root の「ブランチ運用（nightly trunk）」にある nightly → main の merge commit・main での tag・GitHub Release を持っていなかった（v0.30.0 では手で補っていた）。Living Documentation の不一致
  - 背骨: 現在地と形式を聞かずに全部読む（版の正本 / nightly モデルか main モデルか / clean & 最新 / 直前 release commit の流儀 / CI の起点 / 尻尾の有無）→ **確認は 1 回**（版・変更スキル・merge・push・tag・Release・起動する CI と尻尾を一つの提示で GO）→ 書く（CHANGELOG は**無ければ作らない**、Cargo.lock 追随）→ nightly モデルなら `--no-ff` で main へ merge して main で tag、CI が main で tag を打つ形式なら自分で打たない → Tag Verify Gate に「main 上にあること」を追加 → `gh release create` → CI を `gh run watch` で見届ける
  - 尻尾の検出: `mise run release` → `scripts/release*` → リポジトリの `.claude/skills/release*/SKILL.md` / CLAUDE.md の Release 節。実機を伴うもの（署名・配置・転送）は実行して**実機確認待ち**で止める。見つからなければ起動した CI と手で残っていることを報告して終わる。プラグイン形式は marketplace が版を pin していないので同期不要、`claude plugin update` を案内
  - 「尻尾をプロジェクトに置くとき」節: 背骨に分岐を足さず、`mise.toml` の `[tasks.release]` / `scripts/release.sh` / `.claude/skills/release/SKILL.md` のどれかに。尻尾は「tag が打たれた後に何をするか」だけ
  - `codeflow` `4.2.0` → `4.2.1` / `README.md`: Release ステップとコマンド表の説明を同期
- **設計哲学を三本に、reference を「本の要約」から「設計の判断集」に**（mako 2026-09-06「この手法だけで、強く美しいは、むずかしいのでは？」→「責務周りかな？記述がここにあるべきなのか、結構似たような実装があったり、よく交通渋滞を引き起こしてた」→「最初から完璧なコードを目指すのは、未来を予想できないのと同じで無理。開発中に気づく事と、それの改善を継続して行えるかの方向で考えたい」→ GO）
  - `chronista-style` `6.0.0` → `6.1.0`: 設計哲学を **責務・Simplicity・Straightforward** の三本に。冒頭を「最初から完璧を目指さない。開発中に気づき、直し続けるための三つの軸」に。責務 = 置き場・所有・変更の局所性（「この記述が変わるとき、何が変わったからか」「片方のバグはもう片方でもバグか」「何本の道を塞ぐか」「開く理由は何通りあるか」）。Straightforward に「正本は一つ、残りは導出」「次の consumer が現れてから広げる」を追加。適用範囲にリファクタ行
  - `reference/grokking-simplicity.md`（284 行、本の忠実な要約で 3 分の 2 が定義）→ **`reference/design-judgments.md`**（122 行）。design docs の「やってはいけない」18 本・レビュー記録・Ladyland のリファクタ履歴から判断を掘ると、Grokking Simplicity で説明できるのは 3 分の 1 で、残りは責務（VP の「ディレクトリは Project に持たせない」、vpcode の「形が似ていても責務が違えば共通化しない」、Ladyland `RotoService` 1,944 → 1,677 行でも兼務は残る）と Straightforward（「離散状態フラグを再導入しない、全て射影」「供給路は一本」「次の consumer が来てから広げる」）だった。第一部「気づきの問い」（症状 → 問い → 実例、軸ごと）、第二部「気づいたときの作法」（手は止めない・範囲外は `/spark`・抜く前に意図を 1 本のテストで pin・実測と制約は文書に・土台は直列・基準は「次に触るときに前より見通しが良い」）、言語での表現（Rust に加えて Ruby）、チェックリスト。原典は Simplicity の源として残す
 — harness との綱引きの解消と足場の縮約**（mako 裁定 2026-09-06、主題ごとに精査して「大賛成」「いいね」「3 つとも GO」）。全体 2,868 → 1,654 行
  - **語調の原則を root の「基本姿勢」に新設**（決定記録 `mem_1CekeYAi956A8RcpNK4h73`）: 穏やかに、真面目に、ユーモアを忘れずに。きつい言葉を使わない、犯人探しではなくコードと成果物とユーザーへの真摯さから発言する、GO の前は自由な構想で GO の後は走り切る、質問票を作らない。codeflow の「ユーモアを忘れない 🎭」節（OK / NG 例リスト）はここに統合して削除
  - **規律 3 スキル — 中身は残して圧力を抜く**。「合理化を見破る」表を 3 本とも削除（「疲れた ≠ 免罪符」「TDD は教条的」は人間向けの説教で Fable には効かない）。「資格はない」「交渉の余地がない」「削除は削除」「〜するな」を平叙文に。Red Flags は止まる合図として短く残す。末尾の「creo-memories 連携」節 ×3 は root と重複のため削除。Fable は指示に過剰に従うので、圧力は規律を強めず境界をずらす — 効くのは脅しでなく境界の正確さ
    - `tdd` `1.2.0` → `1.3.0`: 例外（プロトタイプ / 自動生成 / 設定ファイル）を「ユーザーに確認」から「該当すれば聞かずに省略してよい、最終報告に書く」に（本体の自律実行文との綱引き解消）。dot 図と `bun test` 固定を外し「そのプロジェクトのテストランナー」に。root から「テストリストの 3 層 SSOT」「連携テスト（Medium）の粒度」を移設し `*.test.ts` / `describe/it` 固定を言語中立に
    - `systematic-debugging` `1.0.2` → `1.1.0`: 「あらゆる技術的問題に使え」を削除（over-trigger の誘い）
    - `verification` `1.2.2` → `1.3.0`: hedge 禁止を「完了宣言の中で」に限定し「検証できていないことは完了とは別に最初に言う」を併記（本体の不確実性表明の要求と綱引きしていた）。Gate Function 5 ステップを 3 行に、「パターン」「最後に」を削除。よくある検証不足に「設計に触れた変更は design が同じ PR にある」を追加 — Living Documentation の唯一の関門をここに置く
  - **`spec-design-guide` `1.1.0` → `2.0.0`（442 → 85 行）— 「何を書くか」は残し「どう書くか」は落とし、「どう生かすか」を本体に**（mako「何を書くかは読みやすい形式を定義したいけど、書き方については細かくしない」「SDG をいかに文書として機能させつつ、Living Doc させやすい形に落とし込むのが大事」）。203 本の実 docs を実測: Status ヘッダ 57 / REQ-ID 21 / Related 7 が生きており、`VP-SPEC-001` ID 体系 6・Author 4・Implements 2 は死んでいる。死んだ規約は全部「手で保守が要るもの」。design には「関連」35・「やってはいけない」18・「Status log」8 が自然発生しており、追記型だから生きていた
    - 残す: 3 層の役割、各層 4 段階の骨格（順番・見出し名は強制しない）、「関連」「やってはいけない」の歓迎、REQ-ID（任意）
    - ヘッダは Status / Related / **対象コードパス**だけ（日付・作者は git）。対象パスが「このコードを触るとき、どの文書を見るか」の grep 索引になる
    - 生かし方: コードと同じ PR で触る / 書き換えより追記（Status log、大改版は Supersedes で新番号）/ 消さず Deprecated / 地雷は「やってはいけない」に戻す / What は文書・Why は memory
    - codeflow との対応表: Conception の「調べる」で対象パスの docs を読む → GO が要った変更（分岐があった）だけ design に書く → Implementation で追記 → PR の前に verification → Release で Status を Active に。**GO の条件がそのまま SDG の条件**なので、起動条件を別に定義しない
    - 削除: テンプレート 3 本（退避せず削除。骨格から生成できる）、`{PRJ}-SPEC-NNN` ID 体系、D{N} 番号、Changelog 運用規則、Status 遷移図、Mermaid 種類テーブル（22 種）、「自動的に適用」「禁止事項」「必須手順 7 ステップ」。`reference/living-documentation.md`（230 行）は SKILL 本文に吸収して削除
    - `commands/sdg.md`: 要件 ID の「候補 3 つを AskUserQuestion」を「任意、NAME を提案して進める」に。ヘッダ規約を同期
  - **`chronista-style` `5.6.2` → `6.0.0`（409 → 236 行）— root は「どこに何があるか」だけ持ち、子スキルの要約を持たない**（要約は本体とずれる。root のフロー図には Requirements ステップがあり codeflow には無かった）。削除: 「開発フロー: codeflow」節と「ドキュメント管理: SDG」節の要約、スキル優先順序・発動テーブル・Rigid / Flexible 分類（「該当判断はモデルに委ねる」と半端に共存していた）、「最新版を読む」（スキルは発動のたびに読まれる）、Update Finalization の 7 種類表（`.fleetflow/*.kdl` / Auth0 tenant 等の特定プロダクト詳細。不可逆操作の確認は本体が既に要求）。テストリスト 3 層と Medium 粒度は tdd へ移設。description から「包括的」を外す（発動判断に使われる語で過剰発動を誘う）。記憶に刻む瞬間に「降ってきた火花（`/spark`）」を追加
  - **`codeflow` `4.1.1` → `4.2.0`（217 → 79 行）**: ユーモア節を root に統合、Bite-Sized Task（「2〜5 分」「完全なコードを明記」「Step 1〜5」= superpowers の計画書作法、計画に実装コードを書かせる二度書き）を「1 振る舞い 1 単位、手順は tdd」に、GO 後の 3 段落目を 1 文に（本体の Delivering work と同文だった）、ベストプラクティス 6 項・SDG 原則節・ディレクトリ構成（`project/spec/` で SDG の `docs/spec/` と食い違っていた）を削除。各ステップに Living Doc の 1 行（調べる / GO / Implementation / Branch & PR / Release / Learning）
  - `commands/release.md`: Step 4「SKILL.md を bump するか」を毎回 AskUserQuestion していたのを、前回タグからの diff で変更スキルを列挙して版の確認と一緒に 1 回で確定に
  - `council` `2.0.0` → `2.0.1`: 「スマホ画面で読める長さ」→「短く」。`parallel-dev` `0.2.0` → `0.2.1`: 「背景」節（CHANGELOG と重複）を削除
  - `README.md`: スキル表・コマンド表を同期、スキルタイプ節と起動タイミング表（root から削除した表の写し）を削除、hooks の説明を追加
- **フローの先頭を Spark → Conception → GO に組み替え、「ヒアリングファースト」を廃止**（mako 裁定 2026-09-06「hearing First も、その時々の進めたいことで変わってくるし、いつも議論したくなったら『ちと相談なんだけど』とか私がトリガーになってる。想起されるのが先で、1st ではない」→ 名前は「Conception だね。それ採用」）。Discovery → Second Opinion → Discussion → Hearing のパイプラインは実態と違い、実際は想起（どちらからでも）→ 順不同の会話 → GO の一本線。硬い関門は GO だけ
  - `codeflow` `3.3.0` → `4.0.0`: 先頭を **Spark（想起）→ Conception（構想）→ GO（実装前の合意）** に。Discovery / Discussion / Hearing / council は Conception の中の「手」に格下げ（順番なし）。Spark は AI からも起きてよい（「気になることがある」で会話を開く）。GO の瞬間に memory を `spark` → `todo` に
  - **Hearing を「質問票」から「理解の提示と差分」に**（mako 裁定「hearing の時点のルールは自由な意見交換じゃなくなるよね。そこ改修していこう」）。「実装前に**必ず**質問」がルートと codeflow に 3 回、`AskUserQuestion` が hearing の「軸」としてコマンド側 6 箇所で指名、「最大 4 問 / ラウンド分け / コツ 4 項」で手順化されていた。実際のリズム（0.29.0 分析: 「進めて」49 回・「どう？」34 回、本セッションも AskUserQuestion 0 回）は AI が理解を提示して人間が訂正か GO を返す形。理解を短く書く → ズレと分岐だけ聞く → 「AI の理解」を起票 memory に書き戻す。AskUserQuestion は分岐が 2〜4 個に離散的に絞れたときだけ
  - `chronista-style` `5.3.1` → `5.5.0`: フロー図・基本姿勢（「ヒアリングファースト」→「GO の一本線」）・「Conception のルール」を同期。Issue-first の起票テンプレートに「AI の理解（Hearing のたびに更新。裁定の原文は不変、理解はその上に積む）」— 人間の言葉は不変、AI の理解は注釈として積む層の非対称（spark `mem_1Cekaq6HzcGZFRd92Ydk3F`）
  - `commands/codeflow.md`: 全面書き換え。「どのステップから入りますか？」メニュー廃止、理解の提示の中で入口を自分の判断として述べる（`commands/hearing.md` も同様に書き換えたが、最終的に削除 — Removed 参照）
  - `hooks/session-start.sh`: 規律エッセンス 4 行目に「GO の前は自由な構想（Conception）」を前置
  - **新コマンド `/spark`**（mako 発意「私が spark したときに、そのモードに切り替わって、アイデアをすぐ書き込む経路が欲しい」→ GO）。`/spark <言葉>` で原文のまま `category: spark` に pack し memory ID を一行返す。引数が無ければ「何が降ってきた？」と一行聞いて次の発言を pack。要約しない・見出しを付け直さない・タグを推測しない・成功基準を聞かない・作業に入らない（整えると火花が死ぬ）。重複検出は切る。Atlas は session-start の候補に exact match が無ければ Personal に入れて一言添える。`codeflow` `4.0.0` → `4.1.0` / `chronista-style` `5.5.0` → `5.6.0` の Spark 節に入口を追記。会話中の「ちと相談なんだけど」の自動 spark 化はしない（Fable のスキル過剰発動で雑談まで積む事故を避ける。構えを Conception に切り替えるだけ）
  - `README.md` / `.claude-plugin/plugin.json`: 「ヒアリングファースト / hearing-first」を Spark → Conception → GO に。keywords `hearing-first` → `conception`

### Removed
- **`commands/hearing.md` を削除、Conception の手から「Hearing」のラベルを外す**（mako「hearing は残しておいた方がよい？」→ 削除を推奨 → GO）。中身が「理解を提示してズレと分岐を聞く」になった時点で `/codeflow` の 3 手目と同じになり、Conception の中では文脈が揃えば言われなくてもやる動きなので、コマンドが加える規律が無い（`/spark` は「解釈するな」の縛りのために入口が要るが、hearing にはそれが無い）。「Hearing」は聞き取りの語で質問票の世界の言葉。見出しと本文が綱引きしないよう「理解を書く」だけ残す。`codeflow` `4.1.1` / `chronista-style` `5.6.2`（起票テンプレート「Hearing のたびに更新」→「理解が変わるたびに更新」）/ `README.md` 同期。コマンドは `/codeflow` `/sdg` `/release` `/spark` の 4 本
- **`commands/dashboard.md` を削除**（mako 裁定 2026-09-06「使った事ないな」→「ならオミットしとこうか」）。0.26.0 で Linear から creo-memories ベースに全面書き直したが、その後一度も呼ばれなかった。「全プロジェクトの active todo を一覧する」需要はセッション開始時の Context Engine 注入と creo の Web UI で満たされていた。0.28.0 の「未使用は削る」原則を適用。`chronista-style` `5.6.0` → `5.6.1` / `README.md` の参照を除去。コマンドは最終的に 4 本（`/spark` 追加、`/dashboard` `/hearing` 削除）

### Fixed
- **スキル棚卸し S 群 — 矛盾・実在しない参照の解消**（mako 発意 2026-09-05「Fable 5.1 の登場前に一度整理したが、もう一度全体を俯瞰してクリーンアップしたい」→ 全 2,868 行を精査し S / A / B / C の 4 段で board 提示 → 「S群着手していこうか」で GO。A / B 群は裁定後の別 PR）
  - `verification` `1.2.1` → `1.2.2`: Iron Law 直下の「**このメッセージ内で**検証コマンドを実行していないなら資格はない」を「同じセッション内で観測した tool_result を指させるときだけ」に。0.30.0 で tripwire をセッション全体に広げたのに本文が旧仕様のままで、本体の「前ターンの観測も含めて単独で読める recap」要求と衝突していた。「1メッセージ1検証。緑宣言の直前は単独でツールを呼ぶ」は本体のバッチ化ナッジと綱引きするため削除
  - `spec-design-guide` `1.0.1` → `1.1.0`: 責務分担を 3 層 → **2 層**（memory = 経緯 / `docs/` = 確定版）。「GitHub Issues/Project = 現場」の行と「GitHub Issue でタスク化」を除去し memory 起票へ。0.26.0 の memory SSOT 裁定に SDG だけ追いついていなかった。`reference/living-documentation.md` のコミットテンプレート `Refs: #issue番号` も memory ID に
  - `codeflow` `3.2.0` → `3.3.0`（283 → 217 行）:
    - Branch & PR の `mako/{slug}` 規約と「main に直コミットしない」を、ルートの「ブランチ運用（nightly trunk）/ Branch slug」への参照に置換。実ブランチは `{type}/{slug}` で運用されており codeflow だけ古かった
    - Release の team-b 連携行（Aerosmith → Sticky Fingers → Gold Experience → `/update-plugin`）を削除。team-bucciarati 0.19.0（インストール中）に Aerosmith / Gold Experience は存在せず、`/update-plugin` は本プラグインの自己参照にしか無いことを実測。手順は `/release` への参照 1 行に
    - Second Opinion の「Gemini MCP 経由で質問」を `council` への参照に置換。Gemini MCP は `.mcp.json.example` にも共有 store にも無い。Discussion の「Geminiさんはこう言ってます」も council の verdict 共有に
    - memory-as-issue の API 詳細（lifecycle = category / `patch_memory` CAS / `supersedeCandidates` / Cross-Project Handoff）を削除し「作法は `creo-memories` スキル、ここには複写しない」の 1 段落に。`commands/dashboard.md`（active / done の 2 値）と creo-memories 0.54.1 自身（lifecycle = status）と 3 通りに割れていた。他プラグインの仕様の複写は複写元が動くたびに腐る
  - `commands/sdg.md` / `spec-design-guide`: spec / design の置き場を **`docs/` のみ**に統一（mako 裁定 2026-09-06「docsのみにしておくか。まずは」）。`/sdg` は spec / design を Creo Memories に保存し guide だけデュアルストレージ、SKILL は `docs/` が確定版、と真逆だった。手元 10 リポジトリで spec 38 / design 154 本が全て `docs/` にあり、memory の `spec` / `design` カテゴリは使用 0 件、design doc はコードと同じ PR で更新される（memory にはブランチが無い）ことを実測して裁定。SKILL の「確定版」を「本文（Draft から置き、コードと同じ PR で育つ）」に言い直し、往復は相互参照（docs ヘッダ Related に memory ID / memory にファイルパス）で閉じる。「repo の外から見える」要件は索引 memory（write-once + `/sdg` 自動生成 + 既存 docs の backfill の 3 点セット）として spark 起票し、今回は含めない
  - `chronista-style` `5.3.0` → `5.3.1` / `README.md`: フロー図の「Second Opinion（Gemini等）」を council に、「プラグイン同期（/update-plugin）」を削除。基本姿勢のセカンドオピニオンも council に同期

## [0.30.0] - 2026-09-03

### Changed
- **Fable 5.1 harness 注入文との衝突解消**（mako 裁定 2026-09-03「衝突は、自分もやだな。解消したいよね」）。Claude Code 本体が [Claude Fable 5.1 のプロンプティング](https://platform.claude.com/docs/ja/build-with-claude/prompt-engineering/prompting-claude-fable-5-1) の推奨文（進捗更新 / バッチ化ナッジ / Delivering work / 自律実行）を原文のまま system prompt に注入していることを実測。同じ文言は足さず、逆向きの文言だけを本体の語彙で言い直した
  - `hooks/session-start.sh`: 規律エッセンス 4 行目「設計判断は短い方針提示 → GO」を「ユーザーが選ぶべき分岐があるときだけ短い方針提示 → GO。GO の後はその範囲を最後まで走り切る」に。本体の「可逆な作業は聞かずに進める」と綱引きしていた
  - `codeflow` `3.1.0` → `3.2.0`: 実装前の合意に「GO の後」を追加 — 合意した範囲は走り切る、質問は回答に依存しない部分を済ませてから進捗と一緒にターン末尾で
  - `hooks/fabrication-tripwire.sh`: 裏付けの tool_result を同一ターンから **transcript 全体**に拡張。本体が求める「単独で読める recap」が前ターンの観測結果を再掲すると false block していた（本セッションで実際に block されて再現）。「一度も produce されていない結果を止める」目的は保持。scratch test 3 ケース（cross-turn recap / 純粋な捏造 / 同一ターン裏付け）で RED → GREEN を観測
  - `verification` `1.2.0` → `1.2.1`: tripwire の説明を「同じセッション内の」に同期。`hooks/hooks.json` の description も同期

### Added
- `chronista-style` `5.2.0` → `5.3.0`: Issue-first に「作業中に見つけた対象外の問題は直さず spark 起票、最終報告で触れる」を追加。docs「follow-up として summary で報告せよ。Fable 5.1 は近くのコードを直したがる」の Chronista 版（follow-up の行き先 = creo-memories）。parallel-dev の「混ざったら `git add -p` で割る」は事後策で、事前策が無かった
- `tdd` `1.1.0` → `1.2.0`: 完了チェックリストにテストの**量**の目安（振る舞い 1 つに 1 本、隣接ファイルと同粒度、使い捨て確認スクリプトは残さない）。docs「Fable 5.1 は変更に見合う以上のテストファイルをコミットする。指示で大幅に減り成功率は不変」への対応

## [0.29.0] - 2026-09-01

### Added
- **セッション分析（29 プロジェクト・509MB の transcript）からの改善盛り込み**（mako 裁定 2026-09-01、全 4 項目採用）
  - `chronista-style` `5.1.0` → `5.2.0`: **North Star「強く美しい構造（Strong & Beautiful）」**を設計哲学の上位に新設し、強さ（変化と時間に耐える）と美しさ（読み手に一目で伝わる）を定義。Simplicity & Straightforward が両方を**同時に**生む技法であることを明文化し、判定基準「これは強く、かつ美しくするか？」と例（重複統合の Yes/No）を付す
  - `hooks/session-start.sh`: **規律エッセンスの常時注入** — 54 セッション中 chronista-style スキルの明示発動が 2 回のみという実測を受け、規律 3 スキル + 合意フローのエッセンス 4 行を additionalContext で常時届ける（スキル本文は従来どおり発動時のみ）
  - `verification` `1.1.0` → `1.2.0`: **ユーザー観測の層** — agent の green で閉じない変更（実機・実 UI・実環境）は「実機確認待ち」で止める。ladyland の実機検証ループ（「実機」言及 75 回）の明文化
  - `codeflow` `3.0.0` → `3.1.0`: **合意の粒度**を明文化 — 短い方針提示に「いいね」「進めて」の GO で走る（「進めて」49 回・「どう？」34 回の実リズムに整合）。Learning に**裁定の原文引用**ルールを追加

## [0.28.0] - 2026-09-01

### Removed
- **fleetstage 関連を全削除**（mako 裁定 2026-09-01「fleetstage はオミット仕様。関わるものは一旦全部削除」）
  - `skills/size-stepper/` — origin = fleetstage-hq。実コード（`~/repos/fleetstage/.../ui/`）が SSOT で、参照先なしでは再現不能
  - `skills/cross-build-image/` — origin = fleetstage Phase B-3。実行例・参考実装とも fleetstage-hq-api 依存（同梱 `scripts/build-and-push.sh` 含む）
  - `skills/route/` の FSC-22 ケーススタディと、`commands/route.md` の FSC 系引数例
- **ミニマム化 — 「プロダクト群を横断する共通の開発スタイル基盤」に絞る**（mako 裁定 2026-09-01）。スキル 15 → 8、コマンド 6 → 5
  - `skills/santa-method/` — **team-bucciarati へ移設**（多 agent 敵対的検証は agent team プラグインのドメイン。中身は無改変で移動、slim 化は team-b 側の棚卸しで行う）
  - `skills/code-review/` — 削除。汎用レビューは Claude Code 標準の `/code-review` が受け、Stand 観点別 dispatch の知識（`reference/stand-mapping.md`）は team-bucciarati へ移設
  - `skills/agent-harness/` / `skills/agent-introspection/` — 削除。発動場面が抽象的で、description のコンテキスト税が全スキル中最大級（計 470 字）だった
  - `skills/route/` + `commands/route.md` — 削除。Survey→Plot→Compare→Choose は codeflow の Discovery→Discussion と重複
  - `bin/setup` / `bin/setup-windows` は存置（コンテキスト税ゼロ、新マシン立ち上げと .mcp.json 復元 path として実用）

### Changed
- `council` `1.0.2` → `2.0.0`: 283 → 99 行に縮約。中核メカニズム（4 voice の役割、fresh subagent への文脈隔離 = anti-anchoring、Position 先行、Synthesize の bias guardrail、strongest dissent の可視化）だけを残し、The Iron Rule・NG パターン表・アンチパターン節・多 round 運用・クイックリファレンス・VP 固有の適用例を削除。santa-method（→ team-b）と `/code-review`（→ Claude Code 標準）への参照を新配置に同期
- `chronista-style` `5.0.0` → `5.1.0`: スキルツリーを 8 スキルに同期。発動テーブルの code-review 行を council 行に置換
- `README.md` / `plugin.json`: 冒頭にプラグインの存在意義を明文化 — 「Chronista のプロダクト群を横断する共通の開発スタイル基盤」（個別プロダクト名は列挙しない — 列挙は腐るため）

## [0.27.0] - 2026-09-01

### Removed
- **codeflow `reference/` 5 ファイル（計 3,969 行）を削除**（`codeflow` `2.1.1` → `3.0.0` の一部）: `claude-code-advanced-discoveries.md`（2025-11-18 時点の内部ツール調査）/ `claude-code-internal-tools.md` / `ask-user-question-tool.md` / `hearing-first.md` / `development-flow.md`。Claude Code 本体が保証するツール仕様のスナップショットはモデルと harness の進化で必ず腐り、古い仕様の注入はむしろ有害。現行モデル（Fable / Opus 世代）には手順の長大な例示も不要
- `chronista-style`: 廃止済み fleetflow プラグインのインフラ節・`openskills read` 参照 ×4・`gh issue create` ベースの旧タスク化フロー（memory-as-issue SSOT と矛盾）・発動テーブルのスキル非実在行（fleetflow / mise / Chrome DevTools）を削除。fleetflow CLI 本体は継続のため `.fleetflow/*.kdl` の変更検出行は温存
- `README.md`: 廃止済み fleetflow の関連プラグイン行を削除

### Changed
- **「モデルを型に嵌める拘束」を判断委任型に書き換え**（mako 裁定 2026-09-01「大胆に削る」— 作り込んだ harness / skill はモデル性能を落としやすい、Fable / Opus を信じる方向へ）
  - `chronista-style` `4.6.0` → `5.0.0`: The Iron Rule（1% でも該当なら発動・交渉不可）+ 合理化の罠テーブル → 「起動の基準」（該当判断はモデルに委ね、規律スキルのみ省略不可）。Ruby-first / KDL-first の「必ず比較案を共有」儀式 → 既定値の表明。creo-memories 節は Context Engine の自動注入を前提化し手動検索儀式を削除。一問一答の絶対化を解除（関連質問は束ねてよい、依存質問はラウンドを分ける）
  - `codeflow` → `3.0.0`: HARD GATE（設計承認なしにコードを書くな）→ 「実装前の合意」（設計判断を伴う変更のみ。明白な小修正は直進。判断軸 = ユーザーが選ぶべき分岐があるか）。Hearing の create_todo / complete_todo 儀式を AskUserQuestion 軸に簡素化
  - `route` `1.0.2` → `1.1.0` / `commands/route.md`: HARD GATE → **Confirm** フェーズに改称。path 選択のユーザー承認自体はスコープ判断として維持
  - `commands/hearing.md`: 質問ごとの todo 登録 → 一覧 → 一問一答ループを廃止し、論点抽出 → AskUserQuestion → 決定事項のみ記録に書き直し
  - `tdd` `1.0.1` → `1.1.0` / `systematic-debugging` → `1.0.2`: 「削除しろ。やり直せ」「資格はない」等の脅迫調を、規律の中身（失敗の観測・調査の完遂）を保ったまま行動指示に変換
  - `hooks/session-start.sh`: Atlas 探索プロトコル（list_atlas → search ×3 → 報告）を撤去し、git コンテキスト + Atlas 候補の提示に縮約（107 → 84 行）。creo-memories v3.0 Context Engine の自動注入と重複していた
  - `council` → `1.0.2` / `code-review` → `2.1.1` / `size-stepper` → `1.0.1`: 一問一答原則への cross-reference を新方針に同期
- `.gitignore`: VS Code Mermaid 拡張が自動生成する `.github/copilot-instructions.md` / `.github/instructions/` を無視対象に追加

## [0.26.0] - 2026-08-31

### Added
- **新スキル `parallel-dev`** (v0.2.0): 並列開発の道具選びを「**隔離・出荷**」の 2 層モデルで判断する規律スキル
  - **隔離**（テスト・ビルドが独立に走る）は worktree が解く — 小タスク = session worktree / 大タスク = VP lane
  - **出荷**（依存 PR の列車）は GitHub native stacked PR (`gh stack`) が解く — bottom merge で server-side cascading rebase
  - 「メイン作業中に別スコープの修正が混ざった」場合は手を止めず、コミット時に `git add -p` でハンク単位に割って別ブランチへ回す（混ざりを咎めず、後から割る）
  - 2026-08-28 に仮想ブランチによる「分流」層を廃止し 3 層 → 2 層へ移行。分流層は VP lane と役割が重複し実運用で出番がなかった
- `chronista-style` に **ブランチ運用（nightly trunk）** セクションを新設。開発 trunk を `nightly` とし、日々の PR は `--base nightly` で積む。リリース時に version bump して `nightly → main` を **merge commit** でマージし、main で tag を打つ（squash すると履歴が発散し次回リリースで全面コンフリクトするため）
  - 併せて **GitHub のデフォルトブランチは `main` のまま**にする理由を明記。プラグイン marketplace（`chronista-club/claude-plugins`）の source 定義に `ref` 指定が無く、**デフォルトブランチがそのまま配布元になる**ため、nightly をデフォルトにすると未リリース版が配布される

### Changed
- **Linear への依存を完全に除去** — 実運用で使われなくなったため、現行ガイダンスから存在ごとオミットした（`CHANGELOG.md` の歴史エントリは記録として温存）
  - `commands/dashboard.md`: **creo-memories ベースに全面書き換え**。`list_todos(status: "active", groupBy: "atlas")` を取得元とし、creo の todo が **active / done の 2 値**で中間状態を持たない事実に合わせ、`priority` → `updatedAt` 順で「今動いているもの」を表現する（旧「In Progress」相当の状態は再現しない）
  - `chronista-style` `4.4.0` → `4.5.0`: Issue 管理の SSOT を memory に変更。Issue-first の原則・Branch slug 規約・テストリストの 3 層 SSOT を memory ベースへ書き換え
  - `codeflow` `2.1.0` → `2.1.1` / `council` `1.0.0` → `1.0.1` / `route` `1.0.1` → `1.0.2`: 残存していた Linear 参照を除去
  - `commands/route.md` / `commands/sdg.md` / `hooks/session-start.sh`: Linear MCP 参照を creo-memories に置換
- `skills/cross-build-image/SKILL.md` / `skills/size-stepper/SKILL.md`: `~/repos/...` を指す参照を **「開発中のエイリアス — あるところには、ある」** として再定義。参照先を持つ環境でのみ解決でき、skill の動作条件ではないことを明示

### Fixed
- `skills/parallel-dev/SKILL.md`: VP の呼び出しが `vp flow_handoff`（MCP ツール名の形）になっていたのを、実際の CLI である `vp flow handoff <name> --task-spec <file|->` に修正（2 箇所）
- **`chronista-style` のスキルツリーが実態と乖離していた** — `4.5.0` → `4.6.0`
  - routing の入口であるルートスキルに `parallel-dev` / `cross-build-image` / `size-stepper` の 3 件が未記載で、実質そのスキルが隠れていた
  - 廃止済みの `fleetflow` が残っていた（marketplace からも削除済み。CLI 本体 `chronista-club/fleetflow` は継続）
  - 記載 15 件 = 実ディレクトリ 15 件を機械的に照合して一致を確認
- `README.md`: スキル一覧が 15 件中 7 件、コマンド表が 6 件中 4 件しか記載していなかったため全件に更新。スキルタイプの分類説明も表の種別と一致させた（`AI 協働` / `実装技術` の 2 分類を追記）
- **バージョン SSoT の記述をリポジトリ実態に同期**（Living Documentation）: `0.24.1` (#7) で内側の `.claude-plugin/marketplace.json` を撤去し `plugin.json` に一本化したにもかかわらず、`commands/release.md` / `README.md` / `CHANGELOG.md` ヘッダが `marketplace.json` を SSoT と記述したままだった。`/release` の Step 1 検出表がプラグインを検出できず手順が破綻するため修正。検出表には marketplace repo 形式も併記し、両方ある場合の優先順位（`plugin.json` が本体の正）を明示
- **`commands/release.md` の frontmatter が YAML として壊れていた**: `description: リリースバージョン（例: 0.3.0, 1.0.0）` の全角括弧内にある 2 つ目の `: ` でパース失敗し、ブロック全体（1 行目の `description` 含む）が失われていた。併せて、コマンド仕様に存在しない `arguments:` フィールドを正規の `argument-hint` に置換
- `commands/route.md`: `$ARGUMENTS` を使うのに `argument-hint` が無かったため追加
- `skills/{codeflow,route,size-stepper}/SKILL.md`: frontmatter の必須キーが `skill:` になっていたのを `name:` に統一（他 12 スキルは `name:`）
- `skills/cross-build-image/SKILL.md`: 同梱スクリプトの呼び出しが cwd 相対（`./build-and-push.sh`）で install 後に解決できなかったため `${CLAUDE_PLUGIN_ROOT}` 経由に修正
- `hooks/hooks.json`: `${CLAUDE_PLUGIN_ROOT}` が未クォートで、install パスにスペースが含まれると hook が起動しなかった。`bash "..."` 形式に修正（スペース入りパスで実行検証済み）

## [0.25.1] - 2026-07-31

### Added
- `.mcp.json.example`: プロジェクト共有可能な MCP サーバー雛形（gitnexus を bunx 起動で環境非依存に定義）。`bin/setup` / `bin/setup-windows` に `.mcp.json` 補完ステップを追加 — **共有 config store**（`$CHRONISTA_SHARED_CONFIG/claude/.mcp.json`、個人設定を集約した repo の `shared/` を想定。未設定なら example にフォールバック）への symlink を優先（`rm` / `git clean` で消えるのはリンクだけ、実体は store 側の git が保護）、store 不在時は example からコピー。Windows は symlink 不安定のため常にコピー運用。dangling symlink は掃除して再解決。運用原則: gitignore する手作りファイルは復元手段（example / 生成スクリプト）とセットにする

### Changed
- `code-review` SKILL.md を `2.0.0` → `2.1.0`: §C 定期実行を削除（未使用のため）。`reference/periodic-setup.md` も削除し、§D 共通規律 → §C、§E 既存スキルとの関係 → §D に再番号。`reference/examples.md` / `reference/modes.md` からも定期 review への言及を除去

## [0.25.0] - 2026-07-04

### Added
- **Stop hook `fabrication-tripwire.sh`** (`hooks/`): ターン終了時に assistant の**最終メッセージ**の「ツール出力の形をした文字列」を検出し、同じターンの本物の tool_result に裏付けが無ければ差し戻す(ツール結果の捏造を外側から止める関門)。fail-open。意図的な引用は明示トークン `TRIPWIRE-ACK` を**単独行**で置いて通す(文中の言及では解除されない)。`hooks/hooks.json` に Stop エントリ(`${CLAUDE_PLUGIN_ROOT}` 参照)を追加
  - 設計は実 transcript で検証済み: ターン境界 = 最後の実 user プロンプト(`content` が string の entry。tool_result entry や `Stop hook feedback:` 注入は境界にしない — 後者を境界にすると block 後の書き直しで同ターン前半の tool_result が孤立し偽陽性 loop になる)
  - 実 harness で live-fire 済み(意図的な捏造行を Stop で block → 差し戻し理由の提示を実観測)。synthetic fixture 9 ケース(block 5 / allow 4)も PASS

### Changed
- `verification` SKILL.md を `1.0.1` → `1.1.0`: 「捏造 — 検証不足の極限形」セクションを追加。ツール結果の捏造(実行せず出力を地の文に書く / 呼んでいない第二意見をでっち上げる / 予測を観測として混ぜる)を「証拠なき完了宣言」の極限形として明文化。認知メカニズム(予測と観測の混同・完了イメージへの引力・自問の脆さ)と、意志ベースの規律に加えて**構造的関門**(Stop hook `fabrication-tripwire.sh` + `TRIPWIRE-ACK` escape hatch)を記載

## [0.24.3] - 2026-05-17

### Added
- `bin/setup-windows`: Windows (Git Bash + winget) 用の開発環境セットアップスクリプト

### Changed
- `codeflow` SKILL.md を `2.0.1` → `2.1.0`: Linear 連携記述を memory-native (memory-as-issue) に更新。2026-04-23 pivot (Linear → creo-memories) を反映し、Cross-Project Handoff subsection を追加 (PR #8)
- `bin/setup` を macOS 専用化し OS 判定を追加 (Windows は `bin/setup-windows` に委譲)。パッケージ群を BUILD_SUPPORT / LSP / LINT / AI / cask / font 等に再編・拡張

## [0.24.2] - 2026-05-04

### Added
- **新スキル `size-stepper`** (v1.0.0): design token を 「演奏できる Live Token」 として扱う 4 層 architecture
  - TS class (SizeStepper) + Solid signal + CSS scope mirror + MIDI 2.0 connector
  - namespace 階層 (UI → BUTTON / HEADER) + parent 継承 + lock per-key
  - adjacent ceiling / per-key precision / bounds override / Export to clipboard
  - Korg Keystage 1 row binding (CC 0-7 = UI 5 step + BUTTON.m + HEADER.{m,l})
  - 「最終 const 化」 lifecycle (探索 → 確定候補 → 焼き戻し → 運用) を仕組み化
  - origin: fleetstage-hq commits 87207917 / 735b5188 / 97e98a24

## [0.24.1] - 2026-05-02

### Changed
- Skill tree refactor: 12 skill dir (agent-harness, agent-introspection, chronista-style, code-review, codeflow, council, route, santa-method, spec-design-guide, systematic-debugging, tdd, verification) を root から `skills/` 下に移動 (公式 spec 準拠)

### Removed
- Redundant inner `.claude-plugin/marketplace.json` (self-referential で冗長、 plugin.json のみに統一)


## [2.4.0] - 2026-05-01

### Added
- **新スキル `council`** (v1.0.0): 4-voice 合議で意思決定
  - Architect / Skeptic / Pragmatist / Critic の 4 視点で trade-off を可視化
  - Anti-anchoring mechanism: subagent を fresh context で召集 (会話履歴を渡さない)
  - 元 ECC `council` から chronista 適合 fork (memory-first 連携、 VP 文脈の例追加)
- **新スキル `santa-method`** (v1.0.0): 多 agent 敵対的検証 (adversarial verification)
  - Generate → Dual Review → Verdict Gate → Fix Until Nice の 4 フェーズ
  - 両者 PASS 必須、 各 round fresh agent (前 round の anchoring 防止)
  - 元 Ronald Skelton (RapportScore.ai) から chronista 適合 fork
- **新スキル `agent-harness`** (v1.0.0): AI agent harness 設計
  - Action space / Observation / Recovery / Context budget の 4 軸
  - VP Stand Actor Framework / ccws worker autonomous mode と整合
- **新スキル `agent-introspection`** (v1.0.0): AI agent 自身の failure self-debug
  - Capture → Diagnose → Contain → Report の 4 フェーズ
  - `systematic-debugging` (コード/システムバグ) と領域分離 (こちらは agent loop / drift / max tool call)

### Changed
- `chronista-style` SKILL.md (v4.3.0 → v4.4.0): スキル構成に 4 新 skill + 既存 `route` を register

### Notes
- 4 新 skill は **AI 協働カテゴリ** として一塊で機能: council (decide) → santa-method (verify) → agent-harness (design) → agent-introspection (debug)
- 元 ECC plugin (everything-claude-code) の同名 skill から chronista 適合 fork。 ECC plugin 全体は disable しつつ、 必要 skill のみ chronista 側に統合する軽量 cherry-pick 戦略
- 各 skill は memory-first 連携セクション (creo-memories integration) を持ち、 VP 文脈の具体例 (D11 / Stand × Pane × Lane / ccws worker / Mailbox) を含む

## [2.3.0] - 2026-04-25

### Changed
- **`code-review` SKILL.md (1.0.1 → 2.0.0)** — 規律スキルから「実行手法 + 規律 + 受信」の統合スキルに刷新 (BREAKING)
  - **§A. レビュアー (主体)** 新設 — Quick / Standard / Deep の 3 mode、`team-bucciarati` Stand 連携 (Aerosmith / Moody Blues / Purple Haze / Spice Girl / Gold Experience)
  - **§B. 著者 (受信)** — 旧 SKILL.md の Part 1, 2 を吸収 (依頼 / 受信 / 禁止レスポンス / YAGNI / 反論)
  - **§C. 定期実行** 新設 — `/schedule` 経由で週次 / 月次 Deep review を回す手順
  - **§D. 共通規律** — performative agreement 禁止、信頼度スコアリング 75+
  - 移行: 既存ユーザは規律部分 (旧 Part 1, 2) は §B + §D に再配置されたが内容は同じ
- `reference/` 配下に詳細手順を分離
  - `modes.md` — Quick / Standard / Deep の詳細フロー
  - `stand-mapping.md` — Pass 1〜8 の観点と Stand 対応表
  - `periodic-setup.md` — `/schedule` 連携手順
  - `examples.md` — 実例 (Quick / Deep / 定期 / 受信側 / 反論)

### Why
- 既存 `code-review` は「規律」のみ、「実行手法」のスキルが穴だった
- multi-pass 手法を別 skill にする案も検討したが、ユーザ feedback「skill 増やしたくない、定期的にやりたいがスコープは可変」を受けて 1 skill に統合
- Hybrid Z (parallel + iterative) で scope に応じて Quick から Deep までシームレスに切替可能

## [2.2.0] - 2026-04-20

### Added
- `chronista-style` SKILL.md (v4.3.0) に **推奨スタイル: 言語と表現** セクション追加
  - **Python が出てきたら、まず Ruby で考える**: スクリプト・CLI・小さなツール・DSL では Ruby を第一候補とし、Python を選ぶ場合も Ruby 案を並べてユーザーに共有してから決める（ML / 数値計算等の Python エコシステム必須ケースは例外として明記）
  - **JSON が出てきたら、まず KDL で考える**: 設定・データ表現で JSON が登場する文脈では KDL を第一候補とし、JSON を選ぶ場合も KDL 表現を並べてユーザーに共有してから決める

### Changed
- 全スキル SKILL.md を patch bump（chronista-style 経由で参照される土台スキルとして整合性を確保）
  - `codeflow` 2.0.0 → 2.0.1
  - `tdd` / `systematic-debugging` / `verification` / `code-review` / `spec-design-guide` / `route` 1.0.0 → 1.0.1

### Fixed
- v2.1.0 タグ欠損を修復（過去 commit `5d69392` に lightweight tag を後付け）

## [2.1.0] - 2026-04-17

### Added
- **新スキル `route`** (v1.0.0): Issue からゴールへの最適 path を探索する経路探索スキル
  - 6 フェーズ: Survey → Plot → Compare → Choose → 🚦 HARD GATE → Travel → Log
  - ケーススタディ: fleetstage FSC-22 (2026-04-17, 半日想定 → 45 分で完走)
  - 「グルーブを忘れない」姿勢セクション（codeflow の姉妹節）
  - 発火の目安・アンチパターン集付き
- **新コマンド `/route`** (`commands/route.md`): Route スキルのエントリポイント
  - Issue ID を引数で受け、Survey〜Choose まで実行して HARD GATE で承認を待つ

## [2.0.1] - 2026-04-17

### Added
- `hooks/session-start.sh` に **Atlas 自動認識フロー** を追加。ディレクトリ名ベース（A）を優先し、git remote URL（C）をフォールバックとするハイブリッド検出
- hook 出力で Claude に「優先候補 A で exact match → フォールバック C → AskUserQuestion」の順序を明示

### Fixed
- hook スクリプトで BSD sed の `+?` 非互換エラーを解消（macOS 対応）

## [2.0.0] - 2026-04-17

大規模リファクタ。**破壊的変更を含む**。

### Added
- `CHANGELOG.md` を初回作成（Keep a Changelog 形式）
- `hooks/hooks.json` + `hooks/session-start.sh` 追加。SessionStart で git コンテキストを注入し、creo-memories 検索を Claude に促す
- 5 スキル（`spec-design-guide` / `tdd` / `systematic-debugging` / `verification` / `code-review`）の SKILL.md に `version:` フロントマター（初期 `1.0.0`）を追加

### Changed
- **バージョン SSoT を `marketplace.json` に一本化**（`.claude-plugin/plugin.json` は廃止）
- **Phase 番号を全廃**、ステップ名で管理に移行（Discovery → Discussion → Hearing → SDG → Branch & PR → Implementation → Release → Learning）
- `commands/codeflow.md` `hearing.md` `sdg.md` を **hearing 起動装置型** に再構築。まず `AskUserQuestion` で意図をキャプチャしてから進める
- `commands/release.md` を汎用化。`marketplace.json` / `Cargo.toml` / `package.json` を自動検出して version bump + CHANGELOG 更新 + git tag まで対応
- `chronista-style` SKILL.md を `3.4.0` → `4.0.0`（Phase 構造の破壊的変更）
- `codeflow` SKILL.md を `1.8.0` → `2.0.0`（Phase → step name への破壊的変更）
- `README.md` の version 3.0.0 表記を削除し、SSoT への参照に差し替え

### Removed
- `.claude-plugin/plugin.json`（marketplace.json 一本化のため廃止）
- `.claude-plugin/skills.txt`（Claude Code 仕様外のレガシー残骸）

### Fixed
- plugin.json / marketplace.json / SKILL.md / README.md のバージョン表記が 4 箇所でズレていた問題を根本解決

## [1.1.0] - 2026-02-XX（遡及記録）

fleetflow を別プラグインとして marketplace に分離。chronista-style 本体は `1.1.0`。

（commit: `fdddbb6 refactor: fleetflowを別プラグインに分離`）

## [1.0.0] - 2025-12-XX（遡及記録・推定）

初回マーケットプレイス対応。

（commit: `bee3ed1 feat: マーケットプレイス対応を追加`）
