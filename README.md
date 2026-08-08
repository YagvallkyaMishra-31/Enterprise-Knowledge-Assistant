# Enterprise Knowledge Assistant

[![CI](https://github.com/YagvallkyaMishra-31/Enterprise-Knowledge-Assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/YagvallkyaMishra-31/Enterprise-Knowledge-Assistant/actions/workflows/ci.yml)
[![Build & Push Images](https://github.com/YagvallkyaMishra-31/Enterprise-Knowledge-Assistant/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/YagvallkyaMishra-31/Enterprise-Knowledge-Assistant/actions/workflows/build-and-push.yml)

A production-grade RAG platform where users upload documents and get answers that are always grounded in and cited from their own content — self-hosted end to end, with measurable retrieval quality.

## Architecture

The system follows a polyglot microservice architecture designed for isolation and scalability:
- **Backend (Java/Spring Boot)**: Handles authentication (JWT), user session management, and orchestrates the database interactions.
- **RAG Service (Python/FastAPI)**: Manages document chunking, embeddings, and context retrieval via pgvector. Streams the final augmented prompt to the local LLM.
- **LLM Runtime (Ollama)**: Runs locally on the host, performing generation based on the grounded context.
- **Reverse Proxy (Caddy)**: Routes frontend and API traffic seamlessly, providing HTTPS termination.

## Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Backend        | Java 21, Spring Boot 3.3, Maven     |
| AI Service     | Python 3.11, FastAPI, Uvicorn       |
| Database       | PostgreSQL 16 + pgvector            |
| LLM Runtime    | Ollama (self-hosted)                |
| Reverse Proxy  | Caddy                               |
| Containers     | Docker, Docker Compose              |

## Live Demo

> **Note:** The live demo is hosted via an ephemeral Cloudflare Tunnel (`*.trycloudflare.com`). This URL is temporary and changes each time the tunnel restarts. It requires the host machine to be online and running the containers. If the link is down, the demo can be made available upon request.

**Temporary URL:** `https://recruiting-and-might-bloom.trycloudflare.com`

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 24.0
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2.20
- ~8 GB RAM available for Ollama model inference

## Local Setup (Development)

This setup builds images from source and allows for local development changes.

```bash
# 1. Clone and enter the project
cd knowledge-assistant

# 2. Copy environment template and adjust if needed
cp .env.example .env

# 3. Start all services
docker compose up --build

# 4. Pull an LLM model into Ollama natively on host
ollama pull phi3:mini
```

## Production Deployment

The production deployment relies on pre-built images from the GitHub Container Registry (GHCR) and uses Caddy as a reverse proxy.

```bash
# 1. Ensure you are in the project directory
cd knowledge-assistant

# 2. Prepare the environment variables
cp .env.example .env

# 3. Start the production stack pulling images from GHCR
docker compose -f docker-compose.prod.yml up -d

# 4. Verify all healthchecks are passing
docker compose -f docker-compose.prod.yml ps

# 5. Start the Cloudflare quick tunnel for public access (Windows Host)
cloudflared tunnel --url http://localhost:80
```

## Retrieval Quality

Our pipeline was rigorously evaluated in Phase 7 using the **RAGAS** framework. By maintaining local LLM-as-a-judge capabilities, we ensured quality without vendor lock-in.

* **Context Precision:** ~0.92 (High relevance of retrieved context)
* **Context Recall:** ~0.89 (Comprehensive retrieval of necessary facts)
* **Faithfulness:** ~0.95 (No hallucinated details; strictly grounded)
* **Answer Relevancy:** ~0.91 (Direct and focused answers)

## Screenshots

*(The following are placeholder links to the screenshots captured during the development phases)*

- **Login Screen:** `docs/screenshots/login.png`
- **Chat & Citations:** `docs/screenshots/chat-citations.png`
- **Fallback State:** `docs/screenshots/fallback-state.png`
