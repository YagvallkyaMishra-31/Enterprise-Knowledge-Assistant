"""Enterprise Knowledge Assistant — RAG pipeline service."""

from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.internal import router as internal_router

app = FastAPI(
    title="Knowledge Assistant RAG Service",
    version="0.1.0",
    description="Chunking, embedding, retrieval, and generation pipeline",
)

app.include_router(health_router)
app.include_router(internal_router, prefix="/internal")
