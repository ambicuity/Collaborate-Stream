"""
Tests for Flink Aggregation Logic
"""
import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flink.windowed_aggregator import (
    WindowedMeetingAggregator,
    TumblingWindowAggregator,
    SlidingWindowAggregator
)


class TestWindowedMeetingAggregator(unittest.TestCase):
    """Test cases for windowed aggregation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.aggregator = WindowedMeetingAggregator(window_size_seconds=30)
    
    def test_create_accumulator(self):
        """Test accumulator initialization"""
        acc = self.aggregator.create_accumulator()
        
        self.assertIsInstance(acc, dict)
        self.assertEqual(len(acc['active_users']), 0)
        self.assertEqual(acc['message_count'], 0)
        self.assertEqual(acc['total_latency'], 0)
    
    def test_add_user_join_event(self):
        """Test adding user join event"""
        acc = self.aggregator.create_accumulator()
        
        event = {
            'user_id': 'user_1',
            'meeting_id': 'meeting_1',
            'event_type': 'join'
        }
        
        acc = self.aggregator.add(acc, event)
        
        self.assertEqual(len(acc['active_users']), 1)
        self.assertIn('user_1', acc['active_users'])
        self.assertEqual(acc['join_count'], 1)
    
    def test_add_user_leave_event(self):
        """Test adding user leave event"""
        acc = self.aggregator.create_accumulator()
        
        # First join
        join_event = {
            'user_id': 'user_1',
            'meeting_id': 'meeting_1',
            'event_type': 'join'
        }
        acc = self.aggregator.add(acc, join_event)
        
        # Then leave
        leave_event = {
            'user_id': 'user_1',
            'meeting_id': 'meeting_1',
            'event_type': 'leave'
        }
        acc = self.aggregator.add(acc, leave_event)
        
        self.assertEqual(len(acc['active_users']), 0)
        self.assertEqual(acc['leave_count'], 1)
    
    def test_add_chat_event(self):
        """Test adding chat event"""
        acc = self.aggregator.create_accumulator()
        
        event = {
            'user_id': 'user_1',
            'meeting_id': 'meeting_1',
            'event_type': 'message'
        }
        
        acc = self.aggregator.add(acc, event)
        
        self.assertEqual(acc['message_count'], 1)
    
    def test_add_meeting_event_with_latency(self):
        """Test adding meeting event with latency"""
        acc = self.aggregator.create_accumulator()
        
        event = {
            'meeting_id': 'meeting_1',
            'event_type': 'network_lag',
            'latency_ms': 150
        }
        
        acc = self.aggregator.add(acc, event)
        
        self.assertEqual(acc['total_latency'], 150)
        self.assertEqual(acc['latency_count'], 1)
    
    def test_get_result_basic(self):
        """Test getting result from accumulator"""
        acc = self.aggregator.create_accumulator()
        
        # Add some events
        acc = self.aggregator.add(acc, {
            'user_id': 'user_1',
            'event_type': 'join'
        })
        acc = self.aggregator.add(acc, {
            'user_id': 'user_2',
            'event_type': 'join'
        })
        acc = self.aggregator.add(acc, {
            'event_type': 'message'
        })
        
        result = self.aggregator.get_result(acc)
        
        self.assertEqual(result['active_users'], 2)
        self.assertEqual(result['message_count'], 1)
        self.assertIn('engagement_score', result)
        self.assertIn('meeting_health', result)
    
    def test_calculate_engagement_score(self):
        """Test engagement score calculation"""
        # Test with high engagement
        score = self.aggregator._calculate_engagement(100, 10, 50)
        self.assertGreater(score, 70)
        
        # Test with low engagement
        score = self.aggregator._calculate_engagement(0, 1, 300)
        self.assertLess(score, 30)
    
    def test_determine_health(self):
        """Test health determination"""
        # Good health
        health = self.aggregator._determine_health(50, 5)
        self.assertEqual(health, 'good')
        
        # Fair health
        health = self.aggregator._determine_health(150, 5)
        self.assertEqual(health, 'fair')
        
        # Poor health
        health = self.aggregator._determine_health(250, 5)
        self.assertEqual(health, 'poor')
        
        # Inactive
        health = self.aggregator._determine_health(0, 0)
        self.assertEqual(health, 'inactive')
    
    def test_merge_accumulators(self):
        """Test merging two accumulators"""
        acc1 = self.aggregator.create_accumulator()
        acc1['active_users'] = {'user_1', 'user_2'}
        acc1['message_count'] = 10
        
        acc2 = self.aggregator.create_accumulator()
        acc2['active_users'] = {'user_2', 'user_3'}
        acc2['message_count'] = 5
        
        merged = self.aggregator.merge(acc1, acc2)
        
        self.assertEqual(len(merged['active_users']), 3)
        self.assertEqual(merged['message_count'], 15)


class TestTumblingWindowAggregator(unittest.TestCase):
    """Test tumbling window aggregator"""
    
    def test_initialization(self):
        """Test tumbling window initialization"""
        aggregator = TumblingWindowAggregator(window_size_seconds=30)
        self.assertEqual(aggregator.window_size, 30)


class TestSlidingWindowAggregator(unittest.TestCase):
    """Test sliding window aggregator"""
    
    def test_initialization(self):
        """Test sliding window initialization"""
        aggregator = SlidingWindowAggregator(
            window_size_seconds=60,
            slide_seconds=15
        )
        self.assertEqual(aggregator.window_size, 60)
        self.assertEqual(aggregator.slide_size, 15)


if __name__ == '__main__':
    unittest.main()
