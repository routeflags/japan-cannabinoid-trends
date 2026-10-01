---
name: update-cbx-guide
description: |
  CBX ガイドページ（guide_cbx_rewrite.html）の月次更新スキル。
  データ収集から HTML 更新、品質チェック、コミットまでを一括で実行する。
---

# CBX ガイドページ更新スキル

CBX ガイドページ `publication/guide_cbx_rewrite.html` の月次更新スキル。

データ収集 → HTML 更新 → 品質チェック → コミット の流れを一括で実行する。

---

## トリガー

- 「CBX ガイドを更新」
- 「guide_cbx を更新」
- 「CBX ガイドの月次更新」
- 「guide_cbx_rewrite.html を更新」

---

## 前提

- OpenCode の MCP 設定に `google-trends` サーバーが登録済み
- Apify アカウント（X / YouTube 収集用）
- `.env.d/apify.env` に `APIFY_TOKEN` が存在

---

## 更新フロー

```text
Step 1: Google Trends 収集
        ↓
Step 2: YouTube 収集
        ↓
Step 3: X (Twitter) 収集（必要に応じて）
        ↓
Step 4: HTML 更新
        ↓
Step 5: 品質チェック
        ↓
Step 6: コミット・プッシュ
```

---

## Step 1: Google Trends 収集

### 収集パラメータ

| パラメータ | 値 |
|-----------|-----|
| キーワード | `CBX`, `H4CBH`, `HHBD`, `CBX リキッド` |
| 地域 | `JP` |
| 期間 | `today 12-m` |
| 保存先 | `datasets/cbx-search-trends/data/raw/google_trends/` |

### 実行方法

```
1. interest_over_time を呼び出し
   terms=["CBX"], geo="JP", timeframe="today 12-m"

2. interest_over_time を呼び出し
   terms=["H4CBH"], geo="JP", timeframe="today 12-m"

3. interest_over_time を呼び出し
   terms=["HHBD"], geo="JP", timeframe="today 12-m"

4. interest_over_time を呼び出し
   terms=["CBX リキッド"], geo="JP", timeframe="today 12-m"

5. compare_terms を呼び出し
   terms=["CBX", "H4CBH", "HHBD", "CBX リキッド"], geo="JP", timeframe="today 12-m"
```

### 保存先

```
datasets/cbx-search-trends/data/raw/google_trends/
└── {YYYYMMDDTHHMMSSZ}-google-trends-{keyword-slug}/
    ├── records_cbx.json
    ├── records_h4cbh.json
    ├── records_hhbd.json
    ├── records_cbx_rikiddo.json
    ├── comparison.json
    └── run_metadata.json
```

---

## Step 2: YouTube 収集

### 収集パラメータ

| パラメータ | 値 |
|-----------|-----|
| クエリ | `CBX リキッド` |
| max_videos | `100` |
| Actor | `gJvjeCYNraSfhIaNd` |
| 保存先 | `datasets/cbx-social-trends/data/raw/youtube/` |

### 実行コマンド

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

KEYWORD="CBX リキッド"
MAX_VIDEOS=100
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
SAVE_RUN_ID="${TIMESTAMP}-youtube-$(echo "$KEYWORD" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"
SAVE_DIR="datasets/cbx-social-trends/data/raw/youtube/${SAVE_RUN_ID}"
mkdir -p "$SAVE_DIR"

R=$(curl -s -X POST "https://api.apify.com/v2/acts/gJvjeCYNraSfhIaNd/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"search_term\":\"$KEYWORD\",\"max_videos\":$MAX_VIDEOS}")

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
RUN_ID=$(echo "$R" | jq -r '.data.id')

curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" > "$SAVE_DIR/records_raw.json"

curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq --arg keyword "$KEYWORD" '.data | {id, status, usageTotalUsd, startedAt, finishedAt, keyword: $keyword}' \
  > "$SAVE_DIR/run_metadata.json"

# 重複排除
python3 -c "
import json
with open('${SAVE_DIR}/records_raw.json') as f:
    data = json.load(f)
seen = set()
unique = []
for item in data:
    vid = item.get('id', {}).get('videoId')
    if vid and vid not in seen:
        seen.add(vid)
        unique.append(item)
