# Issue: publication ゲートの `BLOCKED` が受容記録のないまま公開が続いている

**ID:** ISS-20261015-PUB-015  
**優先度:** P1 (High)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `docs/audits/g6-publication-eligibility.json`, `metadata/publication/`, `config/storage-policies.json`, `docs/specs/validation-framework.md` §22.5

## 概要

公開適格性の監査は `verdict: BLOCKED`（PUB-01 provenance 欠落 / PUB-04 personal-data review
欠落 / PUB-10）を記録したままで、対象成果物（匿名化済み X CSV）は公開されている。
AGENTS.md は「公開ゲートの失敗は解決または明示的に文書化されるまで公開を止める」と定めるが、
その受容の記録が見当たらない。

## 確認された観測

- `docs/audits/g6-publication-eligibility.json` は record-only 設計の監査出力として存在する。
- `audit-issues` は issue 記録の一貫性を検査するが、この監査結果と公開状態の整合は検査しない。
- 2026-10-13 の先例として、公開アーカイブの取り下げが「不要（受容）」と判断された記録がある
  （`docs/specs/validation-framework.md` §21.6）。

## 影響

- 公開ゲートが実効性を持つのか、単なる記録なのかを第三者が判定できない。
- 公開物の可否判断の履歴が、非公開の会話に依存する。

## 対応方針

- (a) 受容を明示的に記録する、または (b) ゲートを再実行して verdict を更新する。
- どちらかを選んだら、その判断を文書（spec の該当節 or 監査の隣）に残す。
- **推測で PASS にしない。**

## 選択と結果（2026-10-15、メンテナ指示は (b)）

指示は「(b) を実施」。ゲートを再実行し、判定を更新した。

- **入力の置き場を変えた**: 従来はその場限りの入力（ad-hoc ファイル）で、判定履歴が
  非公開の会話に依存していた。審査 envelope（artifact descriptor / evidence / decision）
  を `metadata/publication/x-cbx-202608-summary-anonymized/` に**追跡ファイルとして**置き、
  判定は登録された生成コマンドで再現できるようにした
  （`tests/validation/test_audit_report_freshness.py` が再実行一致と hash ピン留めを検査）。
- **再実行結果: `BLOCKED` → `CONDITIONAL`**（公開は拒否されない。レビュア確認は残る）
  - PUB-01 FAIL → PASS: 導出宣言（`src/processing/reproduce.py`）と `audit-processed` の
    機械検証が入り、"manifest の無い legacy 派生" は当時の状態になった。
  - PUB-04 FAIL → PASS: `docs/specs/validation-framework.md` §21.2（メンテナ決定 2026-10-13）
    と §21.3 の施行（匿名化・非公開退避・`audit-x-identity`）を審査記録として引用。
  - PUB-10 FAIL → PASS: 同決定を、内容未変更の当該成果物（hash `f27f979a…`、2026-10-13 の
    記録と同一）への公開承認として記録。
  - **残る WARNING: PUB-06 / PUB-07 / PUB-08**（取得元の利用条件・再配布条件・著作権の
    「確認済み」記録が無い）。`docs/specs/sns-redistribution-assessment.md` が評価を与えて
    いるが確認の記録ではないため、未記録のままにした（§3.3 の未チェック項目）。
- **解釈の明示**: 専用の承認文書は存在しないため、§21.2 の決定文を機械可読な decision に
  転記した（`decision.json` の `basis` と spec §22.5 に明記）。別の形（例:
  `requires_review` のまま）にする場合、フィールド 1 つと再実行で変わる。
- 監査と公開状態の関係: ゲートは record-only で、公開・Release・Zenodo・DOI に触れない。
  対象成果物がすでに公開済みである事実は変わらず、**今後の公開判断に効く記録**が
  「未記録の拒否」から「記録された CONDITIONAL + 残作業 3 件」に変わった。

## 完了条件

- [x] 受容 / 再実行のいずれかを選択（2026-10-15、(b)）
- [x] 選んだ結果の記録（日付付き: 監査 JSON の再生成 + `metadata/publication/README.md` +
      本節 + spec §22.5）
- [x] 監査と公開状態の関係を説明する文章の追記（spec §22.5）

## 追記（2026-10-15）: 残る PUB-06/07/08 と新しい公開候補

- 残る WARNING（PUB-06 取得元の利用条件 / **PUB-07 再配布条件** / PUB-08 著作権）は、
  メンテナの新しい指示 [`docs/issues/closed/resolved/20261014_p1_pub-029-coarse-x-aggregates.md`](20261014_p1_pub-029-coarse-x-aggregates.md)
  （`ISS-20261014-PUB-029`、研究用CSVの非識別化・正規化エクスポート）が扱う。
  同指示の表題の "PUB-07" はゲート検査 PUB-07 を指す。
- **ゲートは成果物単位**: 現在の `CONDITIONAL` は
  `x-cbx-202608-summary-anonymized` のみを対象とする。同指示が作る新しい研究用CSVは
  別の artifact_id であり、公開前に `metadata/publication/<artifact_id>/` の審査
  envelope を作って `gate-publication` を実行するまで**判定が存在しない**
  （「公開可否の最終判定は実装完了とは別」という同指示の注記とも一致）。
- 入力の実測（147 行 / 16 列 / `week` の `unknown` 3 行 / `text_length` の定義 /
  `compound` の根拠 / 出力先の層の扱い）は同指示 §2-3 / §2-4 に記録した。

## 追記 2（2026-10-15）: 方針変更により本件の承認記録も更新対象

`ISS-20261015-COL-030`（X公式API移行指示書）§4.1 が「匿名化しても投稿単位の研究CSVは
公開しない」と定めたため、本 issue で記録した `decision: approved`（= 当該匿名化版 CSV の
公開承認）は**現行方針に反する**。

- 記録の更新（既存公開物の取り下げとゲート入力の再定義）は `ISS-20261015-PUB-035` が扱う。
- 施行（「投稿単位 X データを追跡・公開しない」の機械検査）は `ISS-20261015-XID-034`。
- 本 issue の完了条件（当時の判定の記録）はそのまま有効だが、**記録の内容**が方針変更で
  古くなったことをここに明示する（履歴は書き換えない）。



