
from typing import Literal

from constants import WEEKDAY_MAP
from db import (
    get_predictions_by_request_id,
    get_predictions_by_weekday_page,
    get_predictions_from_db,
)
from fastapi import APIRouter, HTTPException, Query, Request, status
from schema import PaginatedPredictionsResponse, PaginationMeta, PredictionResponse

router = APIRouter(prefix="/predictions", tags=[])

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
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Prediction storage unavailable",
        },
    },
)
async def get_predictions(
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

):
    """
    Получение списка прогнозов.
    """
    preds = await get_predictions_from_db(limit=limit, risk_level=risk_level)
    return [PredictionResponse.from_row(row) for row in preds]


@router.get(
    "/by-weekday",
    response_model=PaginatedPredictionsResponse,
    summary="Прогнозы по дню недели с пагинацией",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Unknown weekday or invalid X-Request-ID",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Page beyond last page",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Prediction storage unavailable",
        },
    },
)
async def get_predictions_by_weekday(
    request: Request,
    weekday: str = Query(
        ...,
        description="День недели: monday, tuesday, wednesday"
        " thursday, friday, saturday, sunday",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Номер страницы",
    ),
    per_page: int = Query(
        default=5,
        ge=1,
        le=100,
        description="Количество записей на одной странице"
    ),
):
    weekday = weekday.lower()
    if weekday not in WEEKDAY_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid weekday string",
        )
    data, total_items, total_pages = await get_predictions_by_weekday_page(
        weekday_number=WEEKDAY_MAP[weekday],
        page=page,
        per_page=per_page
    )

    if total_pages > 0 and page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page} does not exist. Total pages: {total_pages}"
        )

    if total_pages == 0 and page > 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data for this weekday",
        )

    next_page = None

    if page < total_pages:
        next_page = str(
            request.url.include_query_params(
                weekday=weekday,
                page=page+1,
                per_page=per_page
            )
        )

    prev_page = None

    if page > 1 and total_pages > 0:
        prev_page = str(
            request.url.include_query_params(
                weekday=weekday,
                page=page-1,
                per_page=per_page
            )
        )

    return PaginatedPredictionsResponse(
        data=[PredictionResponse.from_row(row) for row in data],
        meta=PaginationMeta(
            weekday=weekday,
            current_page=page,
            per_page=per_page,
            total_pages=total_pages,
            total_items=total_items,
            next_page=next_page,
            prev_page=prev_page
        )
    )


@router.get(
    "/{request_id}",
    response_model=PredictionResponse,
    summary="Получить одиночный прогноз по request_id",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "No predictions for request_id",
        },
        status.HTTP_409_CONFLICT: {
            "description": "request_id has multiple predictions (batch)",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Prediction storage unavailable",
        },
    },
)
async def get_prediction(
    request_id: str
):
    results = await get_predictions_by_request_id(request_id)

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No predictions for this ID",
        )

    if len(results) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This request_id contains multiple predictions. "
            f"Use /requests/{request_id}/predictions"
        )

    return PredictionResponse.from_row(results[0])
