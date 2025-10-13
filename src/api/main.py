from .api import endpoints
from fastapi import FastAPI, Request
from .api.middleware import log_middleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
from api.api.logger import logger

app = FastAPI()
app.include_router(endpoints.api_router)
app.add_middleware(BaseHTTPMiddleware, dispatch=log_middleware)


@app.middleware('http')
async def log_middleware_func(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    logger.info(f"Request started: {request.method} {request.url.path} (request id: {request_id})")

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(f"Request completed: {request.method} {request.url.path} (request_id: {request_id})")

    return response 

