#!/usr/bin/env python3
"""Manual step-by-step recovery diagnosis script.
Each phase prints real output. Run with PYTHONIOENCODING=utf-8."""
import requests, time, sys, json, subprocess, uuid, os

BASE = "http://localhost:8080"
uid = uuid.uuid4().hex[:6]

def register(email):
    r = requests.post(f"{BASE}/api/auth/register",
                      json={"email": email, "password": "Test1234!", "fullName": "Recovery Test"})
    data = r.json()
    return data.get("accessToken") or data.get("token")

# --- Setup: register user, create session, upload doc ---
print("=== SETUP ===")
token = register(f"recovery_{uid}@test.com")
h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print(f"  Registered user, got token: {token[:20]}...")

r = requests.post(f"{BASE}/api/chat/sessions", headers=h, json={"title": "RecoveryTest"})
sid = r.json()["id"]
print(f"  Created session: {sid}")

# Upload a small doc
fact_path = os.path.join(os.path.dirname(__file__), "fact.txt")
if not os.path.exists(fact_path):
    with open(fact_path, "w") as f:
        f.write("The secret code word for the project is FLAMINGO.")
with open(fact_path, "rb") as f:
    r = requests.post(f"{BASE}/api/documents",
                      headers={"Authorization": f"Bearer {token}"},
                      files={"file": ("fact.txt", f, "text/plain")})
doc_id = r.json()["id"]
print(f"  Uploaded doc: {doc_id}")

# Wait for doc to be READY
for _ in range(30):
    r = requests.get(f"{BASE}/api/documents/{doc_id}",
                     headers={"Authorization": f"Bearer {token}"})
    if r.json().get("status") == "READY":
        break
    time.sleep(1)
print(f"  Doc status: {r.json().get('status')}")

# ============================================================
# STEP 2.1: Confirm system healthy with a successful /ask
# ============================================================
print("\n=== STEP 2.1: Healthy /ask request ===")
r = requests.post(f"{BASE}/api/chat/sessions/{sid}/ask", headers=h,
                  json={"question": "What is the secret code word?"}, stream=True, timeout=120)
print(f"  HTTP {r.status_code}")
full_text = ""
for raw in r.iter_lines():
    if not raw:
        continue
    line = raw.decode()
    print(f"  {line}")
    if '"text"' in line:
        try:
            d = json.loads(line.split("data:", 1)[1]) if "data:" in line else json.loads(line)
            full_text += d.get("text", "")
        except:
            pass
    if "done" in line:
        break
print(f"  Full answer: {full_text}")
if full_text:
    print("  >>> STEP 2.1 RESULT: PASS")
else:
    print("  >>> STEP 2.1 RESULT: FAIL")
    sys.exit(1)

# ============================================================
# STEP 2.2: docker compose stop rag-service
# ============================================================
print("\n=== STEP 2.2: Stopping rag-service ===")
result = subprocess.run(["docker", "compose", "stop", "rag-service"],
                       capture_output=True, text=True, cwd=os.path.dirname(__file__))
print(f"  stdout: {result.stdout.strip()}")
print(f"  stderr: {result.stderr.strip()}")
time.sleep(2)

# ============================================================
# STEP 2.3: Send /ask while rag-service is down
# ============================================================
print("\n=== STEP 2.3: /ask with rag-service DOWN ===")
r = requests.post(f"{BASE}/api/chat/sessions/{sid}/ask", headers=h,
                  json={"question": "What is the code word?"}, stream=True, timeout=30)
print(f"  HTTP {r.status_code}")
got_error = False
try:
    for raw in r.iter_lines():
        if not raw:
            continue
        line = raw.decode()
        print(f"  {line}")
        if "error" in line.lower():
            got_error = True
            break
except Exception as e:
    print(f"  Connection error (expected): {e}")
    got_error = True

if got_error:
    print("  >>> STEP 2.3 RESULT: PASS (error event received)")
else:
    print("  >>> STEP 2.3 RESULT: FAIL (no error event)")

# ============================================================
# STEP 2.4: docker compose start rag-service
# ============================================================
print("\n=== STEP 2.4: Starting rag-service ===")
result = subprocess.run(["docker", "compose", "start", "rag-service"],
                       capture_output=True, text=True, cwd=os.path.dirname(__file__))
print(f"  stdout: {result.stdout.strip()}")
print(f"  stderr: {result.stderr.strip()}")

# ============================================================
# STEP 2.5: Wait 5 seconds, then /ask again
# ============================================================
print("\n=== STEP 2.5: Waiting 5 seconds, then recovery /ask ===")
time.sleep(5)

# Verify rag-service is actually up
result = subprocess.run(["docker", "compose", "ps", "rag-service"],
                       capture_output=True, text=True, cwd=os.path.dirname(__file__))
print(f"  rag-service status: {result.stdout.strip()}")

r = requests.post(f"{BASE}/api/chat/sessions/{sid}/ask", headers=h,
                  json={"question": "Tell me the secret code word from the document."},
                  stream=True, timeout=120)
print(f"  HTTP {r.status_code}")
recovered = False
recovery_text = ""
error_data = ""
try:
    for raw in r.iter_lines():
        if not raw:
            continue
        line = raw.decode()
        print(f"  {line}")
        if '"text"' in line:
            try:
                d = json.loads(line.split("data:", 1)[1]) if "data:" in line else json.loads(line)
                recovery_text += d.get("text", "")
            except:
                pass
        if "error" in line.lower():
            error_data = line
        if "done" in line:
            recovered = True
            break
except Exception as e:
    print(f"  Exception: {e}")

print(f"  Full answer: {recovery_text}")
if recovered:
    print("  >>> STEP 2.5 RESULT: PASS (recovery successful)")
else:
    print(f"  >>> STEP 2.5 RESULT: FAIL (recovery failed)")
    if error_data:
        print(f"  >>> Error data: {error_data}")

# ============================================================
# Capture logs for diagnosis
# ============================================================
print("\n=== BACKEND LOGS (last 30 lines) ===")
result = subprocess.run(["docker", "compose", "logs", "backend", "--tail", "30"],
                       capture_output=True, text=True, cwd=os.path.dirname(__file__))
print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)

print("\n=== RAG-SERVICE LOGS (last 15 lines) ===")
result = subprocess.run(["docker", "compose", "logs", "rag-service", "--tail", "15"],
                       capture_output=True, text=True, cwd=os.path.dirname(__file__))
print(result.stdout)

print("\n=== DONE ===")
