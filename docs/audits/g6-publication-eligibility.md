# G6 Publication Eligibility Gate — 実行記録（公開はしない）

**日付:** 2026-10-13
**仕様:** `docs/plans/20261013f.md` §10（10.1 判定状態・10.2 必須検証・10.3 decision）
**機械可読版:** [`g6-publication-eligibility.json`](./g6-publication-eligibility.json)（再生成: 下記 §4）
**厳守:** 判定は記録のみ。`gh release` 作成・Zenodo アップロード・DOI 発行・`origin` への push は行わない。

---

## 1. 対象成果物（実在 1 件）

| 項目 | 値 |
|---|---|
| `artifact_id` | `x-cbx-202608-summary-anonymized` |
| `path` | `datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv` |
| `sha256` | `f27f979a19e7e4925ae0b5d442beeec027e667ce5b10247934066a5b1ed463a6` |
| `byte_length` | 20538 |
| `layer` / `source_kind` | `processed` / `social` |
| `storage_policy_id` | `processed-public-candidate`（`conditional`） |
| Git 状態 | tracked（条件付き追跡。追加審査が必要） |
| 公開 metadata | `metadata/datapackage.json` に schema 記載あり |

選定理由: 匿名化済みの公開候補 derived データであり、PUB-04/PUB-09（個人情報・匿名化）の境界を示せる実在の1件。

## 2. 判定

**`BLOCKED`**（公開不可）。これは成果物の問題の記録であり、ゲート自体の失敗ではない。

| ID | 検証 | 結果 | 根拠 |
|---|---|---|---|
| PUB-01 | 来歴が存在 | FAIL | manifest の無い legacy 派生。`provenance_present: false` |
| PUB-02 | Integrity PASS | PASS | 実ファイルの hash を検証済み |
| PUB-03 | 公開 Schema 妥当 | PASS | datapackage に schema 記載 |
| PUB-04 | 個人情報の審査 | FAIL | 正式な審査記録なし（G6-T11 で拒否） |
| PUB-05 | 秘密情報の検査 | PASS | 審査 envelope に credential 様の値なし（値は出さない） |
| PUB-06 | 取得元の利用条件 | WARNING | 未記録。要レビュー |
| PUB-07 | 再配布条件 | WARNING | 未記録。要レビュー |
| PUB-08 | 著作権・契約 | WARNING | 未記録。要レビュー |
| PUB-09 | 匿名化・集計 | PASS | 匿名化版（hash ID・本文なし） |
| PUB-10 | 公開承認の記録 | FAIL | decision が `requires_review`（G6-T07/T08。承認なし） |

`failed: [PUB-01, PUB-04, PUB-10]` / `warnings: [PUB-06, PUB-07, PUB-08]`。Fail closed（P5）: 未確認は公開不可。

## 3. Decision（記録のみ）

- `decision_id: publication-review-x-cbx-202608-summary`、`status: requires_review`、`artifact_sha256` は上記 sha に一致。
- 承認（`approved` + 承認者・日時・基準版・hash ピン留め）が無いため `can_publish() == False`（§11 最小規則どおり）。
- 内容変更時は承認を引き継がない（G6-T09 は contract test で機械化）。

## 4. 再現手順（read-only）

```bash
python3 - <<'PY'
import json, hashlib
from pathlib import Path
p = Path("datasets/cbx-social-trends/data/processed/x_cbx_202608_summary_anonymized.csv")
sha = hashlib.sha256(p.read_bytes()).hexdigest()
print(sha)
PY
python3 -m validation.cli gate-publication --artifact /tmp/g6-artifact.json --decision /tmp/g6-decision.json --evidence /tmp/g6-evidence.json --output docs/audits/g6-publication-eligibility.json
```

入力 3 ファイル（artifact / decision / evidence）は審査 envelope であり、raw レコード値は読まない。 verdict が `BLOCKED` でも CLI は exit 0（記録専用のため。§10.3 の decision 検証失敗と CLI 入力エラーを区別する）。
