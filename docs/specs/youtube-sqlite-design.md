# YouTube データ格納用 SQLite 設計書

## 1. 概要

YouTube データ収集の冪等性検証と重複管理を行うための SQLite データベース設計。

---

## 2. 設計方針

| 方針 | 内容 |
|------|------|
| **Raw データ不変** | 収集した生データを変更しない |
| **Run 単位管理** | 各 API 実行を独立して記録 |
| **Video 単位一意性** | videoId で重複を排除 |
| **検索結果の完全性** | Run と Video の関係を保持 |

---

## 3. テーブル定義

### 3.1 runs（収集実行）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| run_id | TEXT | PK | 実行 ID（Apify Run ID） |
| search_term | TEXT | NOT NULL | 検索クエリ |
| max_videos | INTEGER | NOT NULL | リクエスト上限 |
| apify_dataset_id | TEXT | — | Apify データセット ID |
| collection_timestamp | TEXT | NOT NULL | 収集日時（ISO 8601） |
| record_count | INTEGER | — | 取得件数（Raw） |
| unique_count | INTEGER | — | ユニーク videoId 数 |
| collector | TEXT | — | 収集方法 |
| collector_version | TEXT | — | Actor バージョン |

```sql
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    search_term TEXT NOT NULL,
    max_videos INTEGER NOT NULL,
    apify_dataset_id TEXT,
    collection_timestamp TEXT NOT NULL,
    record_count INTEGER,
    unique_count INTEGER,
    collector TEXT DEFAULT 'apify',
    collector_version TEXT
);
```

---

### 3.2 videos（動画マスタ）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| video_id | TEXT | PK | YouTube 動画 ID |
| title | TEXT | — | 動画タイトル |
| channel | TEXT | — | チャンネル名 |
| views | INTEGER | — | 再生数 |
| duration | INTEGER | — | 長さ（秒） |
| published_at | TEXT | — | 公開日時（ISO 8601） |
| first_seen_run | TEXT | FK | 初回収集 Run ID |
| first_seen_at | TEXT | NOT NULL | 初回収集日時 |

```sql
CREATE TABLE videos (
    video_id TEXT PRIMARY KEY,
    title TEXT,
    channel TEXT,
    views INTEGER,
    duration INTEGER,
    published_at TEXT,
    first_seen_run TEXT REFERENCES runs(run_id),
    first_seen_at TEXT NOT NULL
);
```

---

### 3.3 run_videos（Run と Video の関係）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| run_id | TEXT | FK | 実行 ID |
| video_id | TEXT | FK | 動画 ID |
| position | INTEGER | — | 検索結果内の順位（1始まり） |
| is_duplicate | INTEGER | DEFAULT 0 | 同一 Run 内での重複フラグ |

```sql
CREATE TABLE run_videos (
    run_id TEXT REFERENCES runs(run_id),
    video_id TEXT REFERENCES videos(video_id),
    position INTEGER,
    is_duplicate INTEGER DEFAULT 0,
    PRIMARY KEY (run_id, video_id)
);
```

---

### 3.4 consistency_metrics（一致率メトリクス）

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| run_id | TEXT | PK | 実行 ID |
| run_number | INTEGER | — | 実行順序（1始まり） |
| unique_count | INTEGER | — | 当該 Run のユニーク ID 数 |
| already_collected | INTEGER | — | 累積と重複した ID 数 |
| new_videos | INTEGER | — | 新規 ID 数 |
| consistency_rate | REAL | — | 一致率（already_collected / unique_count） |
| cumulative_count | INTEGER | — | 累積ユニーク ID 数 |

```sql
CREATE TABLE consistency_metrics (
    run_id TEXT PRIMARY KEY REFERENCES runs(run_id),
    run_number INTEGER,
    unique_count INTEGER,
    already_collected INTEGER,
    new_videos INTEGER,
    consistency_rate REAL,
    cumulative_count INTEGER
);
```

---

## 4. インデックス

```sql
-- 検索クエリで絞り込み
CREATE INDEX idx_runs_search_term ON runs(search_term);
CREATE INDEX idx_runs_timestamp ON runs(collection_timestamp);

-- 動画の検索
CREATE INDEX idx_videos_published_at ON videos(published_at);
CREATE INDEX idx_videos_channel ON videos(channel);

-- Run と Video の関係
CREATE INDEX idx_run_videos_run ON run_videos(run_id);
CREATE INDEX idx_run_videos_video ON run_videos(video_id);
```

---

## 5. ビュー

### 5.1 v_run_summary（Run サマリー）

