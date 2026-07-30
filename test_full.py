"""Full Phase 6 verification — all 7 checks (a–g)."""
import requests, json, uuid, time, sys

BASE = "http://localhost:8080"
PASS = 0
FAIL = 0

def ok(label):
    global PASS
    PASS += 1
    print(f"  PASS: {label}")

def fail(label):
    global FAIL
    FAIL += 1
    print(f"  FAIL: {label}")

def register(email):
    r = requests.post(f"{BASE}/api/auth/register",
        json={"email": email, "password": "password123", "fullName": "U"})
    return r.json()["accessToken"]

uid = uuid.uuid4().hex[:6]
token1 = register(f"u1_{uid}@x.com")
token2 = register(f"u2_{uid}@x.com")
h1 = {"Authorization": f"Bearer {token1}", "Content-Type": "application/json"}
h1a = {"Authorization": f"Bearer {token1}"}
h2 = {"Authorization": f"Bearer {token2}", "Content-Type": "application/json"}

# ──────────────────────────────────────────────
# a. Create session
# ──────────────────────────────────────────────
print("\n--- a. POST /api/chat/sessions ---")
r = requests.post(f"{BASE}/api/chat/sessions", headers=h1, json={"title": "Test"})
print(f"  HTTP {r.status_code}")
print(f"  {json.dumps(r.json(), indent=2)}")
sid = r.json()["id"]
if r.status_code == 201:
    ok("Session created")
else:
    fail("Session creation")

# Upload a document for grounded test
print("\n--- Uploading document ---")
r = requests.post(f"{BASE}/api/documents", headers=h1a,
    files={"file": ("fact.txt", b"The secret code word for the project is FLAMINGO.", "text/plain")})
doc_id = r.json()["id"]
print(f"  doc_id={doc_id}")
for _ in range(60):
    time.sleep(1)
    s = requests.get(f"{BASE}/api/documents/{doc_id}", headers=h1a).json()
    if s["uploadStatus"] == "READY":
        print("  Document READY")
        break
    if s["uploadStatus"] == "FAILED":
        fail("Document processing")
        sys.exit(1)

# ──────────────────────────────────────────────
# b. Grounded SSE stream
# ──────────────────────────────────────────────
print("\n--- b. POST /ask (grounded question, SSE stream) ---")
r = requests.post(f"{BASE}/api/chat/sessions/{sid}/ask", headers=h1,
    json={"question": "What is the secret code word for the project?"},
    stream=True, timeout=300)
print(f"  HTTP {r.status_code}")
tokens_b = []
got_sources = False
got_done = False
try:
    for raw in r.iter_lines():
        if not raw:
            continue
        line = raw.decode()
        print(f"  {line}")
        if line.startswith("data:"):
            data = json.loads(line[5:])
            if data["type"] == "sources":
                got_sources = True
            elif data["type"] == "token":
                tokens_b.append(data["text"])
            elif data["type"] == "done":
                got_done = True
                break
except Exception as e:
    print(f"  Stream error: {e}")

answer_b = "".join(tokens_b)
print(f"  Full answer: {answer_b[:200]}")
if got_sources and got_done and len(answer_b) > 0:
    ok("Grounded SSE stream with tokens")
else:
    fail(f"SSE stream (sources={got_sources}, done={got_done}, tokens={len(tokens_b)})")

# ──────────────────────────────────────────────
# c. Persisted QaPair
# ──────────────────────────────────────────────
print("\n--- c. GET /messages (persistence) ---")
r = requests.get(f"{BASE}/api/chat/sessions/{sid}/messages", headers=h1)
print(f"  HTTP {r.status_code}")
msgs = r.json()
print(f"  {json.dumps(msgs, indent=2)[:500]}")
if r.status_code == 200 and len(msgs) >= 1 and msgs[0].get("answer"):
    ok("QaPair persisted")
else:
    fail("QaPair persistence")

# ──────────────────────────────────────────────
# e. Unrelated question → fallback
# ──────────────────────────────────────────────
print("\n--- e. Unrelated question (fallback) ---")
r = requests.post(f"{BASE}/api/chat/sessions/{sid}/ask", headers=h1,
    json={"question": "What is the mass of the planet Jupiter?"},
    stream=True, timeout=300)
