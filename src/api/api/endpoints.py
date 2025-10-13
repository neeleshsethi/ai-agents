from fastapi import APIRouter, Request
import logging
from httpx import AsyncClient
from api.api.models import RAGRequest, RAGResponse, RAGUsedImage
from api.rag.retrieval import rag_pipeline_wrapper



rag_router = APIRouter(
    prefix="/rag",
    tags=['rag']
)


@rag_router.get("/health")
async def rag_health():
    return {"status": "healthy", "service": "rag"}


@rag_router.post("/", response_model=RAGResponse)
async def rag(payload: RAGRequest) -> RAGResponse:
    """
    RAG endpoint for question answering with product context retrieval

    Args:
        payload: RAGRequest containing the question and top_k parameter

    Returns:
        RAGResponse with answer and retrieved images
    """
    result = rag_pipeline_wrapper(payload.question, payload.top_k)
    return RAGResponse(**result)


api_router = APIRouter()
api_router.include_router(rag_router)
