---
name: research-google-trends
description: |
  研究用の Google Trends 検索スキル。
  キーワード・地域・期間を指定して、Google Trends の検索興味度データを収集する。
---

# Research Google Trends 検索スキル

研究用の Google Trends データ収集スキル。**任意のキーワード・地域・期間** で再利用できるよう抽象化されている。

各研究は `datasets/<study-id>/` 配下にデータを保存し、このスキルは収集と品質チェックのみを担当する。
研究計画書（`docs/plans/` 配下）に定められたパラメータをそのまま入力として使う。

---

## トリガー

- 「Google Trends の研究用データ取って」
- 「<キーワード> の Google Trends 収集」
- 「<study-id> の Google Trends 収集」
- 「Google 検索トレンドデータ取得」
- 「<キーワード> を期間指定で Google Trends 検索」

---

## 前提

- OpenCode の MCP 設定に `google-trends` サーバーが登録済み（`opencode.json`）
- npm パッケージ `google-trends-mcp`（API キー不要）
- MCP サーバーはローカルで実行（trends.google.com の内部エンドポイントを使用）

---

## MCP ツール一覧

| ツール | 説明 | 使用例 |
|--------|------|--------|
| `interest_over_time` | 検索興味度の週次推移（0-100） | 過去1年の「CBX リキッド」の推移 |
| `compare_terms` | 2-5キーワードの比較 | 「CBX リキッド」vs「CBD リキッド」 |
| `related_queries` | 関連クエリ（上昇中を含む） | 「CBX」の関連検索 |
| `trending_now` | 本日のトレンド検索 | 日本のトレンド |
| `interest_by_region` | 地域別の興味度 | 日本の都道府県別 |

---

## 入力パラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| `keyword` | string | ✅ | — | 検索キーワード（研究対象に応じて指定） |
| `study_id` | string | ✅ | — | 研究ID。保存先 `datasets/<study-id>/data/raw/google_trends/` に決定 |
| `geo` | string | — | `JP` | 地域コード（JP=日本, US=米国, ""=全世界） |
| `timeframe` | string | — | `today 12-m` | 期間（`today 1-m`, `today 3-m`, `today 12-m`, `today 5-y`） |
| `comparison_keywords` | array | — | なし | 比較用キーワード（最大4つ、合計5つ） |
| `output_dir` | string | — | `datasets/<study-id>/data/raw/google_trends/` | 保存先 |

> キーワード・期間は研究ごとに異なるため固定しない。研究計画書で定めた値をそのまま使う。

---

## 実行方法

### 方法A — MCP ツール経由（OpenCode 内）

OpenCode のセッション内で MCP ツールを直接呼び出す：

```
1. interest_over_time を呼び出し
   terms=["CBX リキッド"], geo="JP", timeframe="today 12-m"

2. compare_terms を呼び出し（キーワード比較時）
   terms=["CBX リキッド", "CBD リキッド"], geo="JP", timeframe="today 12-m"

3. related_queries を呼び出し
   term="CBX", geo="JP"

4. 結果を datasets/<study-id>/data/raw/google_trends/<run-id>/ に JSON で保存
```

### 方法B — スクリプト経由（バックグラウンド収集）

```bash
# パラメータ設定（研究ごとに指定）
KEYWORD="${1:?keyword required}"        # 例: "CBX リキッド"
STUDY_ID="${2:?study_id required}"      # 例: "cbx-search-trends"
GEO="${3:-JP}"                          # 地域コード
TIMEFRAME="${4:-today 12-m}"            # 期間
OUTPUT_DIR="${5:-datasets/${STUDY_ID}/data/raw/google_trends}"

# タイムスタンプと run-id
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
RUN_ID="${TIMESTAMP}-google-trends-$(echo "$KEYWORD" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"
SAVE_DIR="${OUTPUT_DIR}/${RUN_ID}"
mkdir -p "$SAVE_DIR"

echo "========================================="
echo "研究ID: $STUDY_ID"
echo "キーワード: $KEYWORD"
echo "地域: $GEO"
echo "期間: $TIMEFRAME"
echo "保存先: $SAVE_DIR"
echo "========================================="
echo ""
echo "MCP ツール interest_over_time を使用してデータを取得し、"
echo "以下のパスに JSON で保存してください:"
echo "  $SAVE_DIR/records.json"
echo ""
echo "run_metadata.json に以下を記録:"
echo "  keyword, geo, timeframe, study_id, run_id, collection_timestamp"
```

---

## データ品質チェック

収集後、必ず以下を確認:

```bash
SAVE_DIR="<保存先パス>"
KEYWORD="<使用したキーワード>"

# 1. データ存在確認
echo "=== データ存在 ==="
ls -la "$SAVE_DIR/"

# 2. 興味度スコアの分布確認（0-100 の範囲内か）
echo "=== スコア範囲 ==="
# JSON から interest 値を抽出して確認

# 3. 期間カバレッジ確認
echo "=== 期間カバレッジ ==="
# 過去12ヶ月分のデータがあるか確認

# 4. キーワード一致確認
echo "=== キーワード ==="
# 収集したキーワードが意図したものか確認
```

