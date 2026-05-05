from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.redis_client import get_redis_client
from app.config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        redis_client = get_redis_client()
        
        if not redis_client:
            # If Redis is not available, skip rate limiting
            return await call_next(request)
        
        key = f"rate_limit:{client_ip}"
        current_time = int(time.time())
        window_start = current_time - RATE_LIMIT_WINDOW
        
        # Remove old entries
        redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count requests in current window
        request_count = redis_client.zcard(key)
        
        if request_count >= RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Add current request
        redis_client.zadd(key, {f"{current_time}": current_time})
        redis_client.expire(key, RATE_LIMIT_WINDOW * 2)
        
        response = await call_next(request)
        return response

def rate_limit_decorator(func):
    """Decorator for rate limiting individual endpoints"""
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
                detail="Rate limit exceeded."
            )
        
        redis_client.zadd(key, {f"{current_time}": current_time})
        redis_client.expire(key, RATE_LIMIT_WINDOW * 2)
        
        return await func(request, *args, **kwargs)
    
    return wrapper
