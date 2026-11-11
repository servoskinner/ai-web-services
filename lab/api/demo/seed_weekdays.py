

from db import _seed_weekday_predictions
from fastapi import APIRouter, Query, status

router = APIRouter(prefix="/seed-weekdays", tags=[])

@router.post(
    "",
    summary="Создать демонстрационные прогнозы за разные дни",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Prediction storage unavailable",
        },
    },
)
async def seed_weekdays(
    count : int = Query(
        default=70,
        ge=7,
        le=1000,
        description="Количество демонстрационных записей",
    ),
):
    """
    Создание записей для демонстрации.
    """
    created = await _seed_weekday_predictions(
        count=count
    )

    return {
        "status": "ok",
        "created": created,
        "message": "Demo predictions created. Check with /predictions/by-weekday"
    }