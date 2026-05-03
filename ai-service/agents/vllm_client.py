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

    # Map doctor names to the actual model ID served by the endpoint (crucial for Ollama)
    MODEL_MAP = {
        "Curezy AURIX": os.getenv("AURIX_MODEL", "alibayram/medgemma:4b"),
        "Curezy AURA":  os.getenv("AURA_MODEL",  "casperhansen/llama-3-8b-instruct-awq"),
        "Curezy AURIS": os.getenv("AURIS_MODEL", "mistral:7b"),
    }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True
    )
    async def query_async(self, prompt: str, model_name: str, num_predict: int = 2048,
                          use_json_schema: bool = False, temperature: float = 0.1) -> str:
        """Send a request to the appropriate vLLM/Ollama container."""
        endpoint = self.ENDPOINTS.get(model_name, self.ENDPOINTS["Curezy AURIX"])
        target_model = self.MODEL_MAP.get(model_name, "model")
        
        # Detect if we are using the Native Ollama API or OpenAI-compatible (vLLM) API
        is_native_ollama = "/api/chat" in endpoint
        is_ollama_openai = "11434/v1" in endpoint

        if is_native_ollama:
            # Native Ollama Format
            payload = {
                "model": target_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": num_predict,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
        else:
            # OpenAI Format (vLLM or Ollama OpenAI-bridge)
            payload = {
                "model": target_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": num_predict,
                "temperature": temperature,
                "top_p": 0.9,
            }
            # Only add JSON schema for vLLM (non-11434 endpoints)
            if use_json_schema and not is_ollama_openai:
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
                print(f"[Hybrid] -> {model_name} ({target_model}) @ {endpoint}")
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Extract content based on API type
                if is_native_ollama:
                    return data["message"]["content"]
                else:
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
