from fastapi import APIRouter, status

from schema import HealthResponse

router = APIRouter(prefix="/health", tags=[])

@router.get(
    "",
    response_model=HealthResponse,
    summary="Проверка состояния API",
    description=(
        "Используется для проверки того, "
        "что REST API запущен и отвечает."
    ),
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
        },
    }
)
def health() -> HealthResponse:
    """
    Проверка работоспособности API.
    """

    return HealthResponse(status="ok")
