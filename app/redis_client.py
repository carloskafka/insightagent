import redis
from app.config import REDIS_URL

_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            return None
    return _redis_client