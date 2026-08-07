"""
Benchmark: cold-load vs warm-load Ollama call time.
Uses a 10-minute timeout for cold calls since they can take 5+ min.
"""
import time, json, httpx, sys

OLLAMA_URL = "http://localhost:11434"
MODEL = "phi3:mini"

PROMPT = (
    "Is the statement 'Apollo 11 launched in 1969' supported by "
    "'Apollo 11 launched on July 16, 1969'? Answer Yes or No."
)


def call_ollama(keep_alive: str, label: str, timeout: int = 600) -> float:
    payload = {
        "model": MODEL,
        "prompt": PROMPT,
        "stream": False,
        "options": {"num_predict": 30},
        "keep_alive": keep_alive,
    }
    t0 = time.perf_counter()
    resp = httpx.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=timeout)
    elapsed = time.perf_counter() - t0
    data = resp.json()
    answer = data.get("response", "")[:80]
    print(f"  [{label}] keep_alive={keep_alive} | {elapsed:.1f}s | answer: {answer}")
    return elapsed


# ── COLD START ──
print("=" * 60)
print("STEP 1: Force-unload model, then make a cold call")
print("=" * 60)
# Unload
httpx.post(f"{OLLAMA_URL}/api/generate",
           json={"model": MODEL, "prompt": "", "keep_alive": "0", "stream": False},
           timeout=120)
time.sleep(3)
print("  Model unloaded. Making cold call (timeout=10min)...")
cold_time = call_ollama("0", "COLD", timeout=600)

# ── WARM START ──
print()
print("=" * 60)
print("STEP 2: Load model with keep_alive=5m, then make warm calls")
print("=" * 60)
load_time = call_ollama("5m", "WARM-LOAD")
warm_time = call_ollama("5m", "WARM-HIT")
warm_time2 = call_ollama("5m", "WARM-HIT-2")

# ── RESULTS ──
print()
print("=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)
print(f"  Cold call (model loaded from disk):  {cold_time:.1f}s")
print(f"  Warm-load (first call, model loads):  {load_time:.1f}s")
print(f"  Warm-hit (model already in memory):   {warm_time:.1f}s")
print(f"  Warm-hit-2 (confirms consistency):    {warm_time2:.1f}s")
if warm_time > 0:
    speedup = cold_time / warm_time
    print(f"  Speedup (cold vs warm-hit): {speedup:.1f}x")
    print()
    print(f"  Projected RAGAS time (60 calls):")
    print(f"    Cold (KEEP_ALIVE=0):  {cold_time * 60 / 60:.0f} min")
    print(f"    Warm (KEEP_ALIVE=5m): {warm_time * 60 / 60:.0f} min")
    print()
    if speedup > 2:
        print("  >>> VERDICT: OLLAMA_KEEP_ALIVE=0 is the ROOT CAUSE. <<<")
    else:
        print("  >>> VERDICT: Keep-alive is NOT the dominant factor. <<<")

# Clean up
httpx.post(f"{OLLAMA_URL}/api/generate",
           json={"model": MODEL, "prompt": "", "keep_alive": "0", "stream": False},
           timeout=120)
print("\nModel unloaded. Benchmark complete.")
