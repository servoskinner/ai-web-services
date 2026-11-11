from fastapi import APIRouter, Request, status
from llm import call_llm
from schema import LLMChatRequest, LLMChatResponse

router = APIRouter(prefix="/llm", tags=[])

@router.post(
    "/chat",
    response_model=LLMChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Прямой запрос к LLM",
    description="Отправляет промпт в публичный OpenAI-совместимый API.",
    responses={
        status.HTTP_502_BAD_GATEWAY: {
            "description": "LLM provider error or malformed LLM response",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "LLM unavailable",
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "description": "LLM timeout",
        },
    },
)
async def llm_chat(
    data : LLMChatRequest,
    request : Request,
):
    return await call_llm(
        client=request.app.state.llm_client,
        request_id=request.state.id,
        request_body=data
    )