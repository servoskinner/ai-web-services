import logging
import uuid

from fastapi import APIRouter, HTTPException, status

from constants import *
from model import calculate_risk, get_recommendation, get_risk_level, predictions
from schema import *

router = APIRouter(prefix="/predict", tags=[])
logger = logging.getLogger(__name__)

@router.post(
    "",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Оценить риск хозяйства",
    description=(
        "Принимает характеристики хозяйства, "
        "выполняет валидацию, инференс модели "
        "и возвращает оценку риска."
    )
)
def predict(request: FarmRequest) -> PredictionResponse:
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
    if request.region not in ALLOWED_REGIONS:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unknown region: {request.region}. "
                f"Allowed regions: "
                f"{sorted(ALLOWED_REGIONS)}"
            )
        )
        
    # 3. Логирование входящего запроса
    logger.info(
        "Prediction request received | farm_id=%s",
        request.farm_id
    )
  
    # 4. ИНФЕРЕНС
    score = calculate_risk(request)

    # 5. ПОСТПРОЦЕССИНГ
    level = get_risk_level(score)
    recommendation = get_recommendation(level)

    # 6. СОЗДАЕМ УНИКАЛЬНЫЙ ID ЗАПРОСА
    request_id = str(uuid.uuid4())

    # 7. ФОРМИРУЕМ РЕЗУЛЬТАТ
    result = PredictionResponse(
        request_id=request_id, 
        farm_id=request.farm_id, 
        risk_score=score, 
        risk_level=level, 
        recommendation=recommendation, 
        model_version=MODEL_VERSION
    )

    # 8. СОХРАНЯЕМ РЕЗУЛЬТАТ 
    predictions[request_id] = result

    # 9. ЛОГИРОВАНИЕ РЕЗУЛЬТАТА
    logger.info(
        "Prediction completed | "
        "request_id=%s | "
        "farm_id=%s | "
        "risk_score=%s | "
        "risk_level=%s",
        request_id,
        request.farm_id,
        score,
        level
    )
    return result
