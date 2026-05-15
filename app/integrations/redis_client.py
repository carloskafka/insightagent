import redis

from app.core.config import REDIS_URL


_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        except Exception as exc:
            print(f"Failed to connect to Redis: {exc}")
            return None
    return _redis_client
