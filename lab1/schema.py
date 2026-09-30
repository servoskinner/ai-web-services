from typing import Literal

from pydantic import BaseModel, Field


class FarmRequest(BaseModel):
    """
    Данные сельскохозяйственного предприятия,
    которые клиент передает в POST /predict
    """

    farm_id: str = Field(
        ...,
        min_length=1,
        description="Идентификатор хозяйства"
    )

    region: str = Field(
        ...,
        min_length=1,
        description="Регион хозяйства"
    )

    crop_type: str = Field(
        ...,
        min_length=1,
        description="Основная сельскохозяйственная культура"
    )

    area_ha: float = Field(
        ...,
        gt=0,
        description="Площадь посевов, га"
    )

    temperature_avg: float = Field(
        ...,
        ge=-60,
        le=60,
        description="Средняя температура, °C"
    )

    precipitation_mm: float = Field(
        ...,
        ge=0,
        description="Количество осадков, мм"
    )

    payment_delay_days: int = Field(
        ...,
        ge=0,
        description="Количество дней просрочки платежа"
    )

    previous_defaults: int = Field(
        ...,
        ge=0,
        description="Количество предыдущих дефолтов"
    )

    debt: float = Field(
        ...,
        ge=0,
        description="Текущая задолженность"
    )

# МОДЕЛЬ ОТВЕТА /predictions
class PredictionResponse(BaseModel):
    request_id: str
    farm_id: str
    risk_score: float
    risk_level: Literal["low", "medium", "high"]
    recommendation: str
    model_version: str

# МОДЕЛЬ ОТВЕТА /health
class HealthResponse(BaseModel):
    status: str

# МОДЕЛЬ ОТВЕТА /model-info
class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    model_type: str
    status: str