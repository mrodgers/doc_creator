"""
Tests for LLM Integration Module
"""

from unittest.mock import AsyncMock, patch

import pytest

from ai_doc_gen.core.llm_integration import LLMClient, LLMResponse


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [{
            "message": {
                "content": '{"test": "data", "confidence": 95}'
            }
        }],
        "usage": {
            "total_tokens": 100
        }
    }

@pytest.fixture
def llm_client():
    """Create LLM client instance."""
    return LLMClient(provider="openai")

@pytest.mark.asyncio
async def test_llm_client_initialization():
    """Test LLM client initialization."""
    client = LLMClient(provider="openai")
    assert client.provider_name == "openai"

    client = LLMClient(provider="anthropic")
    assert client.provider_name == "anthropic"

def test_llm_client_invalid_provider():
    """Test LLM client with invalid provider."""
    with pytest.raises(ValueError, match="Unsupported provider"):
        LLMClient(provider="invalid")

@pytest.mark.asyncio
async def test_call_llm_with_confidence(llm_client, mock_openai_response):
    """Test calling LLM with confidence scoring."""
    with patch.object(llm_client.provider.client.chat.completions, 'create') as mock_create:
        mock_create.return_value = type('Response', (), {
            'choices': [type('Choice', (), {
                'message': type('Message', (), {'content': '{"test": "data"}'})()
            })()],
            'usage': type('Usage', (), {'total_tokens': 100})()
        })()

        response = await llm_client.call_llm_with_confidence(
            system_prompt="You are a helpful assistant",
            user_prompt="Test prompt"
        )

        assert isinstance(response, LLMResponse)
        assert response.content == '{"test": "data"}'
        assert response.model_used == "gpt-4o"

@pytest.mark.asyncio
async def test_extract_structured_data(llm_client):
    """Test structured data extraction."""
    with patch.object(llm_client, 'call_llm_with_confidence',
                     new_callable=AsyncMock) as mock_call:
        mock_call.return_value = LLMResponse(
            content='{"data": [{"field": "value", "confidence": 90}]}',
            confidence=95.0,
            model_used="gpt-4o"
        )

        result = await llm_client.extract_structured_data(
            content="Test content",
            extraction_schema={"fields": ["field"]}
        )

        assert "data" in result
        assert "confidence" in result
        assert "model_used" in result

@pytest.mark.asyncio
async def test_generate_sme_questions(llm_client):
    """Test SME question generation."""
    with patch.object(llm_client, 'call_llm_with_confidence',
                     new_callable=AsyncMock) as mock_call:
        mock_call.return_value = LLMResponse(
            content='[{"question": "Test question?", "priority": "High"}]',
            confidence=95.0,
            model_used="gpt-4o"
        )

        questions = await llm_client.generate_sme_questions(
            gap_analysis={"gaps": []},
            context="Test context"
        )

        assert isinstance(questions, list)
        assert len(questions) > 0
        assert "question" in questions[0]

def test_llm_response_validation():
    """Test LLMResponse validation."""
    # Valid response
    response = LLMResponse(
        content="test",
        confidence=95.0,
        model_used="gpt-4o"
    )
    assert response.confidence == 95.0

    # Invalid confidence (should be caught by Pydantic)
    with pytest.raises(ValueError):
        LLMResponse(
            content="test",
            confidence=150.0,  # Invalid confidence
            model_used="gpt-4o"
        )
