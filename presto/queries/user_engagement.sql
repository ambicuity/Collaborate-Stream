-- User Engagement Analysis Query
-- Analyzes user participation and activity patterns

WITH user_activity AS (
  SELECT
    u.user_id,
    u.username,
    u.organization_id,
    COUNT(DISTINCT m.meeting_id) AS meetings_attended,
    SUM(m.message_count) AS total_messages,
    AVG(m.avg_latency_ms) AS avg_connection_quality,
    SUM(CASE WHEN m.event_type = 'screen_share' THEN 1 ELSE 0 END) AS screen_shares,
    SUM(CASE WHEN m.event_type = 'video_start' THEN 1 ELSE 0 END) AS video_sessions,
    MAX(m.timestamp) AS last_activity
  FROM realtime.meeting_metrics m
  JOIN hive.default.user_profiles u ON m.user_id = u.user_id
  WHERE m.timestamp >= CAST(now() - INTERVAL '7' DAY AS BIGINT)
  GROUP BY u.user_id, u.username, u.organization_id
),
engagement_scores AS (
  SELECT
    user_id,
    username,
    organization_id,
    meetings_attended,
    total_messages,
    avg_connection_quality,
    screen_shares,
    video_sessions,
    last_activity,
    -- Calculate engagement score: weighted sum of activities
    (meetings_attended * 10 + 
     total_messages * 0.5 + 
     screen_shares * 5 + 
     video_sessions * 3) AS engagement_score
  FROM user_activity
)
SELECT
  e.*,
  o.plan_type,
  o.organization_name,
  CASE
    WHEN engagement_score > 500 THEN 'Power User'
    WHEN engagement_score > 200 THEN 'Active User'
    WHEN engagement_score > 50 THEN 'Regular User'
    ELSE 'Inactive User'
  END AS user_segment,
  RANK() OVER (PARTITION BY e.organization_id ORDER BY engagement_score DESC) AS org_rank
FROM engagement_scores e
LEFT JOIN hive.default.organization_plans o ON e.organization_id = o.organization_id
ORDER BY engagement_score DESC
LIMIT 100;
