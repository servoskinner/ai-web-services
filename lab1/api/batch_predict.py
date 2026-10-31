import asyncio
import time

from batch import INFERENCE_TIMEOUT_SECONDS, model_predict_batch
from business_logic import validate_business_rules
from db import save_predictions_batch
from fastapi import APIRouter, HTTPException, Request, status
from model import (
    MODEL_READY,
    MODEL_VERSION,
    get_recommendation,
    get_risk_level,
)
from schema import BatchPredictionResponse, BatchRequest, PredictionItem

router = APIRouter(prefix="/batch-predict", tags=[])

@router.post(
    "",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Явный пакетный инференс",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Unknown region in any item or invalid X-Request-ID",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Model or prediction storage unavailable",
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "description": "Batch inference timeout",
        },
    },
)
async def batch_predict(
    batch: BatchRequest,
    request: Request
):
    """Явная батчевая обработка запросов"""
    if not MODEL_READY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is unavailable",
        )

    for item in batch.items:
        validate_business_rules(item)

    request_id = request.state.id
    start_time = time.perf_counter()

    try:
        scores = await asyncio.wait_for(
            model_predict_batch(batch.items),
            timeout=INFERENCE_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Batch inference timeout",
        )

    response_items = []

    for data, score in zip(batch.items, scores):
        level = get_risk_level(score)
        rec = get_recommendation(level)

        response_items.append(PredictionItem(
            farm_id=data.farm_id,
            risk_score=score,
            risk_level=level,
            recommendation=rec,
            model_version=MODEL_VERSION
        ))

    await save_predictions_batch(
        request_id=request_id,
        items=[item.model_dump() for item in response_items],
    )

    processing_time_ms = (time.perf_counter() - start_time) * 1000
    return BatchPredictionResponse(
        request_id=request_id,
        batch_size=len(batch.items),
        processing_time_ms=round(processing_time_ms, 2),
        items=response_items
    )
        