#!/usr/bin/env python3
"""Quick end-to-end test of the app."""
import requests
import json

API_BASE = "http://localhost:8000"

print("Testing SafeSpace end-to-end...\n")

# Test 1: Frontend accessible
print("1. Testing frontend access...")
response = requests.get(f"{API_BASE}/")
assert response.status_code == 200
assert "SafeSpace" in response.text
print("   ✓ Frontend loads")

# Test 2: Health check
print("\n2. Testing health endpoint...")
response = requests.get(f"{API_BASE}/api/health")
assert response.status_code == 200
print("   ✓ API is healthy")

# Test 3: Start session
print("\n3. Testing session start...")
response = requests.post(f"{API_BASE}/api/session/start", json={})
assert response.status_code == 200
data = response.json()
assert "session_id" in data
assert len(data["supervisors"]) == 3
print(f"   ✓ Session started: {data['session_id']}")

# Test 4: Submit input
print("\n4. Testing input submission...")
response = requests.post(
    f"{API_BASE}/api/session/input",
    json={
        "input": "I'm researching AI systems in the workplace.",
        "request_reflection": False
    }
)
assert response.status_code == 200
data = response.json()
assert data["round_number"] == 1
assert "current_impressions" in data
assert len(data["current_impressions"]) == 3
print(f"   ✓ Round 1 complete")
print(f"   ✓ Got impressions for: {', '.join(data['current_impressions'].keys())}")

# Test 5: Verify impression structure
print("\n5. Testing impression structure...")
for name, impression in data["current_impressions"].items():
    assert "stance" in impression
    assert "confidence" in impression
    assert "concerns" in impression
    print(f"   ✓ {name}: {impression['stance']}, {impression['confidence']}, {len(impression['concerns'])} concerns")

print("\n" + "="*60)
print("✅ ALL TESTS PASSED - APP IS FULLY FUNCTIONAL")
print("="*60)
print(f"\nAccess the app at: http://localhost:8000/")
