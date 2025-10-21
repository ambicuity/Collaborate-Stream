"""
S3 Uploader for Collaborate-Stream
Uploads Parquet files to S3 for long-term storage and analytics
"""
import os
import logging
from typing import Optional
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("Warning: boto3 not installed. Install with: pip install boto3")
    boto3 = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Uploader:
    """Handles uploading files to S3"""
    
    def __init__(
        self, 
        bucket_name: str = 'collaborate-stream',
        region: str = 'us-east-1',
        endpoint_url: Optional[str] = None
    ):
        """
        Initialize S3 uploader
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region
            endpoint_url: Custom endpoint URL (for MinIO or LocalStack)
        """
        if boto3 is None:
            raise ImportError("boto3 is required. Install with: pip install boto3")
        
        self.bucket_name = bucket_name
        self.region = region
        
        # Create S3 client
        if endpoint_url:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                region_name=region
            )
        else:
            self.s3_client = boto3.client('s3', region_name=region)
        
        logger.info(f"S3 uploader initialized for bucket: {bucket_name}")
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.region}
                        if self.region != 'us-east-1' else {}
                    )
                    logger.info(f"Created bucket: {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
            else:
                logger.error(f"Error checking bucket: {e}")
    
    def upload_file(
        self, 
        local_path: str, 
        s3_key: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Upload a file to S3
        
        Args:
            local_path: Local file path
            s3_key: S3 object key (path in bucket)
            metadata: Optional metadata dictionary
            
        Returns:
            True if upload successful
        """
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Uploaded {local_path} to s3://{self.bucket_name}/{s3_key}")
            return True
            
        except FileNotFoundError:
            logger.error(f"File not found: {local_path}")
            return False
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return False
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            return False
    
    def upload_directory(
        self, 
        local_dir: str, 
        s3_prefix: str = '',
        pattern: str = '*.parquet'
    ) -> int:
        """
        Upload all files matching pattern from a directory
        
        Args:
            local_dir: Local directory path
            s3_prefix: S3 key prefix
            pattern: File pattern to match
            
        Returns:
            Number of files uploaded
        """
        local_path = Path(local_dir)
        uploaded_count = 0
        
        for file_path in local_path.rglob(pattern):
            if file_path.is_file():
                # Preserve directory structure in S3
                relative_path = file_path.relative_to(local_path)
                s3_key = os.path.join(s3_prefix, str(relative_path))
                
                if self.upload_file(str(file_path), s3_key):
                    uploaded_count += 1
        
        logger.info(f"Uploaded {uploaded_count} files from {local_dir}")
        return uploaded_count
    
    def upload_partitioned_metrics(self, local_base_path: str):
        """
        Upload partitioned Parquet metrics to S3
        
        Args:
            local_base_path: Base path containing date partitions
        """
        return self.upload_directory(
            local_base_path,
            s3_prefix='metrics/',
            pattern='*.parquet'
        )
    
    def list_objects(self, prefix: str = '') -> list:
        """
        List objects in bucket with given prefix
        
        Args:
            prefix: S3 key prefix
            
        Returns:
            List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
            
        except ClientError as e:
            logger.error(f"Failed to list objects: {e}")
            return []
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3
        
        Args:
            s3_key: S3 object key
            local_path: Local file path to save
            
        Returns:
            True if download successful
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
            
            logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to {local_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def delete_object(self, s3_key: str) -> bool:
        """
        Delete an object from S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if deletion successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Deleted s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete object: {e}")
            return False


def main():
    """Example usage"""
    # For local testing with MinIO
    uploader = S3Uploader(
        bucket_name='collaborate-stream',
        endpoint_url='http://localhost:9000'  # MinIO endpoint
    )
    
    # Upload a single file
    # uploader.upload_file('/tmp/metrics.parquet', 'metrics/date=2024-01-01/metrics.parquet')
    
    # Upload partitioned metrics
    # uploader.upload_partitioned_metrics('/tmp/collaborate_stream/metrics')
    
    # List objects
    objects = uploader.list_objects('metrics/')
    print(f"Found {len(objects)} objects in metrics/")


if __name__ == "__main__":
    main()
