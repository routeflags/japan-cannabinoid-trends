# Issue: IPTC Media Topics 未対応の 17 概念

**ID:** ISS-20261015-TAX-025
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-15)
**対象:** `metadata/taxonomy/iptc-mapping.yaml`, `metadata/taxonomy/compound-taxonomy.skos.jsonld`, `metadata/taxonomy/content-taxonomy.skos.jsonld`, `docs/specs/validation-framework.md` §23.4

## 概要

IPTC Media Topics への対応付けが未完了の末端概念が 17 件ある（化合物 9 / intent 4 / format 4）。
現状は `iptc-mapping.yaml` の `coverage` 宣言で `deliberately_unmapped` / `not_applicable`
として明示され、全概念を被覆している。

## 確認された観測

- 2026-10-13 に `coverage` 宣言（mapped / deliberately_unmapped / not_applicable）を追加し、
  全概念が分類されていることを機械検証可能にした。
- 「対応可能だが未対応」と「IPTC 語彙上対応が無い」の区別は、判断待ちのまま。

## 影響

- 外部標準との対応表が不完全なのか、完了なのかを第三者が判定できない。

## 対応方針

- IPTC 語彙を確認したうえで、各概念の対応可否を判断する。
- **推測で対応付けない**（対応不可ならその理由を `coverage` の区分で示す）。

## 完了条件

- [x] IPTC 語彙の確認記録
- [x] 対応可能概念の追加とテスト更新
- [x] 対応不可概念の理由の記録

## 対応記録（2026-10-15）

### IPTC 語彙の確認記録

確認はリポジトリ内の証拠のみで行い、IPTC への live 照会は行っていない
（リポジトリ規則が外部呼び出しを禁じ、推測での対応付けを禁じるため）。
確認方法と参照証拠は `metadata/taxonomy/iptc-mapping.yaml` の `verification.method` に記録した。
参照した証拠:

- 本ファイルの対応済み 6 主題（Chemistry / Products and Services / Health and Fitness /
  Marketing / Reviews / Retail）はいずれも化合物単位ではない広いニュース主題。
  化合物単位の IPTC 主題はリポジトリ内の証拠に無い。
- `docs/specs/standards-compliance-analysis.md` §3.2/§4.3:
  IPTC はニュース主題語彙。`topic` のみ `schema:about` に対応し、intent/format はカスタム。
- `metadata/taxonomy/content-taxonomy.skos.jsonld`:
  topic/intent/format は別 scheme（別次元）。
- `docs/provenance/compound-taxonomy.md`:
  HHC/HHCH/THCH/THC-O は立体異性体・Δ体の総称で単一 exactMatch は混同を招くため、
  CRDP/CRDH は化学構造不明のため、それぞれ外部検証は未実施。

### 判断と理由

- **intent 4 / format 4 → `not_applicable`**（TAX-026 の次元分離規則を適用）。
  投稿意図・表現形式は主題ではなく分類の別次元であり、IPTC の主題語彙に対応する概念を持たない。
  例えば商業意図を Marketing に対応付けると intent 次元と topic 次元を混同することになる。
- **化合物 9 → `deliberately_unmapped` のまま 2 群に分割し、群ごとに理由を記録。**
  第 1 群（cbc/cbdv/thcv）は Wikidata exactMatch を持つが IPTC 側の対応主題が証拠に無い。
  第 2 群（thch/hhc/hhch/thc-o/crdp/crdh）は識別子自体が外部未検証。
  いずれも化合物単位の IPTC 対応付けには IPTC 語彙の外部確認が必要であり、未実施のため
  推測で対応付けない。
- **対応可能と判断できた追加概念は無し。**対応済みの 6 主題は変更なし。
  化合物識別子の正本は ChEBI / Wikidata（taxonomy の exactMatch）のままとする。
- 次元の分離は維持: route/origin は `compound-taxonomy`、化学クラスは
  `chemical-class-taxonomy`（TAX-026）。本対応で SKOS ソースには触っていない。

### 更新内容

- `metadata/taxonomy/iptc-mapping.yaml`（1.1.0 → 1.2.0）:
  coverage の再区分、群ごとの理由、limitations 2 件追加、verification に確認方法を記録。
- 新規 `tests/validation/test_iptc_mapping_verdicts.py`（2 件）:
  IPTC 主題を持つのは topic 次元のみ、intent/format 8 概念は `not_applicable` 宣言を維持。
- `exports/taxonomy/iptc-mapping.yaml` を正規手順（`export-taxonomy.sh` と同じ `cp`）で同期。
  SKOS ソースは不変のため `.ttl` / `.schema.jsonld` の再生成は不要。
- `docs/specs/validation-framework.md` §23.4 の IPTC 引き継ぎ文を判断済みに更新。
  同段落の化学クラス文（TAX-026 が判断済みのはずが「未判断」のまま残存）を合わせて修正。

### 整合テスト

- `pytest tests/validation/test_taxonomy_consistency.py test_chemical_class_dimension.py test_iptc_mapping_verdicts.py`: 15 passed。
- `audit-issues` failures=0、`validate-registries` 全 OK、`git diff --check` OK。

### 残課題（本 issue の範囲外・別管理）

- 化合物 9 の IPTC 対応可否の最終確認には IPTC 語彙へのアクセスを持つ人間による
  外部確認が必要。それまでは `deliberately_unmapped` の判定を維持する
  （`verification.method` の残件に記録）。
- `compound_mapping`（ChEBI / Wikidata）の部分収載（cbc/thcv/cbdv/crdh 等）は本 issue の対象外。
  `docs/provenance/compound-taxonomy.md` の未修正既知事項として残る。
