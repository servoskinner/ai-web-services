
# ПРАКТИЧЕСКОЕ ЗАНЯТИЕ № 1
# Разработка REST API для AI-сервиса на FastAPI

# ------------------------------------------------------------
# ИМПОРТ БИБЛИОТЕК
# ------------------------------------------------------------

import logging
import time

from fastapi import FastAPI, Request

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

app = FastAPI(
    title="Agro Scoring API",
    description=(
        "REST API для оценки риска "
        "сельскохозяйственных предприятий."
    ),
    version="1.0.0"
)

import api.health
import api.model_info
import api.predict
import api.predictions

app.include_router(api.health.router)
app.include_router(api.model_info.router)
app.include_router(api.predict.router)
app.include_router(api.predictions.router)

# ------------------------------------------------------------
# MIDDLEWARE
# Измеряем время обработки каждого HTTP-запроса.
# ------------------------------------------------------------

@app.middleware("http")
async def add_process_time(
    request: Request,
    call_next
):
    """
    Middleware выполняется для каждого HTTP-запроса.
    Добавляет в HTTP-ответ заголовок:

        X-Process-Time

    содержащий время обработки запроса.
    """

    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start_time

    response.headers["X-Process-Time"] = str(
        round(process_time, 6)
    )

    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)