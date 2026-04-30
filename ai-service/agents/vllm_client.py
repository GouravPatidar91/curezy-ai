import os
import json
import httpx
from typing import Optional, Dict

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class VLLMCouncilClient:
    """
    High-performance drop-in replacement for the CouncilLLMClient.
    Routes to vLLM's OpenAI-compatible API instead of Ollama.
    """

    ENDPOINTS = {
        "Curezy AURIX": os.getenv("AURIX_VLLM_URL", "http://localhost:8001/v1/chat/completions"),
        "Curezy AURA":  os.getenv("AURA_VLLM_URL",  "http://localhost:8002/v1/chat/completions"),
        "Curezy AURIS": os.getenv("AURIS_VLLM_URL", "http://localhost:8003/v1/chat/completions"),
    }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def query_async(self, prompt: str, model_name: str, num_predict: int = 2048,
                          use_json_schema: bool = False, temperature: float = 0.1) -> str:
        """Send a request to the appropriate vLLM container."""
        # Note: 'model_name' here is the doctor name or raw model name depending on who calls it.
        # We need to map doctor names to endpoints. If it's a direct model name, default to AURIX.
        endpoint = self.ENDPOINTS.get(model_name, self.ENDPOINTS["Curezy AURIX"])
        
        payload = {
            "model": "model",  # vLLM will serve whatever model it loaded
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": num_predict,
            "temperature": temperature,
            "top_p": 0.9,
            "frequency_penalty": 0.1,  # roughly equivalent to repeat_penalty
        }

        # Phase 1: Enforce Guided Decoding (Structured Output)
        if use_json_schema:
            # Import inside function to avoid circular import since reasoner imports this file
            from agents.clinical_reasoner import CONDITION_JSON_SCHEMA
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "diagnosis",
                    "schema": CONDITION_JSON_SCHEMA,
                    "strict": True
                }
            }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                print(f"[vLLM] → {model_name} @ {endpoint}")
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            print(f"[vLLM] Error querying {model_name}: {exc}")
            return "{}"

    def parse_json(self, text: str) -> dict:
        """Find the last JSON object in text (handles CoT + JSON mixed output)."""
        if not text or not text.strip(): return {}
        # Strategy 1: Last braced block
        last = text.rfind("}")
        if last != -1:
            depth, start = 0, last
            for i in range(last, -1, -1):
                if text[i] == "}": depth += 1
                elif text[i] == "{":
                    depth -= 1
                    if depth == 0: start = i; break
            try:
                r = json.loads(text[start:last+1])
                if r: return r
            except: pass
        # Strategy 2: ```json block
        if "```json" in text:
            try:
                s = text[text.find("```json")+7:]
                e = s.find("```")
                if e != -1: return json.loads(s[:e].strip())
            except: pass
        # Strategy 3: Fix common issues
        try:
            s, e = text.find("{"), text.rfind("}")+1
            if s != -1 and e > s:
                chunk = text[s:e].replace("'",'"').replace("True","true").replace("False","false").replace("None","null")
                return json.loads(chunk)
        except: pass
        print(f"[Council] JSON parse failed on: {text[:150]}")
        return {}
