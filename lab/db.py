import logging
import math
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import aiosqlite
from fastapi import HTTPException, status

# debug 
from model import MODEL_VERSION, get_recommendation, get_risk_level

DB_PATH = Path(__file__).resolve().parent / "tmp/agro_scoring.db"
DB_BUSY_TIMEOUT_MS = 5000


@asynccontextmanager
async def get_db():
    """
    Открывает отдельное асинхронное соединение с SQLite
    на одну логическую операцию.

    """
    db = await aiosqlite.connect(
        str(DB_PATH),
        timeout=DB_BUSY_TIMEOUT_MS / 1000
    )
    db.row_factory = aiosqlite.Row

    await db.execute(
        f"PRAGMA busy_timeout = {DB_BUSY_TIMEOUT_MS};"
    )

    try:
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    """
    Инициализация БД
    """
    DB_PATH.parent.mkdir(exist_ok=True)
    async with get_db() as db:
        await db.execute(
            "PRAGMA journal_mode = WAL;"
        )
        await db.execute(
            "PRAGMA synchronous = NORMAL;"
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                farm_id TEXT NOT NULL,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                model_version TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_predictions_request_id
            ON predictions(request_id);
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_predictions_risk_level
            ON predictions(risk_level);
            """
        )
        await db.commit()

    logging.getLogger().info(
        f"SQLite initialized from: {DB_PATH}"
    )


async def save_prediction(
    result: dict,
    source: str,
) -> None:
    """
    Сохраняет результат (request_id не обязательно биективен с предсказаниями)
    """
    try:
        async with get_db() as db:
            await db.execute(
                """
                INSERT into predictions (
                    request_id,
                    farm_id,
                    risk_score,
                    risk_level,
                    recommendation,
                    model_version,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    result["request_id"],
                    result["farm_id"],
                    result["risk_score"],
                    result["risk_level"],
                    result["recommendation"],
                    result["model_version"],
                    source,
                ),
            )
            await db.commit()
    except aiosqlite.Error as e:
        logging.getLogger().exception(
            f"Database write error (request id {(result.get("request_id"))})"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction storage is unavailable",
        ) from e



async def save_predictions_batch(
    request_id: str,
    items: list[dict]   
) -> None:
    """
    Сохранение всего батча через executemany()
    """
    rows = [
        (
            request_id,
            item["farm_id"],
            item["risk_score"],
            item["risk_level"],
            item["recommendation"],
            item["model_version"],
            "batch"
        )
        for item in items
    ]

    try:
        async with get_db() as db:
            await db.executemany(
                """
                INSERT INTO predictions (
                    request_id,
                    farm_id,
                    risk_score,
                    risk_level,
                    recommendation,
                    model_version,
                    source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                rows
            )
            await db.commit()

    except aiosqlite.Error as e:
        logging.getLogger().exception(
            f"Batch database write error (request id {request_id})"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction storage is unavailable"
        ) from e


async def get_predictions_from_db(
    limit: int,
    risk_level: str | None = None
) -> list[dict]:
    """Возвращает историю прогнозов из SQLite"""
    try:
        async with get_db() as db:
            base_query = """
            SELECT
                request_id,
                farm_id,
                risk_score,
                risk_level,
                recommendation,
                model_version
            FROM predictions 
            """
            if risk_level is None:
                cursor = await db.execute(
                    base_query +
                    """
                    ORDER BY id DESC
                    LIMIT ?;
                    """,
                    (limit,),
                )
            else:
                cursor = await db.execute(
                    base_query +
                    """
                    WHERE risk_level = ?
                    ORDER BY id DESC
                    LIMIT ?;
                    """,
                    (risk_level, limit,),
                )

            rows = await cursor.fetchall()
            await cursor.close()

        return [
            dict(row)
            for row in rows
        ]
    except aiosqlite.Error as e:
        logging.getLogger().exception("Database read error")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction storage is unavailable",
        ) from e

async def get_predictions_by_weekday_page(
    weekday_number: str,
    page: int,
    per_page: int,
) -> tuple[list[dict], int, int]:
    """
    Возвращает страницу прогнозов для выбранного дня недели с offset-pagination
    """
    offset = (page - 1) * per_page
    try:
        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT
                    request_id,
                    farm_id,
                    risk_score,
                    risk_level,
                    recommendation,
                    model_version
                FROM predictions
                WHERE strftime('%w', created_at) = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?;
                """,
                (weekday_number, per_page, offset),
            )
            entry_rows = await cursor.fetchall()
            await cursor.close()

            cursor = await db.execute(
                """
                SELECT COUNT(*)
                FROM predictions
                WHERE strftime('%w', created_at) = ?;
                """,
                (weekday_number,),
            )

            sum_row = await cursor.fetchone()
            await cursor.close()

        total_items = sum_row[0]
        total_pages = math.ceil(max(total_items, 0) / per_page)

        return ([dict(row) for row in entry_rows], total_items, total_pages)
    
    except aiosqlite.Error as e:
        logging.getLogger().exception(f"Database read error (weekday: {weekday_number})")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction storage is unavailable",
        ) from e


async def get_predictions_by_request_id(
    request_id: str,
) -> list[dict]:
    try:
        async with get_db() as db:
            cursor = await db.execute(
                """
                SELECT
                    request_id,
                    farm_id,
                    risk_score,
                    risk_level,
                    recommendation,
                    model_version
                FROM predictions
                WHERE request_id = ?
                ORDER BY id;
                """,
                (request_id,),
            )

            rows = await cursor.fetchall()
            await cursor.close()

        return [
            dict(row)
            for row in rows
        ]
    except aiosqlite.Error as e:
        logging.getLogger().exception(
            f"Database read error (request id: {request_id})"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction storage is unavailable"
        ) from e

# -----------------------
# debug/demo
# -----------------------

async def _seed_weekday_predictions(
    count: int = 70,
) -> int:
    """
    Создает демонстрационные predictions за разные дни.

    created_at распределяется по последним 21 дням,
    поэтому в базе появляются записи для всех дней недели.

    """

    rows = []

    for i in range(count):
        request_id = str(uuid4())
        farm_id = f"DEMO-{i + 1:03d}"

        risk_score = round(
            min(0.1 + (i % 9) * 0.1, 1.0),
            2,
        )

        risk_level = get_risk_level(risk_score)

        rows.append(
            (
                request_id,
                farm_id,
                risk_score,
                risk_level,
                get_recommendation(risk_level),
                MODEL_VERSION,
                "seed",
                f"-{i % 21} days",
            )
        )

    try:
        async with get_db() as db:
            await db.executemany(
                """
                INSERT INTO predictions (
                    request_id,
                    farm_id,
                    risk_score,
                    risk_level,
                    recommendation,
                    model_version,
                    source,
                    created_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    datetime('now', ?)
                );
                """,
                rows,
            )

            await db.commit()

        return count

    except aiosqlite.Error as exc:
        logging.getLogger().exception(
            "Demo seed database error"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction storage is unavailable",
        ) from exc