# Provenance

**Version:** 1.0.0
**Last Updated:** 2026-10-02
**Purpose:** 各データ値がどこから来たか、どのように処理されたかを文書化

---

## 1. Provenance 概要

本ドキュメントは、CBX Online Trend Dataset 2026 に含まれる各データ値の来歴（provenance）を記録する。

### 1.1 Provenance レイヤー

```
SOURCE（ソース）
    ↓
COLLECTION（収集）
    ↓
RAW（生データ）
    ↓
PROCESSING（処理）
    ↓
PROCESSED（処理済み）
    ↓
ANALYSIS（分析）
    ↓
PUBLICATION（公開値）
```

### 1.2 Provenance 記録の原則

| 原則 | 内容 |
|------|------|
| トレーサビリティ | 公開値から raw データまで遡れる |
| 再現性 | 同じ処理を繰り返せば同じ結果になる |
| 透明性 | 処理手順が文書化されている |
| 不変性 | raw データは変更しない |

---

## 2. X (Twitter) データ Provenance

### 2.1 データフロー

```
Apify Actor (cPYLH3QT9GyzKhB4S)
    ↓
raw: data/raw/x/202608/*.json (31ファイル, 2,376件)
    ↓
処理: 重複排除 (tweet_id ベース)
    ↓
processed: data/processed/x_cbx_202608_summary.csv (147件)
    ↓
分析: 週別集計、統計量算出
    ↓
公開: guide_cbx_rewrite.html 掲載値
```

### 2.2 収集パラメータ

| 項目 | 値 |
|------|-----|
| Actor | `cPYLH3QT9GyzKhB4S` (patient_discovery/twitter-search) |
| クエリ | `CBX リキッド` |
| セクション | `latest` |
| 最大ページ数 | 2 (~40件/run) |
| 収集期間 | 2026-08-01 〜 2026-09-08 |
| 収集方法 | 日別 Latest 検索 |
| 重複排除キー | `tweet_id` |
| 重複排除ルール | 完全一致、最初の出現を保持 |

### 2.3 公開値 → raw データ対応表

| 公開値 | 算出方法 | 元データ |
|--------|---------|---------|
| 総投稿数 147件 | tweet_id で重複排除後のカウント | `x_cbx_202608_summary.csv` |
| ユニーク著者数 55人 | username のユニークカウント | 同上 |
| W1 投稿数 12件 | createdAt で週別分類してカウント | 同上 |
| W1 著者数 7人 | W1 の username ユニークカウント | 同上 |
| Views 中央値 963 | 全147件の views 中央値 | 同上 |
| Views P90 4,904 | 全147件の views 90パーセンタイル | 同上 |
| Views 最大値 17,247 | 全147件の views 最大値 | 同上 |
| Views 合計 282,478 | 全147件の views 合計 | 同上 |
| Likes 中央値 7 | 全147件の likes 中央値 | 同上 |
| Reposts 中央値 2 | 全147件の reposts 中央値 | 同上 |

### 2.4 週別分類ロジック

| 週 | 期間 | 分類基準 |
|----|------|---------|
| W1 | 2026-08-03 〜 2026-08-09 | `createdAt` の日付が 8/3-8/9 |
| W2 | 2026-08-10 〜 2026-08-16 | `createdAt` の日付が 8/10-8/16 |
| W3 | 2026-08-17 〜 2026-08-23 | `createdAt` の日付が 8/17-8/23 |
| W4 | 2026-08-24 〜 2026-08-30 | `createdAt` の日付が 8/24-8/30 |
| W5 | 2026-08-31 〜 2026-09-06 | `createdAt` の日付が 8/31-9/6 |
| W6 | 2026-09-07 〜 2026-09-08 | `createdAt` の日付が 9/7-9/8 |

### 2.5 26週データ Provenance

| 項目 | 値 |
|------|-----|
| 収集期間 | 2026-03-19 〜 2026-09-17 |
| 週数 | 26週 |
| raw ファイル | `data/raw/x/26week/W*.json` |
| raw 件数（主要週別） | 321件 |
| raw 件数（全ファイル） | 451件 |
| ユニーク tweet_id | 291件 |
| processed ファイル | **未作成**（raw のみ） |

**注:** 26週データはまだ processed ファイルに統合されていない。

