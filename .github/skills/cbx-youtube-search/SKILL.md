---
name: cbx-youtube-search
description: |
  CBX リキッド研究用の YouTube 検索スキル。
  キーワードを指定して、YouTube 動画を収集する。
  「CBXのYouTubeデータ取って」「cbx-social-trendsのYouTube収集」などで使う。
---

# CBX YouTube 検索スキル

CBX リキッド研究のための YouTube データ収集スキル。
研究計画書 `docs/plans/2026-10-01_cbx-liquid-research-plan.md` に準拠。

---

## トリガー

- 「CBX の YouTube データ取って」
- 「cbx-social-trends の YouTube 収集」
- 「YouTube で CBX リキッド調べて」
- 「CBX リキッドの動画検索」

---

## 入力パラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| `keyword` | string | ✅ | `CBX リキッド` | 検索キーワード |
| `max_videos` | integer | — | `100` | 最大取得数 |
| `output_dir` | string | — | `datasets/cbx-social-trends/data/raw/youtube/` | 保存先 |

---

## 前提

- Apify アカウントに支払い方法登録済み
- `.env.d/apify.env` に `APIFY_TOKEN=apify_api_...` が存在
- 環境変数のパス: `/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env`

---

## 実行コマンド

### 基本収集

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

# パラメータ設定
KEYWORD="${1:-CBX リキッド}"
MAX_VIDEOS="${2:-100}"
OUTPUT_DIR="${3:-datasets/cbx-social-trends/data/raw/youtube}"

# 収集実行
R=$(curl -s -X POST "https://api.apify.com/v2/acts/gJvjeCYNraSfhIaNd/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"search_term\":\"$KEYWORD\",\"max_videos\":$MAX_VIDEOS}")

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
RUN_ID=$(echo "$R" | jq -r '.data.id')
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
SAVE_RUN_ID="${TIMESTAMP}-youtube-$(echo "$KEYWORD" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"

# 保存先
SAVE_DIR="${OUTPUT_DIR}/${SAVE_RUN_ID}"
mkdir -p "$SAVE_DIR"

# データ取得
curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" > "$SAVE_DIR/records_raw.json"

# メタデータ取得
curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq --arg keyword "$KEYWORD" '.data | {id, status, usageTotalUsd, startedAt, finishedAt, keyword: $keyword}' \
  > "$SAVE_DIR/run_metadata.json"

echo "========================================="
echo "キーワード: $KEYWORD"
echo "保存先: $SAVE_DIR"
echo "Cost: $(jq -r '.usageTotalUsd' "$SAVE_DIR/run_metadata.json")"
echo "========================================="
```

### 重複排除（必須）

YouTube 検索はページングで重複を返す。**必ず重複排除する。**

```bash
SAVE_DIR="<保存先パス>"

python3 -c "
import json

with open('${SAVE_DIR}/records_raw.json') as f:
    data = json.load(f)

# videoId で重複排除
seen = set()
unique = []
for item in data:
    vid = item.get('id', {}).get('videoId')
    if vid and vid not in seen:
        seen.add(vid)
        unique.append(item)

# 保存
with open('${SAVE_DIR}/records.json', 'w') as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)

print(f'総件数: {len(data)}')
print(f'重複排除後: {len(unique)}')
"

# CSV 出力
python3 -c "
import json, csv

with open('${SAVE_DIR}/records.json') as f:
    data = json.load(f)

rows = []
for r in data:
    sn = r.get('snippet', {})
    rows.append({
        'videoId': r.get('id', {}).get('videoId', ''),
        'title': sn.get('title', ''),
        'channel': sn.get('channelTitle', ''),
        'views': sn.get('views', 0),
        'duration': sn.get('duration', ''),
        'timestamp': sn.get('timestamp', ''),
        'url': f\"https://youtube.com/watch?v={r.get('id', {}).get('videoId', '')}\"
    })

