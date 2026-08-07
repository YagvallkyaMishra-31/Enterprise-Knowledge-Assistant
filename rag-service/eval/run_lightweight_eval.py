"""
Lightweight RAG Evaluation — designed for memory-constrained systems.

This script avoids the full RAGAS pipeline (which requires 2 models loaded
simultaneously as judge) and instead:
  1. Embeds + retrieves one question at a time
  2. Generates an answer using the chat model
  3. Scores retrieval quality using keyword overlap (no LLM judge needed)
  4. Scores answer quality using keyword overlap with ground truth
  5. Produces a scorecard comparable to RAGAS metrics

This approach works on systems with ~4GB available RAM (enough for one
Ollama model at a time) instead of requiring ~6GB+ for simultaneous models.
"""
import json
import os
import sys
import time
import datetime
import re
import argparse
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.retrieval import retrieve_chunks
from app.core.generation import generate_answer_stream
from app.core.config import settings


def keyword_overlap(text_a: str, text_b: str) -> float:
    """Simple keyword overlap score between two texts (0.0 to 1.0)."""
    if not text_a or not text_b:
        return 0.0
    words_a = set(re.findall(r'\b[a-z]{3,}\b', text_a.lower()))
    words_b = set(re.findall(r'\b[a-z]{3,}\b', text_b.lower()))
    if not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_b)


def key_fact_recall(answer: str, ground_truth: str) -> float:
    """
    Checks how many 'key facts' from the ground truth appear in the answer.
    Key facts are numbers, proper nouns (capitalized words), and important terms.
    """
    if not answer or not ground_truth:
        return 0.0
    
    # Extract key facts: numbers, capitalized words, quoted phrases
    numbers_gt = set(re.findall(r'\b\d+[\d,\.]*\b', ground_truth))
    numbers_ans = set(re.findall(r'\b\d+[\d,\.]*\b', answer))
    
    proper_nouns_gt = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', ground_truth))
    proper_nouns_ans = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', answer))
    
    all_facts_gt = numbers_gt | proper_nouns_gt
    all_facts_ans = numbers_ans | proper_nouns_ans
    
    if not all_facts_gt:
        return keyword_overlap(answer, ground_truth)
    
    return len(all_facts_gt & all_facts_ans) / len(all_facts_gt)


def context_has_answer(contexts: List[str], ground_truth: str) -> float:
    """Checks if the retrieved context contains the key information for the ground truth."""
    combined = " ".join(contexts)
    return key_fact_recall(combined, ground_truth)


def faithfulness_check(answer: str, contexts: List[str]) -> float:
    """
    Simple faithfulness: what fraction of the answer's key claims 
    can be found in the context?
    """
    if not answer or not contexts:
        return 0.0
    combined_context = " ".join(contexts).lower()
    
    # Extract key claims from answer (numbers and proper nouns)
    numbers = set(re.findall(r'\b\d+[\d,\.]*\b', answer))
    proper_nouns = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', answer))
    
    claims = numbers | {pn.lower() for pn in proper_nouns}
    if not claims:
        return keyword_overlap(answer, " ".join(contexts))
    
    supported = sum(1 for c in claims if c.lower() in combined_context)
    return supported / len(claims)