---

## 3. YouTube データ Provenance

### 3.1 データフロー

```
Apify Actor (gJvjeCYNraSfhIaNd)
    ↓
raw: data/raw/youtube/{run_id}/records_raw.json (26件)
    ↓
処理: 重複排除 (videoId ベース)
    ↓
フィルタ: タイムスタンプ基準で除外
    ↓
processed: data/processed/youtube_filtered_202607/records_filtered.csv (24件)
    ↓
公開: guide_cbx_rewrite.html 掲載値
```

### 3.2 収集パラメータ

| 項目 | 値 |
|------|-----|
| Actor | `gJvjeCYNraSfhIaNd` (danek/youtube-search) |
| 検索語 | `CBX リキッド` |
| 最大動画数 | 100 |
| 収集日 | 2026-10-01 |
| 重複排除キー | `videoId` |

### 3.3 フィルタ基準

| 基準 | 詳細 |
|------|------|
| 除外条件 | `timestamp` に "years ago" を含む（2年以上前） |
| 除外理由 | CBX 製品の販売開始（2026年7月）前の動画 |
| 除外件数 | 2件 |
| 除外動画 | filter_metadata.json に記録 |

### 3.4 公開値 → raw データ対応表

| 公開値 | 算出方法 | 元データ |
|--------|---------|---------|
| フィルタ後 24件 | フィルタ適用後のカウント | `records_filtered.csv` |
| 除外 2件 | フィルタで除外された件数 | `filter_metadata.json` |
| 上位動画（再生数順） | `views` でソート | `records_filtered.csv` |

---

## 4. Google Trends データ Provenance

### 4.1 データフロー

```
Google Trends MCP (google-trends-mcp v0.1.1)
    ↓
raw: data/raw/google_trends/{run_id}/records.json
    ↓
集計: クエリ別平均値算出
    ↓
公開: guide_cbx_rewrite.html 掲載値
```

### 4.2 収集パラメータ

| 項目 | 値 |
|------|-----|
| MCP サーバー | `google-trends-mcp` v0.1.1 |
| 地域 | JP |
| 期間 | `today 12-m` |
| 収集日 | 2026-10-01 |
| クエリ | CBX, H4CBH, HHBD, CBX リキッド |
| 比較クエリ | CBX, H4CBH, HHBD, CBX リキッド |
| 判別クエリ | CBX 大麻, CBX カンナビノイド |

### 4.3 公開値 → raw データ対応表

| 公開値 | 算出方法 | 元データ |
|--------|---------|---------|
| CBX 単独平均 68 | CBX の週次 interest の平均 | `records.json` |
| H4CBH 単独平均 56 | H4CBH の週次 interest の平均 | 同上 |
| HHBD 単独平均 33 | HHBD の週次 interest の平均 | 同上 |
| CBX リキッド単独平均 44-92 | CBX リキッドの週次 interest の平均 | 同上 |
| CBX 比較平均 13 | 比較クエリでの CBX の平均 | `comparison.json` |
| H4CBH 比較平均 13 | 比較クエリでの H4CBH の平均 | 同上 |
| HHBD 比較平均 7 | 比較クエリでの HHBD の平均 | 同上 |
| CBX リキッド出現 2026-09-13 | 単独クエリで最初に非ゼロになった週 | 同上 |
| 判別クエリ CBX 大麻 平均 2 | 判別クエリの平均 | 同上 |

### 4.4 バリアンス評価

| 項目 | 値 |
|------|-----|
| 評価日 | 2026-10-01 |
| 評価方法 | 同一日内2回収集（約80分間隔） |
| 最大変動 | ±3ポイント |
| 制約 | 単一日評価。日次・週次変動は未評価 |

---

## 5. COA データ Provenance

### 5.1 データフロー

```
分析依頼者: Hempbin
    ↓
分析実施: KCA Labs (ISO/IEC 17025 認定)
         Anresco (ISO/IEC 17025 認定)
    ↓
受領: PDF 形式の分析報告書
    ↓
変換: PDF → テキスト
    ↓
公開: guide_cbx_rewrite.html 掲載値
```

### 5.2 分析条件

