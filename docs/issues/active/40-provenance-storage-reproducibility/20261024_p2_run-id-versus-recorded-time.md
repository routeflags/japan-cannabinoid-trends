# Issue: run-id（ディレクトリ名）と収集記録の ID・時点が一致しない run がある

**ID:** ISS-20261024-PRV-015  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/*/data/raw/google_trends/*/run_metadata.json`（既存 6 件）,
`src/validation/gates.py`（`gate-run`）, `src/validation/boundary.py`,
`docs/specs/collection-pipeline.md`, `datasets/cannabinoid-raw-collection/methodology.md` §2.1.1・§2.1.3  
**GitHub:** [#12](https://github.com/routeflags/japan-cannabinoid-trends/issues/12)

## 概要

run-id は `YYYYMMDDTHHMMSSZ-source-study`（UTC の収集時刻）という規約で付けるが、
**ディレクトリ名と `run_metadata.json` の `run_id` が一致しない run が 3 件**、
**`run_metadata.json` が無い run が 3 件**、**ディレクトリ名の日付と記録された収集日がずれる run が 3 件**ある（Google Trends の raw 64 run を走査）。
いずれも「いつ収集したか」を一意に決められない状態で、現行の `gate-run` はこの一致を検査していない。

## 実測（2026-10-24、`datasets/*/data/raw/google_trends/` 64 run）

### `run_metadata.json` の `run_id` がディレクトリ名と違う（3 件）

| ディレクトリ名 | `run_metadata.run_id` |
|---|---|
| `20261008T164651Z-google-trends-common-scale-missing` | `common-scale-missing-20261009` |
| `20261001T132500Z-google-trends-disambiguated` | `disambiguated_queries` |
| `20261001T135424Z-google-trends-variance-check` | `variance_check` |

### `run_metadata.json` が無い（3 件、いずれも 2026-10-12 以前の legacy 形状）

`20261008T102022Z-google-trends-crdh` / `20261008T125719Z-google-trends-common-scale-crdh` /
`20261008T125719Z-google-trends-common-scale-thch`

### ディレクトリ名の日付と記録された収集日がずれる（3 件）

| ディレクトリ名（UTC） | 記録 | ずれの原因（推定ではなく、記録から言えること） |
|---|---|---|
| `20261008T093228Z-google-trends-5y-baseline` | `collection_date: "2026-10-06"` | 記録は**日付のみ**。ディレクトリ名とは 2 日違う |
| `20261008T164651Z-google-trends-common-scale-missing` | `collection_timestamp: "2026-10-09"` | 記録は**日付のみ**。16:46Z は JST では翌日 01:46 にあたる |
| `20261024T000000Z-google-trends-crdh-12m` | `collection_started_at`（2026-10-23） | ディレクトリ名の時刻が **00:00:00 のプレースホルダ** |

補足: 収集時刻を持つ run の多くは `collection_started_at` / `collection_finished_at`（UTC の ISO タイムスタンプ）を記録している。
上記 3 件はその形式を満たさない（日付のみ、またはプレースホルダ）。

## 何が問題か

1. **run-id が「いつ収集したか」の正本として使えない。** ディレクトリ名・`run_metadata.run_id`・収集時刻が三者三様になりうる。
2. **`today 5-y` / `today 12-m` は収集時刻で解決される**（`docs/specs/gt-boundary-verification.md`）。
   収集時刻が曖昧な run は、観測窓の根拠も曖昧になる。`window_id` を記録していない legacy run では特に効く。
3. **文書がどちらを引用するかが場当たりになる。** methodology §2.1.1 は記録（2026-10-06）を採り、
   ディレクトリ名（2026-10-08）とは違う日付を書いている。どちらが正しいかを決める規則が無い。
4. **検査が無い。** `gate-run` は artifact manifest と文書の `run_id` 一致だけを見ており
   （`src/validation/gates.py:192-204`）、ディレクトリ名との一致も、収集時刻の形式も検査していない。
   run-id の形式は公開契約の `_RUN_ID_RE`（`src/validation/publication_contract.py:121`）にあるが、
   これは公開ページ上の表記を拾うためのもので、raw 側の整合は見ていない。

## 選択肢

1. **規則を明文化し、新規 run に検査を入れる（推奨）** — (a) ディレクトリ名は UTC のタイムスタンプ必須、
   (b) `run_metadata.run_id` はディレクトリ名と一致必須、(c) `collection_started_at` / `collection_finished_at` は
   UTC の ISO タイムスタンプ必須（日付のみ・プレースホルダ不可）。`audit-new-runs` / `gate-run` で fail close し、
   既存 6 件は raw 不変のため**既知の例外として台帳に列挙**して除外する。docs は記録が日付のみである事実を書く。
2. **記録（`run_metadata`）を正本**とし、ディレクトリ名は単なる格納先とみなす。規則の変更は不要だが、
   ディレクトリ名から収集日を読む既存の慣行（run-id の規約）と矛盾する。
3. **食い違いを台帳に列挙するだけ**（検査は足さない）。再発は防げない。
4. **既存 run の改名で揃える** — raw の変更にあたるため不可（AGENTS.md Raw Data Rule）。

推奨は 1。再発防止は「新規 run の検証」で行い、既存は raw を触らずに例外として明示する。

## 決定依頼

- **Q1**: 1〜3 のどれを採るか（推奨は 1）。
- **Q2**: 既知の例外 6 件（`run_id` 不一致 3・`run_metadata` なし 3）と日付ずれ 3 件を、
  どの台帳に固定するか（`docs/provenance/` の新節か、本 issue 本文か）。
- **Q3**: 文書の表記は「ディレクトリ名の日時」と「記録された収集日時」の両方を書く形にするか、
  片方に統一するか（統一するならどちらを正とするか）。

## 完了条件

- [ ] Q1〜Q3 の回答
- [ ] 規則の明文化（run-id と収集時刻の形式・一致要件）と、新規 run に対する検査＋テスト
- [ ] 既存 6 件（および日付ずれ 3 件）を既知の例外として台帳に記録
- [ ] `methodology.md` §2.1.1・§2.1.3 の収集日表記を、記録が日付のみである事実に合わせる
- [ ] 監査スナップショットの再生成
