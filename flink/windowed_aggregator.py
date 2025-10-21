"""
Windowed Aggregator for Flink
Implements custom aggregation logic for different window types
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class WindowedMeetingAggregator:
    """
    Custom aggregator for meeting metrics with windowed operations
    Supports tumbling and sliding windows
    """
    
    def __init__(self, window_size_seconds: int = 30):
        self.window_size = window_size_seconds
        self.metrics = {}
        
    def create_accumulator(self) -> Dict[str, Any]:
        """Initialize empty accumulator"""
        return {
            'active_users': set(),
            'message_count': 0,
            'total_latency': 0,
            'latency_count': 0,
            'join_count': 0,
            'leave_count': 0,
            'video_starts': 0,
            'screen_shares': 0,
            'window_start': None,
            'window_end': None
        }
    
    def add(self, accumulator: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """Add event to accumulator"""
        event_type = event.get('event_type', '')
        
        # Process user events
        if event_type in ['join', 'leave']:
            if event_type == 'join':
                accumulator['active_users'].add(event['user_id'])
                accumulator['join_count'] += 1
            else:
                accumulator['active_users'].discard(event['user_id'])
                accumulator['leave_count'] += 1
        
        # Process chat events
        elif event_type in ['message', 'reaction', 'emoji']:
            accumulator['message_count'] += 1
        
        # Process meeting events
        elif event_type == 'network_lag':
            if event.get('latency_ms'):
                accumulator['total_latency'] += event['latency_ms']
                accumulator['latency_count'] += 1
        elif event_type == 'video_start':
            accumulator['video_starts'] += 1
        elif event_type == 'screen_share':
            accumulator['screen_shares'] += 1
            
        return accumulator
    
    def get_result(self, accumulator: Dict[str, Any]) -> Dict[str, Any]:
        """Extract final result from accumulator"""
        avg_latency = (
            accumulator['total_latency'] / accumulator['latency_count']
            if accumulator['latency_count'] > 0 else 0
        )
        
        active_user_count = len(accumulator['active_users'])
        churn_rate = (
            (accumulator['join_count'] + accumulator['leave_count']) / 
            max(active_user_count, 1)
        )
        
        # Calculate engagement score
        engagement_score = self._calculate_engagement(
            accumulator['message_count'],
            active_user_count,
            avg_latency
        )
        
        # Determine meeting health
        meeting_health = self._determine_health(avg_latency, active_user_count)
        
        return {
            'active_users': active_user_count,
            'message_count': accumulator['message_count'],
            'avg_latency_ms': avg_latency,
            'join_count': accumulator['join_count'],
            'leave_count': accumulator['leave_count'],
            'churn_rate': churn_rate,
            'video_starts': accumulator['video_starts'],
            'screen_shares': accumulator['screen_shares'],
            'engagement_score': engagement_score,
            'meeting_health': meeting_health,
            'window_size_seconds': self.window_size
        }
    
    def merge(self, acc1: Dict[str, Any], acc2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two accumulators (for sliding windows)"""
        # Handle None values for window_start and window_end
        ws1 = acc1.get('window_start')
        ws2 = acc2.get('window_start')
        if ws1 is None and ws2 is None:
            window_start = None
        elif ws1 is None:
            window_start = ws2
        elif ws2 is None:
            window_start = ws1
        else:
            window_start = min(ws1, ws2)
            
        we1 = acc1.get('window_end')
        we2 = acc2.get('window_end')
        if we1 is None and we2 is None:
            window_end = None
        elif we1 is None:
            window_end = we2
        elif we2 is None:
            window_end = we1
        else:
            window_end = max(we1, we2)
        
        return {
            'active_users': acc1['active_users'].union(acc2['active_users']),
            'message_count': acc1['message_count'] + acc2['message_count'],
            'total_latency': acc1['total_latency'] + acc2['total_latency'],
            'latency_count': acc1['latency_count'] + acc2['latency_count'],
            'join_count': acc1['join_count'] + acc2['join_count'],
            'leave_count': acc1['leave_count'] + acc2['leave_count'],
            'video_starts': acc1['video_starts'] + acc2['video_starts'],
            'screen_shares': acc1['screen_shares'] + acc2['screen_shares'],
            'window_start': window_start,
            'window_end': window_end
        }
    
    def _calculate_engagement(self, messages: int, users: int, latency: float) -> float:
        """
        Calculate composite engagement score
        
        Formula: 
        - 40% message activity (normalized to 100 msgs/window)
        - 30% user participation (normalized to 10 users)
        - 30% network quality (inverse of latency, normalized to 500ms)
        """
        message_score = min(messages / 100.0, 1.0) * 40
        user_score = min(users / 10.0, 1.0) * 30
        latency_score = max(0, (1 - latency / 500.0)) * 30 if latency > 0 else 30
        
        return round(message_score + user_score + latency_score, 2)
    
    def _determine_health(self, latency: float, users: int) -> str:
        """Determine meeting health status"""
        if users == 0:
            return 'inactive'
        elif latency > 200:
            return 'poor'
        elif latency > 100:
            return 'fair'
        else:
            return 'good'


class SlidingWindowAggregator(WindowedMeetingAggregator):
    """Aggregator for sliding windows with overlap"""
    
    def __init__(self, window_size_seconds: int = 60, slide_seconds: int = 15):
        super().__init__(window_size_seconds)
        self.slide_size = slide_seconds
        logger.info(f"Sliding window: {window_size_seconds}s window, {slide_seconds}s slide")


class TumblingWindowAggregator(WindowedMeetingAggregator):
    """Aggregator for tumbling windows (non-overlapping)"""
    
    def __init__(self, window_size_seconds: int = 30):
        super().__init__(window_size_seconds)
        logger.info(f"Tumbling window: {window_size_seconds}s")
