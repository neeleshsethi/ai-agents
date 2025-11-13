from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time
import logging
from contextlib import asynccontextmanager
from api.api.middleware import RequestIDMiddleware
from fastapi.middleware.cors import CORSMiddleware
from api.api.endpoints import api_router
from httpx import AsyncClient
from api.core.config import settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("App starting up")
    yield
    logger.info("App shutting down")
    await client.aclose()


app = FastAPI(lifespan=lifespan)

client = AsyncClient(timeout=settings.DEFAULT_TIMEOUT)

app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

app.include_router(api_router)

@app.get('/')
async def root():
    return {"message": "API"}

@app.get('/health')
async def health():
    return {"status": "healthy"}