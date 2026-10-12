# Collector Inventory（収集手段台帳）

**版:** 1.0.0（2026-10-13）
**目的:** G1 §18 Phase 1（Inventory）の結果として、リポジトリ内で**実在確認
できた収集手段**と capability の検証状態を記録する。レジストリ
（`config/collectors.json`）の証拠台帳であり、推測は書かない。

---

## 1. 登録済み collector（2026-10-13 監査）

| collector_id | source | 手段 | 状態 | capability | 証拠 |
|---|---|---|---|---|---|
| `google-trends-mcp` | google-trends | MCP（npm `google-trends-mcp` v0.1.1、API キー不要） | **active** | `geo_filter`=supported, `relative_date_range`=supported, 他 unknown | `datasets/**/google_trends/**/run_metadata.json` 29 件（mcp_server=mcp_version=0.1.1、geo=JP、today 12-m / 5-y の実使用） / `.github/skills/research-google-trends/SKILL.md` |
| `x-apify-twitter-search` | x | Apify `cPYLH3QT9GyzKhB4S`（patient_discovery/twitter-search） | unverified | 全 unknown | `.github/skills/apify-x-search/SKILL.md` / `src/collection/x/apify-x-search.md` / `docs/provenance.md`（2026-08 収集 147 件） / `datasets/cbx-social-trends/analysis/x-data-collection-plan.md` |
| `youtube-apify-scraper` | youtube | Apify `h7sDV53CddomktSi5`（streamers/youtube-scraper） | unverified | 全 unknown | `.github/skills/apify-youtube-scraper/SKILL.md` / `datasets/cbx-social-trends/data/processed/youtube_filtered_202607/` |
| `youtube-apify-search` | youtube | Apify `gJvjeCYNraSfhIaNd`（danek/youtube-search） | unverified | 全 unknown | `.github/skills/apify-youtube-search/SKILL.md` / `scripts/collect-youtube-japanese-keywords.sh` |
| `tiktok-apify-search` | tiktok | Apify `jQfZ1h9FrcWcliKZX`（novi/tiktok-search-api） | unverified | 全 unknown | `src/collection/tiktok/fetch_tiktok.sh` / `.github/skills/apify-tiktok-search/SKILL.md` |
| `instagram-apify-search` | instagram | Apify `TxU0ZBQIHdR20dr9C`（patient_discovery/instagram-search-reels） | unverified | 全 unknown | `src/collection/instagram/fetch_instagram.sh` / `.github/skills/apify-instagram-search/SKILL.md` |

### 判定基準（この監査で採用）

- `supported` の根拠は「リポジトリ内の**実運行記録**（run_metadata / 保存された
  レスポンス）で使用が確認できること」に限定した。skill 文書や計画書の記述
  だけでは `supported` にしない（未確認は `unknown` のまま）。
- `google-trends-mcp` を `active` としたのは、29 件の機械記録で version・geo・
  timeframe の実使用が確認できるため。他の collector は収集結果の実体が
  リポジトリ内にない（`projects/automation/` 等のリポジトリ外）ため、
  **動作検証は未実施 → unverified**。
- 昇格条件（提案）: `apify-actor-validation` skill の Phase 1〜3 相当の検証
  （既存データによる機能確認 + capability の実測）を行い、本台帳と registry の
  `capabilities` / `verified_at` / `evidence` を同時に更新する。

---

## 2. source として登録済み・collector 未登録

| source_id | 状況 |
|---|---|
| `google-search-console` | `datasets/cbx-search-trends/README.md` に GSC データ取得済み（2026-07 月次、200 クエリ）の記載があるが、**収集手段（コード・スクリプト）がリポジトリ内に存在しない**。新規収集は Gate が fail closed で停止する（`GATE_NO_COLLECTOR_FOR_SOURCE`） |

## 3. 登録していない source

| source | 理由 |
|---|---|
| analytics / ecommerce / web | `project.json` で `planned`。収集手段・データの実在確認なし |
| linkedin 等その他 | リポジトリ内に痕跡なし |

登録する場合は、まず収集手段の実装（adapter）と capability 検証を追加する。

---

## 4. 秘密情報の扱い

本台帳には API トークン・Actor の認証情報を書かない（`external_id` は公開
識別子のみ）。認証は各実行環境の `.env.d/` 等で管理し、リポジトリへ保存しない。
