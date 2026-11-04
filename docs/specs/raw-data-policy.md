# Raw Data Policy

**Effective Date:** 2026-10-01
**Version:** 1.1 (2026-11-02)

---

## 1. Policy Statement

本リポジトリの raw データ（`data/raw/` 配下）について、Repository Storage（Git 追跡）に含めるか、
Local Storage にのみ置くか、公開・リリースできるかを定義する。用語は `docs/specs/contracts.md`
§2・§2.2 と `docs/domain/glossary.md` に従う。

**追跡状態と公開可否は別の事実である。** 本ポリシーが決めるのは追跡状態までであり、公開・
再配布の可否は `validation.cli gate-publication` と判断記録（`metadata/publication/`）、
および owner 判断が決める。

---

## 2. Tracking Rule

raw payload は **Local Storage** に置く。**Repository Storage（Git 追跡）に含めるのは例外**であり、
`.gitignore` の除外と `config/storage-policies.json` の `git_tracking` で宣言する。

```
.gitignore:
  **/data/raw/*
  !**/data/raw/.gitkeep
  !**/data/raw/google_trends/
  !**/data/raw/google_trends/**
```

追跡状態（`docs/specs/contracts.md` §2.2）:

| 追跡状態 | Repository Storage | 意味 |
|---|---|---|
| `tracked` | 含む（**保持**） | payload は Git index にあり、レビュー・再現の対象になる。公開適格を意味しない |
| `ignored` | 含まない（**非保持**） | 追跡方針として意図的に除外する。payload は Local Storage に存在し得る |
| `untracked_unignored` | 未決定 | 追跡方針が決まっていない。事故的な add のリスクがあり、公開候補にしない |

「保持」は `tracked` を指す。ローカルに payload が存在することは保持ではない。raw の不存在
（clone が payload を持たない等）は、非保持・未収集・欠測・0 観測のいずれでもない。
`git_tracked` の run は例外として追跡する（§5.2、`config/storage-policies.json` の
`raw-search-tracked`）。既定値と `.gitignore` の例外は一致していなければならない。

---

## 3. Rationale

### 3.1 Raw Data Is Immutable

Raw データは収集時点の生データであり、改変すべきでない。gitignore は意図しない変更を防ぎ、
`tracked` な Google Trends raw は収集時の bytes のまま Repository Storage に置く。

### 3.2 Redistribution Rights

一部の raw データ（X ツイート、YouTube の動画・検索結果等）は、プラットフォームの利用規約により
再配布が制限される。再配布が制限されるものは追跡しない（`ignored`）。**追跡しないことは権利処理の完了を意味しない。**
公開・再配布の可否は Publication review / `gate-publication` / owner 判断が別途決める。

詳細: `docs/specs/sns-redistribution-assessment.md`

### 3.3 Data Size

raw データは大容量になる可能性があり、リポジトリの管理負担を増加させる。

### 3.4 Privacy

raw データには個人情報（ユーザー名、投稿文等）が含まれる場合がある。追跡しないことは
匿名化・公開審査の代わりにならない（AGENTS.md First-Party Data / Social Data）。

---

## 4. Repository Storage と Local Storage の内訳

### 4.1 Tracked（`tracked`、Repository Storage）

| データ | 場所 | 追跡状態 |
|--------|------|----------|
| processed データ（集計統計、フィルタ済みメタデータ） | `data/processed/` | `tracked` |
| Google Trends raw（run_metadata を含む） | `data/raw/google_trends/` | `tracked`（`.gitignore` の例外） |
| 採用済み run の committed claim（catalog / staging declaration / 訂正記録） | `datasets/*/metadata/data-catalog.json`、`metadata/provenance/` | `tracked` |
| methodology / README / LICENSE / CITATION.cff | 各 study と root | `tracked` |

`.gitignore` の例外は Google Trends のみである。それ以外の raw payload は既定で `ignored` であり、
追跡する場合は `.gitignore` と `config/storage-policies.json` の両方を更新する。

