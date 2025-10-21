# Data Flow Documentation

## End-to-End Data Flow

This document describes how data flows through the Collaborate-Stream analytics platform, from event generation to visualization.

## Flow Stages

### 1. Event Generation → Kafka

```
Application Events → Producer → Kafka Topics
```

**Step 1.1: Event Creation**
- User actions in SaaS application (join meeting, send message, etc.)
- Events are serialized to JSON
- Avro schema validation applied
- Event enriched with metadata (timestamp, event_id)

**Step 1.2: Producer Publishing**
```python
# Example: Publishing a user join event
event = {
    "event_id": "uuid-123",
    "user_id": "user_456",
    "meeting_id": "meeting_789",
    "event_type": "join",
    "timestamp": 1704067200000
}
producer.send("user_events", key="meeting_789", value=event)
```

**Step 1.3: Kafka Storage**
- Event written to appropriate topic partition
- Partition determined by key (meeting_id)
- Multiple replicas for durability
- Retention: 7 days (configurable)

**Topics and Partitioning**:
```
user_events     → 10 partitions → ordered by meeting_id
chat_events     → 10 partitions → ordered by meeting_id
meeting_events  → 10 partitions → ordered by meeting_id
```

---

### 2. Kafka → Flink Stream Processing

```
Kafka Topics → Flink Source → Processing Pipeline → Flink Sink
```

**Step 2.1: Event Consumption**
- Flink Kafka Consumer reads from topics
- Consumer group: `collaborate-stream-flink`
- Checkpointing ensures exactly-once processing
- Offset management automatic

**Step 2.2: Event Parsing**
```python
stream = env.add_source(kafka_source)
parsed_stream = stream.map(EventParser())  # JSON → Python dict
```

**Step 2.3: Event Validation**
- Schema validation
- Required field checks
- Data type validation
- Invalid events → dead letter queue

**Step 2.4: Event Enrichment**
```python
enriched = parsed_stream.map(lambda e: {
    **e,
    'processing_timestamp': now(),
    'processing_date': today()
})
```

**Step 2.5: Keying by Meeting ID**
```python
keyed_stream = enriched.key_by(lambda e: e['meeting_id'])
```

**Step 2.6: Windowing**
```python
# Tumbling window: 30-second non-overlapping
windowed = keyed_stream.window(
    TumblingProcessingTimeWindows.of(Time.seconds(30))
)

# Sliding window: 60-second with 15-second slide
windowed = keyed_stream.window(
    SlidingProcessingTimeWindows.of(
        Time.seconds(60), 
        Time.seconds(15)
    )
)
```

**Step 2.7: Aggregation**
```python
aggregated = windowed.aggregate(MeetingMetricsAggregator())
```

**Aggregation Logic**:
- Accumulate events in window
- Calculate metrics:
  - Count active users (unique user_ids with join - leave)
  - Sum messages
  - Average latency
  - Compute engagement score
  - Determine health status

**Step 2.8: Window Close & Emit**
- Window closes after 30 seconds (tumbling)
- Aggregated metrics emitted
- Results include meeting_id, window_start, window_end, metrics

---

### 3. Flink → Parquet Storage

```
Flink Sink → Parquet Writer → S3 Upload
```

**Step 3.1: Sink Processing**
- Buffered writes (batch of 1000 records or 60 seconds)
- Parquet file creation with schema
- Columnar compression (Snappy)

**Step 3.2: Partitioning**
```
Base Path: s3://collaborate-stream/metrics/
Partition: date=2024-01-15/
File:      metrics_20240115_143025.parquet
```

**Step 3.3: Schema Mapping**
```
Flink Output → Parquet Schema
{
  meeting_id: STRING,
  timestamp: INT64,
  active_users: INT32,
  message_count: INT32,
  avg_latency_ms: DOUBLE,
  engagement_score: DOUBLE,
  meeting_health: STRING,
  date_partition: STRING
}
```

**Step 3.4: File Upload**
- Atomic write to S3
- File size: typically 10-50MB
- New file every minute or when buffer full
- S3 path structure preserves date partitions

---

### 4. Parquet Files → Presto Querying

```
S3 Parquet → Hive Metastore → Presto Query Engine
```

**Step 4.1: Metadata Registration**
```sql
-- External table points to S3 location
CREATE EXTERNAL TABLE meeting_metrics (...)
PARTITIONED BY (date_partition STRING)
STORED AS PARQUET
LOCATION 's3://collaborate-stream/metrics/';
```

**Step 4.2: Partition Discovery**
```sql
-- Automatic or manual partition discovery
MSCK REPAIR TABLE meeting_metrics;

-- Or manual add
ALTER TABLE meeting_metrics 
ADD PARTITION (date_partition='2024-01-15')
LOCATION 's3://collaborate-stream/metrics/date=2024-01-15/';
```

