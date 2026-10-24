# Issue: 成分追加の候補（HHA / THCNM-CRD Distillate）— 識別が未確認のため登録は保留

**ID:** ISS-20261024-TAX-014  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`, `metadata/taxonomy/iptc-mapping.yaml`,
`metadata/queries/query-registry.json`, `docs/data-dictionary.md` §6.4,
`docs/provenance/compound-taxonomy.md`, `datasets/cannabinoid-raw-collection/README.md` の化合物表  
**GitHub:** [#11](https://github.com/routeflags/japan-cannabinoid-trends/issues/11)

## 概要

`HHA` と `THCNM-CRD Distillate` を追跡対象の成分に加える依頼。リポジトリ内には**どちらの語も既存の言及が 0 件**
（taxonomy 25 概念・query registry 35 クエリ・knowledge graph・raw run・README 表のいずれにも無い）。
本 study の化合物は **13 語で閉じた集合**として運用しており、追加は収集・配布物・公開ページまで波及する。

追加の可否は `ISS-20261015-TAX-027` が定めた gate に従う。すなわち
(1) 収集 run / staging 採用 / 文書化された名称の根拠、(2) route・由来配置の根拠、
(3) taxonomy concept ＋ `iptc-mapping.yaml`（`deliberately_unmapped`）＋ `docs/data-dictionary.md` §6.4 ＋
query registry（需要がある場合）＋ provenance 台帳の**同時更新**。`exactMatch` は検証済み ID がある場合のみ付与する。
**現時点で 2 語ともこの gate を満たさない**ため、本 issue は登録の可否を決めるための記録である。

## 外部情報から確認できたこと（未検証。出所は末尾）

| 語 | 市場での位置づけ | 識別情報 | リポジトリ内の既存言及 |
|---|---|---|---|
| `HHA` | 国内の輸入事業者が「USA 産の新原料 HHA（希釈成分ではない純原料）」として告知。同じ告知で `#HHBD` `#H4CBH` `#THA` `#HHA` を並べている | **化学名・CAS・PubChem の記載なし**。同綴りには無関係な用法がある（3,4-dihydroxyamphetamine の略号など） | 0 件 |
| `THCNM-CRD Distillate` | 国内小売ページが商品名として販売。`THCNM` = Tetrahydrocannabinol-N-Methyl（オランダ産、THC は 1ppm 未満の日本向け処方）。輸入事業者は `THA（THCNM）` とも表記 | 構造の説明（N-メチル体）はあるが **CAS / PubChem / ChEBI は確認できず** | 0 件 |

補足（THCNM の測定上の制約）:

- 小売ページの組成は `CBG 22.62% / CBD 27.04% / CBN 非検出 / Δ9-THC 非検出（10ppm 基準適合）`。
- 同ページは「**THCNM は新物質のため標準物質の登録がなく、成分検査で検出されないため COA に表示されない**」と明記している。
  つまり「THCNM が入っている」ことを分析で確認できない語であり、観測できるのは**そう表示された製品の流通**までである。
- `CRD` は国内卸の用法では結晶化耐性ディスタレート（crystal-resistant distillate）を指す製品形として使われている
  （例: `CBD/CBG/CRD 原料卸`）。`THCNM-CRD` は「THCNM の結晶化耐性ディスタレート」という**製品形つきの呼称**であり、
  化合物名そのものではない。

## 何が問題か

1. **識別が未確認の語を化合物概念として登録すると、外部 ID の捏造か検索語の混同を招く。**
   `HHA` は同綴りの無関係な語があり、Google Trends で `HHA` を引くと別現象を測る可能性が高い。
2. **THCNM は COA で検出できないと供給元が明記している。** 「市場に存在する」ことを分析で裏づけられない語を
   観測対象にすると、計測しているのが「物質」なのか「表示」なのかが曖昧になる。
3. **13 化合物は閉じた集合。** 追加すると 12ヶ月・5年 GT、共通スケール、X、YouTube、`platform-trends` の
   配布物、公開ページの化合物表まで波及する。1 語の追加で終わらない。
4. **規制状態が未確認。** HHA が HHC の酢酸エステル（HHC-O）なら HHC 誘導体としての扱いが要り、
   THCNM も指定成分・麻薬の該当を確認していない。推測で書かない。

## 選択肢

1. **保留（推奨）** — 供給元の COA / SDS（化学名・CAS）または標準物質による識別が得られるまで taxonomy・registry に登録しない。
   語と出所は本 issue に記録して残す。
2. **語彙のみ登録（化合物扱いしない）** — 「未確定の市場語」として `docs/provenance/compound-taxonomy.md` の候補語節に記録し、
   検索語には使わない。識別が得られた時点で taxonomy へ昇格する。
3. **製品語として登録** — `THCNM`（と `CRD` という製品形）を製品軸の語として追加する。化合物概念は作らない。
   既存の製品語（リキッド・オイル）と同じ層で扱うが、同綴り衝突の確認が前提。
4. **化合物として即時追加** — gate を満たさないため非推奨（名称・配置・外部 ID の根拠が無い）。

## owner への質問

- **Q1**: `HHA` の識別情報（化学名・CAS・供給元 COA / SDS）を提供できるか。できない場合、選択肢 1（保留）でよいか。
- **Q2**: `HHA` は HHC の酢酸エステル（HHC-O。CAS 3076901-68-0 / 3076901-67-9 / 3093380-78-7、PubChem 165412103）と同一か。
  同一なら新化合物ではなく HHC 誘導体として扱い、`compound_hhc` との関係（別概念か下位か）を決める必要がある。
- **Q3**: `THCNM` を「化合物」として追跡するのか、「原料の呼称（製品軸）」として追跡するのか。
  COA で検出できない制約を limitations に書く前提でよいか。
- **Q4**: `CRD`（結晶化耐性ディスタレート）を製品形の語として語彙に加えるか。
- **Q5**: 追加する場合、収集をどこまで広げるか（GT 12ヶ月 / 5年 / 共通スケール / X / YouTube）。

## 完了条件

- [ ] Q1〜Q5 の回答
- [ ] 追加する場合: TAX-027 gate の全層同時更新（taxonomy concept・`iptc-mapping.yaml`・`data-dictionary.md` §6.4・
      query registry・provenance 台帳）とテスト更新
- [ ] 追加しない場合: 判断理由を `docs/provenance/compound-taxonomy.md` に追記
- [ ] README の化合物表・件数表記の扱いが決まっている

## 出所（外部情報・2026-10-24 参照）

- `HHA`: 国内輸入事業者の SNS 告知（`#HHBD` `#H4CBH` `#THA` `#HHA` を並べた投稿。化学名の記載なし）。
- `THCNM` / `THCNM-CRD Distillate`: 国内小売ページ（商品名・組成・「THCNM は COA に表示されない」の注記）、
  オランダ供給元の製品ページ（`THCNM (Tetrahydrocannabinol-N-Methyl)`、日本向け処方の記載）。
- `HHC-O`（HHC 酢酸エステル）の識別子: PubChem CID 165412103、UNODC 物質情報、EMCDDA 技術報告。

外部ページは URL を本文に貼らず出所の種類だけを記録する（リンク切れと販売ページの変動を避けるため、必要なら owner が原 URL を保持する）。
