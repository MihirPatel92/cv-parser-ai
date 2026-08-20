import google.generativeai as genai
import asyncio

class GeminiProvider:
    def __init__(self, api_key: str, model_name: str = 'gemini-1.5-flash', temperature: float = 0.1):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=model_name, generation_config={"temperature": temperature})

    async def generate(self, prompt: str) -> str:
        retries = 2
        for i in range(retries + 1):
            try:
                response = await asyncio.to_thread(self.model.generate_content, prompt)
                return response.text
            except Exception as e:
                if i == retries:
                    raise e
                await asyncio.sleep(1 * (i + 1))
