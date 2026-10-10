-- 一致率履歴の取得（consistency_metrics 不要版）
-- Run を collection_timestamp 順に番号付けし、直前の Run 群との
-- 重複（already_collected）／新規（new_videos）をその場で計算する。
-- パラメータなし
WITH ordered AS (
    SELECT run_id, collection_timestamp,
           ROW_NUMBER() OVER (ORDER BY collection_timestamp, run_id) as run_number
    FROM runs
),
per_run AS (
    SELECT DISTINCT
        o.run_id, o.run_number, o.collection_timestamp, rv.video_id
    FROM ordered o
    JOIN run_videos rv ON o.run_id = rv.run_id
)
SELECT
    cur.run_number,
    cur.run_id,
    r.search_term,
    cur.collection_timestamp,
    COUNT(*) as unique_count,
    SUM(CASE WHEN EXISTS (
        SELECT 1 FROM per_run prev
        WHERE prev.video_id = cur.video_id
          AND prev.run_number < cur.run_number
    ) THEN 1 ELSE 0 END) as already_collected,
    SUM(CASE WHEN EXISTS (
        SELECT 1 FROM per_run prev
        WHERE prev.video_id = cur.video_id
          AND prev.run_number < cur.run_number
    ) THEN 0 ELSE 1 END) as new_videos,
    ROUND(
        SUM(CASE WHEN EXISTS (
            SELECT 1 FROM per_run prev
            WHERE prev.video_id = cur.video_id
              AND prev.run_number < cur.run_number
        ) THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1
    ) as consistency_pct,
    (SELECT COUNT(DISTINCT pv.video_id)
       FROM per_run pv
      WHERE pv.run_number <= cur.run_number) as cumulative_count
FROM per_run cur
JOIN runs r ON cur.run_id = r.run_id
GROUP BY cur.run_number
ORDER BY cur.run_number;
