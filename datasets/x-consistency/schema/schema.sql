-- X (Twitter) 取得データ スキーマ
-- 対応スクリプト: scripts/debug/x_posts_date_range.py

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'x',
    search_term TEXT NOT NULL,
    max_items INTEGER NOT NULL,
    apify_actor_id TEXT,
    apify_dataset_id TEXT,
    collection_timestamp TEXT NOT NULL,
    record_count INTEGER,
    unique_count INTEGER,
    collector TEXT DEFAULT 'apify',
    collector_version TEXT
);

CREATE TABLE IF NOT EXISTS posts (
    post_id TEXT PRIMARY KEY,
    text TEXT,
    url TEXT,
    created_at TEXT,
    author_name TEXT,
    author_screen_name TEXT,
    author_user_id TEXT,
    favourite_count INTEGER,
    repost_count INTEGER,
    reply_count INTEGER,
    quote_count INTEGER,
    first_seen_run TEXT REFERENCES runs(run_id),
    first_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run_posts (
    run_id TEXT REFERENCES runs(run_id),
    post_id TEXT REFERENCES posts(post_id),
    PRIMARY KEY (run_id, post_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_search_term ON runs (search_term);
CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON runs (collection_timestamp);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts (created_at);
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts (author_screen_name);
CREATE INDEX IF NOT EXISTS idx_run_posts_run ON run_posts (run_id);
CREATE INDEX IF NOT EXISTS idx_run_posts_post ON run_posts (post_id);

CREATE VIEW IF NOT EXISTS v_run_summary AS
SELECT
    r.run_id,
    r.search_term,
    r.collection_timestamp,
    r.max_items,
    r.record_count,
    r.unique_count,
    COUNT(rp.post_id) AS actual_unique,
    ROUND(COUNT(rp.post_id) * 100.0 / NULLIF(r.max_items, 0), 1) AS fill_rate
FROM runs r
LEFT JOIN run_posts rp ON r.run_id = rp.run_id
GROUP BY r.run_id;
