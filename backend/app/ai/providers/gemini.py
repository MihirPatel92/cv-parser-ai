import asyncio
import httpx
from typing import Optional, List
import google.generativeai as genai


class GeminiProvider:
    def __init__(
        self,
        api_key: Optional[str],
        model_name: str = "gemini-1.5-flash",
        temperature: float = 0.1,
    ):
        if not api_key or not str(api_key).strip():
            raise ValueError(
                "Gemini API key is not configured. Please open AI Configuration in the dashboard and enter your Gemini API key."
            )
        self.api_key = str(api_key).strip()
        self.model_name = model_name or "gemini-1.5-flash"
        self.temperature = float(temperature) if temperature is not None else 0.1
        self._working_model: Optional[str] = None

        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            print(f"genai configure note: {e}")

    async def _call_rest_api(self, model: str, prompt: str) -> str:
        """Direct REST fallback to Google Generative Language API."""
        clean_model = model.replace("models/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": 4096,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise ValueError(f"HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError(f"No candidates returned: {data}")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise ValueError(f"Empty parts in candidate: {candidates[0]}")
            return parts[0].get("text", "")

    async def generate(self, prompt: str) -> str:
        # Candidate model names to try in order
        candidate_models = [
            self.model_name,
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-pro-latest",
            "gemini-pro",
        ]

        if self._working_model and self._working_model in candidate_models:
            candidate_models.remove(self._working_model)
            candidate_models.insert(0, self._working_model)

        # 1. Try discovering available models from list_models
        try:
            discovered = await asyncio.to_thread(genai.list_models)
            supported = [
                m.name.replace("models/", "")
                for m in discovered
                if hasattr(m, "supported_generation_methods")
                and "generateContent" in m.supported_generation_methods
            ]
            if supported:
                # Put flash models first, followed by others
                flash_first = [m for m in supported if "flash" in m] + [
                    m for m in supported if "flash" not in m
                ]
                candidate_models = flash_first + [
                    m for m in candidate_models if m not in flash_first
                ]
        except Exception as list_err:
            print(f"list_models note: {list_err}")

        last_error = None
        for model in candidate_models:
            clean_name = model.replace("models/", "")
            # Attempt 1: Try SDK GenerativeModel
            try:
                gen_model = genai.GenerativeModel(
                    model_name=clean_name,
                    generation_config={"temperature": self.temperature},
                )
                response = await asyncio.to_thread(gen_model.generate_content, prompt)
                if hasattr(response, "text") and response.text:
                    self._working_model = clean_name
                    return response.text
                elif response.candidates and response.candidates[0].content.parts:
                    self._working_model = clean_name
                    return response.candidates[0].content.parts[0].text
            except Exception as sdk_err:
                last_error = sdk_err
                print(f"SDK attempt for model {clean_name} failed: {sdk_err}")

            # Attempt 2: Try direct REST API for this model
            try:
                text = await self._call_rest_api(clean_name, prompt)
                if text:
                    self._working_model = clean_name
                    return text
            except Exception as rest_err:
                last_error = rest_err
                print(f"REST attempt for model {clean_name} failed: {rest_err}")

        raise ValueError(
            f"Gemini generation failed on all models. Last error: {last_error}"
        )
