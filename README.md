# Enterprise Knowledge Assistant

A production-grade RAG platform where users upload documents and get answers that are always grounded in and cited from their own content — self-hosted end to end, with measurable retrieval quality.

## Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Backend        | Java 21, Spring Boot 3.3, Maven     |
| AI Service     | Python 3.11, FastAPI, Uvicorn       |
| Database       | PostgreSQL 16 + pgvector            |
| LLM Runtime    | Ollama (self-hosted)                |
| Containers     | Docker, Docker Compose              |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 24.0
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2.20
- ~8 GB RAM available for Ollama model inference

## Quick Start

```bash
# 1. Clone and enter the project
cd knowledge-assistant

# 2. Copy environment template and adjust if needed
cp .env.example .env

# 3. Start all services
docker compose up --build

# 4. Verify health endpoints (in a separate terminal)
curl http://localhost:8080/api/health    # → {"status":"UP"}
curl http://localhost:8000/health        # → {"status":"ok"}

# 5. Pull an LLM model into Ollama natively on host
ollama pull phi3:mini
```

## Services

| Service       | Internal Port | External Port | Purpose                              |
|---------------|---------------|---------------|--------------------------------------|
| `backend`     | 8080          | 8080          | Auth, orchestration, persistence     |
| `rag-service` | 8000          | 8000          | RAG pipeline (chunking, retrieval)   |
| `postgres`    | 5432          | 5432          | Primary data store + vector search   |
| `ollama`      | 11434         | 11434         | Local LLM inference (Native Host)    |

## Project Structure

```
knowledge-assistant/
├── backend/                  Spring Boot service
│   ├── src/main/java/...     Application code
│   ├── src/main/resources/   Config + Flyway migrations
│   ├── Dockerfile
│   └── pom.xml
├── rag-service/              FastAPI service
│   ├── app/                  Application code
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml        Local development
├── docker-compose.prod.yml   Production (stub — Phase 9)
├── PROJECT_BRIEF.md          Non-negotiable USPs
├── .env.example              Environment variable template
└── .gitignore
```

## Local Development Notes

Ollama runs natively on Windows (not in Docker) for local development due to WSL2 memory constraints on resource-limited dev machines — this avoids double-virtualization overhead. Production deployment on the VPS runs Ollama in Docker as originally designed, since the VPS has dedicated RAM with no competing desktop workload.
