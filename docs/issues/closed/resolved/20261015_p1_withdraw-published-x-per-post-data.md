# Issue: 公開済みの投稿単位 X 匿名化 CSV が新方針下で公開禁止になっている

**ID:** ISS-20261015-PUB-035  
**優先度:** P1 (High)  
**ステータス:** RESOLVED (2026-10-15) — 追跡から取り下げ、ゲート記録を denied に更新  
**対象:** `datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv`, `src/processing/reproduce.py`, `metadata/publication/x-cbx-202608-summary-anonymized/`, `docs/audits/g6-publication-eligibility.{json,md}`, `metadata/datapackage.json`, `docs/provenance.md`

## 概要

`ISS-20261015-COL-030` §4.1 は「匿名化した場合でも、投稿単位の研究CSVは公開しない」と定める。
しかし現在、投稿単位の匿名化版 CSV は**追跡・公開**されており、先の公開審査記録
（`ISS-20261015-PUB-015`）でも `decision: approved` / `CONDITIONAL` として承認されている。
方針変更により、この成果物は公開禁止となる。

## 確認された観測

- 対象: `datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv`
  （147 行・16 列・sha256 `f27f979a19e7e4925ae0b5d442beeec027e667ce5b10247934066a5b1ed463a6`、20538 bytes）。
- 追加 commit `6ef52a9` は **8 タグ**に含まれる。§21.1 の記録によれば Zenodo アーカイブ
  （`10.5281/zenodo.23253840`）にも含まれる。
- `metadata/publication/x-cbx-202608-summary-anonymized/decision.json` は `status: approved`、
  `docs/audits/g6-publication-eligibility.json` は `verdict: CONDITIONAL`（PUB-01/02/03/04/05/09/10 PASS、
  PUB-06/07/08 WARNING）。
- 参照は tracked な約 25 ファイルに及ぶ（`metadata/datapackage.json`、`docs/data-dictionary.md`、
  `docs/specs/*`、`docs/audits/*`、`src/processing/*`、`tests/*` 等）。
- 2026-10-13 の先例（全 14 タグ・ Zenodo を含む公開アーカイブの取り下げは「不要」と受容: `validation-framework.md` §21.6）
  との整合をどう取るかは未確定（`ISS-20261015-COL-030` U5）。

## 影響

- 公開ゲートの記録（承認・CONDITIONAL）が現行方針と矛盾したまま残る。
- 今後の公開（Release / Zenodo）に投稿単位データが含まれ続ける。
- `datapackage.json` / data-dictionary の「公開用」記述が誤りになる。

## 対応方針

- 取り下げの手順は 2026-10-15 に `early-warning-index-v1.csv` と 2026-10-13 に
  `x_cbx_202608_summary.csv` で使ったものを踏襲する:
  - `git rm` で追跡から外す（履歴は書き換えない）。
  - `src/processing/reproduce.py` の `WITHDRAWN` に理由・代替・露出（どのタグ／Release に含まれたか）を
    日付付きで記録する（黙って消さない）。
  - 参照側（datapackage / data-dictionary / provenance 等）に日付付きの追記を行う。
  - 監査スナップショット（g4 / g6 / g7）を登録コマンドで再生成する。
- **ゲート記録の更新**: `metadata/publication/` の `decision.json` / `evidence.json` は方針変更を
  表現できないため、表現方法を決める（候補: evidence に方針参照を加えて verdict を再評価する、
  または「方針で禁止」を入力とする検査をゲートに追加する）。**推測で PASS/FAIL を書かない**。
  決定後、`docs/audits/g6-publication-eligibility.json` を再生成する。
- 未確定 U5（既公開アーカイブの取り下げ・制限の要否）と U6（派生物の扱い）の決定を待って
  履歴側の作業範囲を確定する。

## 完了条件

- [x] 追跡からの取り下げと `WITHDRAWN` への理由・露出の記録
- [x] 参照文書の整合（datapackage / data-dictionary / provenance / spec）
- [x] ゲート記録の更新方法の決定と監査再生成（`test_audit_report_freshness` green）
- [x] 監査スナップショット再生成（g4 / g6 / g7）
- [x] 既公開アーカイブの扱いの決定記録（U5）

