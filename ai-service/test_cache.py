import requests
import time

url = "http://localhost:8000/analyze"

# Test Case 1: Initial (Should miss and take minutes)
payload = {
    "conversation_id": "test_case_123",
    "message": "I have had a runny nose and a mild fever for the past 2 days. No other symptoms.",
    "selected_model": "council"
}

print("--- RUN 1 (Should Miss and Cache) ---")
start = time.time()
try:
    res = requests.post(url, json=payload, timeout=200)
    print(f"Status: {res.status_code}")
    print(f"Latency: {time.time() - start:.2f} seconds")
    # if it's returning the mock we need to push it through trigger stage
except Exception as e:
    print(f"Error: {e}")

# Wait a sec
time.sleep(2)

print("\n--- RUN 2 (Should Hit Cache instantly) ---")
payload2 = {
    "conversation_id": "test_case_456",
    "message": "Runny nose and mild fever for 48 hours. Nothing else.",
    "selected_model": "council"
}
start2 = time.time()
try:
    res2 = requests.post(url, json=payload2, timeout=200)
    print(f"Status: {res2.status_code}")
    ans = res2.json()
    print(f"Cached Flag: {ans.get('cached', False)}")
    print(f"Latency: {time.time() - start2:.2f} seconds")
except Exception as e:
    print(f"Error: {e}")
