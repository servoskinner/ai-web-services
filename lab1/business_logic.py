from fastapi import HTTPException, status
from schema import FarmRequest

# Разрешенные регионы.
# Это пример бизнес-справочника.
ALLOWED_REGIONS = {
    "Krasnodar",
    "Rostov",
    "Stavropol"
}

def validate_business_rules(
    data: FarmRequest,
) -> None:
    """
    Pydantic проверяет типы, обязательность и диапазоны.
    Здесь проверяются правила предметной области.
    """

    if data.region not in ALLOWED_REGIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unknown region: {data.region}. "
                f"Allowed regions: {sorted(ALLOWED_REGIONS)}"
            ),
        )