with open('${SAVE_DIR}/records.json', 'w') as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)
print(f'総件数: {len(data)}')
print(f'重複排除後: {len(unique)}')
"
```

---

## Step 3: X (Twitter) 収集（必要に応じて）

### 収集パラメータ

| パラメータ | 値 |
|-----------|-----|
| クエリ | `CBX リキッド since:{前月1日} until:{当月1日}` |
| section | `latest` |
| maxPages | `2` |
| Actor | `cPYLH3QT9GyzKhB4S` |
| 保存先 | `datasets/cbx-liquid-online-trend/data/raw/x/` |

### 実行コマンド

```bash
source /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env

KEYWORD="CBX リキッド"
START_DATE="$(date -u -d '1 month ago' +%Y-%m-%d 2>/dev/null || date -u -v-1m +%Y-%m-%d)"
END_DATE="$(date -u +%Y-%m-%d)"
QUERY="${KEYWORD} since:${START_DATE} until:${END_DATE}"
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
SAVE_RUN_ID="${TIMESTAMP}-x-$(echo "$KEYWORD" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"
SAVE_DIR="datasets/cbx-liquid-online-trend/data/raw/x/${SAVE_RUN_ID}"
mkdir -p "$SAVE_DIR"

R=$(curl -s -X POST "https://api.apify.com/v2/acts/cPYLH3QT9GyzKhB4S/runs?waitForFinish=60" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"$QUERY\",\"section\":\"latest\",\"maxPages\":2}")

DS=$(echo "$R" | jq -r '.data.defaultDatasetId')
RUN_ID=$(echo "$R" | jq -r '.data.id')

curl -s "https://api.apify.com/v2/datasets/$DS/items?clean=true&format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" > "$SAVE_DIR/records.json"

curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID" \
  -H "Authorization: Bearer $APIFY_TOKEN" | jq --arg query "$QUERY" '.data | {id, status, usageTotalUsd, query: $query}' \
  > "$SAVE_DIR/run_metadata.json"
```

---

## Step 4: HTML 更新

### 更新対象ファイル

```
publication/guide_cbx_rewrite.html
```

### 更新箇所

| # | セクション | ID | 更新内容 |
|---|-----------|-----|---------|
| 1 | 構造化データ | — | `dateModified` を本日に |
| 2 | meta description | — | 必要に応じて更新 |
| 3 | メソドロジー | — | データソース・取得期間を更新 |
| 4 | Google Trends 検索需要 | `data-search` | 最新の興味度スコアに更新 |
| 5 | GSC 参考データ | `data-gsc-ref` | 必要に応じて更新 |
| 6 | Google Trends 比較 | `data-comparison` | キーワード比較を更新 |
| 7 | COA データ | `data-coa` | 変更なければそのまま |
| 8 | X トレンド | `data-x` | 新データを追加 |
| 9 | YouTube トレンド | `data-youtube` | 最新の動画データに更新 |
| 10 | タイムライン | `timeline` | 新イベントがあれば追加 |
| 11 | 引用 | `citation` | バージョン番号を更新 |

### HTML 更新テンプレート

#### 構造化データ

```html
"dateModified": "YYYY-MM-DD",
```

#### メソドロジー

```html
<p class="data-note"><strong>最終更新:</strong> YYYY-MM-DD。{変更内容の概要}。</p>
```

#### Google Trends 検索需要（データ反映用）

```html
<h3>キーワード別サマリー</h3>
<table class="data-table">
  <thead>
    <tr>
      <th>キーワード</th>
      <th class="num">単独平均</th>
      <th class="num">比較平均</th>
      <th class="num">ピーク</th>
      <th>ピーク週</th>
      <th>データ開始</th>
    </tr>
  </thead>
  <tbody>
    <!-- Google Trends データを反映 -->
  </tbody>
</table>
```

#### YouTube 動画テーブル

```html
<table class="data-table">
  <thead>
    <tr>
      <th>動画タイトル</th>
      <th>チャンネル</th>
      <th class="num">再生数</th>
    </tr>
  </thead>
  <tbody>
    <!-- 再生数上位10件を反映 -->
  </tbody>
