# Enterprise Knowledge Assistant

**One-line pitch:** A production-grade RAG platform where users upload documents and get answers that are always grounded in and cited from their own content — self-hosted end to end, with measurable retrieval quality.

## Non-Negotiable USPs

### 1. Polyglot Architecture
Java Spring Boot owns auth, orchestration, and persistence. Python FastAPI owns the RAG pipeline (chunking, embedding, retrieval, generation). These are separate services communicating over REST, not one service pretending to be two.

### 2. Grounded, Cited Answers
The system must never answer from the LLM's general knowledge. Every answer must be traceable to specific retrieved chunks, and the API response must always include which document/page/chunk the answer came from. If retrieval finds nothing relevant, the system says so — it does not let the LLM guess.

### 3. Fully Self-Hosted, Zero Vendor Lock-In
LLM inference runs on Ollama, embeddings are open-source, the vector store is self-hosted Postgres/pgvector. No API keys to a paid LLM provider are required for the system to function end to end.

### 4. Measurable Retrieval Quality
A RAGAS evaluation harness (context precision, context recall, faithfulness, answer relevancy) is a first-class part of the system, not an afterthought script. It must be runnable on demand and produce a readable scorecard.

### 5. Secure Multi-User
Every user's documents and chat history are isolated. Auth uses JWT. No document or chat data is ever readable across accounts.

### 6. Production Deployment
The system runs as containerized microservices behind a reverse proxy with HTTPS, deployed on a self-managed VPS, with CI/CD building and pushing images automatically on push to main.

### 7. Streaming Responses
Answers stream to the frontend token by token, not returned as one blocking response.
