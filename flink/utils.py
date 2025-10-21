"""
Utility functions for Flink stream processing
"""
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_event(event_string: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON event string
    
    Args:
        event_string: JSON string representation of event
        
    Returns:
        Parsed event dictionary or None if parsing fails
    """
    try:
        return json.loads(event_string)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse event: {e}")
        return None


def validate_event(event: Dict[str, Any], required_fields: list) -> bool:
    """
    Validate event has required fields
    
    Args:
        event: Event dictionary
        required_fields: List of required field names
        
    Returns:
        True if all required fields present
    """
    return all(field in event for field in required_fields)


def enrich_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich event with additional metadata
    
    Args:
        event: Original event
        
    Returns:
        Enriched event
    """
    event['processing_timestamp'] = int(datetime.now().timestamp() * 1000)
    event['processing_date'] = datetime.now().strftime('%Y-%m-%d')
    return event


def format_metric_output(metrics: Dict[str, Any], meeting_id: str) -> Dict[str, Any]:
    """
    Format aggregated metrics for output
    
    Args:
        metrics: Raw metrics dictionary
        meeting_id: Meeting identifier
        
    Returns:
        Formatted metrics dictionary
    """
    return {
        'meeting_id': meeting_id,
        'timestamp': int(datetime.now().timestamp() * 1000),
        'metrics': metrics,
        'schema_version': '1.0'
    }


def calculate_percentile(values: list, percentile: float) -> float:
    """
    Calculate percentile of values
    
    Args:
        values: List of numeric values
        percentile: Percentile to calculate (0-100)
        
    Returns:
        Percentile value
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    index = int(len(sorted_values) * (percentile / 100))
    return sorted_values[min(index, len(sorted_values) - 1)]


def create_kafka_config(bootstrap_servers: str, group_id: str) -> Dict[str, str]:
    """
    Create Kafka consumer configuration
    
    Args:
        bootstrap_servers: Kafka broker addresses
        group_id: Consumer group ID
        
    Returns:
        Configuration dictionary
    """
    return {
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'latest',
        'enable.auto.commit': 'false'
    }


def create_s3_path(base_path: str, meeting_id: str, partition_date: str) -> str:
    """
    Create partitioned S3 path for output
    
    Args:
        base_path: Base S3 path
        meeting_id: Meeting identifier
        partition_date: Date for partitioning (YYYY-MM-DD)
        
    Returns:
        Full S3 path with partitions
    """
    return f"{base_path}/date={partition_date}/meeting={meeting_id}/"


class MetricsBuffer:
    """Buffer for collecting metrics before writing"""
    
    def __init__(self, max_size: int = 1000):
        self.buffer = []
        self.max_size = max_size
        
    def add(self, metric: Dict[str, Any]) -> bool:
        """
        Add metric to buffer
        
        Returns:
            True if buffer should be flushed
        """
        self.buffer.append(metric)
        return len(self.buffer) >= self.max_size
    
    def flush(self) -> list:
        """Get and clear buffer"""
        data = self.buffer.copy()
        self.buffer.clear()
        return data
    
    def size(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)
