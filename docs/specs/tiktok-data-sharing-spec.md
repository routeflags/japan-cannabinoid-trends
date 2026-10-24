# TikTok データ共有仕様書

**作成日:** 2026-10-01
**改訂:** 2026-10-15（Instagram を対象外に。定点観測の廃止に合わせて TikTok のみに改訂）
**目的:** 別リポジトリで定点観測されている TikTok データを `japan-cannabinoid-trends` と共有するための仕様書
**ステータス:** DRAFT（TikTok のみ。Instagram は廃止済み = §2.1）

---

## 1. 背景

| 項目 | 内容 |
|------|------|
| データ所有リポジトリ | social-media-operations（仮称） |
| 共有先リポジトリ | japan-cannabinoid-trends |
| 対象プラットフォーム | TikTok（Instagram は 2026-10-01 に廃止 — §2.1） |
| 収集方法 | Apify Actor（定点観測） |
| 共有の目的 | CBX トレンド分析のクロスプラットフォーム対応 |

---

## 2. 共有データの定義

### 2.1 Instagram（対象外: 2026-10-01 廃止）

Instagram の定点観測は **2026-10-01 に廃止**された（カンナビノイド関連が 0 件で、
化粧品・バイクのノイズが支配的だったため）。共有仕様の対象から外す。

- 廃止前に想定していた Actor は `TxU0ZBQIHdR20dr9C`
  (patient_discovery/instagram-search-reels)、クエリは `CBX リキッド`、取得上限 maxPages=1〜3。
  投稿単位のフィールド（Reel ID / キャプション / ユーザー名 / 再生数 / 投稿日時など）を
  想定していたが、**共有も取り込みも行っていない**（`data/raw/instagram/` は存在しない）。
- 再開する場合は、投稿単位の表現の扱いを含めて本仕様を先に改訂する
  （`ISS-20261015-XID-034`、`publication/research_*.html` の X と同様の粒度規則）。

### 2.2 TikTok

| 項目 | 値 |
|------|-----|
| Actor | `jQfZ1h9FrcWcliKZX` (novi/tiktok-search-api) |
| 検索キーワード | `CBX リキッド`（または定点観測用キーワード） |
| 取得上限 | limit=20~50 |
| 地域 | `JP` |
| 収集頻度 | 週次（または定点観測スケジュールに従う） |

**出力フィールド:**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `aweme_info.aweme_id` | string | 動画ID |
| `aweme_info.desc` | string | キャプション |
| `aweme_info.statistics.play_count` | integer | 再生数 |
| `aweme_info.statistics.digg_count` | integer | いいね数 |
| `aweme_info.statistics.comment_count` | integer | コメント数 |
| `aweme_info.statistics.share_count` | integer | 共有数 |
| `author.unique_id` | string | 作者ID |
| `author.nickname` | string | 作者表示名 |
| `aweme_info.createTime` | integer | Unix timestamp |

---

## 3. データ形式

### 3.1 生データ（raw）

**保存先:**

```
datasets/cbx-social-trends/data/raw/
└── tiktok/
    └── <run-id>/
        ├── records.json
        └── run_metadata.json
```

**run-id 形式:**

```
YYYYMMDDTHHMMSSZ-tiktok-cbx-liquid
```

例: `20261001T120000Z-tiktok-cbx-liquid`

（`instagram/` 配下は存在しない。§2.1）

### 3.2 run_metadata.json スキーマ

```json
{
  "run_id": "20261001T120000Z-tiktok-cbx-liquid",
  "source": "tiktok",
  "actor_id": "TxU0ZBQIHdR20dr9C",
  "query": "CBX リキッド",
  "parameters": {
    "maxPages": 1
  },
  "collection_timestamp": "2026-10-01T12:00:00Z",
  "apify_run_id": "whiuCNcuRxmDVWjLF",
  "apify_dataset_id": "gN4fgq80j5H58dA8C",
  "raw_record_count": 6,
  "collector": "social-media-operations",
  "collector_version": "1.0"
}
```

---

## 4. 共有プロトコル

### 4.1 共有方法（選択肢）

