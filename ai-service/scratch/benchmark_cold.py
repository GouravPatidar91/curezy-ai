import httpx
import time
import json
import sys

def benchmark_backend():
    url = "http://localhost:8000/debug/council"
    payload = {
        "symptoms": "Severe abdominal pain in the lower right side, nausea, and low-grade fever for 12 hours.",
        "age": 24,
        "gender": "female"
    }
    
    print("\n" + "="*60)
    print("CUREZY AI - CLINICAL DIAGNOSTIC BENCHMARK")
    print("="*60)
    print(f"INPUT SYMPTOMS: {payload['symptoms']}")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(url, json=payload)
            
            if response.status_code == 404:
                print("Error: The /debug/council endpoint was removed for security.")
                print("Please use the production /analyze endpoint.")
                return

            response.raise_for_status()
            result = response.json()
            
            end_time = time.time()
            total_latency = end_time - start_time
            
            print(f"DIAGNOSIS RECEIVED IN: {total_latency:.2f} seconds")
            print("-" * 60)
            
            if result.get("success"):
                analysis = result.get("analysis", {})
                conditions = analysis.get("top_3_conditions", [])
                
                if conditions:
                    top = conditions[0]
                    print(f"PRIMARY DIAGNOSIS: {top.get('condition')}")
                    print(f"PROBABILITY:       {top.get('probability')}%")
                    print(f"CONFIDENCE:        {top.get('confidence')}%")
                    
                    print("\nCLINICAL EVIDENCE:")
                    for ev in top.get("evidence", []):
                        print(f" - {ev}")
                    
                    print(f"\nREASONING: {top.get('reasoning')}")
                else:
                    print("No conditions found in the response JSON.")
            else:
                print(f"BACKEND ERROR: {result.get('error')}")
                
    except Exception as e:
        print(f"CRITICAL FAILURE: {str(e)}")

    print("="*60 + "\n")

if __name__ == "__main__":
    benchmark_backend()
