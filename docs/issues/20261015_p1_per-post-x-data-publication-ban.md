# Issue: 「投稿単位の X データは匿名化しても公開しない」方針が施行されていない

**ID:** ISS-20261015-XID-034  
**優先度:** P1 (High)  
**ステータス:** OPEN  
**対象:** `src/validation/x_identity.py`, `config/storage-policies.json`, `docs/specs/validation-framework.md`（§21 / §22）, `docs/data-dictionary.md` §1.2, `docs/specs/raw-data-policy.md`, `docs/specs/sns-redistribution-assessment.md`

## 概要

`ISS-20261015-COL-030` §4.1 は「匿名化した場合でも、投稿単位の研究CSVは公開しない」と定める
（方針変更）。現在の施行は**識別子の混入検査まで**で、「投稿単位 X 成果物を公開物として追跡しない」
という規則が存在せず、実際に匿名化済み投稿単位 CSV が追跡・公開されている。

この issue は**施行（検査と語彙・文書）**を担当する。既存公開物の取り下げは
`ISS-20261015-PUB-035`。

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

## 対応方針

- **新しい検査を 1 つ追加**する（既存規則と同じ実行点 = `validation.cli audit-x-identity` と
  pre-commit チェック 6）: 追跡下のファイルが「X の投稿単位データ」と判定される場合に fail させる。
  判定は**構造**（行単位の X 投稿を示す列セット / datasets 配下の data 層にある X 由来の
  行指向ファイル）で行い、列名のリストを 1 か所で持つ（規則を二重実装しない）。
  依存する既存宣言（`src/processing/reproduce.py`）と設定語彙（storage policy）は参照するだけにする。
- 保存方針の語彙を拡張する（例 `publication: not_permitted` を X 投稿単位データに与える）。
  既存 registry の schema 検証と `validate-registries` を同時に更新する。
- 文書を方針変更に合わせる: `data-dictionary.md` §1.2（用途）、
  `sns-redistribution-assessment.md`（日付付き追記）、`validation-framework.md` §21/§22、
  `raw-data-policy.md`（X の扱い）。既存の日付付き記述は当時の事実として残す。
- 検査自体のテスト（非空虚性: 投稿単位 CSV を検体にすると落ち、集計 CSV は通る）。

## 完了条件

- [ ] 「投稿単位 X データを追跡・公開しない」の機械検査（テスト付き・非空虚）
- [ ] 保存方針の語彙拡張と `validate-registries` green
- [ ] 文書の整合（§21 / §22 / data-dictionary / redistribution assessment / raw-data-policy）
- [ ] 既存の追跡対象が 0 件になったことを検査で確認（PUB-035 と連携）

## 依存

- `ISS-20261015-PUB-035`（既存公開物の取り下げ）と同じ変更にまとめられる