def run_lightweight_eval(user_id: str):
    """Run the lightweight evaluation."""
    run_start = time.perf_counter()
    
    print(f"{'='*60}")
    print("LIGHTWEIGHT RAG EVALUATION")
    print(f"{'='*60}")
    print(f"User ID: {user_id}")
    print(f"TOP_K: {settings.RAG_TOP_K}, MAX_DISTANCE: {settings.RAG_MAX_DISTANCE}")
    print(f"LLM: {settings.OLLAMA_CHAT_MODEL} at {settings.OLLAMA_BASE_URL}")
    print()

    with open("eval/test_questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    results = []
    
    print(f"--- Evaluating {len(questions)} questions ---\n")
    
    for idx, q_data in enumerate(questions, 1):
        q_start = time.perf_counter()
        q = q_data["question"]
        gt = q_data["expected_answer"]
        category = q_data.get("category", "unknown")
        
        print(f"[{idx}/{len(questions)}] {q}")
        
        # 1. Retrieve
        try:
            chunks = retrieve_chunks(
                user_id=user_id,
                question=q,
                top_k=settings.RAG_TOP_K,
                max_distance=settings.RAG_MAX_DISTANCE
            )
            context_texts = [c["chunkText"] for c in chunks]
            print(f"  Retrieved: {len(chunks)} chunks")
        except Exception as e:
            print(f"  ERROR retrieving: {e}")
            chunks = []
            context_texts = []
        
        # 2. Generate
        try:
            answer = ""
            for token_json in generate_answer_stream(q, chunks):
                try:
                    token_data = json.loads(token_json)
                    if token_data.get("type") == "token":
                        answer += token_data.get("text", "")
                except Exception:
                    pass
            print(f"  Answer: {answer[:150]}{'...' if len(answer) > 150 else ''}")
        except Exception as e:
            print(f"  ERROR generating: {e}")
            answer = ""
        
        # 3. Score (no LLM judge needed!)
        ctx_recall = context_has_answer(context_texts, gt)
        keyword_overlap_score = context_has_answer(context_texts, gt)
        ans_relevancy = keyword_overlap(answer, q)
        fact_mention_rate = faithfulness_check(answer, context_texts)
        fact_recall = key_fact_recall(answer, gt)
        
        q_elapsed = time.perf_counter() - q_start
        
        result = {
            "question": q,
            "category": category,
            "answer": answer,
            "ground_truth": gt,
            "num_chunks": len(chunks),
            "keyword_overlap_score": round(keyword_overlap_score, 4),
            "answer_relevancy": round(ans_relevancy, 4),
            "fact_mention_rate": round(fact_mention_rate, 4),
            "fact_recall": round(fact_recall, 4),
            "time_s": round(q_elapsed, 1),
        }
        results.append(result)
        
        print(f"  Scores: keyword_overlap_score={keyword_overlap_score:.2f} | fact_mention_rate={fact_mention_rate:.2f} | fact_recall={fact_recall:.2f} | relevancy={ans_relevancy:.2f}")
        print(f"  Time: {q_elapsed:.1f}s")
        print()
        
        # Save incrementally
        _save_results(results, run_start)

    total_elapsed = time.perf_counter() - run_start
    
    # Final scorecard
    print(f"\n{'='*60}")
    print("AGGREGATE SCORECARD")
    print(f"{'='*60}")
    
    metrics = ["context_recall", "faithfulness", "fact_recall", "answer_relevancy"]
    aggregate = {}
    for m in metrics:
        vals = [r[m] for r in results]
        avg = sum(vals) / len(vals) if vals else 0
        aggregate[m] = round(avg, 4)
        print(f"  {m}: {avg:.4f}")
    
    print(f"\n{'='*60}")
    print("PER-CATEGORY BREAKDOWN")
    print(f"{'='*60}")
    
    categories = set(r["category"] for r in results)
    for cat in sorted(categories):
        cat_results = [r for r in results if r["category"] == cat]
        print(f"\n  {cat} ({len(cat_results)} questions):")
        for m in metrics:
            vals = [r[m] for r in cat_results]
            avg = sum(vals) / len(vals) if vals else 0
            print(f"    {m}: {avg:.4f}")
    
    print(f"\n{'='*60}")
    print("TIMING")
    print(f"{'='*60}")
    times = [r["time_s"] for r in results]
    print(f"  Total: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"  Avg per question: {sum(times)/len(times):.1f}s")
    print(f"  Min: {min(times):.1f}s | Max: {max(times):.1f}s")
    
    # Save final
    _save_results(results, run_start, final=True, aggregate=aggregate)
    print(f"\nResults saved to eval/results/")


def _save_results(results, run_start, final=False, aggregate=None):
    os.makedirs("eval/results", exist_ok=True)
    total_elapsed = time.perf_counter() - run_start
    
    output = {
        "status": "complete" if final else "in_progress",
        "aggregate": aggregate or {},
        "questions": results,
        "timing": {
            "total_s": round(total_elapsed, 1),
            "total_min": round(total_elapsed / 60, 1),
        },
        "config": {
            "model": settings.OLLAMA_CHAT_MODEL,
            "top_k": settings.RAG_TOP_K,
            "max_distance": settings.RAG_MAX_DISTANCE,
            "eval_type": "lightweight_keyword",
        },
    }
    
    with open("eval/results/latest_run.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    
    if final:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"eval/results/lightweight_{ts}.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lightweight RAG evaluation")
    parser.add_argument("--user_id", required=True)
    args = parser.parse_args()
    run_lightweight_eval(args.user_id)
