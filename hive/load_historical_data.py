"""
Load Historical Data into Hive
Utility script to populate Hive tables with sample data
"""
import random
import csv
from datetime import datetime, timedelta
from typing import List, Dict
import os


def generate_user_profiles(num_users: int = 1000) -> List[Dict]:
    """Generate sample user profile data"""
    users = []
    organizations = [f"org_{i}" for i in range(1, 51)]
    
    for i in range(1, num_users + 1):
        created_date = datetime.now() - timedelta(days=random.randint(1, 365))
        last_login = datetime.now() - timedelta(hours=random.randint(1, 720))
        
        users.append({
            'user_id': f'user_{i}',
            'username': f'user_{i}@example.com',
            'email': f'user_{i}@example.com',
            'organization_id': random.choice(organizations),
            'created_at': int(created_date.timestamp() * 1000),
            'last_login': int(last_login.timestamp() * 1000),
            'user_role': random.choice(['admin', 'member', 'guest']),
            'timezone': random.choice(['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo']),
            'is_active': random.choice([True, True, True, False])  # 75% active
        })
    
    return users


def generate_organizations(num_orgs: int = 50) -> List[Dict]:
    """Generate sample organization data"""
    orgs = []
    plan_types = ['free', 'starter', 'professional', 'enterprise']
    
    for i in range(1, num_orgs + 1):
        plan = random.choice(plan_types)
        max_users = {
            'free': 10,
            'starter': 50,
            'professional': 200,
            'enterprise': 1000
        }[plan]
        
        features = []
        if plan in ['professional', 'enterprise']:
            features.extend(['recording', 'analytics'])
        if plan == 'enterprise':
            features.extend(['sso', 'custom_branding', 'dedicated_support'])
        
        orgs.append({
            'organization_id': f'org_{i}',
            'organization_name': f'Organization {i}',
            'plan_type': plan,
            'max_users': max_users,
            'features': ','.join(features) if features else '',
            'created_at': int((datetime.now() - timedelta(days=random.randint(30, 730))).timestamp() * 1000),
            'billing_status': random.choice(['active', 'active', 'active', 'trial'])
        })
    
    return orgs


def generate_meeting_history(num_meetings: int = 10000) -> List[Dict]:
    """Generate sample historical meeting data"""
    meetings = []
    organizations = [f"org_{i}" for i in range(1, 51)]
    
    for i in range(1, num_meetings + 1):
        start_time = datetime.now() - timedelta(days=random.randint(1, 90), hours=random.randint(0, 23))
        duration = random.randint(300, 7200)  # 5 min to 2 hours
        end_time = start_time + timedelta(seconds=duration)
        
        meetings.append({
            'meeting_id': f'meeting_{i}',
            'organization_id': random.choice(organizations),
            'start_time': int(start_time.timestamp() * 1000),
            'end_time': int(end_time.timestamp() * 1000),
            'duration_seconds': duration,
            'max_participants': random.randint(2, 20),
            'total_messages': random.randint(0, 500),
            'avg_latency_ms': random.uniform(20, 300),
            'meeting_type': random.choice(['video', 'audio', 'screen_share']),
            'year': start_time.year,
            'month': start_time.month,
            'day': start_time.day
        })
    
    return meetings


def write_to_csv(data: List[Dict], filename: str):
    """Write data to CSV file"""
    if not data:
        return
    
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Written {len(data)} records to {filename}")


def main():
    """Main execution"""
    print("Generating historical data...")
    
    # Create output directory
    output_dir = '/tmp/collaborate_stream_data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate and write data
    print("\nGenerating user profiles...")
    users = generate_user_profiles(1000)
    write_to_csv(users, f'{output_dir}/user_profiles.csv')
    
    print("\nGenerating organizations...")
    orgs = generate_organizations(50)
    write_to_csv(orgs, f'{output_dir}/organization_plans.csv')
    
    print("\nGenerating meeting history...")
    meetings = generate_meeting_history(10000)
    write_to_csv(meetings, f'{output_dir}/meeting_history.csv')
    
    print("\n" + "="*50)
    print("Data generation complete!")
    print(f"Output directory: {output_dir}")
    print("="*50)
    print("\nNext steps:")
    print("1. Convert CSV to Parquet (use pyarrow or spark)")
    print("2. Upload to S3: aws s3 cp <file> s3://collaborate-stream/hive/")
    print("3. Run Hive DDL to create tables")
    print("4. Verify with: SELECT COUNT(*) FROM user_profiles;")


if __name__ == "__main__":
    main()
