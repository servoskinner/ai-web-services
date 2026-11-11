from schema import FarmRequest

# ------------------------------------------------------------
# МОДЕЛЬ МАШИННОГО ОБУЧЕНИЯ

# Позже подключим обученную ML модель
# Сейчас определим функцию с условной конструкцией
# ------------------------------------------------------------

MODEL_NAME = "agro-risk-model"
MODEL_VERSION = "1.0"
MODEL_TYPE = "risk-scoring"

# Имитация состояния модели.
# Если False, endpoints инференса возвращаем HTTP 503.
MODEL_READY = True

# debug
MODEL_FIXED_OVERHEAD_SECONDS = 0.02
MODEL_PER_ITEM_SECONDS = 0.003

def calculate_risk(
    data: FarmRequest,
) -> float:
    """
    Имитация ML-модели.
    """
    score = 0.1

    if data.payment_delay_days > 30:
        score += 0.3

    if data.previous_defaults > 0:
        score += 0.3

    if data.debt > 5_000_000:
        score += 0.2

    if data.precipitation_mm < 100:
        score += 0.1

    return round(
        min(score, 1.0),
        2,
    )

# ПОЛУЧЕНИЕ РИСК-ПРОФИЛЯ
def get_risk_level(score: float) -> str:
    """
    Преобразует score в категорию риска.
    """
    if score < 0.3:
        return "low"
    if score < 0.7:
        return "medium"
    return "high"


# ВЫДАЧА РЕКОМЕНДАЦИИ
def get_recommendation(level: str) -> str:
    """
    Возвращает рекомендацию в зависимости от категории риска.
    """

    match level.lower():
        case "low":
            return "Стандартное рассмотрение"
        case "medium":
            return "Требуется дополнительная проверка"
        case "high":
            return "Высокий риск. Требуется ручное рассмотрение"
        
    return ""