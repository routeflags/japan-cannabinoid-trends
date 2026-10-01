---
name: research-youtube-search
description: |
  研究用の YouTube 検索スキル。
  キーワード・研究ID を指定して、YouTube 動画を収集する。
---

# Research YouTube 検索スキル

研究用の YouTube データ収集スキル。**任意のキーワード・研究ID** で再利用できるよう抽象化されている。

各研究は `datasets/<study-id>/` 配下にデータを保存し、このスキルは収集・重複排除・品質チェックのみを担当する。
研究計画書（`docs/plans/` 配下）に定められたパラメータをそのまま入力として使う。

---

## トリガー

- 「YouTube の研究用データ取って」
- 「<キーワード> の YouTube 動画収集」
- 「<study-id> の YouTube 収集」
- 「YouTube で <キーワード> 調べて」

---

## 入力パラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| `keyword` | string | ✅ | — | 検索キーワード（研究対象に応じて指定） |
| `study_id` | string | ✅ | — | 研究ID。保存先 `datasets/<study_id>/data/raw/youtube/` に決定 |
| `max_videos` | integer | — | `100` | 最大取得数（Actor 上限 100） |
| `output_dir` | string | — | `datasets/<study_id>/data/raw/youtube/` | 保存先 |

> キーワードは研究ごとに異なるため固定しない。研究計画書で定めた値をそのまま使う。

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

# パラメータ設定（研究ごとに指定）
KEYWORD="${1:?keyword required}"    # 例: "CBX リキッド", "CBD リキッド"
STUDY_ID="${2:?study_id required}"  # 例: "cbx-social-trends"
MAX_VIDEOS="${3:-100}"
OUTPUT_DIR="${4:-datasets/${STUDY_ID}/data/raw/youtube}"

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
  -H "Authorization: Bearer $APIFY_TOKEN" | jq --arg keyword "$KEYWORD" --arg study "$STUDY_ID" '.data | {id, status, usageTotalUsd, startedAt, finishedAt, keyword: $keyword, study_id: $study}' \
  > "$SAVE_DIR/run_metadata.json"

COUNT_RAW=$(jq 'length' "$SAVE_DIR/records.json")
echo "========================================="
echo "研究ID: $STUDY_ID"
echo "キーワード: $KEYWORD"
echo "保存先: $SAVE_DIR"
echo "件数(重複排除前): ${COUNT_RAW}"
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

上記コマンドをスクリプトとして保存して使う場合の例（キーワード・研究IDは研究ごとに置き換える）:

```bash
# 1. キーワード + 研究ID 指定
bash research-youtube-search.sh "CBX リキッド" "cbx-social-trends"

# 2. 別キーワード + 別研究
bash research-youtube-search.sh "CBD リキッド" "cbd-social-trends"

# 3. キーワード + 研究ID + 件数指定
bash research-youtube-search.sh "カンナビノイド リキッド" "cannabinoid-social-trends" "50"
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

# 2. キーワード含有件数確認（キーワードは研究ごとに変更。
#    関連語フィルタが必要な場合は研究の定義に従ってパターンを指定する）
echo "=== キーワード含有件数 ==="
jq -r '.[].snippet.title' "$SAVE_DIR/records.json" | grep -ci "$KEYWORD" || echo "0"

# 3. チャンネル分布
echo "=== チャンネル分布 ==="
jq -r '.[].snippet.channelTitle' "$SAVE_DIR/records.json" | sort | uniq -c | sort -rn | head -10

# 4. 再生数上位
echo "=== 再生数上位10 ==="
jq -r '.[] | "\(.snippet.views) \(.snippet.title)"' "$SAVE_DIR/records.json" | sort -rn | head -10
```

---

## 保存先

研究IDごとに保存先が分かれる。

```
datasets/<study-id>/data/raw/youtube/
└── {YYYYMMDDTHHMMSSZ}-youtube-{keyword-slug}/
    ├── records_raw.json      ← 生データ（重複あり）
    ├── records.json          ← 重複排除後
    ├── records.csv           ← CSV 形式
    └── run_metadata.json     ← 実行メタデータ（keyword / study_id 付き）
```

**run-id 形式:** `YYYYMMDDTHHMMSSZ-youtube-{keyword-slug}`（keyword を小文字・ハイフン連結）
**例:** `20261001T120000Z-youtube-cbd-liquid`（キーワード `CBD リキッド` の場合）

---

## 費用

| 項目 | 単価 | 件数/回（max_videos=100 の場合） | 収集費用 |
|------|------|---------|---------|
| Actor 起動 | $0.00005 | 1 | $0.00005 |
| 取得 | $0.0005/件 | ~100 | ~$0.050 |
| **合計** | | | **~$0.050/回** |
| **月額** | | 収集回数に依存 | 収集回数 × ~$0.050 |

---

## 制約・注意

| 制約 | 対策 |
|------|------|
| ページング重複 | 必ず videoId で重複排除 |
| max_videos 上限 | 100 件で制限 |
| 検索結果の非決定性 | 複数回収集、run-id で区別 |
| 一般動画の混入 | タイトルでキーワード関連を手動フィルタ |
| キーワードの固定化 | 研究ごとに keyword / 保存先をパラメータで渡す（スキル内にハードコードしない） |

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| 関連 0 件 | クエリが一般動画に回避 | キーワードを確認、別クエリ試行 |
| 重複が多い | YouTube 検索の仕様 | records_raw.json から重複排除 |
| 401 Unauthorized | APIFY_TOKEN 無効 | `.env.d/apify.env` を確認 |
| max_videos 超過 | 上限 100 | 100 で制限 |

---

## 収集実績の記録

実行のたびに、実績（クエリ・件数・重複排除後件数・費用）は各研究のメタデータに記録する:

- `datasets/<study-id>/data/raw/youtube/{run-id}/run_metadata.json` … 実行単位の記録
- `datasets/<study-id>/metadata/runs/` … 研究全体の実行履歴

スキル内に特定研究の実績を固定で書き込まない（別キーワード・別期間での再利用を妨げないため）。

---

## 関連

- **研究計画書:** `docs/plans/` 配下（研究ごとに作成）
- **methodology:** `datasets/<study-id>/methodology.md`（研究ごとに作成）
- **上位スキル:** `apify-youtube-search`（汎用 YouTube 検索）
- **管理スキル:** `apify-mcp`（MCP 起動・認証）
