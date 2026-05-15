import time

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW
from app.integrations.redis_client import get_redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        redis_client = get_redis_client()

        if not redis_client:
            return await call_next(request)

        key = f"rate_limit:{client_ip}"
        current_time = int(time.time())
        window_start = current_time - RATE_LIMIT_WINDOW

        redis_client.zremrangebyscore(key, 0, window_start)
        request_count = redis_client.zcard(key)
        if request_count >= RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

        redis_client.zadd(key, {f"{current_time}": current_time})
        redis_client.expire(key, RATE_LIMIT_WINDOW * 2)
        return await call_next(request)


def rate_limit_decorator(func):
    from functools import wraps

    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        client_ip = request.client.host
        redis_client = get_redis_client()

        if not redis_client:
            return await func(request, *args, **kwargs)

        key = f"rate_limit:{client_ip}"
        current_time = int(time.time())
        window_start = current_time - RATE_LIMIT_WINDOW

        redis_client.zremrangebyscore(key, 0, window_start)
        request_count = redis_client.zcard(key)
        if request_count >= RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded.",
            )

        redis_client.zadd(key, {f"{current_time}": current_time})
        redis_client.expire(key, RATE_LIMIT_WINDOW * 2)
        return await func(request, *args, **kwargs)

    return wrapper