---

## 保存先

研究IDごとに保存先が分かれる。

```
datasets/<study-id>/data/raw/google_trends/
└── {YYYYMMDDTHHMMSSZ}-google-trends-{keyword-slug}/
    ├── records.json          ← 収集データ（interest_over_time 結果）
    ├── comparison.json       ← 比較データ（compare_terms 結果、場合のみ）
    ├── related_queries.json  ← 関連クエリ（related_queries 結果、場合のみ）
    └── run_metadata.json     ← 実行メタデータ（keyword / geo / timeframe / study_id 付き）
```

**run-id 形式:** `YYYYMMDDTHHMMSSZ-google-trends-{keyword-slug}`（keyword を小文字・ハイフン連結）
**例:** `20261001T120000Z-google-trends-cbx-rikiddo`（キーワード `CBX リキッド` の場合）

---

## 制約・注意

| 制約 | 対策 |
|------|------|
| **低ボリュームクエリ** | 「CBX リキッド」等のニッチキーワードは 0 件や不安定な値になる可能性。比較用に「CBX」等の広いキーワードも収集 |
| **相対指数 (0-100)** | Google Trends の値は相対的。絶対検索数ではない |
| **レート制限 (429)** | 複数リクエストを短時間に連打しない。2-5分待機で回復 |
| **非公式エンドポイント** | trends.google.com の内部API使用。仕様変更の可能性あり |
| **データ非決定性** | 同一クエリでも結果が変動する場合あり。複数回収集してばらつきを記録 |
| **期間の制約** | 短い期間（1ヶ月未満）はデータが表示されない場合あり。`today 3-m` 以上推奨 |

---

## 低ボリュームクエリへの対処

「CBX リキッド」のようなニッチキーワードで Google Trends がデータを返さない場合：

| 対策 | 説明 |
|------|------|
| **キーワードを広げる** | 「CBX リキッド」→「CBX」→「CBX 大麻」と段階的に広げる |
| **期間を延長** | `today 12-m` や `today 5-y` で期間を延ばす |
| **スペースを変える** | 「CBX リキッド」（スペースあり）vs「CBXリキッド」（スペースなし） |
| **比較で相対化** | 他キーワードと比較して相対的な興味度を把握 |
| **GSC と補完** | 自社サイトの GSC データ（`cbx-search-trends/`）と組み合わせる |

---

## 他のデータソースとの関係

| データソース | 研究 ID | 関係 |
|-------------|---------|------|
| X (Twitter) | `cbx-liquid-online-trend` | ソーシャルでの言及（絶対件数） |
| Google Trends | `cbx-search-trends`（推奨） | 市場全体の検索需要（相対指数） |
| GSC | `cbx-search-trends` | 自社サイトの検索実測 |
| YouTube | `cbx-social-trends` | 動画コンテンツ |

**注意:** Google Trends の相対指数と X の絶対件数は直接比較不可。別々の指標として扱う。

---

## コスト

| 項目 | コスト |
|------|--------|
| API キー | 不要 |
| 収集コスト | **無料** |
| レート制限 | 短時間の連続リクエストのみ制限あり |

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| 0 件 / データなし | 低ボリュームクエリ | キーワードを広げる、期間を延長 |
| 429 Too Many Requests | レート制限 | 2-5分待機して再試行 |
| データが不安定 | 相対指数の特性 | 複数回収集、比較で補完 |
| MCP ツールが見つからない | OpenCode 再起動が必要 | opencode を再起動して設定を反映 |
| スコアが全て 0 | クエリが閾値未満 | 広いキーワードで再収集 |

---

## 使用例

### 例1: CBX リキッドの検索興味度推移

```
研究ID: cbx-search-trends
キーワード: "CBX リキッド"
地域: JP
期間: today 12-m

→ interest_over_time を呼び出し
→ 結果を datasets/cbx-search-trends/data/raw/google_trends/<run-id>/records.json に保存
```

### 例2: CBX リキッド vs CBD リキッド 比較

```
研究ID: cbx-search-trends
キーワード: ["CBX リキッド", "CBD リキッド"]
地域: JP
期間: today 12-m

→ compare_terms を呼び出し
→ 結果を comparison.json に保存
```

### 例3: CBX の関連クエリ調査

```
研究ID: cbx-search-trends
キーワード: "CBX"
地域: JP

→ related_queries を呼び出し
→ 結果を related_queries.json に保存
```

---

## 関連

- **研究計画書:** `docs/plans/` 配下（研究ごとに作成）
- **methodology:** `datasets/<study-id>/methodology.md`（研究ごとに作成）
- **MCP 設定:** `opencode.json` の `mcp.google-trends`
- **上位スキル:** 研究用データ収集スキル
- **MCP パッケージ:** [google-trends-mcp](https://github.com/purahmanian/google-trends-mcp)（MIT License）
