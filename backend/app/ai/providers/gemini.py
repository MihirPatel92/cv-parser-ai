import google.generativeai as genai
import asyncio
from typing import Optional


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

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={"temperature": self.temperature},
        )

    async def generate(self, prompt: str) -> str:
        retries = 2
        last_error = None
        for i in range(retries + 1):
            try:
                response = await asyncio.to_thread(self.model.generate_content, prompt)
                if hasattr(response, "text") and response.text:
                    return response.text
                elif response.candidates and response.candidates[0].content.parts:
                    return response.candidates[0].content.parts[0].text
                raise ValueError("Empty response received from Gemini model.")
            except Exception as e:
                last_error = e
                print(f"Gemini API attempt {i+1} failed: {e}")
                if i == retries:
                    raise ValueError(f"Gemini generation failed: {last_error}")
                await asyncio.sleep(1.5 * (i + 1))
        raise ValueError(f"Gemini generation failed: {last_error}")
