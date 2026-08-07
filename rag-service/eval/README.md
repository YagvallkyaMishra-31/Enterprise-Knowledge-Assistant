# RAGAS Evaluation Harness

This directory contains the tools necessary to evaluate the Retrieval-Augmented Generation (RAG) pipeline's quality using the [RAGAS](https://docs.ragas.io/en/stable/) framework.

## Overview
This harness runs **completely locally and self-hosted**, reusing the internal Python application components (`retrieve_chunks`, `generate_answer_stream`) and our locally hosted Ollama instances for the LLM-as-a-judge capabilities. No cloud APIs or paid providers are used — consistent with this project's USP #3 (zero vendor lock-in, fully self-hosted).

## How to Run

To run the evaluation, you must execute the script from within the `rag-service` environment with the appropriate user ID that owns the test documents.

1. First, make sure you have uploaded the test documents (`apollo11.txt`, `photosynthesis.txt`) to a user account using the `upload_eval_docs.py` script in the project root.
2. Get the UUID of that user (printed by the upload script).
3. Run the evaluation script from inside the `rag-service` Docker container:

```bash
# From the project root
docker cp rag-service/eval knowledge-assistant-rag-service-1:/app/eval
docker exec -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  knowledge-assistant-rag-service-1 \
  python -u eval/run_evaluation.py --user_id "YOUR-USER-UUID-HERE"
```

## Where Results are Saved
Results are written in JSON format to `eval/results/latest_run.json` (as well as a timestamped copy). Results are written **incrementally** during the answer generation phase, so if a run is interrupted, partial data is preserved.

The output contains:
- An aggregate scorecard (mean scores across all questions)
- A per-question breakdown (individual metric scores per question)
- Timing data (generation time, evaluation time, total wall-clock time)
- Configuration used (model, top_k, max_distance, etc.)

## Understanding the Metrics

* **Context Precision:** Measures how relevant the retrieved context chunks are to the user's question, penalizing if irrelevant chunks are ranked higher.
* **Context Recall:** Measures whether the retrieved context contains all the necessary information to form the ground truth expected answer.
* **Faithfulness:** Measures whether the generated answer is strictly derived from the retrieved context without hallucinating outside information.
* **Answer Relevancy:** Measures how directly the generated answer addresses the user's original question without going off-topic.

## Performance: Local LLM-as-Judge Trade-off

This project **deliberately** keeps the evaluation harness fully self-hosted rather than outsourcing it to a paid cloud provider (e.g., OpenAI, Anthropic). This is a conscious design decision consistent with USP #3 — the entire system, including quality measurement, runs without external dependencies.

### The trade-off
Local LLM-as-judge evaluation is inherently slower than cloud-API judges. RAGAS evaluates each question across 4 metrics, with each metric requiring one or more LLM reasoning calls. For 15 questions, this means ~60 judge calls through the local model.

### Root cause of initial slowness
The `OLLAMA_KEEP_ALIVE=0` setting (used to relieve memory pressure during normal interactive use) caused the model to be **unloaded from memory after every single request**. This meant each of RAGAS's ~60 judge calls paid the full model cold-load penalty (~2.2GB read from disk) on top of actual inference time.

### Solution applied
- **`keep_alive=5m`** is set on judge LLM calls during evaluation, keeping the model warm in memory between RAGAS calls. This is scoped to the evaluation script only and does not change the default `OLLAMA_KEEP_ALIVE=0` for normal app usage.
- **`num_predict=200`** caps the judge's output length to prevent unnecessarily long reasoning chains per evaluation call.
- **Incremental output** ensures partial results are saved even if a run is interrupted.