| 方法 | 仕組み | 利点 | 欠点 |
|------|--------|------|------|
| **A. Git サブモジュール** | 別リポジトリをサブモジュールとして参照 | バージョン管理が容易 | セットアップが複雑 |
| **B. 手動エクスポート** | 定期的に CSV/JSON をエクスポートしてコピー | 簡単 | 手動作業、遅延 |
| **C. API 経由** | 共有 API を構築 | 自動化可能 | インフラ構築が必要 |
| **D. 共有ディレクトリ** | ローカル/クラウドの共有フォルダ | 簡単 | バージョン管理困難 |

### 4.2 推奨方法: B. 手動エクスポート

**理由:**
- データ量が小さい（週次数十件）
- インフラ構築不要
- AGENTS.md の raw data immutability 規則に適合

**手順:**

```
1. social-media-operations で定点観測を実行
2. 取得データを JSON でエクスポート
3. run_metadata.json を作成
4. japan-cannabinoid-trends の対象ディレクトリにコピー
5. README.md のデータソース表を更新
6. コミット
```

### 4.3 コピー先パス

```
# TikTok
japan-cannabinoid-trends/datasets/cbx-social-trends/data/raw/tiktok/<run-id>/
```

---

## 5. データ品質チェックリスト

コピー前に以下を確認:

| # | チェック項目 | 確認方法 |
|---|-------------|---------|
| 1 | CBX 関連件数 | キャプションに `CBX` を含む件数 |
| 2 | 日付範囲 | 対象期間内の投稿であるか |
| 3 | 重複 | 前回データと重複していないか |
| 4 | メタデータ | run_metadata.json が完全か |
| 5 | ファイル形式 | JSON としてパース可能か |

---

## 6. 既知の問題と対策

| 問題 | 対策 |
|------|------|
| TikTok の description 空 | API バージョン確認、別 Actor への切替検討 |
| クエリ非決定性 | 複数回収集、run-id で区別 |
| 取得上限超過 | limit で制限 |

過去に想定していた Instagram のシャドウバン対策（クエリ多様化）は、2026-10-01 の
定点観測廃止により対象外（§2.1）。

---

## 7. 運用の分担

| 項目 | 負担 |
|------|------|
| 収集の実行 | social-media-operations（データ所有者） |
| ストレージ | japan-cannabinoid-trends（共有先） |
| 人手 | 双方（エクスポート・コピー） |

---

## 8. ライセンス・再配布

| 項目 | 方針 |
|------|------|
| データのライセンス | CC-BY-4.0（推奨） |
| 再配布 | 研究目的に限り可 |
| 個人情報 | ユーザー名は保持（公開プロフィール） |
| 投稿本文 | 引用は可、全文再配布は要確認 |
| 機密情報 | なし（公開データのみ） |

---

## 9. 実装チェックリスト

### social-media-operations 側

- [ ] 定点観測スケジュールを定義
- [ ] エクスポートスクリプトを作成
- [ ] run_metadata.json 生成機能を実装
- [ ] 共有ディレクトリを設定

### japan-cannabinoid-trends 側

- [ ] `data/raw/tiktok/` ディレクトリを確認
- [ ] README.md のデータソース表を更新
- [ ] methodology.md に共有プロトコルを記載

---

## 10. スケジュール

| フェーズ | 内容 | 期日 |
|---------|------|------|
| 1 | 仕様書レビュー | 2026-10-01 |
| 2 | social-media-operations 側の実装 | 2026-10-08 |
| 3 | 初回データ共有 | 2026-10-15 |
| 4 | 定期運用開始 | 2026-10-22 |

---

## 11. 連絡先

| 役割 | リポジトリ | 担当 |
|------|-----------|------|
| データ所有者 | social-media-operations | (未定) |
| データ共有先 | japan-cannabinoid-trends | Research Data Librarian |

---

## 12. 変更履歴

| 日付 | 変更内容 |
|------|---------|
| 2026-10-01 | 初版作成 |
| 2026-10-15 | Instagram を対象外に改訂（2026-10-01 の定点観測廃止に合わせる）。
タイトル・背景・保存先・コピー先・チェックリストを TikTok のみにし、
廃止の事実は §2.1 に日付付きで残す |
