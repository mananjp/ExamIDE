import requests
from datetime import datetime, timedelta
import json

BASE_URL = "http://localhost:8000"

def test_create_room():
    print("Testing create_room...")
    
    # Create start time (now + 1 min)
    start_time = (datetime.now() + timedelta(minutes=1)).isoformat()
    duration = 60
    
    payload = {
        "room_name": "Test Exam Room",
        "teacher_name": "Tester",
        "language": "Python",
        "duration": duration,
        "start_time": start_time
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/rooms/create", json=payload)
        response.raise_for_status()
        data = response.json()
        
        print("Response:", json.dumps(data, indent=2))
        
        # Verify fields
        assert "duration_minutes" in data
        assert data["duration_minutes"] == duration
        assert "start_time" in data
        assert "end_time" in data
        
        # Verify end_time calculation
        start_dt = datetime.fromisoformat(data["start_time"])
        end_dt = datetime.fromisoformat(data["end_time"])
        diff = (end_dt - start_dt).total_seconds() / 60
        
        print(f"Time difference (minutes): {diff}")
        assert abs(diff - duration) < 0.1 # Allow small float error
        
        print("SUCCESS: create_room test passed!")
        return data["room_id"]
        
    except Exception as e:
        print(f"FAILURE: create_room test failed: {e}")
        return None

def test_get_room(room_id):
    print(f"\nTesting get_room for {room_id}...")
    try:
        response = requests.get(f"{BASE_URL}/api/rooms/{room_id}")
        response.raise_for_status()
        data = response.json()
        
        # Verify fields again
        assert "duration_minutes" in data
        assert "start_time" in data
        assert "end_time" in data
        
        print("SUCCESS: get_room test passed!")
    except Exception as e:
        print(f"FAILURE: get_room test failed: {e}")

if __name__ == "__main__":
    room_id = test_create_room()
    if room_id:
        test_get_room(room_id)
