from api.api.logger import logger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware






async def log_middleware(request: Request, call_next):
    log_dir = {
        'url': request.url.path,
        'method': request.method,


    }
    logger.info(log_dir)
    response = await call_next(request)
    return response 
