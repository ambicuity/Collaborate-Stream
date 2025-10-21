-- Meeting Health Analysis Query
-- Combines real-time metrics with historical user data

SELECT
  m.meeting_id,
  m.timestamp,
  AVG(m.avg_latency_ms) AS avg_latency,
  SUM(m.active_users) AS total_participants,
  COUNT(DISTINCT u.user_id) AS unique_users,
  SUM(m.message_count) AS total_messages,
  AVG(m.engagement_score) AS avg_engagement_score,
  CASE 
    WHEN AVG(m.avg_latency_ms) > 200 THEN 'Poor'
    WHEN AVG(m.avg_latency_ms) BETWEEN 100 AND 200 THEN 'Fair'
    ELSE 'Good'
  END AS meeting_health,
  CASE
    WHEN AVG(m.engagement_score) > 70 THEN 'High'
    WHEN AVG(m.engagement_score) BETWEEN 40 AND 70 THEN 'Medium'
    ELSE 'Low'
  END AS engagement_level
FROM realtime.meeting_metrics m
LEFT JOIN hive.default.user_profiles u 
  ON m.user_id = u.user_id
WHERE m.timestamp >= CAST(now() - INTERVAL '1' HOUR AS BIGINT)
GROUP BY m.meeting_id, m.timestamp
ORDER BY avg_engagement_score DESC;
