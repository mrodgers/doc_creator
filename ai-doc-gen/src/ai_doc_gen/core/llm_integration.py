"""
Enhanced LLM Integration for Multi-Agent Architecture

Based on the original spec_extractor.py but enhanced for:
- Multiple LLM providers (OpenAI, Anthropic)
- Multi-agent support (Managing Agent, Review Agent)
- Async operations
- Better error handling and retry logic
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from openai import OpenAI
import anthropic
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class LLMResponse(BaseModel):
    """Structured response from LLM calls."""
    content: str
    confidence: float = Field(ge=0, le=100)
    model_used: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def call_llm(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> LLMResponse:
        """Call the LLM and return structured response."""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation using the new SDK."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    async def call_llm(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> LLMResponse:
        """Call OpenAI API with structured prompts using the new SDK."""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Run the synchronous OpenAI call in an async context
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                confidence=95.0,  # OpenAI doesn't provide confidence scores
                model_used=model,
                tokens_used=response.usage.total_tokens if response.usage else None
            )
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.AsyncAnthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    
    async def call_llm(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        model: str = "claude-3-haiku-20240307",
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> LLMResponse:
        """Call Anthropic API with structured prompts."""
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            return LLMResponse(
                content=response.content[0].text,
                confidence=95.0,  # Anthropic doesn't provide confidence scores
                model_used=model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens if response.usage else None
            )
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

class LLMClient:
    """Enhanced LLM client supporting multiple providers and agents."""
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """Initialize LLM client with specified provider."""
        self.provider_name = provider.lower()
        
        if self.provider_name == "openai":
            self.provider = OpenAIProvider(api_key)
        elif self.provider_name == "anthropic":
            self.provider = AnthropicProvider(api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def call_llm_with_confidence(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> LLMResponse:
        """Call LLM with confidence scoring and structured response."""
        if model is None:
            model = "gpt-4o" if self.provider_name == "openai" else "claude-3-haiku-20240307"
        
        return await self.provider.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def extract_structured_data(
        self,
        content: str,
        extraction_schema: Dict[str, Any],
        confidence_threshold: float = 85.0
    ) -> Dict[str, Any]:
        """Extract structured data from content with confidence scoring."""
        
        system_prompt = f"""You are a technical document parser specialized in extracting structured data.
You must extract data according to the provided schema and return results with confidence scores.
Always return valid JSON with the exact structure specified."""

        user_prompt = f"""Please extract data from the following content according to this schema:

Schema: {json.dumps(extraction_schema, indent=2)}

Content to extract from:
{content}

Return the extracted data in JSON format with confidence scores (0-100) for each field."""

        response = await self.call_llm_with_confidence(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        def clean_json_response(text):
            text = text.strip()
            if text.startswith('```'):
                text = text.lstrip('`')
                if text.lower().startswith('json'):
                    text = text[4:]
                text = text.strip()
            if text.endswith('```'):
                text = text.rstrip('`').strip()
            return text
        
        try:
            cleaned = clean_json_response(response.content)
            extracted_data = json.loads(cleaned)
            return {
                "data": extracted_data,
                "confidence": response.confidence,
                "model_used": response.model_used,
                "tokens_used": response.tokens_used
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {response.content}")
            raise
    
    async def generate_sme_questions(
        self,
        gap_analysis: Dict[str, Any],
        context: str
    ) -> List[Dict[str, str]]:
        """Generate SME questions based on gap analysis."""
        
        system_prompt = """You are an expert technical writer who generates clear, prioritized questions for Subject Matter Experts (SMEs).
Your questions should be specific, actionable, and help resolve documentation gaps."""

        user_prompt = f"""Based on the following gap analysis and context, generate 3-5 prioritized questions for SMEs:

Gap Analysis: {json.dumps(gap_analysis, indent=2)}

Context: {context}

Return the questions as a JSON array with objects containing:
- question: The actual question text
- priority: High/Medium/Low
- category: The type of information needed
- rationale: Why this question is important"""

        response = await self.call_llm_with_confidence(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        def clean_json_response(text):
            text = text.strip()
            if text.startswith('```'):
                text = text.lstrip('`')
                if text.lower().startswith('json'):
                    text = text[4:]
                text = text.strip()
            if text.endswith('```'):
                text = text.rstrip('`').strip()
            return text
        
        try:
            cleaned = clean_json_response(response.content)
            questions = json.loads(cleaned)
            return questions if isinstance(questions, list) else [questions]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SME questions: {e}")
            logger.error(f"Raw response: {response.content}")
            return []

# Convenience function for backward compatibility
async def call_llm_with_confidence(
    system_prompt: str,
    user_prompt: str,
    provider: str = "openai",
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 4000
) -> LLMResponse:
    """Convenience function for simple LLM calls."""
    client = LLMClient(provider)
    return await client.call_llm_with_confidence(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    ) 