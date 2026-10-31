from typing import Literal

from constants import (
    LLM_DEFAULT_MAX_TOKENS,
    LLM_DEFAULT_TEMPERATURE,
    LLM_MODEL,
    MAX_BATCH_SIZE,
)
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


class BatchRequest(BaseModel):
    """Явный batch, который клиент отправляет одним HTTP-запросом."""

    items: list[FarmRequest] = Field(
        ...,
        min_length=1,
        max_length=MAX_BATCH_SIZE,
        description="Список объектов для пакетного инференса",
    )


# МОДЕЛЬ ОТВЕТА /predictions
class PredictionItem(BaseModel):
    farm_id: str
    risk_score: float
    risk_level: Literal["low", "medium", "high"]
    recommendation: str
    model_version: str


class PredictionResponse(BaseModel):
    request_id: str
    item : PredictionItem

    @classmethod
    def from_row(cls, row: dict) -> "PredictionResponse":
        """Плоская строка БД -> вложенный ответ"""
        return cls(
            request_id=row["request_id"],
            item=PredictionItem(**{k: v for k, v in row.items() if k != "request_id"}),
        )
    

class BatchPredictionResponse(BaseModel):
    request_id: str
    batch_size: int
    processing_time_ms: float
    items: list[PredictionItem]


class PaginationMeta(BaseModel):
    weekday: str
    current_page: int
    per_page: int
    total_pages: int
    total_items: int
    next_page: str | None
    prev_page: str | None


class PaginatedPredictionsResponse(BaseModel):
    data: list[PredictionResponse]
    meta: PaginationMeta


class LLMChatRequest(BaseModel):
    prompt: str = Field(
        min_length=1, 
        max_length=5000,
        description="Текст запроса к LLM"
    )

    model: str = Field(
        default=LLM_MODEL,
        min_length=1,
        description="Название модели"
    )

    temperature: float = Field(
        default=LLM_DEFAULT_TEMPERATURE,
        ge=0.0, 
        le=2.0
    )

    max_tokens: int = Field(
        default=LLM_DEFAULT_MAX_TOKENS,
        ge=1,
        le=2000
    )


class LLMChatResponse(BaseModel):
    request_id: str
    requested_model: str
    returned_model: str | None
    answer: str
    reasoning: str | None
    finish_reason: str | None
    usage: dict | None
    latency_ms: float


class PredictWithLLMResponse(BaseModel):
    prediction: PredictionResponse
    llm: LLMChatResponse

    

# МОДЕЛЬ ОТВЕТА /health
class HealthResponse(BaseModel):
    status: str


# МОДЕЛЬ ОТВЕТА /model-info
class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    model_type: str
    status: str