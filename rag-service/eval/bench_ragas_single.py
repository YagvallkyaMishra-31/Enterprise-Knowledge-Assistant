"""
Throwaway benchmark: make TWO consecutive RAGAS faithfulness calls.
Call 1 = cold (model loads from disk).
Call 2 = warm (model should still be in memory if OLLAMA_KEEP_ALIVE>=5m).
Reports wall-clock seconds for each call.
"""
import os, time, sys
os.environ.setdefault("OPENAI_API_KEY", "not-needed")

from ragas import evaluate
from ragas.metrics import faithfulness
from datasets import Dataset
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

# One minimal sample — just enough to trigger a real RAGAS faithfulness computation
sample = {
    "question": ["When did Apollo 11 launch?"],
    "answer": ["Apollo 11 launched on July 16, 1969, at 13:32 UTC from Kennedy Space Center."],
    "contexts": [["Apollo 11 was launched by a Saturn V rocket from Kennedy Space Center on Merritt Island, Florida, on July 16 at 13:32 UTC."]],
    "ground_truth": ["Apollo 11 launched on July 16, 1969."],
}

ds = Dataset.from_dict(sample)

llm = ChatOllama(model="phi3:mini", base_url=OLLAMA_URL, temperature=0)
embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_URL)

print(f"OLLAMA_BASE_URL: {OLLAMA_URL}")
print(f"OLLAMA_KEEP_ALIVE env: {os.environ.get('OLLAMA_KEEP_ALIVE', '(not set)')}")
print()

# --- CALL 1 (cold) ---
print("=== CALL 1 (cold — model loading from disk) ===")
t1_start = time.perf_counter()
result1 = evaluate(ds, metrics=[faithfulness], llm=llm, embeddings=embeddings)
t1_end = time.perf_counter()
t1 = t1_end - t1_start
print(f"  faithfulness score: {result1['faithfulness']:.4f}")
print(f"  wall-clock: {t1:.1f}s")
print()

# --- CALL 2 (warm — model should still be in memory) ---
print("=== CALL 2 (warm — model should be cached in RAM) ===")
t2_start = time.perf_counter()
result2 = evaluate(ds, metrics=[faithfulness], llm=llm, embeddings=embeddings)
t2_end = time.perf_counter()
t2 = t2_end - t2_start
print(f"  faithfulness score: {result2['faithfulness']:.4f}")
print(f"  wall-clock: {t2:.1f}s")
print()

# --- COMPARISON ---
print("=== COMPARISON ===")
print(f"  Cold call: {t1:.1f}s")
print(f"  Warm call: {t2:.1f}s")
speedup = t1 / t2 if t2 > 0 else float('inf')
print(f"  Speedup:   {speedup:.1f}x")
if t1 > 60 and t2 < t1 * 0.5:
    print(f"  CONCLUSION: Model-reload was the bottleneck. Cold={t1:.0f}s vs Warm={t2:.0f}s.")
    print(f"              With OLLAMA_KEEP_ALIVE=5m, the model stays warm between calls.")
else:
    print(f"  CONCLUSION: Both calls took similar time. Raw inference is the bottleneck, not model reload.")
