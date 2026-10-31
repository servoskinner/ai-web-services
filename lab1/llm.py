import logging
import time

import httpx
from fastapi import HTTPException, status
from constants import LLM_BASE_URL
from schema import LLMChatRequest, LLMChatResponse, PredictionItem

async def call_llm(
    client: httpx.AsyncClient,
    request_id: str,
    request_body: LLMChatRequest
) -> LLMChatResponse:
    """
    Асинхронный запрос к API Vireonix для инференса большой языковой модели.
    """

    url = f"{LLM_BASE_URL}/chat/completions"

    payload = {
        "model": request_body.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты -- помощник сервиса по оценке риска"
                    " кредитования сельскохозяйственных предприятий."
                    " отвечай кратко и ёмко, избегай любезностей и лишних"
                    " оборотов речи. Запрещено изменять risk_score и risk_level,"
                    " делать предположения, придумывать необоснованные данными"
                    " аргументы."
                )
            },
            {
                "role": "user",
                "content": request_body.prompt,
            },
        ],
        "temperature": request_body.temperature,
        "max_tokens": request_body.max_tokens,
    }

    request_started = time.perf_counter()

    try:
        response = await client.post(
            url,
            headers={
                "Content-Type": "application/json"
            },
            json=payload,
        )
    except httpx.TimeoutException as e:
        logging.getLogger().exception(
            f"LLM timeout (request id {request_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LLM request timeout"
        ) from e

    except httpx.RequestError as e:
        logging.getLogger().exception(
            f"LLM connection error (request id {request_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service is unavailable"
        ) from e

    latency_ms = (time.perf_counter() - request_started) * 1000.0

    if response.status_code != status.HTTP_200_OK:
        logging.getLogger().error(
            f"LLM upstream error (request id: {request_id} status: "
            f"{response.status_code}, body = {response.text[:500]})"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "LLM provider returned an error "
                f"(HTTP {response.status_code})"
            )
        )

    try:
        data = response.json()

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM provider returned invalid JSON"
        ) from e

    choices = data.get("choices", [])

    if not choices:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM response does not contain choices"
        )

    choice = choices[0]
    message = choice.get("message", {})
    content = message.get("content")

    if not content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM response does not contain message content"
        )

    return LLMChatResponse(
        request_id=request_id,
        requested_model=request_body.model,
        returned_model=data.get("model"),
        answer=content,
        reasoning=message.get("reasoning_content"),
        finish_reason=choice.get("finish_reason"),
        usage=data.get("usage"),
        latency_ms=round(latency_ms, 2)
    )


def build_scoring_explanation_prompt(
    prediction : PredictionItem,
) -> str:
    """
    Формирует промпт из результата скоринга.
    """
    return (
        "Сформируй краткое объяснение для оператора банка "
        "по результату алгоритмического агроскоринга.\n\n"
        f"risk_score: {prediction.risk_score}\n"
        f"risk_level: {prediction.risk_level}\n"
        f"базовая рекомендация: {prediction.recommendation}\n\n"
        "Требования к ответу:\n"
        "1. 2-4 предложения.\n"
        "2. Не меняй категорию риска.\n"
        "3. Не придумывай дополнительные факторы риска.\n"
        "4. Укажи, что решение требует применения правил банка "
        "и при необходимости проверки оператором."
    )