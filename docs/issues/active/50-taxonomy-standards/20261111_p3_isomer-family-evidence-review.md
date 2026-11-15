# Issue: 同族体・アセテート語の異性体別根拠レビュー — ファミリー登録と既存runは維持

**ID:** ISS-20261111-TAX-042
**優先度:** P2 (Medium)
**ステータス:** OPEN
**対象:** cannabinoid-raw-collection の `THCP`、`THCJD`、`THCPO`、`THCB-O-acetate` のscopeNote・README審査欄と、今後の異性体別概念・query登録判断
**関連:** `ISS-20261111-TAX-040`（owner確認したTHCP / THCJDファミリーとTHCPOの意味）、`ISS-20261111-TAX-041`（THCA / THCBの個別検索トピック）

## 問いと現状

owner は、ファミリー語を異性体別の検索トピックへ精密化する場合も、既存のファミリーqueryとそのrunを別トピックとして保持し、過去runを個別異性体へ遡及配賦しないという方針を了承した。登録queryを廃止するか、将来のprimary coverageから外すかは別のowner判断である。

このレビューは文献・構造レジストリ・法令資料の確認のみであり、taxonomyの分類・identifier・`exactMatch`・query registry・collection plan・raw/runを変更しない。外部構造レコードが確認できても、ファミリー概念には個別異性体のidentifierを付けない。個別フォームへの登録、family queryのlifecycle変更、収集はownerの別判断を待つ。

## 異性体別の根拠

| 登録中の語 | あり得る個別フォーム | 確認した根拠 | 審査上の結論 |
|---|---|---|---|
| `THCP`（C7 family） | `Δ8-THCP` / `Δ9-THCP` | Citti et al. 2019（DOI `10.1038/s41598-019-56785-1`, PMID 31889124）はΔ9体を植物から単離・構造確認。Giorgetti et al. 2026（DOI `10.1016/j.forsciint.2026.113114`, PMID 42641241）はオンライン製品からΔ9体とΔ8体を検出（各19.2%、15.4%）。 | 両フォームは個別トピックとして根拠あり。現在の`THCP` queryはΔ8/Δ9未指定のfamilyのまま。 |
| `THCJD`（C8 / 3-octyl-THC family） | `Δ8-THCJD` / `Δ9-THCJD`（資料表記: `Δ8/Δ9-THCjd`, `Δ8/Δ9-3-octyl-THC`） | Tanaka & Kikura-Hanajiri 2024（DOI `10.1248/yakushi.24-00029`, PMID 39085059）は日本で流通した油製品5点から両異性体をNMRで同定。Munger et al. 2026（DOI `10.26828/cannabis/2026/000348`, PMID 41853707）はΔ8-THC-JD標準品を使ったが、対象5製品でTHC-JDを検出しなかった。 | 両フォームは個別トピックとして根拠あり。`THCJD`の綴りはownerのfamily検索語であり、単一異性体名ではない。 |
| `THCPO`（THCP-O-acetate、異性体未指定） | `Δ8-THCP-O-acetate` / `Δ9-THCP-O-acetate` | 令和6年厚生労働省令第81号と別添は両構造を別々に列挙（いずれも「麻薬を除く」）。Tanaka et al. 2025（DOI `10.1002/dta.3883`, PMID 40075559）はΔ9体を製品から同定。調べた範囲ではΔ8体の製品同定を確認していない。 | 両フォームの構造・registry recordは別々に扱う。Δ9は分析検出、Δ8は現状で法令・registry根拠。`THCPO`自体はfamilyのまま。 |
| `THCB-O-acetate`（異性体未指定） | `Δ8-THCB-O-acetate` / `Δ9-THCB-O-acetate` | 令和6年厚生労働省令第81号の別添は両構造を別々に列挙（n=4）。調べた範囲では、いずれのアセテート体についても製品中の分析同定を確認していない。Tanaka et al. 2025が同定したTHCB-O体は**別のエステル**`Δ9-THCB-O-butanoate`。 | 現時点ではファミリーqueryを維持し、異性体別conceptは追加しないことを推奨。butanoateをacetateに含めない。 |

MHLW資料はΔ8 / Δ9の構造範囲を示す法令上の根拠であり、各商品・検索結果の内容を同定する根拠ではない。調査範囲はPubMed / Europe PMC、MHLW資料、PubChem PUG REST、FDA GSRS、Wikidataである。文献検索で見つからなかったことは不存在の証明ではない。

## 個別フォームのregistry記録（family概念には割当てない）

| 個別フォーム | 記録された識別子 | 注意 |
|---|---|---|
| `Δ9-THCP` | PubChem CID 6453074; CAS 54763-99-4; UNII WTK87HN3LG; Wikidata Q85806080 | Δ9個別フォームの記録。 |
| `Δ8-THCP` | PubChem CID 44307335; CAS 51768-60-6; UNII Q6P6W9SNR2; Wikidata Q141317106 | registry記録に加え2026年の製品検出論文あり。 |
| `Δ9-THCB` | PubChem CID 6453891; CAS 60008-00-6; UNII LIC9QAS59U; Wikidata Q7706539 | Δ9個別フォームの記録。 |
| `Δ8-THCB` | PubChem CID 6452496; CAS 51768-59-3; Wikidata Q83072633 | GSRS recordは確認できず。 |
| `Δ9-THCJD` / `Δ9-3-octyl-THC` | PubChem CID 155318984; CAS 2552798-63-5 | stereo-defined record。 |
| `Δ8-THCJD` / `Δ8-3-octyl-THC` | PubChem CID 102024084; CAS 431041-39-3; Wikidata Q114242092 | Wikidata label `JWH-138`は構造を確認せずaliasとして使わない。 |
| `Δ9-THCP-O-acetate` | PubChem CID 172677450; CAS 2829292-82-0; Wikidata Q122689235 | Wikidata itemはfamily風のlabelだがΔ9構造にkeyed。 |
| `Δ8-THCP-O-acetate` | PubChem CID 172874392 | CAS / GSRS / Wikidata recordを確認できず。 |
| `Δ9-THCB-O-acetate` | PubChem CID 172875699 | CAS / GSRS / Wikidata recordを確認できず。 |
| `Δ8-THCB-O-acetate` | PubChem CID 172871934 | CAS / GSRS / Wikidata recordを確認できず。 |

これらのidentifierは個別異性体についての証拠であり、現在のfamily query（`THCP`、`THCJD`、`THCPO`、`THCB-O-acetate`）へ転記したり、family概念の`skos:exactMatch`に使ったりしない。CAS値は一部APIを認証なしで直接照会できず、GSRS・PubChem・Wikidata・vendor record間の照合に基づくものを含む。

## ownerに残るscope判断

1. `THCP`、`THCJD`、`THCPO`をそれぞれΔ8/Δ9個別queryに分けるか。分ける場合もfamily queryと過去runは保持し、新queryだけを追加する。
2. `THCB-O-acetate`は法令上の構造差だけで分割せず、分析的な検出証拠が限られるため現状family queryを維持することを推奨する。個別フォームが必要なら明示的なowner scope決定を要する。
3. `THCJD-O-acetate`（C8 acetate）はMHLW資料に記載されるが、今回の4 familyには含めない。対象追加は別のowner決定を要する。
4. 個別queryの登録とcollection authorizationは別工程である。collectionを始める場合はsource、query terms、windows、family queriesをfuture primary coverageに残すかを先に決める。既存runへの異性体帰属はしない。
