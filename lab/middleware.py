import logging
import re
import time
from uuid import UUID, uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse

UUID_REGEX = re.compile("[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}", re.IGNORECASE)
UUID_FIELD = "X-Request-ID"

async def ensure_request_id(
    request: Request,
    call_next,
):
    if "X-Request-ID" in request.headers:
        req_id = request.headers[UUID_FIELD]
        if not UUID_REGEX.fullmatch(req_id):
            # exception handlers don't cover middleware
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": f"{UUID_FIELD} must be a UUID"},
            )
        request.state.id = str(UUID(req_id))
    else:
        request.state.id = str(uuid4())

    try:
        response = await call_next(request)
    except Exception:
        logging.getLogger().exception(
            f"Unhandled error (request id {request.state.id})"
        )  

        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "request_id": request.state.id,
            }
        )

    response.headers[UUID_FIELD] = request.state.id
    return response


async def add_process_time(
    request: Request,
    call_next,
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