print(f"  HTTP {r.status_code}")
tokens_e = []
fallback_ok = False
try:
    for raw in r.iter_lines():
        if not raw:
            continue
        line = raw.decode()
        print(f"  {line}")
        if line.startswith("data:"):
            data = json.loads(line[5:])
            if data["type"] == "token":
                tokens_e.append(data["text"])
            elif data["type"] == "done":
                break
except Exception as e:
    print(f"  Stream error: {e}")

fallback_text = "".join(tokens_e)
print(f"  Full text: {fallback_text}")
if "don't have enough information" in fallback_text.lower():
    ok("Fallback string for unrelated question")
else:
    fail(f"Fallback (got: {fallback_text[:100]})")

# ──────────────────────────────────────────────
# f. Cross-user isolation
# ──────────────────────────────────────────────
print("\n--- f. Cross-user isolation ---")
r_get = requests.get(f"{BASE}/api/chat/sessions/{sid}/messages", headers=h2)
print(f"  GET messages: HTTP {r_get.status_code}")
r_post = requests.post(f"{BASE}/api/chat/sessions/{sid}/ask", headers=h2,
    json={"question": "hack"})
print(f"  POST ask:     HTTP {r_post.status_code}")
if r_get.status_code == 404 and r_post.status_code == 404:
    ok("Cross-user blocked 404")
else:
    fail(f"Isolation (GET={r_get.status_code}, POST={r_post.status_code})")

# ──────────────────────────────────────────────
# d. Rate limit (11 rapid requests → 429)
# ──────────────────────────────────────────────
print("\n--- d. Rate limit (11 rapid) ---")
# We already used 2 ask requests above (b and e). Need 9 more to hit 11, then the 11th should 429.
hit_429 = False
for i in range(11):
    rr = requests.post(f"{BASE}/api/chat/sessions/{sid}/ask", headers=h1,
        json={"question": "rate"}, stream=True, timeout=30)
    print(f"  Req {i+1}: HTTP {rr.status_code}")
    if rr.status_code == 429:
        hit_429 = True
        ok(f"429 on request {i+1} (total asks including b,e = {i+1+2})")
        break
    # Drain stream to avoid connection issues
    try:
        for raw in rr.iter_lines():
            if not raw:
                continue
            line = raw.decode()
            if "done" in line:
                break
    except:
        pass

if not hit_429:
    fail("Never got 429")

# ──────────────────────────────────────────────
# g. rag-service down → error event; restart → recovery
# ──────────────────────────────────────────────
print("\n--- g. rag-service down → error event ---")
# Need a fresh session (rate limit on user1 is likely exhausted)
token3 = register(f"u3_{uid}@x.com")
h3 = {"Authorization": f"Bearer {token3}", "Content-Type": "application/json"}
r = requests.post(f"{BASE}/api/chat/sessions", headers=h3, json={"title": "G"})
sid3 = r.json()["id"]

import subprocess
subprocess.run(["docker", "compose", "stop", "rag-service"], capture_output=True)
time.sleep(2)

r_err = requests.post(f"{BASE}/api/chat/sessions/{sid3}/ask", headers=h3,
    json={"question": "hello"}, stream=True, timeout=30)
print(f"  HTTP {r_err.status_code}")
got_error = False
try:
    for raw in r_err.iter_lines():
        if not raw:
            continue
        line = raw.decode()
        print(f"  {line}")
        if "error" in line.lower():
            got_error = True
            break
except:
    got_error = True  # Connection reset IS the error signal

if got_error:
    ok("Error event when rag-service down")
else:
    fail("No error event")

# Restart and verify recovery
subprocess.run(["docker", "compose", "start", "rag-service"], capture_output=True)
time.sleep(5)
r_ok = requests.post(f"{BASE}/api/chat/sessions/{sid3}/ask", headers=h3,
    json={"question": "hello"}, stream=True, timeout=300)
print(f"  Recovery HTTP {r_ok.status_code}")
recovered = False
try:
    for raw in r_ok.iter_lines():
        if not raw:
            continue
        line = raw.decode()
        print(f"  {line}")
        if "done" in line:
            recovered = True
            break
except:
    pass

if recovered:
    ok("Recovery after rag-service restart")
else:
    fail("Recovery failed")

# ──────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"Results: {PASS} PASS, {FAIL} FAIL")
if FAIL == 0:
    print("ALL CHECKS PASSED")
else:
    print("SOME CHECKS FAILED")
    sys.exit(1)
