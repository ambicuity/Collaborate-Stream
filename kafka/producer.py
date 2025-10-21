"""
Kafka Producer for Collaborate-Stream
Generates synthetic SaaS usage events for real-time analytics
"""
import json
import random
import time
import uuid
from datetime import datetime
from typing import Dict, List

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
except ImportError:
    print("Warning: kafka-python not installed. Install with: pip install kafka-python")
    KafkaProducer = None


class CollaborateStreamProducer:
    """Produces synthetic user, chat, and meeting events to Kafka topics"""
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: Kafka broker address
        """
        if KafkaProducer is None:
            raise ImportError("kafka-python is required. Install with: pip install kafka-python")
            
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        
        # Simulation state
        self.active_meetings: Dict[str, List[str]] = {}
        self.user_pool = [f"user_{i}" for i in range(1000)]
        
    def generate_user_event(self, meeting_id: str, user_id: str, event_type: str) -> dict:
        """Generate a user event (join/leave)"""
        return {
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "meeting_id": meeting_id,
            "event_type": event_type,
            "timestamp": int(time.time() * 1000)
        }
    
    def generate_chat_event(self, meeting_id: str, user_id: str) -> dict:
        """Generate a chat event (message/reaction)"""
        event_type = random.choice(["message", "reaction", "emoji"])
        return {
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "meeting_id": meeting_id,
            "event_type": event_type,
            "message_length": random.randint(10, 500) if event_type == "message" else None,
            "timestamp": int(time.time() * 1000)
        }
    
    def generate_meeting_event(self, meeting_id: str) -> dict:
        """Generate a meeting event (video start/stop, screen share, lag)"""
        event_type = random.choice(["video_start", "video_stop", "screen_share", "network_lag"])
        return {
            "event_id": str(uuid.uuid4()),
            "meeting_id": meeting_id,
            "event_type": event_type,
            "latency_ms": random.randint(20, 500) if event_type == "network_lag" else None,
            "packet_loss": random.uniform(0, 5) if event_type == "network_lag" else None,
            "timestamp": int(time.time() * 1000)
        }
    
    def simulate_meeting_lifecycle(self, meeting_id: str = None) -> None:
        """Simulate a complete meeting lifecycle"""
        if meeting_id is None:
            meeting_id = f"meeting_{uuid.uuid4().hex[:8]}"
        
        # Users join
        num_users = random.randint(2, 10)
        users = random.sample(self.user_pool, num_users)
        self.active_meetings[meeting_id] = users
        
        for user in users:
            event = self.generate_user_event(meeting_id, user, "join")
            self.producer.send("user_events", key=meeting_id, value=event)
        
        print(f"Meeting {meeting_id} started with {num_users} users")
        
    def generate_activity(self, meeting_id: str) -> None:
        """Generate random activity for an active meeting"""
        if meeting_id not in self.active_meetings or not self.active_meetings[meeting_id]:
            return
            
        users = self.active_meetings[meeting_id]
        
        # Generate chat events
        if random.random() < 0.7:  # 70% chance of chat activity
            user = random.choice(users)
            event = self.generate_chat_event(meeting_id, user)
            self.producer.send("chat_events", key=meeting_id, value=event)
        
        # Generate meeting events
        if random.random() < 0.3:  # 30% chance of meeting event
            event = self.generate_meeting_event(meeting_id)
            self.producer.send("meeting_events", key=meeting_id, value=event)
    
    def run_simulation(self, duration_seconds: int = 300, events_per_second: int = 100):
        """
        Run continuous event generation
        
        Args:
            duration_seconds: How long to run the simulation
            events_per_second: Target event generation rate
        """
        print(f"Starting simulation for {duration_seconds} seconds...")
        print(f"Target rate: {events_per_second} events/second")
        
        start_time = time.time()
        event_count = 0
        
        # Create initial meetings
        for _ in range(10):
            self.simulate_meeting_lifecycle()
        
        while time.time() - start_time < duration_seconds:
            iteration_start = time.time()
            
            # Generate events
            for _ in range(events_per_second):
                if self.active_meetings:
                    meeting_id = random.choice(list(self.active_meetings.keys()))
                    self.generate_activity(meeting_id)
                    event_count += 1
                
                # Occasionally start new meetings
                if random.random() < 0.01:
                    self.simulate_meeting_lifecycle()
                
                # Occasionally end meetings
                if random.random() < 0.005 and self.active_meetings:
                    meeting_to_end = random.choice(list(self.active_meetings.keys()))
                    for user in self.active_meetings[meeting_to_end]:
                        event = self.generate_user_event(meeting_to_end, user, "leave")
                        self.producer.send("user_events", key=meeting_to_end, value=event)
                    del self.active_meetings[meeting_to_end]
                    print(f"Meeting {meeting_to_end} ended")
            
            # Sleep to maintain rate
            elapsed = time.time() - iteration_start
            sleep_time = max(0, 1.0 - elapsed)
            time.sleep(sleep_time)
            
            # Progress update
            if event_count % 10000 == 0:
                print(f"Generated {event_count} events, Active meetings: {len(self.active_meetings)}")
        
        print(f"\nSimulation complete!")
        print(f"Total events generated: {event_count}")
        print(f"Average rate: {event_count / duration_seconds:.2f} events/second")
        
    def close(self):
        """Close the producer"""
        self.producer.flush()
        self.producer.close()


def main():
    """Main entry point"""
    producer = CollaborateStreamProducer(bootstrap_servers='localhost:9092')
    
    try:
        # Run simulation for 5 minutes at 100 events/second
        producer.run_simulation(duration_seconds=300, events_per_second=100)
    except KeyboardInterrupt:
        print("\nStopping producer...")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
