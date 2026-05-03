import os
import asyncio
import time
import json
import sys
from dotenv import load_dotenv

# Add the ai-service directory to sys.path so we can import internal modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.clinical_reasoner import ClinicalReasoner

async def main():
    print("Initializing Clinical Council Test (GCP Backend)...")
    
    # 1. Initialize Reasoner
    # This will read OLLAMA_HOST from .env
    reasoner = ClinicalReasoner()
    
    # 2. Prepare Indian context patient state (Dengue symptoms)
    patient_state = {
        "patient_id": "test-patient-001",
        "symptoms_text": "High fever for 3 days, severe headache especially behind the eyes, intense muscle and joint pain (breakbone fever feel), mild skin rash on trunk, and feeling very weak.",
        "medical_history_text": "No chronic illnesses. Living in Indore, MP. Recent mosquito bites reported in the locality.",
        "age": 28,
        "gender": "male",
        "symptoms": ["high fever", "headache", "pain behind eyes", "muscle pain", "joint pain", "rash", "weakness"],
        "opqrst": {
            "onset": "3 days ago, sudden",
            "provocation": "movement makes joint pain worse",
            "quality": "aching, sharp",
            "region": "whole body, eyes",
            "severity": "8/10",
            "timing": "constant"
        }
    }
    
    print(f"\nInput Symptoms: {patient_state['symptoms_text']}")
    print(f"Location: Indore, MP (India-First Context)")
    print("-" * 50)
    
    # 3. Run Analysis and Measure Time
    start_time = time.time()
    try:
        # We don't provide a progress_callback here to keep it simple for terminal output
        result = await reasoner.analyze(patient_state)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # 4. Output Results
        print("\n" + "="*50)
        print("TEST RESULTS")
        print("="*50)
        print(f"Total Execution Time: {duration:.2f} seconds")
        print(f"Overall Confidence: {result.consensus_confidence}%")
        print(f"Agents Agreed: {result.agents_agreed}")
        
        print("\nTop 3 Conditions:")
        for i, cond in enumerate(result.top_3_conditions):
            print(f"  {i+1}. {cond.condition} ({cond.probability}%)")
            print(f"     Evidence: {', '.join(cond.evidence[:2])}...")
            
        print("\nReasoning Summary:")
        print(result.reasoning_summary)
        
        print("\nSafety Flags:")
        for flag in result.safety_flags:
            print(f"  - {flag}")
            
        print("\nDiagnostic Plan:")
        for step in getattr(result, 'diagnostic_plan', []):
            print(f"  - {step}")
            
        print("\nCounterfactuals:")
        for cf in getattr(result, 'counterfactuals', []):
            print(f"  - {cf}")

            
        print("="*50)
        
    except Exception as e:
        print(f"\n[FAIL] Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
