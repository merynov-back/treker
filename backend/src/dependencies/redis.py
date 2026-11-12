from functools import lru_cache
import redis
from src.config import settings
from src.services.redis_service import RedisService


@lru_cache
def get_redis_service() -> RedisService:
    # Один клієнт з пулом з'єднань на весь застосунок
    return RedisService(redis.from_url(settings.REDIS_URL, decode_responses=True))
