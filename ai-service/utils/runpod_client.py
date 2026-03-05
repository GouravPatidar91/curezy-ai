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

    def _extract_output(self, result):
        # Shape A: direct, B: success/analysis, C: array, D: double wrapped
        output = result.get("output")
        if not output: return None
        
        if isinstance(output, dict) and "output" in output and isinstance(output["output"], dict):
            output = output["output"]
            
        if isinstance(output, list) and len(output) > 0 and isinstance(output[0], dict):
            output = output[0]
            
        return output

    def _is_valid_output(self, output):
        if not output or not isinstance(output, dict): return False
        if "analysis" in output or "clinical_analysis" in output: return True
        if "top_3_conditions" in output or "conditions" in output: return True
        return output.get("success") is True

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

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Initial synchronous request
            response = await client.post(self.url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            job_id = result.get("id")
            
            # If it's already done (hot start)
            output = self._extract_output(result)
            if result.get("status") == "COMPLETED" and self._is_valid_output(output):
                return output
                
            # If we need to wait / poll (cold start or long inference)
            if result.get("status") in ["IN_PROGRESS", "IN_QUEUE"]:
                import asyncio
                status_url = f"https://api.runpod.ai/v2/{self.endpoint_id}/status/{job_id}"
                
                print(f"[RunPodClient] Job {job_id} is {result.get('status')}. Polling for completion...")
                
                for _ in range(60): # wait up to ~3 minutes
                    await asyncio.sleep(3)
                    status_res = await client.get(status_url, headers=self.headers)
                    status_res.raise_for_status()
                    
                    poll_data = status_res.json()
                    status = poll_data.get("status")
                    
                    if status == "COMPLETED":
                        poll_out = self._extract_output(poll_data)
                        if self._is_valid_output(poll_out):
                            print(f"[RunPodClient] Job {job_id} Completed!")
                            return poll_out
                        else:
                            raise RuntimeError(f"RunPod execution failed internally: {poll_data}")
                    elif status == "FAILED":
                        raise RuntimeError(f"RunPod job FAILED: {poll_data}")
                        
            raise RuntimeError(f"RunPod execution timed out or failed: {result}")