追跡される run metadata は、取得日時（collection_timestamp）・クエリ条件・取得件数・
フィルタ基準を含む。Actor ID・MCP サーバー情報を含む場合も、公開可否は §4.3 の review に従う。
この表は公開の判断ではない。rawをRepository Storage（Git追跡）として保持するかは§5で定める。

### 4.2 Ignored（`ignored`、Local Storage のみ）

run metadataは、追跡される来歴文書（`staging-declaration-v1`、catalog、集計・派生成果物）
としてGitに含める。`data/raw/`内の`run_metadata.json` / `artifact-manifest.json`は、
そのrunが`git_untracked`の場合ローカルに留まり、リポジトリには含まれない（§5）。

以下は、追跡される来歴文書に記録する:

以下の raw payload は Repository Storage に含めない（`ignored`）:

- X ツイート本文（raw text）とユーザー名（usernames）
- YouTube 動画ファイルと検索結果 payload
- Apify レスポンス全文
- その他 `data/raw/` 配下で §2 の例外に該当しない payload と run_metadata

これらは Local Storage に存在し得る。存在は保持（`tracked`）ではなく、不存在は非保持の証明ではない。

### 4.3 Publication Eligibility

`tracked` / `ignored` の別は公開可否ではない。`config/storage-policies.json` の全 policy は
`publication: requires_review` を持ち、公開は `validation.cli gate-publication`
（PUB-10: `approved` + 同一 sha256）と判断記録で決める。

---

## 5. Repository Storage Retention（保持＝Git 追跡状態）

### 5.1 定義

本ポリシーで「保持（retention）」とは、raw payload を **Repository Storage**
（Git 管理下の repository）として保持するかどうかを指す。ローカル環境に raw
が存在するかどうかは保持の定義に含めない（`docs/domain/glossary.md` の
「ローカル保管」「リポジトリ保管」「追跡状態」）。

- ローカル保管: worktree / checkout / `data/raw/` など。存在するだけでは
  commit・公開・リリースを意味しない。
- リポジトリ保管: Git 追跡下にあり、clone で再現できる。
- `git_tracked` でも公開適格とは限らない。公開は §4 と公開 gate による。

状態名に `retainable` / `not_retainable` は使わない。これらは「ローカル raw
が存在するか」と混同されやすい。語彙は追跡状態を直接表す次の 2 値とする。

### 5.2 語彙（2 状態）

| `retention_status` | 定義 | 満たすべき条件 |
|---|---|---|
| `git_tracked` | raw payload を Repository Storage として保持する | payload（少なくとも run ディレクトリ内のファイル）が Git 追跡下にあり、clone で取得できる。`.gitignore` の raw 例外はこの状態と一致していること |
| `git_untracked` | raw payload を Repository Storage として保持しない | payload を Git に追加しない。ローカル raw は `data/raw/`（gitignore 対象）に存在してよい。リポジトリには非 content の来歴のみを保持する（query / request 条件 / timestamps / 件数 / 利用可能な SHA-256 / 集計・派生証拠 / 判断記録参照） |

- `git_untracked` は「raw が存在しない」「収集しなかった」を意味しない。
- `git_tracked` は「公開してよい」を意味しない。
- `data-catalog.json` の `layer: raw` entry は artifact の metadata であり、
  Repository Storage の主張ではない。追跡の有無は Git index で検査する。
- 行単位の social / video データは `git_untracked` でも `git_tracked` でも
  公開しない（`AGENTS.md`、`ISS-20261015-COL-030` §4.1）。

### 5.3 状態の決め方（優先順）

1. **明示判断**: `metadata/provenance/retention/<date>-<slug>.json`
   （`record: "raw_retention_decision"`）がその run を名指す場合、その
   `retention_status` を使う。
2. **storage policy の既定値**: 判断が無い場合、`config/storage-policies.json`
   の `artifact_layer: "raw"` と `config/sources.json` の `kind` の組み合わせで
   決まる `git_tracking` を使う（`tracked` → `git_tracked`、`ignored` →
   `git_untracked`）。`.gitignore` の raw 例外はこの既定値と一致していなければ
   ならない。
3. **fail closed**: policy registry が読めない場合は `git_tracked` とする。
   欠落を「保持しない」で免除しない。

