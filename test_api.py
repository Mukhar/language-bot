#!/usr/bin/env python3
"""
Simple API test script to verify the healthcare bot endpoints work correctly.
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health test failed: {e}")
        return False

def test_scenario_generation():
    """Test scenario generation"""
    print("\nTesting scenario generation...")
    try:
        data = {
            "category": "emergency",
            "difficulty": "beginner"
        }
        response = requests.post(f"{BASE_URL}/scenarios/generate", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200, response.json().get('id') if response.status_code == 200 else None
    except Exception as e:
        print(f"Scenario generation test failed: {e}")
        return False, None

def test_response_submission(scenario_id):
    """Test response submission and evaluation"""
    print(f"\nTesting response submission for scenario {scenario_id}...")
    try:
        data = {
            "scenario_id": scenario_id,
            "response_text": "I would stay calm, assess the patient's vital signs, call for emergency assistance, and provide basic first aid while waiting for help to arrive."
        }
        response = requests.post(f"{BASE_URL}/responses", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Response submission test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting API tests...\n")
    
    # Give server time to start
    time.sleep(2)
    
    # Test health endpoint
    if not test_health():
        print("❌ Health test failed - server may not be running")
        return
    print("✅ Health test passed")
    
    # Test scenario generation
    scenario_success, scenario_id = test_scenario_generation()
    if not scenario_success:
        print("❌ Scenario generation test failed")
        return
    print("✅ Scenario generation test passed")
    
    # Test response submission if we have a scenario
    if scenario_id:
        if test_response_submission(scenario_id):
            print("✅ Response submission test passed")
        else:
            print("❌ Response submission test failed")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    main()