

from db import get_predictions_by_request_id
from fastapi import APIRouter, HTTPException, status
from schema import PredictionResponse

router = APIRouter(prefix="/requests", tags=[])

@router.get(
    "/{request_id}/predictions",
    response_model=list[PredictionResponse],
    summary="Получить все прогнозы, соответствущие request_id",
    description=(
        "Возвращает сохраненные прогнозы "
        "по уникальному идентификатору."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "No predictions for request_id",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Prediction storage unavailable",
        },
    },
)
async def get_request_prediction(request_id: str):
    """
    Получение одного прогноза
    по request_id.
    """

    results = await get_predictions_by_request_id(
        request_id=request_id
    )

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )

    return [PredictionResponse.from_row(row) for row in results]
