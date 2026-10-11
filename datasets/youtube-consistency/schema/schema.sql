-- ============================================================
-- 収集データ統合 DB スキーマ（YouTube 対応分）
-- 仕様: docs/specs/youtube-sqlite-design.md
--
-- DB 名は複数ソース拡張に備えて抽象化してあり（trends.db）、
-- ソース種別は runs.source で識別する。
-- 新規ソース追加時は本ファイルに対応テーブル群を追加する。
--
-- 運用履歴:
-- - 2026-10-12: YouTube Data API v3 由来 run（collector='youtube-api'、
--   55 件）と関連 run_videos を方針決定により削除。
--   同時に existing_data 4 件の collection_timestamp 汚染を訂正、
--   v_run_summary の fill_rate をセンチネル対応に変更。
--   削除前バックアップはローカル保持（data/trends.db.bak-*、Git 管理外）。
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- 3.1 runs（収集実行）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'youtube',
    search_term TEXT NOT NULL,
    max_videos INTEGER NOT NULL,
    apify_dataset_id TEXT,
    collection_timestamp TEXT NOT NULL,
    record_count INTEGER,
    unique_count INTEGER,
    collector TEXT DEFAULT 'apify',
    collector_version TEXT
);

-- ------------------------------------------------------------
-- 3.2 videos（動画マスタ）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    title TEXT,
    channel TEXT,
    url TEXT,
    views INTEGER,
    duration INTEGER,
    published_at TEXT,
    first_seen_run TEXT REFERENCES runs(run_id),
    first_seen_at TEXT NOT NULL
);

-- ------------------------------------------------------------
-- 3.3 run_videos（Run と Video の関係）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS run_videos (
    run_id TEXT REFERENCES runs(run_id),
    video_id TEXT REFERENCES videos(video_id),
    position INTEGER,
    is_duplicate INTEGER DEFAULT 0,
    PRIMARY KEY (run_id, video_id)
);

-- ------------------------------------------------------------
-- 4. インデックス
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_runs_search_term ON runs(search_term);
CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON runs(collection_timestamp);
CREATE INDEX IF NOT EXISTS idx_videos_published_at ON videos(published_at);
CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel);
CREATE INDEX IF NOT EXISTS idx_run_videos_run ON run_videos(run_id);
CREATE INDEX IF NOT EXISTS idx_run_videos_video ON run_videos(video_id);

-- ------------------------------------------------------------
-- 5. ビュー
-- ------------------------------------------------------------

-- 5.1 v_run_summary（Run サマリー）
-- 注: max_videos=999999 は「無制限」センチネル。fill_rate は算出しない（NULL）。
CREATE VIEW IF NOT EXISTS v_run_summary AS
SELECT
    r.run_id,
    r.search_term,
    r.collection_timestamp,
    r.max_videos,
    r.record_count,
    r.unique_count,
    COUNT(rv.video_id) as actual_unique,
    CASE WHEN r.max_videos >= 999999 THEN NULL
         ELSE ROUND(COUNT(rv.video_id) * 100.0 / r.max_videos, 1) END as fill_rate
FROM runs r
LEFT JOIN run_videos rv ON r.run_id = rv.run_id
GROUP BY r.run_id;

-- 5.2 v_video_appearance（動画の出現履歴）
CREATE VIEW IF NOT EXISTS v_video_appearance AS
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
