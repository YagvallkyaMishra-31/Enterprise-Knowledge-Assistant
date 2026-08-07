"""
Evaluation script for the RAG pipeline using RAGAS.
Executes locally and directly imports the RAG service internals.

Performance notes:
- Sets keep_alive=5m on Ollama judge calls so the model stays loaded
  between RAGAS's ~60 evaluation requests (avoids cold-loading 2.2GB
  from disk on every single call).
- Caps judge output to 200 tokens via num_predict to prevent
  unnecessarily long reasoning chains.
- Writes results incrementally so partial runs still produce data.
- Prints per-question timing and metric scores as they complete.
"""
import json
import os
import argparse
import datetime
import time
from typing import List, Dict, Any

# Ensure we can import from app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.retrieval import retrieve_chunks
from app.core.generation import generate_answer_stream
from app.core.config import settings

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings


def warm_model(ollama_url: str, chat_model: str, embed_model: str):
    """Pre-load both models into Ollama memory with keep_alive=5m."""
    import httpx
    print("Pre-warming chat model into memory (keep_alive=5m)...")
    try:
        resp = httpx.post(
            f"{ollama_url}/api/generate",
            json={"model": chat_model, "prompt": "Hello", "stream": False,
                  "keep_alive": "5m", "options": {"num_predict": 1}},
            timeout=600,
        )
        print(f"  Chat model warm-up complete (status {resp.status_code}).")
    except Exception as e:
        print(f"  Warning: chat warm-up call failed: {e}")
        
    print("Pre-warming embedding model into memory (keep_alive=5m)...")
    try:
        resp = httpx.post(
            f"{ollama_url}/api/embeddings",
            json={"model": embed_model, "prompt": "Hello", "keep_alive": "5m"},
            timeout=600,
        )
        print(f"  Embedding model warm-up complete (status {resp.status_code}).")
    except Exception as e:
        print(f"  Warning: embedding warm-up call failed: {e}")