## 施行の記録（2026-10-15）

- **取り下げ**: `git rm` で追跡から外し、`src/processing/reproduce.py` の `WITHDRAWN` に
  理由（2026-10-15 の決定）・代替（None = 投稿単位の表現は公開しない）・露出
  （v1.6.2 / v1.7.0 / v1.7.1 / v1.8.0 / v1.9.0 / v1.10.0 / v1.11.0 / v1.12.0 と
  Zenodo DOI 10.5281/zenodo.23253840）を日付付きで記録した。当時宣言していた導出
  （kind / 16 列 / `week` 3 行の乖離）も同エントリの notes に残した。
- **参照の整合**: `metadata/datapackage.json` から資源を削除（`modified` を 2026-10-15 へ）、
  `docs/data-dictionary.md` §1.1/§1.2、`docs/provenance.md`、`docs/specs/sns-redistribution-
  assessment.md` §5、`docs/specs/standards-compliance-implementation-plan.md`、
  `datasets/*/methodology.md`、`datasets/cbx-search-trends/analysis/` に日付付きの追記。
  `scripts/validation/validate-data-schema.sh` は、CSV を検証する節を
  **「追跡下に無いこと」を検査する節**に置き換えた（不活性な検証を残さない）。
- **ゲート記録**: `metadata/publication/x-cbx-202608-summary-anonymized/decision.json` を
  `status: denied`（2026-10-15、根拠 `ISS-20261015-COL-030` §4.1）に置き換え。
  2026-10-13 の approved は notes に残した（削除ではなく置き換え）。
  再実行した verdict は `BLOCKED`（PUB-10 FAIL = 公開拒否）。
  freshness テストは、取り下げ済みの成果物について **descriptor の sha256 と不在**を
  検査する形に変更した（`Report.envelope`）。
- **U5（既公開アーカイブ）**: 取り下げない。§21.6 の 2026-10-13 の判断（露出は受容済み・
  記録する）を維持した（メンテナはこの先例を変更する指示をしていない。変更する場合は
  Zenodo 側の操作と `exposure` の再記述が必要）。

## 依存

- `ISS-20261015-XID-034`（施行の機械検査。同じ変更にまとめられる）
- 未確定: `ISS-20261015-COL-030` U5 / U6

## 追記（2026-10-15、ゲート記録の表現方法の調査結果）

- **「方針で禁止」は新しい語彙を作らずに表現できる**: `publication-decision-v1` の `status` は
  `approved` / `denied` / `requires_review` / `unknown` を許す
  （`src/validation/schemas/storage_policy.py` の `PUBLICATION_STATES`）。
  `decision.json` を **`status: "denied"`** とし、`basis` に `ISS-20261015-COL-030` §4.1
  （メンテナ決定 2026-10-15）を日付付きで引く。同じ語彙が `config/storage-policies.json` の
  policy item にも適用されるので、成果物の宣言側も同時に `publication: "denied"` にできる。
- **連鎖する変更（実装上の帰結）**:
  - `tests/validation/test_audit_report_freshness.py` は `g6-publication-eligibility.json` を
    **invocation record** として登録し、`test_invocation_record_still_describes_its_artifact` が
    **対象 artifact の現在の sha256** と記録値を照合する。取り下げ後はファイルが無いため、
    この登録は「`denied` の決定記録 + 記録済み hash（`decision.json` に固定）」に切り替える必要が
    ある（存在検査は取り下げ記録を見る）。
  - `src/processing/reproduce.py` の `WITHDRAWN` に理由 / 代替 / 露出（8 タグ + Zenodo DOI）を書く
    （直前の 2 件 `x_cbx_202608_summary.csv` / `early-warning-index-v1.csv` と同じ形式）。
  - 参照側（`metadata/datapackage.json` / `docs/data-dictionary.md` / `docs/provenance.md` /
    `docs/specs/*`）に日付付きの追記を行い、`docs/audits/g4|g6|g7` を再生成する。
- **未確定 U5 の推奨**: 既公開アーカイブ（8 タグ・Zenodo）の取り下げは §21.6 の先例
  （記録して取り下げない）に従う。対象 publication（HTML）は未公開なので影響しない。

