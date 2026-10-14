# Issue: 「投稿単位の X データは匿名化しても公開しない」方針が施行されていない

**ID:** ISS-20261015-XID-034  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `src/validation/x_identity.py`, `config/storage-policies.json`, `docs/specs/validation-framework.md`（§21 / §22）, `docs/data-dictionary.md` §1.2, `docs/specs/raw-data-policy.md`, `docs/specs/sns-redistribution-assessment.md`, `publication/`

## 概要

`ISS-20261015-COL-030` §4.1 は「匿名化した場合でも、投稿単位の研究CSVは公開しない」と定める
（方針変更）。現在の施行は**識別子の混入検査まで**で、「投稿単位 X 成果物を公開物として追跡しない」
という規則が存在せず、実際に匿名化済み投稿単位 CSV が追跡・公開されている。

この issue は**施行（検査と語彙・文書）**を担当する。既存公開物の取り下げは
`ISS-20261015-PUB-035`。

施行点は 2 つある: **格納・追跡の禁止**（既存方針）と、**公開物における投稿単位の表現の禁止**
（2026-10-15 のメンテナ決定で追加。§決定記録）。

## 確認された観測

- 追跡されている投稿単位 X データ: `datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv`
  （147 行・16 列）。`git ls-files` 上で X の投稿単位データはこの 1 件のみ。
- `src/validation/x_identity.py` の規則は `identity_column`（追跡 CSV のヘッダが username 等を名乗る）、
  `post_permalink`（x.com/.../status/...）、`known_handle`（denylist のソルト付き
  ダイジェスト照合）の 3 つで、**疑似名化の済んだ投稿単位 CSV は通過する**
  （`audit-x-identity`: findings 0）。
- `config/storage-policies.json` に「公開禁止」を表す値が無い（`publication` は
  `requires_review` のみ）。
- `docs/data-dictionary.md` §1.2 と `metadata/datapackage.json` は同 CSV を
  「公開用」として記述している。
- `docs/specs/sns-redistribution-assessment.md` §1.4/§3.1 は集計のみ公開と結論しているが、
  投稿単位 CSV の公開禁止は明記していない。

## 影響

- 方針変更が文書だけで、機械的な施行点が無い（同型の失敗は §21.1 で記録済み）。
- 今後も投稿単位 CSV が知らずに追跡される（公開ゲートも通してしまう）。

## 決定記録（2026-10-15）

**メンテナ決定:** 投稿単位の表現は、リポジトリへの格納禁止と同じく**禁止**とする。
したがって方針は「格納しない」だけでなく「**表現しない**」に及ぶ。

| 区分 | 内容 |
|---|---|
| 禁止 | 1 行 = 1 投稿の表・列挙、投稿本文の引用、投稿 ID / permalink、投稿日時の列、投稿ごとのエンゲージメント値、`username` / `author_id` の掲載、**投稿レコードの列構成に言及する記述**（例: フィールド別の完全率） |
| 許可 | 集計（件数・比率・分布・中央値等）、収集メタデータ（クエリ・期間・件数）、分類カテゴリ別の集計 |
| 境界（別途確認） | 「1 行 = 1 アカウント」の表は投稿単位ではないが境界事例（`publication/guide_cbx_rewrite.html` の「上位投稿者」表。現状は疑似名 A〜E で実名非公開）。判断は `docs/reports/20261015c-publication-refresh-plan.md` §11-U4b |

決定は「投稿単位データを公開しない」であり、集計値の公開は妨げない。

## 対応方針

- **公開物側の検査は実装済み（2026-10-15）**。ただし実行点は当初案の `audit-x-identity` ではなく
  **公開契約**（`src/validation/publication_contract.py` の PC-3、`validation.cli audit-publication`）
  とした。理由: この規則が対象とするのは `publication/` の成果物であり、同一の走査を 2 か所に
  置かないため（`x_identity.py` は追跡データファイル、公開契約は公開 HTML を見る）。判定パターンは
  PC-3 側の 1 か所にある（permalink / `@handle` / 投稿レコードの列名 3 つ以上）。
  実測（2026-10-15）: guide の「全フィールド（views, likes, …）147件中147件」記述を検出→
  集計表現に修正済み（現在 findings 0）。
- **格納・追跡側**の検査を追加する: 追跡下のファイルが「X の投稿単位データ」と判定される場合に
  fail させる。判定は**構造**（行単位の X 投稿を示す列セット / datasets 配下の data 層にある X 由来の
  行指向ファイル）で行い、列名のリストを 1 か所で持つ（規則を二重実装しない）。
  依存する既存宣言（`src/processing/reproduce.py`）と設定語彙（storage policy）は参照するだけにする。
- 保存方針の語彙を拡張する（例 `publication: not_permitted` を X 投稿単位データに与える）。
  既存 registry の schema 検証と `validate-registries` を同時に更新する。
- 文書を方針変更に合わせる: `data-dictionary.md` §1.2（用途）、
  `sns-redistribution-assessment.md`（日付付き追記）、`validation-framework.md` §21/§22、
  `raw-data-policy.md`（X の扱い）。既存の日付付き記述は当時の事実として残す。
- **公開物側の検査を追加する**（本決定で追加された施行点）: publication の成果物が投稿単位の表現
  （permalink、`@handle`、投稿単位の列見出し、投稿レコードの列構成への言及）を含む場合に fail させる。
  → 2026-10-15 実装済み（上記「対応方針」のとおり公開契約 PC-3 として）。
- 検査自体のテスト（非空虚性: 投稿単位 CSV を検体にすると落ち、集計 CSV は通る）。
  公開物側も同様に、投稿単位の表現を含むフィクスチャで落ち、集計のみのフィクスチャで通ることを固定する。

## 完了条件

- [ ] 「投稿単位 X データを追跡・公開しない」の機械検査（テスト付き・非空虚）
- [ ] 保存方針の語彙拡張と `validate-registries` green
- [ ] 文書の整合（§21 / §22 / data-dictionary / redistribution assessment / raw-data-policy）
- [ ] 既存の追跡対象が 0 件になったことを検査で確認（PUB-035 と連携）
- [x] 公開物に投稿単位の表現が 0 件（2026-10-15 実装。公開契約 PC-3 の実施で guide の
      投稿レコード列記述を修正。`docs/audits/publication-contract.json` で findings 0）

## 依存

- `ISS-20261015-PUB-035`（既存公開物の取り下げ）と同じ変更にまとめられる
