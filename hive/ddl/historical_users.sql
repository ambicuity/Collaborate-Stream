-- Historical Users Table DDL
-- Stores user profile and organizational data

CREATE DATABASE IF NOT EXISTS collaborate_stream;

USE collaborate_stream;

-- User profiles table
CREATE EXTERNAL TABLE IF NOT EXISTS user_profiles (
  user_id STRING,
  username STRING,
  email STRING,
  organization_id STRING,
  created_at BIGINT,
  last_login BIGINT,
  user_role STRING,
  timezone STRING,
  is_active BOOLEAN
)
COMMENT 'Historical user profile data'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS PARQUET
LOCATION 's3://collaborate-stream/hive/user_profiles/';

-- Organization plans table
CREATE EXTERNAL TABLE IF NOT EXISTS organization_plans (
  organization_id STRING,
  organization_name STRING,
  plan_type STRING,
  max_users INT,
  features ARRAY<STRING>,
  created_at BIGINT,
  billing_status STRING
)
COMMENT 'Organization subscription and plan data'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS PARQUET
LOCATION 's3://collaborate-stream/hive/organization_plans/';

-- Meeting history table (for long-term storage)
CREATE EXTERNAL TABLE IF NOT EXISTS meeting_history (
  meeting_id STRING,
  organization_id STRING,
  start_time BIGINT,
  end_time BIGINT,
  duration_seconds INT,
  max_participants INT,
  total_messages INT,
  avg_latency_ms DOUBLE,
  meeting_type STRING
)
COMMENT 'Historical meeting data'
PARTITIONED BY (year INT, month INT, day INT)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS PARQUET
LOCATION 's3://collaborate-stream/hive/meeting_history/';

-- User activity summary (aggregated)
CREATE EXTERNAL TABLE IF NOT EXISTS user_activity_summary (
  user_id STRING,
  activity_date DATE,
  meetings_attended INT,
  total_messages INT,
  total_duration_seconds INT,
  avg_engagement_score DOUBLE
)
COMMENT 'Daily user activity summary'
PARTITIONED BY (year INT, month INT)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS PARQUET
LOCATION 's3://collaborate-stream/hive/user_activity_summary/';

-- Create indexes for better query performance
-- Note: Hive 3.0+ supports indexes, adjust based on your Hive version
CREATE INDEX idx_user_id ON TABLE user_profiles(user_id) AS 'COMPACT' WITH DEFERRED REBUILD;
CREATE INDEX idx_org_id ON TABLE organization_plans(organization_id) AS 'COMPACT' WITH DEFERRED REBUILD;

-- Show created tables
SHOW TABLES;
