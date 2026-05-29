import json
from dataclasses import dataclass
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError, APIConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import get_settings
from app.schemas.qualification import QualifyRequest, QualificationResult
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger
from app.prompt.qualification_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = get_logger(__name__)


@dataclass(frozen=True)
class AIQualificationResponse:
    result: QualificationResult
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


# Retry on transient OpenAI errors: rate limits, timeouts, and connection failures.
# with exponential back-off (2s, 4s, 8s)
_RETRYABLE = retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError))

_retry = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=_RETRYABLE,
)


async def qualify_creator(request: QualifyRequest) -> AIQualificationResponse:
    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        raise AIServiceError("OPENAI_API_KEY is not configured.")

    posts_text = (
        "\n".join(f"- {p}" for p in request.recent_posts)
        if request.recent_posts
        else "- No recent posts provided"
    )

    user_message = USER_PROMPT_TEMPLATE.format(
        platform=request.platform,
        followers=request.followers,
        bio=request.creator_bio,
        posts=posts_text,
    )

    # AsyncOpenAI is fully non-blocking — safe to await inside FastAPI's event loop
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    @_retry
    async def _call_openai():
        return await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )

    try:
        response = await _call_openai()
        raw_text = response.choices[0].message.content.strip()
        data = json.loads(raw_text)
        result = QualificationResult(**data)
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)

        logger.info(
            "ai_qualification_done",
            score=result.score,
            is_qualified=result.is_qualified,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        return AIQualificationResponse(
            result=result,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    except json.JSONDecodeError as exc:
        logger.error("ai_response_parse_error", error=str(exc))
        raise AIServiceError(f"AI returned non-JSON response: {exc}") from exc
    except APIError as exc:
        logger.error("openai_api_error", error=str(exc))
        raise AIServiceError(f"OpenAI API error: {exc}") from exc
    except Exception as exc:
        logger.error("ai_service_unexpected_error", error=str(exc))
        raise AIServiceError(f"Unexpected AI service error: {exc}") from exc
