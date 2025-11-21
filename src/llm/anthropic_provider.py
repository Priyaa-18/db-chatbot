"""
Anthropic (Claude) LLM provider implementation.
"""
import json
from typing import Dict, Any, Optional
from anthropic import AsyncAnthropic
from src.llm.base import LLMProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = AsyncAnthropic(api_key=api_key)
        logger.info("Initialized Anthropic provider", model=model)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Generate completion from Claude."""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                system=system_prompt if system_prompt else "",
                messages=messages
            )
            
            result = response.content[0].text
            
            logger.info(
                "Generated completion",
                model=self.model,
                prompt_length=len(prompt),
                response_length=len(result),
                tokens_used=response.usage.input_tokens + response.usage.output_tokens
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
        """Generate structured JSON output from Claude."""
        # Add JSON formatting instructions to system prompt
        json_instruction = """
You must respond with valid JSON only. Do not include any text outside the JSON structure.
Do not use markdown code blocks or backticks. Output raw JSON directly.
"""
        
        if response_format:
            json_instruction += f"\n\nThe JSON should follow this structure:\n{json.dumps(response_format, indent=2)}"
        
        full_system_prompt = f"{system_prompt}\n\n{json_instruction}" if system_prompt else json_instruction
        
        try:
            response_text = await self.generate(
                prompt=prompt,
                system_prompt=full_system_prompt,
                **kwargs
            )
            
            # Clean up response - remove markdown if present
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            logger.info("Generated structured output", keys=list(result.keys()))
            return result
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e), response=response_text[:500])
            raise ValueError(f"LLM did not return valid JSON: {str(e)}")
        except Exception as e:
            logger.error("Failed to generate structured output", error=str(e))
            raise
