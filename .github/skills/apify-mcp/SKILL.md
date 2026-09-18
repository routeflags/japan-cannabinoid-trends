---
name: apify-mcp
description: |
  .mcp.json の apify/apify-hosted エントリと .env.d/apify.env を正しく保つスキル。「Apify MCP」「apifyつながらない」「APIFY_TOKEN」などで使う。
---

# Apify MCP 管理

`.mcp.json` の `apify` / `apify-hosted` エントリと、対応する認証ファイル `.env.d/apify.env` を正しく保つためのスキル。

## .mcp.json 定義

```json
{
  "apify": {
    "command": "/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.github/bin/run-with-env.sh",
    "args": [
      "/Users/bookair18/OS/media/06_symphony/symphony_workspaces/.env.d/apify.env",
      "/Users/bookair18/.anyenv/envs/nodenv/versions/24.13.1/bin/npx",
      "-y",
      "@apify/actors-mcp-server"
    ]
  },
  "apify-hosted": {
    "command": "/Users/bookair18/.anyenv/envs/nodenv/versions/24.13.1/bin/npx",
    "args": ["-y", "mcp-remote", "https://mcp.apify.com"]
  }
}
```

| 項目 | 値 |
|------|-----|
| ローカル | `npx @apify/actors-mcp-server`（stdio, Node v18+） |
| ホステッド | `npx mcp-remote https://mcp.apify.com`（Streamable HTTP, OAuth/Bearer） |
| envファイル | `.env.d/apify.env`（`APIFY_TOKEN`） |
| バージョン | `0.15.3`（2026-09-01確認） |
| Python補助 | なし（MCP stdioで完結） |

## 認証ファイル

### .env.d/apify.env
```
APIFY_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Optional: TOOLS=actors,docs,apify/rag-web-browser
# Optional: TELEMETRY_ENABLED=false
```
- 取得先: https://console.apify.com/settings/integrations → API Token
- パーミッション: `chmod 600 .env.d/apify.env`
- `run-with-env.sh` が `source` して `APIFY_TOKEN` を注入

### 置換コマンド
```bash
echo 'APIFY_TOKEN=apify_api_xxx...' > .env.d/apify.env
chmod 600 .env.d/apify.env
```

## 前提

- Node.js v18+（本環境 v24.13.1）
- `npx -y @apify/actors-mcp-server --help` で疎通確認
- `APIFY_TOKEN` なしでも匿名ツールは可（下記）

## ツール一覧

| ツール | カテゴリ | デフォルト | 説明 |
|--------|----------|------------|------|
| `search-actors` | actors | ✅ | Store検索 |
| `fetch-actor-details` | actors | ✅ | Actor詳細・inputSchema・README取得 |
| `call-actor` | actors | ❔ | Actor実行（`waitSecs` 0-45, 返り値はrunId+storageIds） |
| `apify/rag-web-browser` | Actor | ✅ | 汎用Web検索・取得 |
| `apify/web-fetch` | Actor | ✅ | 単一URLのJSレンダリング取得 |
| `search-apify-docs` / `fetch-apify-docs` | docs | ✅ | Apify Docs検索 |
| `get-actor-run` / `get-actor-run-list` / `get-actor-log` | runs |  | 実行ログ取得 |
| `get-dataset` / `get-dataset-items` / `get-dataset-schema` / `get-dataset-list` | storage |  | Dataset取得 |
| `get-key-value-store-*` | storage |  | KV Store取得 |
| `get-actor-output` | - | ✅ | Actor出力の完全取得（previewが省略された場合） |

### 匿名アクセス（Tokenなしで可）
`https://mcp.apify.com?tools=search-actors,fetch-actor-details,search-apify-docs,fetch-apify-docs`
Token必須: `call-actor` / storage系 / run系

## 使い方

### 疎通確認
```bash
/Users/bookair18/.anyenv/envs/nodenv/versions/24.13.1/bin/npx -y @apify/actors-mcp-server --help
# MCP経由
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | /Users/bookair18/OS/media/06_symphony/symphony_workspaces/.github/bin/run-with-env.sh .env.d/apify.env /Users/bookair18/.anyenv/envs/nodenv/versions/24.13.1/bin/npx -y @apify/actors-mcp-server 2>&1 | head -5
```

### Actor詳細 → 実行 → 結果取得（MCP stdio）
```bash
# 1. 詳細取得（inputSchema確認）
# tools/call fetch-actor-details {"actor":"TxU0ZBQIHdR20dr9C"}
# → patient_discovery/instagram-search-reels / input: {query:string, maxPages:integer}

# 2. 実行（CBXリキッド例）
# tools/call call-actor {"actor":"TxU0ZBQIHdR20dr9C","input":{"query":"CBXリキッド","maxPages":1},"waitSecs":45}
# → {runId:"whiuCNcuRxmDVWjLF", storages:{datasets:{default:{id:"gN4fgq80j5H58dA8C",itemCount:6}}}}

# 3. 結果取得
# tools/call get-dataset-items {"datasetId":"gN4fgq80j5H58dA8C","limit":6,"clean":true}
```

### API直叩き（MCP不調時のフォールバック）
```bash
source .env.d/apify.env
curl -s "https://api.apify.com/v2/datasets/gN4fgq80j5H58dA8C/items?clean=true&format=json&limit=6" -H "Authorization: Bearer $APIFY_TOKEN" | jq .
curl -s "https://api.apify.com/v2/actor-runs/whiuCNcuRxmDVWjLF" -H "Authorization: Bearer $APIFY_TOKEN" | jq '{status, stats}'
```

### 実績（2026-09-01）
- Actor `TxU0ZBQIHdR20dr9C` = `patient_discovery/instagram-search-reels`（Instagram Reels Keyword Scraper, No Login）
- Input `CBXリキッド` / `maxPages:1` → 6件（全てCBX400Fバイク関連、CBXリキッド該当0件、Instagramでは規制でリキッド系はシャドウバン）
- Cost: 起動$0.002 + 6×$0.0025 = $0.017

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `401 Unauthorized` / `Invalid token` | `APIFY_TOKEN` 未設定・誤り・失効 | https://console.apify.com/settings/integrations で再発行 → `echo 'APIFY_TOKEN=...' > .env.d/apify.env && chmod 600 ...` |
| `Invalid arguments: must have required property 'actor'` | `fetch-actor-details` に `actorId` を渡した | `{"actor":"TxU0ZBQIHdR20dr9C"}`（`actor`キー）で渡す |
| `mcp-remote: command not found` | `mcp-remote` 未インストール | `npx -y mcp-remote --help` で自動DL確認 |
| Tokenがログに平文出力された | 検証時に `cat .env.d/apify.env` した | `Rotate Token` して再設定（プライベートログなら直ちに危険ではない） |
| `CBXリキッド`で0件 | Instagram規制・キーワード曖昧（CBX400Fに引っ張られる） | `apify/rag-web-browser` でWeb検索、または `query:"CBX リキッド"` `maxPages:3` で再試行 |

## 出力先

| 種別 | パス |
|------|------|
| MCP生JSON | 標準出力（stdio） |
| Dataset JSON | `https://api.apify.com/v2/datasets/{datasetId}/items` |
| ローカル保存例 | `/tmp/cbx_dataset.json` |

## 関連

* 上位スキル: `seo-data-analysis`（Web取得の代替としてRAG Browserを利用）
* 参照MCP: `serpbear`（順位取得）、`ga4` / `google-search-console`
* ドキュメント: https://docs.apify.com/integrations/mcp / https://mcp.apify.com
