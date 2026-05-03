import requests
import time
import json

def test_cloud_run_analysis():
    url = "https://ai-service-abuuzdzvbq-uc.a.run.app/analyze"
    
    payload = {
        "patient_id": "test-patient-001",
        "symptoms_text": "High fever for 3 days, severe headache especially behind the eyes, intense muscle and joint pain (breakbone fever feel), mild skin rash on trunk, and feeling very weak.",
        "medical_history_text": "No chronic illnesses. Living in Indore, MP. Recent mosquito bites reported in the locality.",
        "age": 28,
        "gender": "male"
    }
    
    print(f" Sending request to Cloud Run: {url}")
    print(f" Symptoms: {payload['symptoms_text']}")
    print("-" * 50)
    
    start_time = time.time()
    try:
        # Long timeout because council analysis is slow
        response = requests.post(url, json=payload, timeout=600) 
        duration = time.time() - start_time
        
        print(f"[TIME] Total Time: {duration:.2f} seconds")
        print(f" Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n[OK] Analysis Complete!")
            print(json.dumps(result, indent=2)[:1000] + "...")
        else:
            print(f"[FAIL] Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"[FAIL] Failed to reach Cloud Run: {e}")

if __name__ == "__main__":
    test_cloud_run_analysis()
