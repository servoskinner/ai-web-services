import asyncio
import logging
import time
from dataclasses import dataclass

from constants import MAX_BATCH_SIZE
from model import (
    MODEL_FIXED_OVERHEAD_SECONDS,
    MODEL_PER_ITEM_SECONDS,
    calculate_risk,
)
from schema import FarmRequest

QUEUE_MAX_SIZE = 128
MAX_BATCH_WAIT_MS = 50
INFERENCE_TIMEOUT_SECONDS = 2.0

QUEUE = asyncio.Queue(QUEUE_MAX_SIZE)
model_lock = asyncio.Lock()

@dataclass
class InferenceTask:
    data : FarmRequest
    request_id : str
    future : asyncio.Future


async def batch_worker() -> None:
    """Фоновый worker для обработки очереди"""
    logging.getLogger().info("Worker started")

    while True:
        first_task = await QUEUE.get()

        if first_task.future.cancelled():
            QUEUE.task_done()
            continue

        batch = [first_task]
        deadline = time.perf_counter() + MAX_BATCH_WAIT_MS / 1000.0

        while len(batch) < MAX_BATCH_SIZE:
            remaining_time = deadline - time.perf_counter()
            if remaining_time <= 0.0:
                break
            try:
                task = await asyncio.wait_for(
                    QUEUE.get(),
                    timeout=remaining_time,
                )
                if task.future.cancelled():
                    QUEUE.task_done()
                    continue
                batch.append(task)
            except TimeoutError:
                break

        logging.getLogger().info(
            f"Created batch with size {len(batch)}, "
            f"{QUEUE.qsize()} jobs left in queue"
        )
        try:
            scores = await asyncio.wait_for(
                model_predict_batch([task.data for task in batch]),
                timeout=INFERENCE_TIMEOUT_SECONDS,
            )
            for task, score in zip(batch, scores):
                if not task.future.done():
                    task.future.set_result(score)

        except Exception as exc:
            logging.getLogger().exception(f"Batch inference failed: {exc}")
            for task in batch:
                if not task.future.done():
                    task.future.set_exception(exc)

        finally:
            for _ in batch:
                QUEUE.task_done()


async def model_predict_single(
    data : FarmRequest
) -> float:
    """Одиночный вызов модели"""
    async with model_lock:
        await asyncio.sleep(
            MODEL_FIXED_OVERHEAD_SECONDS
            + MODEL_PER_ITEM_SECONDS
        )
        return calculate_risk(
            data
        )


async def model_predict_batch(
    items : list[FarmRequest],
) -> list[float]:
    """Пакетный вызов модели"""
    async with model_lock:
        await asyncio.sleep(
            MODEL_FIXED_OVERHEAD_SECONDS
            + MODEL_PER_ITEM_SECONDS * len(items)
        )

        return [
            calculate_risk(item)
            for item in items
        ]
