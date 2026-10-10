# Japan Cannabinoid Trends — データ品質・再現性改善指示書

## 1. 目的

既存の研究データセットを監査し、第三者が検証・再利用・引用できる状態に改善する。

対象：  
[`https://github.com/routeflags/japan-cannabinoid-trends`](https://github.com/routeflags/japan-cannabinoid-trends)

優先する品質要件：

1. Data Integrity（データ完全性）
2. Provenance（データ来歴）
3. Reproducibility（再現可能性）
4. Methodological Validity（方法論的妥当性）
5. Citation Integrity（引用情報の整合性）

**最重要原則：実測値、推定値、解釈を混同しない。**

## 2. 作業上の制約

- 既存のRawデータは削除・上書きしない。
- データを推測で補完しない。
- 観測ゼロと欠測を区別する。
- 新たな有料API取得は行わない。
- 研究範囲や対象化合物を勝手に変更しない。
- 元データに誤りがある場合は、根拠を記録してProcessedデータを修正する。
- 公開済みのリリースやDOIアーカイブは変更しない。
- 既存のテスト・検証処理を優先して再利用する。
- 変更は新規ブランチで実施し、mainへの直接反映は行わない。

## 3. P0 — X / YouTubeの収集データの妥当性

対象：

- `datasets/cannabinoid-multi-trends/`
- 関連する収集コード・メタデータ・集計コード

### 3.1 取得件数の再定義

現状のXデータは、キーワードによって `maxPages` が2または3となっている。

この状態で取得件数を投稿総数や市場の言及量として比較してはならない。

次の値を区別すること。

- `collected_count`：実際に取得したレコード数
- `unique_count`：重複排除後のレコード数
- `collection_limit`：設定した取得上限
- `limit_reached`：上限到達の有無
- `collection_complete`：設定された収集処理の正常完了
- `population_complete`：対象期間の全投稿を網羅したと判断できるか

`collection_complete = true` は `population_complete = true` を意味しない。

### 3.2 欠測状態の分類

以下の状態を明確に区別する。


| 状態                 | 定義           |
| ------------------ | ------------ |
| observed           | 有効な観測結果      |
| observed\_zero     | 観測範囲内で0件を確認  |
| not\_collected     | 収集未実施        |
| collection\_failed | 取得処理失敗       |
| rate\_limited      | API等の制限      |
| truncated          | 取得上限による打ち切り  |
| unavailable        | データソース側で取得不可 |
| unknown            | 状態を確定できない    |


`observed_zero` は、収集処理が成功し、対象範囲について0件と判断できる根拠がある場合のみ使用する。

検索結果0件でも、取得条件の不確実性が残る場合は、その制約を別途記録する。

### 3.3 YouTube

- `videoId` による重複排除を検証する。
- 公開日時と取得日時を区別する。
- 相対日時から絶対日時への変換がある場合、変換条件を記録する。
- `max_videos` による打ち切りを明示する。
- 動画投稿数、取得動画数、視聴回数を異なる指標として扱う。

### 完了条件

- 全収集結果に取得条件と収集状態が記録される。
- 取得上限が異なるデータを総投稿量として直接比較していない。
- 重複排除の結果を再計算できる。
- RawとProcessedの件数差を説明できる。

## 4. P0 — Early Warning Indexの検証

対象：

`datasets/cannabinoid-multi-trends/data/processed/early-warning-index-v1.csv`

### 4.1 算出根拠の追跡

以下の項目について、定義・計算方法・根拠データを確認する。

- `first_mention_date`
- `left_censored`
- `first_value`
- `peak_value`
- `peak_week`
- `mean_12m`
- `persistence_class`
- `emergence_score`
- `first_regulation_date`
- `current_status`
- `source_run_ids`

特に `emergence_score` の1〜4という値について、以下を確認する。

1. 計算式または判定ルールが存在するか。
2. 閾値が明文化されているか。
3. 元データから同じ値を再計算できるか。
4. 研究者の裁量判断が含まれるか。
5. スコアの妥当性が検証されているか。

計算式が存在しない場合、既存値を推測で正当化しない。

その場合は、スコアを暫定的な研究者分類として明示し、数理的指数と区別する改善案を提示する。

### 4.2 First Mentionの定義

`first_mention_date` が意味するものを明確にする。

例：

- Google Trendsにおける最初の非ゼロ観測
- Xにおける最初の取得投稿
- 複数データソースを統合した最初の観測

「最初の観測日」と「日本市場への初出日」を同一視しない。

左側打ち切り（Left Censoring）の扱いも検証する。

### 4.3 規制データ

規制情報について以下を区別する。

- 公布日
- 施行日
- 指定日
- 規制対象の化学的範囲
- 法令の根拠
- 確認日

各規制情報は、可能な限り官報・厚生労働省・e-Gov等の一次資料へ追跡できるようにする。

法的状態の変更を推測で行わない。

### 完了条件

- 全列の定義がデータ辞書に存在する。
- 数値の生成根拠を追跡できる。
- 再計算可能な項目は自動検証できる。
- 検証不能な値が明示される。
- 規制情報に一次資料と確認日が対応付けられる。

## 5. P1 — Google Trendsの正規化と比較可能性

対象：

- Google Trends Rawデータ
- 収集メタデータ
- 集計コード
- 研究方法論

### 5.1 正規化単位

以下を区別する。

**単独取得**

1キーワードの指定期間内の相対変化。

**比較取得**

同じリクエスト内に含めた複数キーワードの相対比較。

単独取得した異なるキーワードの平均値を直接比較してはならない。

### 5.2 必須メタデータ

各取得結果に以下を保持する。

- 検索キーワード
- 地域
- 取得期間
- 取得日時
- 比較セットID
- Google Trendsの検索種別
- 時間粒度
- 取得ツールとバージョン
- 収集実行ID

### 5.3 比較可能性の検証

- 同一条件で取得した比較セットか確認する。
- 比較セット間の指数を無条件に連結しない。
- 低検索ボリュームによるゼロ・欠測を明示する。
- 比較セットを接続する場合は、アンカー方式等の手法と誤差を文書化する。
- 過去の取得結果を再収集した場合、値が変化する可能性を明示する。

### 完了条件

比較可能な値と比較不可能な値を、データとドキュメントの両方で判別できる。

## 6. P1 — 自動品質検証

既存の検証コードを調査し、必要最小限の追加を行う。

必須テスト：

1. Schema Validation
2. Null / Missing Value Validation
3. Duplicate Detection
4. Date Range Validation
5. Provenance Validation
6. Google Trends Scale Validation
7. Collection Limit Validation
8. Derived Value Recalculation
9. Regulatory Source Validation
10. Citation Metadata Consistency

検証結果は機械可読なJSONと、人間が読めるMarkdownで出力する。

各検証結果は以下に分類する。

- PASS
- WARN
- FAIL
- NOT_VERIFIABLE

**検証不能をPASSとして扱わない。**

## 7. P2 — 引用情報とリリースの整合性

対象：

- `CITATION.cff`
- [`CHANGELOG.md`](http://CHANGELOG.md)
- GitHub Releases
- Zenodo DOI
- データセットのバージョン情報

以下を確認する。

- 現行バージョンの整合性
- DOIと対象バージョンの対応
- GitHub ReleaseとZenodoアーカイブの一致
- ライセンス
- 著者情報
- 公開日
- データセット名
- 利益相反（COI）の開示

DOIが登録済みであることと、DOIが指すデータ内容の正確性は別々に検証する。

既存の公開済み成果物を上書きせず、必要な訂正は新しいバージョンとして扱う。

## 8. 成果物

以下を作成する。

**A. 監査報告書**

`docs/audit/[data-quality-audit.md](http://data-quality-audit.md)`

各問題について以下を記載する。

- 対象ファイル
- 問題の内容
- 根拠
- 重大度
- 実施した修正
- 残存リスク

**B. データ辞書**

既存のデータ辞書を更新し、指標の定義、単位、欠測状態、計算方法を明文化する。

**C. 自動検証コード**

既存の検証基盤を拡張する。

**D. 検証結果**

機械可読JSONおよびMarkdown形式。

**E. 変更履歴**

修正内容と、既存の研究結果に与える影響を記録する。

## 9. 作業順序

Phase 1 — Inventory

既存ファイル、データ、収集コード、検証コードを確認する。

Phase 2 — Audit

元データとProcessedデータを突合し、問題を特定する。

Phase 3 — Remediation

P0から順に修正する。

Phase 4 — Validation

自動テストを実行し、結果を記録する。

Phase 5 — Review

研究結果への影響を整理し、未解決事項を報告する。

## 10. 最終報告形式

以下の形式で報告すること。


| 項目       | 内容                                   |
| -------- | ------------------------------------ |
| 監査対象     | ファイル数・データセット数                        |
| P0       | 発見件数・修正件数                            |
| P1       | 発見件数・修正件数                            |
| P2       | 発見件数・修正件数                            |
| テスト      | PASS / WARN / FAIL / NOT\_VERIFIABLE |
| 研究結果への影響 | 変更された指標と結論                           |
| 残存課題     | 未解決事項                                |
| 追加API費用  | 実績                                   |


最後に、以下の3点を明確に回答する。

1. 既存データから研究結果を再現できるか。
2. 第三者が研究方法を独立して検証できるか。
3. 現時点で学術引用に適した公開状態か。

各回答は YES / PARTIAL / NO とし、根拠を付ける。

**最終ゴール：研究成果の信頼性を高めることであり、単にテストを通すことではない。**