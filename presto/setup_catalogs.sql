-- Presto Catalog Setup
-- Configure catalogs for Hive and real-time data sources

-- Create Hive catalog for historical data
CREATE CATALOG hive USING hive
WITH (
  "hive.metastore.uri" = 'thrift://localhost:9083',
  "hive.config.resources" = '/etc/hadoop/conf/core-site.xml,/etc/hadoop/conf/hdfs-site.xml'
);

-- Create catalog for real-time metrics (S3/Parquet)
CREATE CATALOG realtime USING hive
WITH (
  "hive.metastore.uri" = 'thrift://localhost:9083',
  "hive.s3.path-style-access" = 'true',
  "hive.s3.endpoint" = 'http://localhost:9000',
  "hive.allow-drop-table" = 'true'
);

-- Create schema for real-time metrics
CREATE SCHEMA IF NOT EXISTS realtime.default
WITH (location = 's3://collaborate-stream/metrics/');

-- Create external table for meeting metrics
CREATE TABLE IF NOT EXISTS realtime.meeting_metrics (
  meeting_id VARCHAR,
  user_id VARCHAR,
  timestamp BIGINT,
  active_users INTEGER,
  message_count INTEGER,
  avg_latency_ms DOUBLE,
  join_count INTEGER,
  leave_count INTEGER,
  churn_rate DOUBLE,
  engagement_score DOUBLE,
  meeting_health VARCHAR,
  event_type VARCHAR,
  date_partition VARCHAR
)
WITH (
  format = 'PARQUET',
  external_location = 's3://collaborate-stream/metrics/',
  partitioned_by = ARRAY['date_partition']
);

-- Sample queries to verify setup
SHOW CATALOGS;
SHOW SCHEMAS FROM hive;
SHOW TABLES FROM realtime.default;