def append_partial_result(out_path: str, entry: dict):
    """Append one question result to the incremental output file."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # Read existing partial data or start fresh
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"questions": [], "status": "in_progress"}
    data["questions"].append(entry)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def run_evaluation(user_id: str):
    """
    Runs the RAGAS evaluation harness against the uploaded test questions.

    Args:
        user_id (str): The UUID of the user who owns the uploaded documents.
    """
    run_start = time.perf_counter()

    print(f"Starting evaluation for user_id: {user_id}")
    print(f"Using RAG settings -> TOP_K: {settings.RAG_TOP_K}, MAX_DISTANCE: {settings.RAG_MAX_DISTANCE}")
    print(f"Using LLM: {settings.OLLAMA_CHAT_MODEL} at {settings.OLLAMA_BASE_URL}")

    # Initialize Judge LLM and Embeddings
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    chat_model = os.getenv("OLLAMA_CHAT_MODEL", "phi3:mini")
    embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    # ── Performance: keep model warm and cap output length ──
    judge_llm = ChatOllama(
        model=chat_model,
        base_url=ollama_url,
        keep_alive="5m",
        num_predict=200,
    )
    judge_embeddings = OllamaEmbeddings(model=embed_model, base_url=ollama_url)

    # Pre-warm the models so the first calls don't pay cold-load cost
    warm_model(ollama_url, chat_model, embed_model)

    with open("eval/test_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    data = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": []
    }

    partial_out = "eval/results/latest_run.json"
    # Clear any previous partial data
    os.makedirs("eval/results", exist_ok=True)
    if os.path.exists(partial_out):
        os.remove(partial_out)

    print(f"\n--- Generating Answers ({len(questions)} questions) ---")
    for idx, q_data in enumerate(questions, 1):
        q_start = time.perf_counter()
        q = q_data["question"]
        gt = q_data["expected_answer"]

        # 1. Retrieve Contexts
        chunks = retrieve_chunks(
            user_id=user_id,
            question=q,
            top_k=settings.RAG_TOP_K,
            max_distance=settings.RAG_MAX_DISTANCE
        )

        # 2. Generate Answer Stream
        answer = ""
        for token_json in generate_answer_stream(q, chunks):
            try:
                token_data = json.loads(token_json)
                if token_data.get("type") == "token":
                    answer += token_data.get("text", "")
            except Exception:
                pass

        context_texts = [c["chunkText"] for c in chunks]

        data["question"].append(q)
        data["answer"].append(answer)
        data["contexts"].append(context_texts)
        data["ground_truth"].append(gt)

        q_elapsed = time.perf_counter() - q_start

        print(f"[{idx}/{len(questions)}] Q: {q}")
        print(f"     A: {answer[:200]}{'...' if len(answer) > 200 else ''}")
        print(f"     Chunks: {len(chunks)} | {q_elapsed:.1f}s elapsed")

        # Write incrementally
        append_partial_result(partial_out, {
            "question": q,
            "answer": answer,
            "ground_truth": gt,
            "num_chunks": len(chunks),
            "generation_time_s": round(q_elapsed, 1),
        })

    gen_elapsed = time.perf_counter() - run_start
    print(f"\nAnswer generation complete in {gen_elapsed:.1f}s")

    # Build HuggingFace Dataset
    dataset = Dataset.from_dict(data)

    metrics = [
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
    ]

    print(f"\n--- Running RAGAS Evaluation ({len(metrics)} metrics × {len(questions)} questions = {len(metrics) * len(questions)} judge calls) ---")
    print("Model is kept warm (keep_alive=5m) to avoid cold-load penalty.")
    eval_start = time.perf_counter()

    result = evaluate(
        dataset,
        metrics=metrics,
        llm=judge_llm,
        embeddings=judge_embeddings,
    )

    eval_elapsed = time.perf_counter() - eval_start
    total_elapsed = time.perf_counter() - run_start

    df = result.to_pandas()

    print(f"\n{'='*60}")
    print("=== AGGREGATE SCORECARD ===")
    print(f"{'='*60}")
    result_dict = {}
    for k, v in dict(result).items():
        if isinstance(v, (int, float)):
            result_dict[k] = round(v, 4)
            print(f"  {k}: {v:.4f}")

    print(f"\n{'='*60}")
    print("=== PER-QUESTION BREAKDOWN ===")
    print(f"{'='*60}")
    cols = ["question", "context_precision", "context_recall", "faithfulness", "answer_relevancy"]
    display_cols = [c for c in cols if c in df.columns]
    print(df[display_cols].to_string())

    print(f"\n{'='*60}")
    print("=== TIMING ===")
    print(f"{'='*60}")
    print(f"  Answer generation:  {gen_elapsed:.1f}s")
    print(f"  RAGAS evaluation:   {eval_elapsed:.1f}s ({eval_elapsed/len(questions):.1f}s per question)")
    print(f"  Total wall-clock:   {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")

    # Save final results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"eval/results/latest_run_{timestamp}.json"

    final_output = {
        "aggregate": result_dict,
        "per_question": json.loads(df.to_json(orient="records")),
        "timing": {
            "generation_s": round(gen_elapsed, 1),
            "evaluation_s": round(eval_elapsed, 1),
            "total_s": round(total_elapsed, 1),
            "per_question_eval_s": round(eval_elapsed / len(questions), 1),
        },
        "config": {
            "model": chat_model,
            "embed_model": embed_model,
            "top_k": settings.RAG_TOP_K,
            "max_distance": settings.RAG_MAX_DISTANCE,
            "keep_alive": "5m",
            "num_predict": 200,
        },
        "run_timestamp": timestamp,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    with open(partial_out, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    print(f"\nResults saved to {out_file} and {partial_out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation locally.")
    parser.add_argument("--user_id", required=True, help="UUID of the test user who owns the documents")
    args = parser.parse_args()

    # Run from the root of rag-service so relative paths work
    run_evaluation(args.user_id)
