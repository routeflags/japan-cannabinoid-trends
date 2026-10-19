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

- **netloom v0.5.4+**（`netloom google-trends …`。ピン留めした `google-trends-mcp@0.1.1` の 5 ツールを全部呼べる）
- Node / `npx`（netloom が `google-trends-mcp` を npx で起動する。API キー不要）
- OpenCode の MCP 登録（`opencode.json` の `mcp.google-trends`）は**任意**。netloom 経由なら不要
- MCP サーバーはローカルで起動し、trends.google.com の内部エンドポイントを使用する

---

## ツール一覧（netloom コマンド）

| netloom コマンド | 元 MCP ツール | 説明 | 使用例 |
|---|---|---|---|
| `google-trends interest-over-time` | `interest_over_time` | 検索興味度の推移（0-100） | 過去1年の「CBX リキッド」の推移 |
| `google-trends compare-terms` | `compare_terms` | 2-5キーワードの比較 | 「CBX リキッド」vs「CBD リキッド」 |
| `google-trends related-queries` | `related_queries` | 関連クエリ（top / rising） | 「CBX」の関連検索 |
| `google-trends trending-now` | `trending_now` | 本日のトレンド検索（geo のみ） | 日本のトレンド |
| `google-trends interest-by-region` | `interest_by_region` | 地域別の興味度（provider 上位 30 件） | 日本の都道府県別 |

- 各 **1 コマンド = 1 MCP 往復**。`--format` は `json`（既定）/ `text` / `verbatim`。**`csv` は無い**（exit 2）
- **バケット粒度は timeframe で違う**: `today 1-m` / `today 3-m` は日次、`today 12-m` / `today 5-y` は週次・日曜起点（実測は netloom skill の GT 節）
- 空の答え（関連クエリ 0 件など）は空配列で **exit 0**（失敗ではない）

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

### 方法A — netloom（推奨）

```bash
# 興味度の推移（1語）
netloom google-trends interest-over-time --keyword "CBX リキッド" --geo JP --timeframe "today 12-m" \
  --format json --out /tmp/records.json

# 比較（2-5語）
netloom google-trends compare-terms --terms "CBX リキッド,CBD リキッド" --geo JP --timeframe "today 12-m"

# 関連クエリ（top / rising）
netloom google-trends related-queries --term "CBX" --geo JP --timeframe "today 12-m"

# 本日のトレンド（geo だけ。term / timeframe は取らない）
netloom google-trends trending-now --geo JP

# 地域別（provider 上位 30 件）
netloom google-trends interest-by-region --term "CBX" --geo JP --timeframe "today 12-m"
```

- 往復は cassette に残る（`.cassettes/` のみ・コミットしない）。`--replay` でオフライン再現できる
- `--out FILE` で応答を保存できる（省略時は stdout）

### 方法B — 収集結果を raw run として保存する場合

netloom の応答は**独自の envelope**（`{source, tool, geo, timeframe, terms:[…]}`）で、repository pipeline が読む MCP verbatim 形状（`src/collection/adapters/google_trends/adapter.py`）とは異なる。pipeline 用の run は従来どおり `make collect … --live`（collector: `google-trends-mcp`）で作り、この手順は手動・探索的な収集に使う。

これは netloom 非対応という意味ではない。**意図的な選択**である: (a) adapter は `data` 配列と `content`（MCP tool result）の 2 形状だけを契約として受ける、(b) production の収集経路は CI（`.venv` + pytest）に閉じており、netloom バイナリを配備していない、(c) raw run は verbatim の MCP payload・導出系列・境界検証を既に保存している。transport を差し替える場合は、別 collector（例 `netloom-google-trends`）として registry に載せ、境界検証を再実行した上で owner 判断とする。

```bash
# パラメータ設定（研究ごとに指定）
KEYWORD="${1:?keyword required}"        # 例: "CBX リキッド"
STUDY_ID="${2:?study_id required}"      # 例: "cbx-search-trends"
GEO="${3:-JP}"
TIMEFRAME="${4:-today 12-m}"
OUTPUT_DIR="${5:-datasets/${STUDY_ID}/data/raw/google_trends}"

TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
RUN_ID="${TIMESTAMP}-google-trends-$(echo "$KEYWORD" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"
SAVE_DIR="${OUTPUT_DIR}/${RUN_ID}"
mkdir -p "$SAVE_DIR"

netloom google-trends interest-over-time \
  --keyword "$KEYWORD" --geo "$GEO" --timeframe "$TIMEFRAME" \
  --format json --out "$SAVE_DIR/records.json"

# run_metadata.json には最低限を記録する（response_shape を必ず入れる）:
#   keyword, geo, timeframe, study_id, run_id, collection_timestamp,
#   response_shape: "netloom-envelope-v1"
# datasets/**/data/raw/google_trends 配下の run は collection-run-v1 の対象で、
# `make audit-new-runs` が現行契約を検査する。契約を満たさない run を置くと監査で落ちる。
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
    ├── records.json          ← 収集データ（interest-over-time。netloom envelope v1）
    ├── comparison.json       ← 比較データ（compare-terms 結果、場合のみ）
    ├── related_queries.json  ← 関連クエリ（related-queries 結果、場合のみ）
    ├── trending_now.json     ← 本日のトレンド（trending-now 結果、場合のみ）
    ├── interest_by_region.json ← 地域別（interest-by-region 結果、場合のみ）
    └── run_metadata.json     ← 実行メタデータ（keyword / geo / timeframe / study_id / response_shape 付き）
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
| MCP ツールが見つからない（netloom 経由） | npx / Node が無い、またはサーバー起動失敗 | `npx --version` を確認し、`netloom google-trends …` の stderr と cassette を読む |
| `--format csv` で exit 2 | GT の related-queries / trending-now / interest-by-region は csv 非対応 | `json` / `text` / `verbatim` を使う |
| スコアが全て 0 | クエリが閾値未満 | 広いキーワードで再収集 |

---

## 使用例

### 例1: CBX リキッドの検索興味度推移

```
研究ID: cbx-search-trends
キーワード: "CBX リキッド"
地域: JP
期間: today 12-m

→ `netloom google-trends interest-over-time` を実行
→ 結果を datasets/cbx-search-trends/data/raw/google_trends/<run-id>/records.json に保存
```

### 例2: CBX リキッド vs CBD リキッド 比較

```
研究ID: cbx-search-trends
キーワード: ["CBX リキッド", "CBD リキッド"]
地域: JP
期間: today 12-m

→ `netloom google-trends compare-terms` を実行
→ 結果を comparison.json に保存
```

### 例3: CBX の関連クエリ調査

```
研究ID: cbx-search-trends
キーワード: "CBX"
地域: JP

→ `netloom google-trends related-queries` を実行
→ 結果を related_queries.json に保存
```

---

## 関連

- **研究計画書:** `docs/plans/` 配下（研究ごとに作成）
- **methodology:** `datasets/<study-id>/methodology.md`（研究ごとに作成）
- **実行ツール:** `.github/skills/netloom/SKILL.md`（`netloom google-trends` の正本）
- **上位スキル:** 研究用データ収集スキル
- **MCP パッケージ:** [google-trends-mcp](https://github.com/purahmanian/google-trends-mcp)（MIT License。netloom が npx で起動）
