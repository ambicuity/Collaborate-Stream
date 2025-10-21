"""
Tests for Kafka Producer
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from kafka.producer import CollaborateStreamProducer


class TestCollaborateStreamProducer(unittest.TestCase):
    """Test cases for Kafka producer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.meeting_id = "test_meeting_001"
        self.user_id = "test_user_001"
    
    @patch('kafka.producer.KafkaProducer')
    def test_producer_initialization(self, mock_kafka_producer):
        """Test producer initializes correctly"""
        producer = CollaborateStreamProducer(bootstrap_servers='localhost:9092')
        
        self.assertIsNotNone(producer)
        self.assertEqual(producer.user_pool[0], 'user_0')
        self.assertEqual(len(producer.user_pool), 1000)
        self.assertEqual(len(producer.active_meetings), 0)
    
    @patch('kafka.producer.KafkaProducer')
    def test_generate_user_event(self, mock_kafka_producer):
        """Test user event generation"""
        producer = CollaborateStreamProducer()
        
        event = producer.generate_user_event(self.meeting_id, self.user_id, "join")
        
        self.assertEqual(event['meeting_id'], self.meeting_id)
        self.assertEqual(event['user_id'], self.user_id)
        self.assertEqual(event['event_type'], 'join')
        self.assertIn('event_id', event)
        self.assertIn('timestamp', event)
    
    @patch('kafka.producer.KafkaProducer')
    def test_generate_chat_event(self, mock_kafka_producer):
        """Test chat event generation"""
        producer = CollaborateStreamProducer()
        
        event = producer.generate_chat_event(self.meeting_id, self.user_id)
        
        self.assertEqual(event['meeting_id'], self.meeting_id)
        self.assertEqual(event['user_id'], self.user_id)
        self.assertIn(event['event_type'], ['message', 'reaction', 'emoji'])
        self.assertIn('event_id', event)
        self.assertIn('timestamp', event)
    
    @patch('kafka.producer.KafkaProducer')
    def test_generate_meeting_event(self, mock_kafka_producer):
        """Test meeting event generation"""
        producer = CollaborateStreamProducer()
        
        event = producer.generate_meeting_event(self.meeting_id)
        
        self.assertEqual(event['meeting_id'], self.meeting_id)
        self.assertIn(event['event_type'], 
                     ['video_start', 'video_stop', 'screen_share', 'network_lag'])
        self.assertIn('event_id', event)
        self.assertIn('timestamp', event)
    
    @patch('kafka.producer.KafkaProducer')
    def test_simulate_meeting_lifecycle(self, mock_kafka_producer):
        """Test meeting lifecycle simulation"""
        mock_producer_instance = Mock()
        mock_kafka_producer.return_value = mock_producer_instance
        
        producer = CollaborateStreamProducer()
        producer.simulate_meeting_lifecycle(self.meeting_id)
        
        # Check that meeting was created with users
        self.assertIn(self.meeting_id, producer.active_meetings)
        self.assertGreater(len(producer.active_meetings[self.meeting_id]), 0)
        
        # Check that events were sent
        self.assertTrue(mock_producer_instance.send.called)


class TestEventValidation(unittest.TestCase):
    """Test event validation"""
    
    @patch('kafka.producer.KafkaProducer')
    def test_user_event_fields(self, mock_kafka_producer):
        """Test user event has all required fields"""
        producer = CollaborateStreamProducer()
        event = producer.generate_user_event("m1", "u1", "join")
        
        required_fields = ['event_id', 'user_id', 'meeting_id', 'event_type', 'timestamp']
        for field in required_fields:
            self.assertIn(field, event)
    
    @patch('kafka.producer.KafkaProducer')
    def test_chat_event_fields(self, mock_kafka_producer):
        """Test chat event has all required fields"""
        producer = CollaborateStreamProducer()
        event = producer.generate_chat_event("m1", "u1")
        
        required_fields = ['event_id', 'user_id', 'meeting_id', 'event_type', 'timestamp']
        for field in required_fields:
            self.assertIn(field, event)
    
    @patch('kafka.producer.KafkaProducer')
    def test_meeting_event_fields(self, mock_kafka_producer):
        """Test meeting event has all required fields"""
        producer = CollaborateStreamProducer()
        event = producer.generate_meeting_event("m1")
        
        required_fields = ['event_id', 'meeting_id', 'event_type', 'timestamp']
        for field in required_fields:
            self.assertIn(field, event)


if __name__ == '__main__':
    unittest.main()
