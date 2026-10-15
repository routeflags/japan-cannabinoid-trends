---
name: study-release-prep
description: |
  契約に従って新しい Study（研究）を作り、dataset release の直前まで進める。
  「新しい study を作る」「研究データセットをリリース前まで整える」「release prep」
  「研究テーマから processed dataset を作る」などで使う。
---

# Study Release Prep Skill

このスキルは、DDD 上の **Study = 研究** を新規作成し、公開操作の直前まで進めるための手順である。

Study は HTML ページでも GitHub Release でもない。
Study は、研究質問・対象範囲・入力証拠・処理方法・成果物・制約・検証結果を
`datasets/<study-id>/` と `metadata/studies/study-registry.json` に束ねる研究集約である。

## 停止条件

このスキルは **release 直前で止める**。

やってよい:

- study ディレクトリ作成
- methodology / schema / processed artifact 作成
- deterministic processing code 作成
- Makefile target 追加
- registry / audit snapshot / tests 更新
- release prep commit

やってはいけない:

- Git tag 作成
- GitHub Release 作成
- Zenodo upload / publish
- DOI の発明
- raw data の手編集
- 外部 payload を declaration なしに採用

Tag / GitHub Release / Zenodo は、ユーザーが別途「release してよい」と明示した時だけ行う。

## 入力確認

最初に、最低限次を確定する。

1. 研究質問
2. `study_id`
3. 対象 source
4. 除外 source
5. 公開対象の粒度
6. raw / private / processed / publication のどの layer を触るか
7. version を上げるか、release metadata 更新まで行うか

不明なまま進めない。特に source の除外・欠測・公開粒度は、推測で補完しない。

## 参照する契約

作業前に確認する。

- `AGENTS.md`
- `docs/specs/contracts.md`
- `docs/specs/collection-pipeline.md`
- `docs/specs/release-process.md`
- `metadata/studies/study-registry.json`
- 必要に応じて `metadata/queries/query-registry.json`

DDD 用語では `docs/specs/contracts.md` の定義を正本にする。

## 実装手順

### 1. Study 集約を作る

作成先:

```text
datasets/<study-id>/
├── README.md
├── methodology.md
├── data/
│   └── processed/
└── metadata/
    └── schema/
```

必要に応じて `analysis/` を追加する。
`data/raw/` は、実際に catalog 済み raw run を置く場合だけ使う。

README には次を含める。

- Study ID
- 研究質問
- included sources
- excluded sources
- processed files
- regeneration command
- publication / privacy posture

methodology には次を含める。

- research question
- release scope
- inputs
- transformation
- derived fields
- validation
- limitations
- evidence level

### 2. Study registry に登録する

`metadata/studies/study-registry.json` に追加する。

規則:

- `research_questions` は README に verbatim で存在させる
- `sources` は今回の release scope に含む source だけにする
- 除外 source は README / methodology に書くが、registry の `sources` には入れない

研究 CLI / tests が study 数を固定している場合は、意図した増加として tests も更新する。

### 3. 生産コードを作る

processed artifact は手作業で作らず、`src/processing/` に deterministic builder を置く。

CLI は `src/processing/cli.py` に追加する。

Makefile に production target を追加する。

例:

```text
make <study-target>
```

Production target は downstream layer だけに書く。
raw / private / publication / release 操作はしない。

### 4. Processed artifact と schema を作る

`data/processed/` に出す。

各 file について:

- source-specific unit を保持する
- cross-platform common scale を発明しない
- missing / not_collected / observed_zero を区別する
- social / video / post の row-level record を公開しない
- manifest / row counts / source references を残す

`metadata/schema/` には CSV / JSON の機械可読 schema を置く。

### 5. 再導出監査へ接続する

`src/processing/reproduce.py` に登録する。

優先:

1. `DERIVATIONS` に executable derivation を登録
2. どうしても再導出不能なら `NON_REPRODUCIBLE` に理由・欠落 input・上流 step を記録

新しい processed artifact が `undeclared` のままなら完了ではない。

### 6. 監査と tests を更新する

最低限実行する。

```bash
make <study-target>
.venv/bin/python -m processing.cli audit-processed
make audit-snapshots
make gates
.venv/bin/python -m pytest -q
```

必要に応じて追加する。

- `tests/processing/test_<study>.py`
- `tests/research/test_registries.py`
- `tests/research/test_research_cli.py`

監査 snapshot は生成物として更新する。raw が変更されていないことを確認する。

### 7. Release 直前の確認

Release metadata を更新する場合は、ユーザーに version を確認する。

更新候補:

- `CHANGELOG.md`
- `CITATION.cff`
- `metadata/datapackage.json`
- clean archive 検証

ただし、次はこのスキルでは実行しない。

- `git tag`
- `git push origin vX.Y.Z`
- `gh release create`
- Zenodo API / Web publish

## 完了報告

報告には次を含める。

- 作成した study ID
- research question
- included / excluded sources
- processed artifact と row counts
- regeneration command
- validation commands and results
- release 直前で止めたこと
- tag / GitHub Release / Zenodo は未実行であること
