---
name: research-keyword-trends
description: |
  キーワードごとの Google Trends 調査スキル。
  キーワードを指定して、検索需要データを収集し、言及開始時期を特定する。
  「<キーワード> のトレンド調べて」「<キーワード> の Google Trends 収集」
  「<キーワード> がいつから出始めたか」などで使う。
---

# Research Keyword Trends スキル

キーワードごとの Google Trends 調査スキル。**任意のキーワード**で再利用できるよう抽象化されている。

各調査結果は `research/` 配下に Markdown で保存し、データは `datasets/cannabinoid-multi-trends/data/raw/google_trends/` に JSON で保存する。

---

## トリガー

- 「<キーワード> のトレンド調べて」
- 「<キーワード> の Google Trends 収集」
- 「<キーワード> がいつから出始めたか」
- 「<キーワード> の言及開始時期を特定して」
- 「<キーワード> を追加して調査」

---

## 入力パラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| `keyword` | string | ✅ | — | 調査対象キーワード |
| `geo` | string | — | `JP` | 地域コード |
| `timeframe_12m` | string | — | `today 12-m` | 12ヶ月データの期間 |
| `timeframe_5y` | string | — | `today 5-y` | 5年データの期間 |
| `output_dir` | string | — | `datasets/cannabinoid-multi-trends/data/raw/google_trends/` | 保存先 |
| `report_path` | string | — | `research/` | レポート保存先 |

---

## データ収集フロー

### Step 1: 12ヶ月データ収集

```
1. interest_over_time を呼び出し
   terms=["<keyword>"], geo="JP", timeframe="today 12-m"

2. 結果を {YYYYMMDDTHHMMSS}Z-google-trends-{keyword}-12m/ に保存
   - records_{keyword}_12m.json
   - run_metadata.json
```

### Step 2: 5年データ収集

```
1. interest_over_time を呼び出し
   terms=["<keyword>"], geo="JP", timeframe="today 5-y"

2. 結果を {YYYYMMDDTHHMMSS}Z-google-trends-{keyword}-5y/ に保存
   - records_{keyword}_5y.json
   - run_metadata.json
```

### Step 3: 初出時期の特定

```python
# 5年データから初出時期を特定
data_5y = load_json("records_{keyword}_5y.json")
nonzero_points = [d for d in data_5y["data"] if d["value"] > 0]

if len(nonzero_points) == 0:
    first_mention = "データなし"
elif data_5y["data"][0]["value"] > 0:
    # 5年ウィンドウ起点時点ですでに存在
    first_mention = f"{data_5y['data'][0]['date']}以前"
else:
    # 5年ウィンドウ内で初出
    first_mention = nonzero_points[0]["date"]
```

### Step 4: レポート作成

調査結果を Markdown レポートにまとめる。

---

## 出力フォーマット

### データファイル

```
datasets/cannabinoid-multi-trends/data/raw/google_trends/
├── {YYYYMMDDTHHMMSS}Z-google-trends-{keyword}-12m/
│   ├── records_{keyword}_12m.json
│   └── run_metadata.json
└── {YYYYMMDDTHHMMSS}Z-google-trends-{keyword}-5y/
    ├── records_{keyword}_5y.json
    └── run_metadata.json
```

### データスキーマ

```json
{
  "keyword": "string",
  "geo": "JP",
  "timeframe": "today 12-m | today 5-y",
  "collected_at": "YYYY-MM-DD",
  "note": "string",
  "first_mention": "YYYY-MM-DD | YYYY-MM-DD以前 | データなし",
  "first_value": "number",
  "peak": {"date": "YYYY-MM-DD", "value": "number"},
  "data": [
    {"date": "YYYY-MM-DD", "value": "number"}
  ]
}
```

### レポートフォーマット

```markdown
## {KEYWORD}

| 項目 | 内容 |
|------|------|
| **カテゴリ** | Major/Minor Phytocannabinoid, Semi-Synthetic, etc. |
| **初出時期** | YYYY-MM-DD または YYYY-MM-DD以前 |
| **初出値** | number |
| **ピーク** | YYYY-MM-DD（値NN） |
| **5年平均** | 約NN-NN |
| **特徴** | 一言で特徴を記述 |

### 時系列推移
- YYYY-MM-DD: 初出（値NN）
- YYYY-MM-DD: ピーク（値NN）
- YYYY-MM-DD: NNに上昇/低下

### 所見
考察（意見）を記述。
```

---

## 注意事項

| 項目 | 内容 |
|------|------|
| **5年制限** | Google Trends の最大取得期間は `today 5-y` |
| **起点時点データ** | 5年ウィンドウ起点時点ですでにデータがある場合、「YYYY-MM-DD以前」と記載 |
| **低ボリューム** | 閾値未満のキーワードはデータが返らない場合あり |
| **レート制限** | 429 エラー時は 2-5 分待機 |
| **相対指数** | Google Trends は相対指数（0-100）であり、絶対検索数ではない |
| **多義語** | CBD/THC 等は多義語のためコンテキスト分析が必要 |

---

## 実行例

### 例1: CBN の調査

```
1. interest_over_time: terms=["CBN"], geo="JP", timeframe="today 12-m"
   → 保存: .../20261002T081839Z-google-trends-cbn-12m/

2. interest_over_time: terms=["CBN"], geo="JP", timeframe="today 5-y"
   → 保存: .../20261002T082000Z-google-trends-cbn-5y/

3. 初出時期特定: 2021-09-26以前（5年ウィンドウ起点時点ですでに存在）

4. レポート更新: research/20261002-first-mention-timeline.md
```

### 例2: 新規キーワード CBC の調査

```
1. interest_over_time: terms=["CBC"], geo="JP", timeframe="today 12-m"
2. interest_over_time: terms=["CBC"], geo="JP", timeframe="today 5-y"
3. 初出時期特定
4. レポート作成: research/YYYYMMDD-first-mention-timeline.md
```

---

## 保存先ディレクトリ

### データ

```
datasets/cannabinoid-multi-trends/data/raw/google_trends/
```

### レポート

```
research/
├── YYYYMMDD-first-mention-timeline.md  # 言及開始時期レポート
└── YYYYMMDD-{keyword}-trend-report.md  # 個別キーワードレポート
```

---

## 関連

- **研究計画書:** `research/20261002-keyword-coverage-expansion.md`
- **既存レポート:** `research/20261002-first-mention-timeline.md`
- **上位スキル:** `research-google-trends`（Google Trends 収集）
- **データセット:** `datasets/cannabinoid-multi-trends/`
- **タクソノミー:** `metadata/taxonomy/compound-taxonomy.skos.jsonld`
