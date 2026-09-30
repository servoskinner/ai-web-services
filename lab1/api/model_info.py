from fastapi import APIRouter, status

from constants import *
from schema import ModelInfoResponse

router = APIRouter(prefix="/model_info", tags=[])

@router.get(
    "",
    response_model=ModelInfoResponse,
    summary="Информация о модели",
    description=(
        "Возвращает название, версию, тип "
        "и текущее состояние модели."
    ),
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
        },
    }
)
def model_info() -> ModelInfoResponse:
    """
    Возвращает информацию
    об используемой ML-модели.
    """

    model_status = (
        "ready"
        if MODEL_READY
        else "unavailable"
    )

    return ModelInfoResponse(
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        model_type=MODEL_TYPE,
        status=model_status,
    )