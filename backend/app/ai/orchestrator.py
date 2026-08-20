import json
import re
from ..db.models import AIModelConfig
from .prompts import CV_EXTRACTION_PROMPT, PLACEHOLDER_MAPPING_PROMPT, STRUCTURE_ANALYSIS_PROMPT, FREEFORM_MAPPING_PROMPT
from .providers.gemini import GeminiProvider
from .providers.openai_provider import OpenAIProvider
from .providers.ollama_provider import OllamaProvider

class AIOrchestrator:
    def __init__(self, config: AIModelConfig):
        self.config = config
        self.provider = self.get_provider()

    def get_provider(self):
        if self.config.provider == 'gemini':
            return GeminiProvider(self.config.api_key_encrypted, self.config.model_name, float(self.config.temperature))
        elif self.config.provider == 'openai':
            return OpenAIProvider(self.config.api_key_encrypted, self.config.model_name, float(self.config.temperature))
        elif self.config.provider == 'ollama':
            return OllamaProvider(self.config.ollama_base_url, self.config.model_name, float(self.config.temperature))
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

    def parse_json_response(self, response: str) -> dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON block using regex if model included markdown
            match = re.search(r'```json(.*?)```', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except:
                    pass
            match = re.search(r'```(.*?)```', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except:
                    pass
            # Fallback
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                try:
                    return json.loads(response[start:end+1])
                except:
                    pass
            raise ValueError("Could not parse JSON from AI response")

    async def extract_cv_data(self, cv_text: str) -> dict:
        prompt = CV_EXTRACTION_PROMPT.format(cv_text=cv_text)
        response = await self.provider.generate(prompt)
        return self.parse_json_response(response)

    async def map_to_placeholders(self, placeholders: list, cv_data: dict) -> dict:
        prompt = PLACEHOLDER_MAPPING_PROMPT.format(
            placeholders_list=json.dumps(placeholders),
            cv_data_json=json.dumps(cv_data)
        )
        response = await self.provider.generate(prompt)
        return self.parse_json_response(response)

    async def analyze_template_structure(self, template_text: str) -> dict:
        prompt = STRUCTURE_ANALYSIS_PROMPT.format(template_text=template_text)
        response = await self.provider.generate(prompt)
        return self.parse_json_response(response)

    async def freeform_map(self, template_structure: str, cv_data: dict) -> dict:
        prompt = FREEFORM_MAPPING_PROMPT.format(
            template_structure=template_structure,
            cv_data_json=json.dumps(cv_data)
        )
        response = await self.provider.generate(prompt)
        return self.parse_json_response(response)
