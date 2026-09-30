
from fastapi import APIRouter, HTTPException, Query, status
from typing import Literal

from model import predictions
from schema import PredictionResponse

router = APIRouter(prefix="/predictions", tags=[])

@router.get(
    "/{request_id}",
    response_model=PredictionResponse,
    summary="Получить прогноз по request_id",
    description=(
        "Возвращает сохраненный прогноз "
        "по его уникальному идентификатору."
    ),
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Not found",
        },
    }
)
def get_prediction(request_id: str) -> PredictionResponse:
    """
    Получение одного прогноза
    по request_id.
    """
    # Проверяем наличие прогноза
    if request_id not in predictions:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    # Возвращаем прогноз
    return predictions[request_id]

@router.get(
    "",
    response_model=list[PredictionResponse],
    summary="Получить список прогнозов",
    description=(
        "Возвращает список выполненных прогнозов. "
        "Поддерживает ограничение количества результатов "
        "и фильтрацию по уровню риска."
    ),
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
        }
    }
)
def get_predictions(

    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Максимальное количество результатов"
    ),

    risk_level: Literal["low", "medium", "high"] | None = Query(
        default=None,
        description=(
            "Фильтр по категории риска"
        )
    )

) -> list[PredictionResponse]:
    """
    Получение списка прогнозов.
    """
    # Преобразуем словарь в список
    values = list(predictions.values())

    if risk_level is not None:
        # Фильтрация
        values = [
            item
            for item in values
            if item.risk_level == risk_level
        ]

    # Ограничение количества результатов
    return values[:limit]
