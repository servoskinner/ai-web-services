
from batch import (
    INFERENCE_TIMEOUT_SECONDS,
    MAX_BATCH_SIZE,
    MAX_BATCH_WAIT_MS,
    QUEUE,
    QUEUE_MAX_SIZE,
)
from fastapi import APIRouter, status

router = APIRouter(prefix="/queue-status", tags=[])

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Состояние очереди и настройки batching",
)
async def queue_status():
    return {
        "queue_size": QUEUE.qsize(),
        "queue_max_size": QUEUE_MAX_SIZE,
        "max_batch_size": MAX_BATCH_SIZE,
        "max_batch_wait_ms": MAX_BATCH_WAIT_MS,
        "inference_timeout_seconds": INFERENCE_TIMEOUT_SECONDS
    }