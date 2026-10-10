-- Run 挿入（データフロー Step 2）
-- パラメータ: :run_id :search_term :max_videos :collection_timestamp
--             :record_count :unique_count :apify_dataset_id
INSERT INTO runs (
    run_id, source, search_term, max_videos,
    apify_dataset_id, collection_timestamp,
    record_count, unique_count, collector, collector_version
) VALUES (
    :run_id, 'youtube', :search_term, :max_videos,
    :apify_dataset_id, :collection_timestamp,
    :record_count, :unique_count, 'apify', :collector_version
);

-- 動画マスタ挿入（Step 3）: 既存 video_id は保持（Raw 相当の不変）
-- パラメータ: :video_id :title :channel :views :duration
--             :published_at :run_id :collection_timestamp
INSERT OR IGNORE INTO videos (
    video_id, title, channel, views, duration,
    published_at, first_seen_run, first_seen_at
) VALUES (
    :video_id, :title, :channel, :views, :duration,
    :published_at, :run_id, :collection_timestamp
);

-- Run-Video 関係挿入（Step 4）
-- パラメータ: :run_id :video_id :position :is_duplicate
INSERT OR REPLACE INTO run_videos (run_id, video_id, position, is_duplicate)
VALUES (:run_id, :video_id, :position, :is_duplicate);
