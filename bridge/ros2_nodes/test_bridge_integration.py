#!/usr/bin/env python3
"""
Test ROS2-MAVSDK Bridge Integration with Mock Data
"""

import json
import time
import requests
from datetime import datetime

def test_mavsdk_integration():
    """Test bridge integration with MAVSDK"""
    base_url = "http://localhost:5002"
    
    print("🧪 Testing MAVSDK Integration...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ MAVSDK Writer health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to MAVSDK Writer: {e}")
        return False
    
    # Test 2: Send takeoff command
    takeoff_cmd = {
        "type": "takeoff",
        "agent": "test_bridge",
        "altitude": 20.0
    }
    
    try:
        response = requests.post(f"{base_url}/command", json=takeoff_cmd, timeout=5)
        if response.status_code == 200:
            print("✅ Takeoff command sent successfully")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Takeoff command failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending takeoff: {e}")
    
    # Test 3: Send goto command
    goto_cmd = {
        "type": "goto",
        "agent": "test_bridge",
        "latitude": -6.2088,
        "longitude": 106.8456,
        "altitude": 25.0
    }
    
    try:
        response = requests.post(f"{base_url}/command", json=goto_cmd, timeout=5)
        if response.status_code == 200:
            print("✅ Goto command sent successfully")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Goto command failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending goto: {e}")
    
    # Test 4: Send spray command
    spray_cmd = {
        "type": "spray",
        "agent": "test_bridge",
        "latitude": -6.2088,
        "longitude": 106.8456,
        "flow_rate": 5.0,
        "duration": 10.0
    }
    
    try:
        response = requests.post(f"{base_url}/command", json=spray_cmd, timeout=5)
        if response.status_code == 200:
            print("✅ Spray command sent successfully")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Spray command failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending spray: {e}")
    
    # Test 5: Check status
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            print("✅ Status check passed")
            print(f"Status: {response.json()}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking status: {e}")
    
    print("🎉 MAVSDK Integration Test Complete!")
    return True

def simulate_disease_detection():
    """Simulate disease detection and spray scenario"""
    print("\n🔬 Simulating Disease Detection Scenario...")
    
    base_url = "http://localhost:5002"
    
    # Simulate disease location
    disease_location = {
        "latitude": -6.2088,
        "longitude": 106.8456
    }
    
    print(f"📍 Disease detected at: {disease_location['latitude']}, {disease_location['longitude']}")
    
    # Step 1: Goto disease location
    goto_cmd = {
        "type": "goto",
        "agent": "detection_system",
        "latitude": disease_location['latitude'],
        "longitude": disease_location['longitude'],
        "altitude": 20.0
    }
    
    try:
        response = requests.post(f"{base_url}/command", json=goto_cmd, timeout=5)
        if response.status_code == 200:
            print("✅ Drone navigating to disease location...")
            time.sleep(2)  # Simulate travel time
        else:
            print(f"❌ Navigation failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Navigation error: {e}")
        return
    
    # Step 2: Start spraying
    spray_cmd = {
        "type": "spray",
        "agent": "detection_system",
        "latitude": disease_location['latitude'],
        "longitude": disease_location['longitude'],
        "flow_rate": 5.0,
        "duration": 10.0
    }
    
    try:
        response = requests.post(f"{base_url}/command", json=spray_cmd, timeout=5)
        if response.status_code == 200:
            print("✅ Started spraying treatment...")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Spraying failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Spraying error: {e}")
    
    print("🎯 Disease Treatment Scenario Complete!")

if __name__ == "__main__":
    # Test basic integration
    if test_mavsdk_integration():
        # Simulate disease detection scenario
        simulate_disease_detection()