with open('${SAVE_DIR}/records.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f'CSV保存完了: {len(rows)}件')
"
```

### 使用例

```bash
# 1. デフォルト（CBX リキッド）
bash cbx-youtube-search.sh

# 2. キーワード指定
bash cbx-youtube-search.sh "CBD リキッド"

# 3. キーワード + 件数指定
bash cbx-youtube-search.sh "カンナビノイド リキッド" "50"

# 4. キーワード + 件数 + 保存先
bash cbx-youtube-search.sh "CBX リキッド" "100" "datasets/cbx-social-trends/data/raw/youtube"
```

---

## データ品質チェック

収集後、必ず以下を確認:

```bash
SAVE_DIR="<保存先パス>"
KEYWORD="<使用したキーワード>"

# 1. 重複排除後の件数確認
echo "=== ユニーク件数 ==="
jq 'length' "$SAVE_DIR/records.json"

# 2. CBX 関連件数確認
echo "=== キーワード関連件数 ==="
jq -r '.[].snippet.title' "$SAVE_DIR/records.json" | grep -ci "$KEYWORD\|cbx\|cbd\|カンナビノイド\|hemp\|大麻\|リキッド\|vape" || echo "0"

# 3. チャンネル分布
echo "=== チャンネル分布 ==="
jq -r '.[].snippet.channelTitle' "$SAVE_DIR/records.json" | sort | uniq -c | sort -rn | head -10

# 4. 再生数上位
echo "=== 再生数上位10 ==="
jq -r '.[] | "\(.snippet.views) \(.snippet.title)"' "$SAVE_DIR/records.json" | sort -rn | head -10
```

---

## 保存先

```
datasets/cbx-social-trends/data/raw/youtube/
└── {YYYYMMDDTHHMMSSZ}-youtube-{keyword}/
    ├── records_raw.json      ← 生データ（重複あり）
    ├── records.json          ← 重複排除後
    ├── records.csv           ← CSV 形式
    └── run_metadata.json     ← 実行メタデータ
```

**run-id 形式:** `YYYYMMDDTHHMMSSZ-youtube-{keyword}`
**例:** `20261001T120000Z-youtube-cbx-rikiddo`

---

## 費用

| 項目 | 単価 | 件数/回 | 収集費用 |
|------|------|---------|---------|
| Actor 起動 | $0.00005 | 1 | $0.00005 |
| 取得 | $0.0005/件 | ~100 | $0.050 |
| **合計** | | | **~$0.050/回** |
| **月額** | | 1回 | **~$0.050** |

---

## 制約・注意

| 制約 | 対策 |
|------|------|
| ページング重複 | 必ず videoId で重複排除 |
| max_videos 上限 | 100 件で制限 |
| 検索結果の非決定性 | 複数回収集、run-id で区別 |
| 一般動画の混入 | タイトルでキーワード関連を手動フィルタ |

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| 関連 0 件 | クエリが一般動画に回避 | キーワードを確認、別クエリ試行 |
| 重複が多い | YouTube 検索の仕様 | records_raw.json から重複排除 |
| 401 Unauthorized | APIFY_TOKEN 無効 | `.env.d/apify.env` を確認 |
| max_videos 超過 | 上限 100 | 100 で制限 |

---

## 実績（2026-10-01）

| 項目 | 値 |
|------|-----|
| クエリ | `CBX リキッド` |
| max_videos | 100 |
| 生レコード | 100 件（重複あり） |
| 重複排除後 | **26 件** |
| CBX 関連 | 26 件 (100%) |
| 費用 | $0.0402 |
| 最大再生数 | 61,241 (CBDチャンネルWEEDMAN) |

---

## 関連

- **研究計画書:** `docs/plans/2026-10-01_cbx-liquid-research-plan.md`
- **methodology:** `datasets/cbx-social-trends/methodology.md`
- **上位スキル:** `apify-youtube-search`（汎用 YouTube 検索）
- **管理スキル:** `apify-mcp`（MCP 起動・認証）
