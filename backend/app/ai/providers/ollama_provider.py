import httpx
import asyncio
import json

class OllamaProvider:
    def __init__(self, base_url: str = 'http://localhost:11434', model_name: str = 'deepseek-r1', temperature: float = 0.1):
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature

    async def generate(self, prompt: str) -> str:
        retries = 2
        async with httpx.AsyncClient() as client:
            for i in range(retries + 1):
                try:
                    payload = {
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature
                        }
                    }
                    response = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=120.0)
                    response.raise_for_status()
                    data = response.json()
                    return data.get("response", "")
                except Exception as e:
                    if i == retries:
                        raise e
                    await asyncio.sleep(1 * (i + 1))
