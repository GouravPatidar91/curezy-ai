import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class RunpodClient:
    """Connects Curezy Backend to the Production RunPod Serverless GPU."""
    
    def __init__(self):
        self.api_key = os.getenv("RUNPOD_API_KEY")
        self.endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
        self.is_configured = bool(self.api_key and self.endpoint_id)
        
        if self.is_configured:
            self.url = f"https://api.runpod.ai/v2/{self.endpoint_id}/runsync"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

    async def run_council_analysis(self, patient_state: dict, mode: str = "council", model_key: str = None) -> dict:
        """
        Sends the exact patient state to RunPod, which runs Preprocessing, 
        Clinical Reasoning, and Uncertainty Analysis on the GPU and returns the final JSON.
        """
        if not self.is_configured:
            raise ValueError("RunPod credentials not found in environment.")

        payload = {
            "input": {
                "mode": mode,
                "model_key": model_key,
                **patient_state
            }
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(self.url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("status") == "COMPLETED" and result.get("output", {}).get("success"):
                return result["output"]
            else:
                raise RuntimeError(f"RunPod execution failed: {result}")