**Step 4.3: Query Execution**
```sql
-- Query real-time metrics
SELECT meeting_id, AVG(avg_latency_ms)
FROM meeting_metrics
WHERE date_partition >= '2024-01-15'
GROUP BY meeting_id;
```

**Query Flow**:
1. Presto Coordinator receives query
2. Query parsed and optimized
3. Workers read Parquet files from S3
4. Columnar predicate pushdown (only read needed columns)
5. Parallel processing across workers
6. Results aggregated and returned

**Step 4.4: Joining with Historical Data**
```sql
-- Join real-time with historical
SELECT 
  m.meeting_id,
  m.avg_latency_ms,
  u.username,
  o.plan_type
FROM realtime.meeting_metrics m
JOIN hive.user_profiles u ON m.user_id = u.user_id
JOIN hive.organization_plans o ON u.organization_id = o.organization_id
WHERE m.date_partition >= '2024-01-15';
```

---

### 5. Presto Results → Visualization

```
Query Results → Dashboard Backend → UI Rendering
```

**Step 5.1: Streamlit Data Fetch**
```python
import presto
import pandas as pd

# Connect to Presto
conn = presto.connect(host='localhost', port=8080)

# Execute query
df = pd.read_sql("""
    SELECT * FROM meeting_metrics 
    WHERE timestamp >= now() - INTERVAL '15' MINUTE
""", conn)

# Display in Streamlit
st.dataframe(df)
st.plotly_chart(create_chart(df))
```

**Step 5.2: Grafana Data Source**
- Prometheus exporter for Kafka/Flink metrics
- Direct Presto connection for business metrics
- Time-series queries with auto-refresh

**Step 5.3: Visualization Update Cycle**
```
Every 5-10 seconds:
1. Dashboard queries Presto
2. Results transformed to chart data
3. UI re-renders with new data
4. User sees near real-time updates
```

---

## Timing Characteristics

### Latency Breakdown

**Event to Kafka**: < 10ms
- Network latency: ~5ms
- Kafka write: ~5ms

**Kafka to Flink Processing**: < 100ms
- Consumer poll: ~50ms
- Processing: ~50ms

**Window Aggregation**: 0-30 seconds
- Waiting for window to close
- Tumbling window adds up to 30s latency

**Flink to Parquet**: < 5 seconds
- Buffering: 0-60s (configurable)
- Write to S3: ~2s

**Parquet to Query**: < 1 second
- Metadata lookup: ~100ms
- S3 read: ~500ms
- Query execution: ~500ms

**Total End-to-End Latency**: 30-45 seconds (typical)
- For immediate window: ~1 second
- For windowed aggregation: ~35 seconds

### Throughput Characteristics

**Kafka Ingestion**: 1M+ events/second
- Per partition: ~100K events/second
- 10 partitions → 1M events/second

**Flink Processing**: 500K events/second per TaskManager
- Parallelism 10 → 5M events/second capacity

**Parquet Writes**: 10K aggregated records/second
- Much lower than input (aggregation reduces volume)

**Query Throughput**: 100+ concurrent queries
- Presto workers scale horizontally

---

## Data Volume Examples

### Typical Meeting (30 minutes, 10 users)

**Input Events**:
- User events: 20 (joins/leaves)
- Chat events: 200 (messages, reactions)
- Meeting events: 600 (video, screen share, network)
- **Total**: ~820 events

**Aggregated Output** (30-second windows):
- Windows per meeting: 60 (30 min / 30 sec)
- Records created: 60
- **Compression ratio**: 820:60 ≈ 14:1

### Daily Volume (1000 concurrent meetings)

**Input**:
- Events per meeting: 820
- Meetings per day: 1000
- **Total events**: 820,000 per day

**Storage**:
- Kafka (7 days): ~5.7M events × 1KB ≈ 5.7GB
- Parquet (aggregated): ~60K records × 500B ≈ 30MB/day
- **Annual storage**: ~11GB aggregated metrics

### Large Scale (100K concurrent meetings)

**Input Rate**: 82M events/day
**Aggregated Output**: 6M records/day
**Storage/year**: 1.1TB aggregated metrics

---

## Data Retention Policies

**Kafka**:
- Retention: 7 days
- Purpose: Replay capability, failure recovery

**Parquet (Real-time metrics)**:
- Retention: 90 days
- Purpose: Recent analytics, troubleshooting

**Hive (Historical data)**:
- Retention: Indefinite
- Purpose: Long-term trends, compliance

**Archival**:
- After 90 days: Move to S3 Glacier
- Cost reduction: ~80% vs. standard S3
