
# ПРАКТИЧЕСКОЕ ЗАНЯТИЕ № 2
# Разработка REST API для AI-сервиса на FastAPI

# ------------------------------------------------------------
# ИМПОРТ БИБЛИОТЕК
# ------------------------------------------------------------

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from batch import batch_worker
from db import init_db
from exceptions import http_exception_handler, validation_exception_handler
from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from constants import LLM_TIMEOUT_SECONDS
from middleware import add_process_time, ensure_request_id

# ------------------------------------------------------------
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# FASTAPI-ПРИЛОЖЕНИЕ
# ------------------------------------------------------------

@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    """Управление жизненным циклом приложения"""
    await init_db()
    app.state.llm_client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            LLM_TIMEOUT_SECONDS
        )
    )
    worker = asyncio.create_task(batch_worker())
    app.state.batch_worker = worker

    yield

    worker.cancel()
    try:
        await worker
    except asyncio.CancelledError:
        pass

    await app.state.llm_client.aclose()


app = FastAPI(
    title="Agro Scoring API",
    description=(
        "REST API для оценки риска "
        "сельскохозяйственных предприятий."
    ),
    version="1.0.0",
    lifespan=lifespan,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid X-Request-ID header (not a UUID)",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
        },
    },
)

import api.batch_predict
import api.demo.seed_weekdays
import api.health
import api.llm
import api.model_info
import api.predict
import api.predict_queued
import api.predict_with_llm
import api.predictions
import api.queue_status
import api.requests

app.include_router(api.health.router)
app.include_router(api.model_info.router)
app.include_router(api.predict.router)
app.include_router(api.predict_queued.router)
app.include_router(api.predict_with_llm.router)
app.include_router(api.batch_predict.router)
app.include_router(api.llm.router)
app.include_router(api.queue_status.router)
app.include_router(api.predictions.router)
app.include_router(api.requests.router)
app.include_router(api.demo.seed_weekdays.router, prefix="/demo")


@app.get("/")
async def root():
    return {
        "message": "Agro Scoring API is running",
        "docs": "/docs",
        "health": "/health"
    }

# ------------------------------------------------------------
# MIDDLEWARE
# ------------------------------------------------------------

app.middleware("http")(ensure_request_id)
app.middleware("http")(add_process_time)

app.exception_handler(HTTPException)(http_exception_handler)
app.exception_handler(RequestValidationError)(validation_exception_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)