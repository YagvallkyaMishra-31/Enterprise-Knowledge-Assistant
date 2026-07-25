"""Enterprise Knowledge Assistant — RAG pipeline service."""

from fastapi import FastAPI
from app.api.health import router as health_router

app = FastAPI(
    title="Knowledge Assistant RAG Service",
    version="0.1.0",
    description="Chunking, embedding, retrieval, and generation pipeline",
)

app.include_router(health_router)
