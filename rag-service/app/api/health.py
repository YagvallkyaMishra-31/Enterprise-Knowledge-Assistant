"""Liveness probe for the RAG service."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Returns service health status."""
    return {"status": "ok"}
