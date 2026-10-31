import asyncio

from batch import INFERENCE_TIMEOUT_SECONDS, QUEUE, InferenceTask
from business_logic import validate_business_rules
from db import save_prediction
from fastapi import APIRouter, HTTPException, Request, status
from model import (
    MODEL_READY,
    MODEL_VERSION,
    get_recommendation,
    get_risk_level,
)
from schema import FarmRequest, PredictionItem, PredictionResponse

router = APIRouter(prefix="/predict-queued", tags=[])

@router.post(
    "",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Динамический пакетный инференс",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Unknown region or invalid X-Request-ID",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "Inference queue full, retry after Retry-After seconds",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Model or prediction storage unavailable",
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "description": "Inference timeout",
        },
    },
)
async def predict_queued(
    data: FarmRequest,
    request: Request
):
    """Обработка запросов с динамическими батчами"""
    if not MODEL_READY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is unavailable",
        )

    validate_business_rules(data)
    request_id = request.state.id

    loop = asyncio.get_running_loop()
    future = loop.create_future()

    task = InferenceTask(
        data=data,
        request_id=request_id,
        future=future
    )

    try:
        QUEUE.put_nowait(task)
    except asyncio.QueueFull:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Inference queue is full. Try again later",
            headers={"Retry-After": "1"},
        )

    try:
        score = await asyncio.wait_for(
            future,
            timeout=INFERENCE_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        if not future.done():
            future.cancel()

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Inference timeout",
        )
    
    level = get_risk_level(score)
    rec = get_recommendation(level)
    result = PredictionResponse(
        request_id=request_id,
        item=PredictionItem(
            farm_id=data.farm_id,
            risk_score=score,
            risk_level=level,
            recommendation=rec,
            model_version=MODEL_VERSION,
        )
    )

    await save_prediction(
        result.item.model_dump() | {"request_id": request_id},
        source="queued",
    )

    return result