# Metrics Reference

## Complete Metrics Catalog for Collaborate-Stream

This document provides a comprehensive reference of all metrics tracked by the Collaborate-Stream analytics platform.

---

## Metric Categories

1. [Participant Metrics](#participant-metrics)
2. [Message Activity Metrics](#message-activity-metrics)
3. [Network Quality Metrics](#network-quality-metrics)
4. [Engagement Metrics](#engagement-metrics)
5. [Meeting Health Metrics](#meeting-health-metrics)
6. [System Performance Metrics](#system-performance-metrics)

---

## Participant Metrics

### `active_users`
- **Description**: Number of users currently active in a meeting
- **Type**: Gauge (Integer)
- **Calculation**: `COUNT(DISTINCT user_id WHERE event_type='join') - COUNT(DISTINCT user_id WHERE event_type='leave')`
- **Window**: 30s tumbling, 1m sliding
- **Range**: 0 - 1000+
- **Use Cases**:
  - Monitor meeting size
  - Capacity planning
  - Detect abnormal drops (crashes)

**Example**:
```python
active_users = 15  # 15 people in the meeting
```

### `join_count`
- **Description**: Number of users who joined during the window
- **Type**: Counter (Integer)
- **Calculation**: `COUNT(event_type='join')`
- **Window**: 30s tumbling, 5m sliding
- **Range**: 0 - 100+
- **Use Cases**:
  - Meeting start detection
  - Popular meeting times
  - Onboarding patterns

### `leave_count`
- **Description**: Number of users who left during the window
- **Type**: Counter (Integer)
- **Calculation**: `COUNT(event_type='leave')`
- **Window**: 30s tumbling, 5m sliding
- **Range**: 0 - 100+
- **Use Cases**:
  - Meeting end detection
  - User drop-off analysis
  - Technical issue detection

### `churn_rate`
- **Description**: Rate of user joins and leaves relative to active users
- **Type**: Ratio (Float, 0.0 - 1.0+)
- **Calculation**: `(join_count + leave_count) / max(active_users, 1)`
- **Window**: 5m tumbling
- **Range**: 0.0 - 2.0+ (can exceed 1.0 in high-churn scenarios)
- **Interpretation**:
  - `< 0.1`: Stable meeting
  - `0.1 - 0.3`: Normal churn
  - `> 0.3`: High churn (investigate)
- **Use Cases**:
  - Meeting stability analysis
  - Quality of service indicator
  - User experience metric

**Example**:
```python
churn_rate = 0.15  # 15% churn - normal
# Calculation: (3 joins + 2 leaves) / 15 active users = 5/15 = 0.33
```

---

## Message Activity Metrics

### `message_count`
- **Description**: Total messages sent in the meeting
- **Type**: Counter (Integer)
- **Calculation**: `COUNT(event_type='message')`
- **Window**: 30s tumbling, 1m sliding
- **Range**: 0 - 1000+
- **Use Cases**:
  - Engagement measurement
  - Chat usage patterns
  - Meeting activity level

### `message_rate`
- **Description**: Messages per second
- **Type**: Rate (Float)
- **Calculation**: `message_count / window_duration_seconds`
- **Window**: 30s sliding
- **Range**: 0 - 100+ msg/sec
- **Interpretation**:
  - `< 0.1`: Quiet meeting
  - `0.1 - 1.0`: Normal activity
  - `> 1.0`: High activity (e.g., Q&A session)

**Example**:
```python
message_rate = 2.5  # 2.5 messages per second
# In 30s window: 75 messages total
```

### `reaction_count`
- **Description**: Number of emoji reactions and quick responses
- **Type**: Counter (Integer)
- **Calculation**: `COUNT(event_type='reaction' OR event_type='emoji')`
- **Window**: 30s tumbling
- **Range**: 0 - 500+
- **Use Cases**:
  - Non-verbal engagement
  - Sentiment analysis
  - Feature usage tracking

### `avg_message_length`
- **Description**: Average length of messages in characters
- **Type**: Gauge (Float)
- **Calculation**: `SUM(message_length) / COUNT(messages)`
- **Window**: 5m tumbling
- **Range**: 0 - 500+ characters
- **Interpretation**:
  - `< 20`: Short responses
  - `20 - 100`: Normal discussion
  - `> 100`: Detailed explanations

---

## Network Quality Metrics

### `avg_latency_ms`
- **Description**: Average network latency in milliseconds
- **Type**: Gauge (Float)
- **Calculation**: `AVG(latency_ms) WHERE event_type='network_lag'`
- **Window**: 30s tumbling, 1m sliding
- **Range**: 20 - 500+ ms
- **Thresholds**:
  - `< 100ms`: Excellent (green)
  - `100 - 200ms`: Fair (yellow)
  - `> 200ms`: Poor (red)
- **Use Cases**:
  - Quality of service monitoring
  - Network issue detection
  - User experience optimization

**Example**:
```python
avg_latency_ms = 85.5  # Good latency
```

### `p50_latency_ms`
- **Description**: 50th percentile (median) latency
- **Type**: Gauge (Float)
- **Calculation**: `PERCENTILE(latency_ms, 0.5)`
- **Window**: 1m tumbling
- **Use Cases**: Typical user experience

### `p95_latency_ms`
- **Description**: 95th percentile latency
- **Type**: Gauge (Float)
- **Calculation**: `PERCENTILE(latency_ms, 0.95)`
- **Window**: 1m tumbling
- **Use Cases**: Worst-case user experience

### `p99_latency_ms`
- **Description**: 99th percentile latency
- **Type**: Gauge (Float)
- **Calculation**: `PERCENTILE(latency_ms, 0.99)`
- **Window**: 1m tumbling
- **Use Cases**: SLA monitoring, outlier detection

### `packet_loss_pct`
- **Description**: Percentage of packets lost
- **Type**: Gauge (Float, 0.0 - 100.0)
- **Calculation**: `AVG(packet_loss) WHERE event_type='network_lag'`
- **Window**: 30s tumbling
- **Range**: 0 - 100%
- **Thresholds**:
  - `< 1%`: Excellent
  - `1 - 5%`: Acceptable
  - `> 5%`: Poor
- **Use Cases**:
  - Video/audio quality prediction
  - Network path optimization

---

## Engagement Metrics

### `engagement_score`
- **Description**: Composite metric representing overall meeting engagement
- **Type**: Score (Float, 0 - 100)
- **Calculation**:
  ```python
  message_component = min(message_count / 100, 1.0) * 40
  user_component = min(active_users / 10, 1.0) * 30
  quality_component = max(0, (1 - avg_latency_ms / 500)) * 30
  engagement_score = message_component + user_component + quality_component
  ```
- **Window**: 1m tumbling, 15m sliding
- **Range**: 0 - 100
- **Interpretation**:
  - `0 - 30`: Low engagement
  - `30 - 70`: Medium engagement
  - `70 - 100`: High engagement
- **Use Cases**:
  - Meeting quality assessment
  - User satisfaction proxy
  - Feature effectiveness

**Example**:
```python
# Meeting with 8 users, 50 messages, 80ms latency
message_score = min(50/100, 1.0) * 40 = 20
user_score = min(8/10, 1.0) * 30 = 24
quality_score = max(0, (1 - 80/500)) * 30 = 25.2
engagement_score = 20 + 24 + 25.2 = 69.2  # Medium-high
```

### `screen_share_count`
- **Description**: Number of screen sharing sessions started
- **Type**: Counter (Integer)
- **Calculation**: `COUNT(event_type='screen_share')`
- **Window**: 5m tumbling
- **Range**: 0 - 20+
- **Use Cases**:
  - Presentation tracking
  - Feature usage
  - Meeting type classification

### `video_participation_rate`
- **Description**: Percentage of users with video enabled
- **Type**: Ratio (Float, 0.0 - 1.0)
- **Calculation**: `COUNT(DISTINCT user_id WHERE event_type='video_start') / active_users`
- **Window**: 1m tumbling
- **Range**: 0.0 - 1.0
- **Interpretation**:
  - `< 0.3`: Low video usage (audio-only meeting)
  - `0.3 - 0.7`: Mixed usage
  - `> 0.7`: High video usage
- **Use Cases**:
  - Video adoption tracking
  - Bandwidth estimation
  - User preference analysis

---

## Meeting Health Metrics

### `meeting_health`
- **Description**: Overall health status of the meeting
- **Type**: Enum (String)
- **Values**: `'good'`, `'fair'`, `'poor'`, `'inactive'`
- **Calculation**:
  ```python
  if active_users == 0:
      return 'inactive'
  elif avg_latency_ms > 200:
      return 'poor'
  elif avg_latency_ms > 100:
      return 'fair'
  else:
      return 'good'
  ```
- **Window**: 30s tumbling
- **Use Cases**:
  - Dashboard status indicators
  - Alerting triggers
  - Quality monitoring

**Thresholds**:
```python
{
  'good': avg_latency < 100ms AND active_users > 0,
  'fair': 100ms <= avg_latency < 200ms,
  'poor': avg_latency >= 200ms,
  'inactive': active_users == 0
}
```

### `meeting_duration_seconds`
- **Description**: Duration of the meeting
- **Type**: Gauge (Integer)
- **Calculation**: `max_timestamp - min_timestamp`
- **Unit**: Seconds
- **Range**: 0 - 14400+ (4 hours+)
- **Use Cases**:
  - Billing calculations
  - Usage patterns
  - Meeting length trends

---

## System Performance Metrics

### `events_processed_per_second`
- **Description**: Number of events processed by Flink per second
- **Type**: Rate (Integer)
- **Calculation**: Flink internal metric
- **Range**: 0 - 1M+
- **Use Cases**:
  - System capacity monitoring
  - Scaling decisions
  - Performance optimization

### `processing_lag_ms`
- **Description**: Delay between event generation and processing
- **Type**: Gauge (Integer, milliseconds)
- **Calculation**: `processing_timestamp - event_timestamp`
- **Range**: 0 - 5000+ ms
- **Thresholds**:
  - `< 500ms`: Excellent
  - `500 - 2000ms`: Acceptable
  - `> 2000ms`: Behind, scale up
- **Use Cases**:
  - Real-time guarantee verification
  - System health monitoring

### `kafka_consumer_lag`
- **Description**: Number of messages waiting to be consumed
- **Type**: Gauge (Integer)
- **Calculation**: Kafka metric
- **Range**: 0 - 1M+
- **Thresholds**:
  - `< 1000`: Healthy
  - `1000 - 10000`: Monitor
  - `> 10000`: Critical, scale consumers
- **Use Cases**:
  - Backpressure detection
  - Scaling triggers

---

## Metric Aggregation Windows

| Metric Category | Tumbling Window | Sliding Window |
|----------------|-----------------|----------------|
| Participant | 30s | 1m (15s slide) |
| Message Activity | 30s | 1m (30s slide) |
| Network Quality | 30s | 1m (15s slide) |
| Engagement | 1m | 15m (5m slide) |
| Health | 30s | N/A |
| System | N/A | 1m (10s slide) |

---

## Metric Storage Format

**Parquet Schema**:
```python
{
  'meeting_id': 'string',
  'timestamp': 'int64',  # Unix timestamp (ms)
  'active_users': 'int32',
  'message_count': 'int32',
  'avg_latency_ms': 'double',
  'join_count': 'int32',
  'leave_count': 'int32',
  'churn_rate': 'double',
  'engagement_score': 'double',
  'meeting_health': 'string',
  'video_starts': 'int32',
  'screen_shares': 'int32',
  'window_size_seconds': 'int32',
  'date_partition': 'string'  # YYYY-MM-DD
}
```

---

## Query Examples

### Get Active Meetings with High Engagement
```sql
SELECT meeting_id, engagement_score, active_users
FROM meeting_metrics
WHERE engagement_score > 70
  AND timestamp > now() - INTERVAL '15' MINUTE
ORDER BY engagement_score DESC;
```

### Latency Percentiles per Meeting
```sql
SELECT 
  meeting_id,
  APPROX_PERCENTILE(avg_latency_ms, 0.5) as p50,
  APPROX_PERCENTILE(avg_latency_ms, 0.95) as p95,
  APPROX_PERCENTILE(avg_latency_ms, 0.99) as p99
FROM meeting_metrics
WHERE date_partition = '2024-01-15'
GROUP BY meeting_id;
```

### Meeting Health Distribution
```sql
SELECT 
  meeting_health,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM meeting_metrics
WHERE timestamp > now() - INTERVAL '1' HOUR
GROUP BY meeting_health;
```

---

## Alerting Rules

**High Latency Alert**:
```yaml
alert: HighLatency
expr: avg_latency_ms > 200
for: 2m
severity: warning
message: "Meeting {{ meeting_id }} has high latency ({{ avg_latency_ms }}ms)"
```

**Low Engagement Alert**:
```yaml
alert: LowEngagement
expr: engagement_score < 30 AND active_users > 5
for: 5m
severity: info
message: "Meeting {{ meeting_id }} has low engagement despite {{ active_users }} participants"
```

**System Lag Alert**:
```yaml
alert: ProcessingLag
expr: kafka_consumer_lag > 10000
for: 1m
severity: critical
message: "Kafka consumer lag is {{ kafka_consumer_lag }} - system falling behind"
```
