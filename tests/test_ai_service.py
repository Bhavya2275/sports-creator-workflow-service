import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.schemas.qualification import QualifyRequest, QualificationResult
from app.services.ai_service import qualify_creator
from app.core.exceptions import AIServiceError


SAMPLE_REQUEST = QualifyRequest(
    creator_bio="Professional cricket commentator and sports analyst with 5 years experience.",
    platform="youtube",
    followers=500000,
    recent_posts=["Live match analysis #Cricket", "Top 10 IPL moments", "Interview with national team coach"],
)

MOCK_AI_RESPONSE = """{
  "score": 87.5,
  "is_qualified": true,
  "confidence": "HIGH",
  "category": "sports_commentary",
  "reasoning": "Strong sports relevance with high follower count and cricket-focused content.",
  "strengths": ["High follower count", "Niche sports focus"],
  "weaknesses": ["Limited platform diversity"],
  "sports_relevance": "Excellent fit for a cricket-focused sports platform.",
  "recommended_next_state": "QUALIFIED",
  "suggested_outreach_angle": "Invite for cricket analysis and fan engagement campaigns.",
  "risk_flags": ["Limited platform diversity"]
}"""


@pytest.mark.asyncio
async def test_qualify_creator_success():
    mock_choice = MagicMock()
    mock_choice.message.content = MOCK_AI_RESPONSE
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 610
    mock_response.usage.completion_tokens = 170
    mock_response.usage.total_tokens = 780

    with patch("app.services.ai_service.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        # AsyncOpenAI.chat.completions.create is a coroutine
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.ai_service.get_settings") as mock_settings:
            mock_settings.return_value.OPENAI_API_KEY = "test-key"
            mock_settings.return_value.OPENAI_MODEL = "gpt-5.4-mini"

            response = await qualify_creator(SAMPLE_REQUEST)

    result = response.result
    assert isinstance(result, QualificationResult)
    assert result.score == 87.5
    assert result.is_qualified is True
    assert result.confidence == "HIGH"
    assert result.recommended_next_state == "QUALIFIED"
    assert len(result.strengths) == 2
    assert response.prompt_tokens == 610
    assert response.completion_tokens == 170
    assert response.total_tokens == 780


@pytest.mark.asyncio
async def test_qualify_creator_no_api_key():
    with patch("app.services.ai_service.get_settings") as mock_settings:
        mock_settings.return_value.OPENAI_API_KEY = ""

        with pytest.raises(AIServiceError) as exc_info:
            await qualify_creator(SAMPLE_REQUEST)

    assert "OPENAI_API_KEY" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_qualify_creator_invalid_json():
    mock_choice = MagicMock()
    mock_choice.message.content = "not valid json at all"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("app.services.ai_service.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.ai_service.get_settings") as mock_settings:
            mock_settings.return_value.OPENAI_API_KEY = "test-key"
            mock_settings.return_value.OPENAI_MODEL = "gpt-5.4-mini"

            with pytest.raises(AIServiceError):
                await qualify_creator(SAMPLE_REQUEST)
