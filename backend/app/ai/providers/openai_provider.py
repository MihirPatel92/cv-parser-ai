from openai import AsyncOpenAI
import asyncio

class OpenAIProvider:
    def __init__(self, api_key: str, model_name: str = 'gpt-4o-mini', temperature: float = 0.1):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature

    async def generate(self, prompt: str) -> str:
        retries = 2
        for i in range(retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature
                )
                return response.choices[0].message.content
            except Exception as e:
                if i == retries:
                    raise e
                await asyncio.sleep(1 * (i + 1))