</table>
```

### 更新ルール

| ルール | 内容 |
|--------|------|
| データ区分 | Google Trends / X / YouTube / COA = 一次データ、GSC / OpenSEO = 参考データ |
| 日付形式 | YYYY-MM-DD |
| バージョン | 1件の更新ごとに +0.1（例: 1.5 → 1.6） |
| 所見 | 事実と意見を分離（「〜という所見」/「〜という可能性） |
| 削除禁止 | 過去データは消さず、最新データを追加 |

---

## Step 5: 品質チェック

### チェックリスト

```bash
# 1. dateModified の確認
grep "dateModified" publication/guide_cbx_rewrite.html

# 2. バージョンの確認
grep "Version 1\." publication/guide_cbx_rewrite.html

# 3. Google Trends 提及回数
grep -c "Google Trends" publication/guide_cbx_rewrite.html

# 4. YouTube データの確認
grep -c "26件\|YouTube" publication/guide_cbx_rewrite.html

# 5. HTML 構造の確認（タグの対応）
python3 -c "
from html.parser import HTMLParser
class Checker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
    def handle_starttag(self, tag, attrs):
        if tag not in ['br', 'hr', 'img', 'meta', 'link', 'input']:
            self.stack.append(tag)
    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f'Mismatched: {tag}')
with open('publication/guide_cbx_rewrite.html') as f:
    checker = Checker()
    checker.feed(f.read())
    if checker.errors:
        print('Errors:', checker.errors[:5])
    else:
        print('HTML structure OK')
"
```

### 品質基準

| 項目 | 基準 |
|------|------|
| dateModified | 本日の日付 |
| バージョン | 前回から +0.1 |
| Google Trends | 最新データが反映されている |
| YouTube | 最新の収集データが反映されている |
| HTML 構造 | タグの対応が取れている |
| 事実/意見 | 区分が明確 |

---

## Step 6: コミット・プッシュ

### コミットメッセージテンプレート

```
Update guide_cbx_rewrite.html (YYYY-MM)

- Google Trends: {サマリー}
- YouTube: {件数}件 ({CBX関連率})
- X: {件数}件 (期間)
- dateModified: YYYY-MM-DD
- Version: X.Y
```

### 実行コマンド

```bash
cd /Users/bookair18/OS/home/Codes/github.com/routeflags/japan-cannabinoid-trends

git add publication/ \
  datasets/cbx-search-trends/ \
  datasets/cbx-social-trends/ \
  datasets/cbx-liquid-online-trend/

git commit -m "Update guide_cbx_rewrite.html (YYYY-MM)

- Google Trends: {サマリー}
- YouTube: {件数}件
- dateModified: YYYY-MM-DD
- Version: X.Y"

git push
```

---

## 使用例

### 例: 2026年11月分の更新

```
1. Google Trends 収集（CBX / H4CBH / HHBD / CBX リキッド）
2. YouTube 収集（CBX リキッド, 100件）
3. X 収集（2026-10-01 ～ 2026-11-01）
4. HTML 更新:
   - dateModified: 2026-11-01
   - Version: 1.6
   - Google Trends データを最新に
   - YouTube データを最新に
5. 品質チェック実行
6. コミット・プッシュ
```

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| Google Trends 0 件 | 低ボリュームクエリ | キーワードを広げる、期間を延長 |
| Google Trends 429 | レート制限 | 2-5分待機して再試行 |
| YouTube 0 件 CBX 関連 | クエリが一般語に回避 | `CBX リキッド` にクエリ変更 |
| X 0 件 | シャドウバン | 時間を置いて再試行 |
| HTML 構造エラー | タグの対応ミス | Python で検証して修正 |

---

## 関連ファイル

| ファイル | 役割 |
|---------|------|
| `publication/guide_cbx_rewrite.html` | 更新対象の HTML |
| `publication/README.md` | データソース一覧 |
| `datasets/cbx-search-trends/` | Google Trends / GSC データ |
| `datasets/cbx-social-trends/` | YouTube / X データ |
| `datasets/cbx-liquid-online-trend/` | X 週次データ |

---

## コスト目安

| 項目 | 費用 |
|------|------|
| Google Trends | **無料** |
| YouTube (100件) | ~$0.05 |
| X (40件程度) | ~$0.10 |
| **合計** | **~$0.15/回** |
