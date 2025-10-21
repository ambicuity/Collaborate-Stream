"""
Parquet Writer for Collaborate-Stream
Writes aggregated metrics to Parquet format for efficient storage and querying
"""
import os
from typing import List, Dict, Any
from datetime import datetime
import logging

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    print("Warning: PyArrow not installed. Install with: pip install pyarrow")
    pa = None
    pq = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParquetWriter:
    """Writes metrics data to Parquet files with partitioning"""
    
    def __init__(self, base_path: str = '/tmp/collaborate_stream/metrics'):
        """
        Initialize Parquet writer
        
        Args:
            base_path: Base directory for Parquet files
        """
        if pa is None:
            raise ImportError("PyArrow is required. Install with: pip install pyarrow")
        
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        logger.info(f"Parquet writer initialized at: {base_path}")
    
    def create_schema(self) -> pa.Schema:
        """Define Parquet schema for meeting metrics"""
        return pa.schema([
            ('meeting_id', pa.string()),
            ('timestamp', pa.int64()),
            ('active_users', pa.int32()),
            ('message_count', pa.int32()),
            ('avg_latency_ms', pa.float64()),
            ('join_count', pa.int32()),
            ('leave_count', pa.int32()),
            ('churn_rate', pa.float64()),
            ('engagement_score', pa.float64()),
            ('meeting_health', pa.string()),
            ('video_starts', pa.int32()),
            ('screen_shares', pa.int32()),
            ('window_size_seconds', pa.int32()),
            ('date_partition', pa.string())
        ])
    
    def write_batch(self, metrics: List[Dict[str, Any]], partition_date: str = None):
        """
        Write a batch of metrics to Parquet
        
        Args:
            metrics: List of metric dictionaries
            partition_date: Date partition (YYYY-MM-DD), defaults to today
        """
        if not metrics:
            logger.warning("No metrics to write")
            return
        
        if partition_date is None:
            partition_date = datetime.now().strftime('%Y-%m-%d')
        
        # Add partition column to each record
        for metric in metrics:
            metric['date_partition'] = partition_date
        
        # Convert to PyArrow table
        schema = self.create_schema()
        table = self._dict_list_to_table(metrics, schema)
        
        # Create partitioned path
        partition_path = os.path.join(self.base_path, f'date={partition_date}')
        os.makedirs(partition_path, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'metrics_{timestamp}.parquet'
        filepath = os.path.join(partition_path, filename)
        
        # Write Parquet file
        pq.write_table(table, filepath, compression='snappy')
        logger.info(f"Written {len(metrics)} metrics to {filepath}")
        
        return filepath
    
    def write_partitioned(self, metrics: List[Dict[str, Any]]):
        """
        Write metrics with automatic date partitioning
        
        Args:
            metrics: List of metric dictionaries with timestamp field
        """
        # Group metrics by date
        partitioned_metrics = {}
        
        for metric in metrics:
            timestamp = metric.get('timestamp', int(datetime.now().timestamp() * 1000))
            date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
            
            if date not in partitioned_metrics:
                partitioned_metrics[date] = []
            partitioned_metrics[date].append(metric)
        
        # Write each partition
        files_written = []
        for date, date_metrics in partitioned_metrics.items():
            filepath = self.write_batch(date_metrics, date)
            files_written.append(filepath)
        
        logger.info(f"Written {len(files_written)} partitioned files")
        return files_written
    
    def _dict_list_to_table(self, data: List[Dict[str, Any]], schema: pa.Schema) -> pa.Table:
        """Convert list of dictionaries to PyArrow table"""
        # Prepare data for each column
        arrays = []
        for field in schema:
            column_data = [row.get(field.name) for row in data]
            arrays.append(pa.array(column_data, type=field.type))
        
        return pa.Table.from_arrays(arrays, schema=schema)
    
    def read_parquet(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Read Parquet file back to list of dictionaries
        
        Args:
            filepath: Path to Parquet file
            
        Returns:
            List of metric dictionaries
        """
        table = pq.read_table(filepath)
        return table.to_pylist()
    
    def read_partition(self, partition_date: str) -> List[Dict[str, Any]]:
        """
        Read all metrics for a specific date partition
        
        Args:
            partition_date: Date partition (YYYY-MM-DD)
            
        Returns:
            List of all metrics for that date
        """
        partition_path = os.path.join(self.base_path, f'date={partition_date}')
        
        if not os.path.exists(partition_path):
            logger.warning(f"Partition not found: {partition_path}")
            return []
        
        all_metrics = []
        for filename in os.listdir(partition_path):
            if filename.endswith('.parquet'):
                filepath = os.path.join(partition_path, filename)
                metrics = self.read_parquet(filepath)
                all_metrics.extend(metrics)
        
        logger.info(f"Read {len(all_metrics)} metrics from {partition_date}")
        return all_metrics


def main():
    """Example usage"""
    writer = ParquetWriter()
    
    # Sample metrics
    sample_metrics = [
        {
            'meeting_id': 'meeting_001',
            'timestamp': int(datetime.now().timestamp() * 1000),
            'active_users': 5,
            'message_count': 42,
            'avg_latency_ms': 85.5,
            'join_count': 5,
            'leave_count': 0,
            'churn_rate': 0.0,
            'engagement_score': 72.5,
            'meeting_health': 'good',
            'video_starts': 5,
            'screen_shares': 1,
            'window_size_seconds': 30
        }
    ]
    
    # Write metrics
    filepath = writer.write_batch(sample_metrics)
    print(f"Wrote metrics to: {filepath}")
    
    # Read back
    read_metrics = writer.read_parquet(filepath)
    print(f"Read back {len(read_metrics)} metrics")


if __name__ == "__main__":
    main()
