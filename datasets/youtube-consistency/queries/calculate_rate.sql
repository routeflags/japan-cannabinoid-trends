-- Run 間の一致率計算（consistency_metrics 不要版）
-- 直前に収集 timestamp のある Run 群との重複を計算する。
-- パラメータ: :target_run_id
WITH cumulative AS (
    SELECT DISTINCT rv.video_id
    FROM run_videos rv
    JOIN runs r ON rv.run_id = r.run_id
    WHERE r.collection_timestamp < (
        SELECT collection_timestamp FROM runs WHERE run_id = :target_run_id
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