既定値は source 種別に対するリポジトリ方針であり、個別 run の法的判断ではない。
たとえば現在の YouTube は `raw-social-default`（`source_kind: social` →
`git_tracking: ignored`）により `git_untracked`、Google Trends は
`raw-search-tracked`（`source_kind: search` → `git_tracking: tracked`）により
`git_tracked` になる。

### 5.4 判断記録（`raw_retention_decision`）

明示判断は 1 判断 1 ファイルで記録する。判断主体は owner / legal /
publication review のいずれかであり、本リポジトリは法的結論を導かない。

| フィールド | 必須 | 内容 |
|---|---|---|
| `schema_version` | ✅ | `"1.0.0"` |
| `record` | ✅ | `"raw_retention_decision"` |
| `retention_decision_id` | ✅ | 判断 ID。一意 |
| `decided_at` | ✅ | `YYYY-MM-DD` |
| `decided_by` | ✅ | 判断主体（例: `owner`, `legal`, `publication_review`） |
| `retention_status` | ✅ | `git_tracked` / `git_untracked` |
| `reason` | ✅ | 判断理由。ローカル raw の有無ではなく Repository Storage の可否 |
| `decision_reference` | ✅ | 判断が記録されたリポジトリ相対パス。実在すること |
| `publication_status` | ✅ | `approved` / `denied` / `requires_review` / `unknown`（既存 `publication-decision-v1` と同じ語彙） |
| `publication_reason` | `denied` のとき ✅ | 公開不可の理由 |
| `publication_decision_reference` | — | 公開判断の記録パス（任意。実在すること） |
| `runs[]` | ✅ | `study_id` / `source_id` / `run_id` |
| `supersedes[]` | — | 置き換える以前の `retention_decision_id`。同じ run に有効な判断が複数ある場合は conflict として fail する |

形式例（実在の run・判断ではない）:

```json
{
  "schema_version": "1.0.0",
  "record": "raw_retention_decision",
  "retention_decision_id": "<date>-<slug>",
  "decided_at": "<YYYY-MM-DD>",
  "decided_by": "owner",
  "retention_status": "git_untracked",
  "reason": "<Repository Storage として保持しない理由>",
  "decision_reference": "<判断が記録された tracked 文書への相対パス>",
  "publication_status": "requires_review",
  "runs": [
    {"study_id": "<study-id>", "source_id": "<source-id>", "run_id": "<run-id>"}
  ]
}
```

`reason` と `decision_reference` は保持状態にかかわらず必須とする。明示判断は
「この run をどう扱うか」を記録するものであり、根拠のない上書きを許さない。
`publication_status` は保持状態と独立である。

### 5.5 公開との関係

- `retention_status` は**保存・再現性の状態**であり、公開許可ではない。
- `git_untracked` の run でも、集計・派生成果物は公開審査の対象になり得る。
- `git_tracked` の run でも、公開 gate（`AGENTS.md` Publication Gate）を
  通らなければ公開しない。
- `publication_status` は **raw payload 自体**の公開可否であり、派生成果物の
  判断を置き換えない。
- 判断は owner / legal / publication review が行う。validator は記録の存在・
  参照の解決・Git index との一致を検査するだけで、法的可否を判定しない。

### 5.6 既存 run の扱い

- 判断記録が無い run は §5.3 の既定値を使う。既存の YouTube run は
  `git_untracked`、Google Trends run は `git_tracked` として扱われる。
- 既存 run を `git_untracked`（または `git_tracked`）と明示するには、owner /
  legal / publication review の判断記録が必要である。判断が無い run を推測で
  `git_untracked` にしない。
- `git_untracked` の run のローカル raw は削除しない。必要ならローカルに保持し、
  リポジトリには非 content の来歴を残す。

### 5.7 検査

