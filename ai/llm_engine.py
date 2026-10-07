import httpx, json
from typing import Optional

SYSTEM_PROMPT = """You are an expert MDM (Mobile Device Management) AI assistant managing 20-100 Android devices.
Capabilities: natural language → device actions, threat analysis, MITRE ATT&CK mapping, policy generation.
Always respond with structured JSON when asked. Be concise and security-focused."""

class LLMEngine:
    def __init__(self, model: str = "mistral"):
        self.model    = model
        self.base_url = "http://localhost:11434"

    def query_sync(self, prompt: str, system: str = None) -> str:
        payload = {"model": self.model,
                   "messages": [{"role":"system","content": system or SYSTEM_PROMPT},
                                 {"role":"user","content": prompt}],
                   "stream": False, "options": {"temperature": 0.1}}
        try:
            with httpx.Client(timeout=60.0) as client:
                r = client.post(f"{self.base_url}/api/chat", json=payload)
                return r.json()["message"]["content"]
        except Exception as e:
            return f"[LLM unavailable: {e}]"

    async def query(self, prompt: str, system: str = None) -> str:
        payload = {"model": self.model,
                   "messages": [{"role":"system","content": system or SYSTEM_PROMPT},
                                 {"role":"user","content": prompt}],
                   "stream": False, "options": {"temperature": 0.1}}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(f"{self.base_url}/api/chat", json=payload)
                return r.json()["message"]["content"]
        except Exception as e:
            return f"[LLM unavailable: {e}]"

    def extract_json(self, text: str) -> Optional[dict]:
        try:
            start = text.find("{"); end = text.rfind("}") + 1
            return json.loads(text[start:end])
        except: return None
