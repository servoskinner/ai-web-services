import asyncio

from batch import INFERENCE_TIMEOUT_SECONDS, model_predict_single
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

router = APIRouter(prefix="/predict", tags=[])

@router.post(
    "",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Оценить риск хозяйства",
    description=(
        "Принимает характеристики хозяйства, "
        "выполняет валидацию, инференс модели "
        "и возвращает оценку риска."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Unknown region or invalid X-Request-ID",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Model or prediction storage unavailable",
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "description": "Inference timeout",
        },
    },
)
async def predict(
    data: FarmRequest,
    request: Request
):
    """
    Основной endpoint сервиса.
    """
    # 1. Проверяем состояние ML-модели
    if not MODEL_READY:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is temporarily unavailable"
        )

    # 2. Бизнес-валидация
    #
    # Pydantic уже проверил:
    # - типы данных;
    # - обязательность;
    # - диапазоны.
    #
    # Осталось проверить бизнес-правила (например, разрешённые регионы).
    validate_business_rules(data)
    request_id = request.state.id
  
    # 4. ИНФЕРЕНС
    try:
        score = await asyncio.wait_for(
            model_predict_single(data),
            timeout=INFERENCE_TIMEOUT_SECONDS
        )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Inference timeout"
        )

    # 5. ПОСТПРОЦЕССИНГ
    level = get_risk_level(score)
    recommendation = get_recommendation(level)

    # 7. ФОРМИРУЕМ РЕЗУЛЬТАТ
    prediction = PredictionItem(
        farm_id=data.farm_id, 
        risk_score=score, 
        risk_level=level, 
        recommendation=recommendation, 
        model_version=MODEL_VERSION
    )

    # 8. СОХРАНЯЕМ РЕЗУЛЬТАТ 
    await save_prediction(
        prediction.model_dump() | {"request_id": request_id},
        source="single",
    )

    return PredictionResponse(request_id=request_id, item=prediction)
