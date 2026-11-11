import asyncio

from batch import INFERENCE_TIMEOUT_SECONDS, model_predict_single
from business_logic import validate_business_rules
from db import save_prediction
from fastapi import APIRouter, HTTPException, Request, status
from llm import build_scoring_explanation_prompt, call_llm
from model import MODEL_READY, MODEL_VERSION, get_recommendation, get_risk_level
from schema import (
    FarmRequest,
    LLMChatRequest,
    PredictionItem,
    PredictionResponse,
    PredictWithLLMResponse,
)

router = APIRouter(prefix="/predict-with-llm", tags=[])

@router.post(
    "",
    response_model=PredictWithLLMResponse,
    status_code=status.HTTP_200_OK,
    summary="Агроскоринг с текстовым объяснением LLM",
    description=(
        "Сначала выполняет детерминированный агроскоринг и сохраняет "
        "результат в SQLite. Затем Vireonix LLM формирует только "
        "текстовое объяснение результата. LLM не определяет risk_score."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Unknown region or invalid X-Request-ID",
        },
        status.HTTP_502_BAD_GATEWAY: {
            "description": "LLM provider error or malformed LLM response",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Model, prediction storage or LLM unavailable",
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "description": "Inference or LLM timeout",
        },
    },
)
async def predict_with_llm(
    data: FarmRequest,
    request: Request,
):
    if not MODEL_READY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is unavailable",
        )

    validate_business_rules(data)
    request_id = request.state.id
    try:
        score = await asyncio.wait_for(
            model_predict_single(data),
            timeout=INFERENCE_TIMEOUT_SECONDS
        )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Inference timeout",
        )

    risk_level = get_risk_level(score)
    recommendation = get_recommendation(risk_level)
    item = PredictionItem(
        farm_id=data.farm_id,
        risk_score=score,
        recommendation=recommendation,
        risk_level=risk_level,
        model_version=MODEL_VERSION,
    )
    await save_prediction(
        result = item.model_dump() | {"request_id": request_id},
        source="single+llm",
    )

    prompt = build_scoring_explanation_prompt(item)
    llm_result = await call_llm(
        client=request.app.state.llm_client,
        request_id=request_id,
        request_body=LLMChatRequest(prompt=prompt))

    return PredictWithLLMResponse(
        prediction=PredictionResponse(request_id=request_id, item=item),
        llm=llm_result
    )