```sql
CREATE VIEW v_run_summary AS
SELECT 
    r.run_id,
    r.search_term,
    r.collection_timestamp,
    r.max_videos,
    r.record_count,
    r.unique_count,
    COUNT(rv.video_id) as actual_unique,
    ROUND(COUNT(rv.video_id) * 100.0 / r.max_videos, 1) as fill_rate
FROM runs r
LEFT JOIN run_videos rv ON r.run_id = rv.run_id
GROUP BY r.run_id;
```

### 5.2 v_consistency_history（一致率履歴）

```sql
CREATE VIEW v_consistency_history AS
SELECT 
    run_number,
    search_term,
    collection_timestamp,
    unique_count,
    already_collected,
    new_videos,
    ROUND(consistency_rate * 100, 1) as consistency_pct,
    cumulative_count
FROM consistency_metrics cm
JOIN runs r ON cm.run_id = r.run_id
ORDER BY run_number;
```

### 5.3 v_video_appearance（動画の出現履歴）

```sql
CREATE VIEW v_video_appearance AS
SELECT 
    v.video_id,
    v.title,
    v.channel,
    v.published_at,
    COUNT(rv.run_id) as appearance_count,
    MIN(r.collection_timestamp) as first_seen,
    MAX(r.collection_timestamp) as last_seen
FROM videos v
JOIN run_videos rv ON v.video_id = rv.video_id
JOIN runs r ON rv.run_id = r.run_id
GROUP BY v.video_id
ORDER BY appearance_count DESC;
```

---

## 6. 一致率計算クエリ

### 6.1 Run 間の一致率を計算

```sql
-- Run N の一致率を計算
WITH cumulative AS (
    SELECT DISTINCT video_id
    FROM run_videos
    WHERE run_id IN (
        SELECT run_id 
        FROM consistency_metrics 
        WHERE run_number < :target_run_number
    )
),
current_run AS (
    SELECT DISTINCT video_id
    FROM run_videos
    WHERE run_id = :target_run_id
)
SELECT 
    COUNT(*) as unique_count,
    SUM(CASE WHEN c.video_id IN (SELECT video_id FROM cumulative) THEN 1 ELSE 0 END) as already_collected,
    SUM(CASE WHEN c.video_id NOT IN (SELECT video_id FROM cumulative) THEN 1 ELSE 0 END) as new_videos
FROM current_run c;
```

---

## 7. データフロー

```
Step 1: API 実行
        ↓
Step 2: runs テーブルに INSERT
        ↓
Step 3: videos テーブルに INSERT OR IGNORE
        ↓
Step 4: run_videos テーブルに INSERT
        ↓
Step 5: 一致率を計算
        ↓
Step 6: consistency_metrics テーブルに INSERT
```

---

## 8. 使用例

### 8.1 データベース初期化

```bash
sqlite3 youtube.db < schema.sql
```

### 8.2 Run の記録

```sql
-- Run テーブルに追加
INSERT INTO runs (run_id, search_term, max_videos, collection_timestamp, record_count, unique_count)
VALUES ('run_001', 'CBD リキッド', 100, '2026-10-10T15:00:00Z', 100, 25);

-- 動画を追加
INSERT OR IGNORE INTO videos (video_id, title, channel, first_seen_run, first_seen_at)
VALUES ('abc123', 'CBD リキッドレビュー', 'チャンネル名', 'run_001', '2026-10-10T15:00:00Z');

-- Run と Video の関係を追加
INSERT INTO run_videos (run_id, video_id, position)
VALUES ('run_001', 'abc123', 1);
```

### 8.3 一致率の確認

```sql
-- 一致率履歴を取得
SELECT * FROM v_consistency_history
WHERE search_term = 'CBD リキッド'
ORDER BY run_number;
```

---

## 9. 制約事項

| 制約 | 内容 |
|------|------|
| **Raw データ不変** | runs, videos テーブルの既存行は変更しない |
| **Run ID 一意性** | 同一 Run ID で複数回 INSERT しない |
| **Video ID 一意性** | videos テーブルでは videoId で一意 |
| **日付形式** | ISO 8601 形式で統一 |

---

## 10. ファイル構成

```
datasets/youtube-consistency/
├── data/
│   └── youtube.db          # SQLite データベース
├── schema/
│   └── schema.sql          # スキーマ定義
├── queries/
│   ├── insert_run.sql      # Run 挿入
│   ├── calculate_rate.sql  # 一致率計算
│   └── view_history.sql    # 履歴取得
└── README.md
```
