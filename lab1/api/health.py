from fastapi import APIRouter
from schema import HealthResponse

router = APIRouter(prefix="/health", tags=[])

@router.get(
    "/",
    response_model=HealthResponse,
    summary="Проверка состояния API",
    description=(
        "Используется для проверки того, "
        "что REST API запущен и отвечает."
    )
)
def health():
    """
    Проверка работоспособности API.
    """

    return {
        "status": "ok"
    }
