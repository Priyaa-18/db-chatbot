"""
OpenAI LLM provider implementation.
"""
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from src.llm.base import LLMProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI GPT LLM provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key)
        logger.info("Initialized OpenAI provider", model=model)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Generate completion from GPT."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens)
            )
            
            result = response.choices[0].message.content
            
            logger.info(
                "Generated completion",
                model=self.model,
                prompt_length=len(prompt),
                response_length=len(result),
                tokens_used=response.usage.total_tokens
            )
            
            return result
            
        except Exception as e:
            logger.error("Failed to generate completion", error=str(e))
            raise
    
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Generate structured JSON output from GPT."""
        # Use OpenAI's JSON mode
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add JSON instruction to prompt
            json_prompt = f"{prompt}\n\nRespond with valid JSON only."
            messages.append({"role": "user", "content": json_prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            logger.info("Generated structured output", keys=list(result.keys()))
            return result
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e))
            raise ValueError(f"LLM did not return valid JSON: {str(e)}")
        except Exception as e:
            logger.error("Failed to generate structured output", error=str(e))
            raise
