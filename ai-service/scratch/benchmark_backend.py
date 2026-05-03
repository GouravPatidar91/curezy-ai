import httpx
import time
import json

def benchmark_backend():
    # url = "http://localhost:8000/debug/council"
    url = "http://34.28.213.87:8000/debug/council"
    payload = {
        "symptoms": "High fever, headache, joint pain, and skin rash. I live in Indore.",
        "age": 28,
        "gender": "male"
    }
    
    print("\n" + "="*50)
    print("CUREZY AI -- BACKEND LATENCY BENCHMARK")
    print("="*50)
    print(f"Endpoint: {url}")
    print(f"Symptoms: {payload['symptoms']}")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            end_time = time.time()
            total_latency = end_time - start_time
            
            print(f"\n[OK] BACKEND RESPONSE RECEIVED")
            print(f"[TIME]  Total Latency: {total_latency:.2f} seconds")
            print("-" * 50)
            
            if result.get("success"):
                analysis = result.get("analysis", {})
                print(f"Diagnosis: {analysis.get('top_3_conditions', [{}])[0].get('condition', 'Unknown')}")
                print(f"Confidence: {analysis.get('consensus_confidence', 0):.1f}%")
                
                # New Latency Telemetry
                breakdown = analysis.get("latency_breakdown")
                if breakdown:
                    print("\nLATENCY BREAKDOWN:")
                    for phase in breakdown.get("phases", []):
                        print(f"  - {phase['phase']:<25}: {phase['duration_s']}s")
                    
                    if breakdown.get("models"):
                        print("\nMODEL PERFORMANCE:")
                        for model in breakdown["models"]:
                            print(f"  - {model['model']:<15}: {model['duration_s']}s ({model['chars_per_sec']} chars/s)")
            else:
                print(f"[FAIL] Error: {result.get('error')}")
                
    except Exception as e:
        print(f"[FAIL] Connection Failed: {e}")

    print("="*50 + "\n")

if __name__ == "__main__":
    # Wait a bit for server to spin up
    time.sleep(5)
    benchmark_backend()