| 項目 | 値 |
|------|-----|
| 分析対象 | CBX 配合製品（原料） |
| 分析依頼者 | Hempbin |
| 分析実施 | KCA Labs, Anresco |
| 認証 | ISO/IEC 17025 |
| 分析時期 | 2026年（詳細は COA 参照） |

### 5.3 公開値 → 分析報告書対応表

| 公開値 | 単位 | KCA | Anresco |
|--------|------|-----|---------|
| CBG | % | 30.4 | 30.28 |
| CBD | % | 5.74 | 5.27 |
| Total Cannabinoids | % | 36.1 | 35.55 |
| Δ9-THC | % | 0.000045 | ND |
| Δ9-THC | ppm | 0.45 | — |
| Δ8-THC | % | ND | ND |
| HHC | % | ND | ND |
| HHCH | % | ND | ND |
| THCP | % | ND | ND |

**ND = Not Detected（未検出）**

---

## 6. GSC データ Provenance

### 6.1 データフロー

```
Google Search Console
    ↓
エクスポート: CSV
    ↓
加工: クエリ別集計
    ↓
公開: guide_cbx_rewrite.html 掲載値（参考データ）
```

### 6.2 収集パラメータ

| 項目 | 値 |
|------|-----|
| ソース | Google Search Console |
| 対象サイト | thch-vape.shop |
| 対象期間 | 2026-07 |
| クエリ数 | 200 |

### 6.3 公開値 → GSC データ対応表

| 公開値 | 算出方法 |
|--------|---------|
| cbx リキッド 46クリック | GSC のクリック数 |
| cbx リキッド 449インプレッション | GSC のインプレッション数 |
| CTR 10.2% | クリック ÷ インプレッション |
| 平均順位 8.4位 | GSC の平均順位 |

**注意:** GSC データは当社サイトのみの検索パフォーマンスであり、市場全体の需要を示すものではない。

---

## 7. 再現手順

### 7.1 X データの再現

```bash
# 1. 収集（Apify Actor）
curl -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -d '{"query":"CBX リキッド","section":"latest","maxPages":2}'

# 2. 重複排除
python3 -c "
import json
with open('raw.json') as f:
    data = json.load(f)
seen = set()
unique = []
for item in data:
    tid = item.get('tweet_id')
    if tid and tid not in seen:
        seen.add(tid)
        unique.append(item)
with open('processed.json', 'w') as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)
"

# 3. 週別集計
python3 -c "
import csv
from datetime import datetime
from collections import defaultdict

with open('x_cbx_202608_summary.csv') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

weekly = defaultdict(lambda: {'posts': 0, 'authors': set()})
for row in rows:
    dt = datetime.fromisoformat(row['createdAt'].replace('Z', '+00:00'))
    # 週分類ロジック
    week = get_week(dt)
    weekly[week]['posts'] += 1
    weekly[week]['authors'].add(row['username'])
"
```

### 7.2 Google Trends データの再現

```bash
# MCP ツールを使用
interest_over_time(terms=["CBX"], geo="JP", timeframe="today 12-m")
interest_over_time(terms=["H4CBH"], geo="JP", timeframe="today 12-m")
interest_over_time(terms=["HHBD"], geo="JP", timeframe="today 12-m")
interest_over_time(terms=["CBX リキッド"], geo="JP", timeframe="today 12-m")
compare_terms(terms=["CBX", "H4CBH", "HHBD", "CBX リキッド"], geo="JP", timeframe="today 12-m")
```

**注意:** Google Trends は非決定的であり、同じクエリでも結果が変動する可能性がある。

---

## 8. 制約事項

| データセット | 制約 |
|-------------|------|
| X データ | 検索結果の非決定性。完全な網羅性は保証されない |
| YouTube データ | 検索結果の非決定性。公開動画のみ取得 |
| Google Trends | 相対指数。非決定的。低ボリュームクエリは不安定 |
| COA データ | 分析依頼者（Hempbin）と発行者（Routeflags）の関係は未開示 |
| GSC データ | 当社サイトのみ。市場全体を代表しない |

---

## 9. 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| `docs/data-dictionary.md` | カラム定義 |
| `methodology.md` | 収集・処理方法 |
| `datasets/*/methodology.md` | データセット別方法論 |
| `docs/specs/raw-data-policy.md` | raw データ公開方針 |
| `docs/specs/sns-redistribution-assessment.md` | SNS 再配布評価 |