| コマンド | 内容 | raw payload |
|---|---|---|
| `make audit-raw-retention` | 判断記録・policy 既定・Git index を照合し、run ごとの 2 状態を表示 | 不要 |
| `make audit-raw-completeness` | 追跡状態とローカル raw の存在を分離して報告。`git_tracked` の欠落は fail、`git_untracked` の不在は `not_repository_retained` | 任意（無くても動く） |
| `make audit-snapshots` の preflight | `git_tracked` の欠落・不整合と保持判断の不正だけ拒否する。`git_untracked` の raw 不在では拒否しない。snapshot は checkout-local inventory で、`docs/audits/snapshot-scope.json` が scope と `not_repository_retained_run_ids` を記録する | 不要（guard は raw を読まない） |

snapshot に現れない run は未収集・0 観測ではない。完全な provenance claim の
正本は catalog と declaration であり、snapshot はそのうちこの checkout で見える
raw の inventory である。`snapshot-scope.json` は raw を読まず、committed な
claim と保持状態から次を固定する。

- `audit_scope: "checkout_local"`
- `raw_visibility: "partial"`
- `raw_rows_generated: false` / `raw_dependent_facts: "unavailable"`
- `git_tracked_run_ids` / `not_repository_retained_run_ids`
- `runs[]` の `availability` / `raw_dependent_facts`（untracked は `unavailable`）
- `runs[]` の `record_count: null` / `sha256: null`（0 ではなく、raw を読まないことを表す）
- `absence_interpretation: "... not an uncollected or zero observation ..."`

`git_untracked` の run が Git index に載っている場合は `audit-raw-retention` が
fail する。`snapshot-guard` は同じ事実を warning として報告する（snapshot の
停止条件は `git_tracked` の欠落・不整合と判断不正だけ）。

`g6-git-tracking` は実際の追跡状態を棚卸しし、`g6-private-catalog` は private
境界を記録する。本節の状態はそれらを置き換えず、run 単位の期待状態を与える。

---

## 6. How to Access Raw Data

### 6.1 For Research Purposes

研究者が必要な場合、以下により raw データにアクセスできる：

1. **再収集:** 収集方法論（methodology.md）に従い、同じパラメータで再収集
2. **引用:** 公開済みの集計データを引用
3. **リクエスト:** 研究目的で raw データへのアクセスをリクエスト

clone に payload が無いことは Local Storage の状態であり、非保持・未収集の証明ではない
（`docs/specs/contracts.md` §2.2）。

### 6.2 Reproducibility

Raw payload が追跡されない場合、再現性は以下の要素に依存する：

- 収集方法論の詳細さ（methodology.md）
- run metadata と committed claim（catalog / staging declaration）の完全性
- 公開済み processed データとの整合性

**注意:** Google Trends は非公式エンドポイントを使用しており、同一クエリでも結果が変動する場合がある。再収集しても同一の値が得られるとは限らない。

---

## 7. Versioning and DOI

### 7.1 DOI Archive Contents

リリース（Zenodo DOI アーカイブ）に含めるものは追跡状態から自動で決まらない。
`scripts/release/create-clean-archive.sh` の `INCLUDE_PATHS` とリリース判断で決める。

✅ **含める（既定）:**
- processed データ（集計統計、フィルタ済みメタデータ）
- run metadata（Repository Storage にあるもの）
- `git_tracked` の Google Trends raw（run_metadata を含む）
- study metadata（catalog / 計画 / 窓 / 採用宣言）
- methodology.md
- LICENSE
- CITATION.cff
- README.md

❌ **含めない（既定）:**
- raw payload（X ツイート本文、YouTube 動画・検索結果等）
- 認証情報（.env、API キー等）

アーカイブは Git index（`git ls-files`）から構築する。`git_untracked` の raw は
checkout に存在していても含まれない（`scripts/release/create-clean-archive.sh`）。

`tracked` であることはリリース対象であることを意味しない。Google Trends raw を
アーカイブに含めることは 2026-11-04 のリリース判断であり、YouTube / X raw は
引き続き含めない。

### 7.2 Citation

DOI を引用する際は、公開済みの集計データとメタデータを参照する。raw データの引用が必要な場合は、再収集方法論を併記する。

---

## 8. Updates to This Policy

このポリシーは、法的要件の変更、プラットフォーム TOS の変更、またはリポジトリ管理方針の変更に応じて更新される。
