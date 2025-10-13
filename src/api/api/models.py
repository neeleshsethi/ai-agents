from pydantic import BaseModel
from typing import List, Optional


class RAGRequest(BaseModel):
    """Request model for RAG endpoint"""
    question: str
    top_k: int = 5


class RAGUsedImage(BaseModel):
    """Model for retrieved images"""
    image_url: str
    price: Optional[float] = None
    description: str


class RAGResponse(BaseModel):
    """Response model for RAG endpoint"""
    answer: str
    retrieved_images: List[RAGUsedImage]
