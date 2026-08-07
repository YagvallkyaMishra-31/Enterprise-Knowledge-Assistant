import requests
import json
import uuid
import time
import os

BASE = "http://localhost:8080"
uid = uuid.uuid4().hex[:6]
email = f"eval_user_{uid}@test.com"

# 1. Register User
print(f"Registering user {email}...")
r = requests.post(f"{BASE}/api/auth/register",
                  json={"email": email, "password": "Test1234!", "fullName": "Eval User"})
r.raise_for_status()
data = r.json()
token = data.get("accessToken") or data.get("token")

# Extract userId from JWT payload (or we could just login if backend returns it, but JWT is easier)
import base64
payload = token.split('.')[1]
# pad if needed
payload += "=" * ((4 - len(payload) % 4) % 4)
jwt_data = json.loads(base64.b64decode(payload).decode('utf-8'))
user_id = jwt_data.get("userId") or jwt_data.get("sub")
# Actually Spring Boot usually puts sub as email, but we might have a specific claim. Let's see.

# Wait, `test_full.py` does:
# r.json().get("accessToken")
# The best way to get the exact user ID string is to look at the database or if the auth response includes it.
# Let's print the JWT decoded and the user_id.
print(f"JWT Data: {jwt_data}")

docs_to_upload = ["eval_docs/apollo11.txt", "eval_docs/photosynthesis.txt"]
doc_ids = []

for doc_path in docs_to_upload:
    print(f"Uploading {doc_path}...")
    with open(doc_path, "rb") as f:
        res = requests.post(
            f"{BASE}/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (os.path.basename(doc_path), f, "text/plain")}
        )
        res.raise_for_status()
        d_id = res.json()["id"]
        doc_ids.append(d_id)
        print(f"  -> Uploaded as ID: {d_id}")

print("Waiting for documents to be READY...")
for d_id in doc_ids:
    while True:
        res = requests.get(
            f"{BASE}/api/documents/{d_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        doc_data = res.json()
        status = doc_data.get("uploadStatus") or doc_data.get("status")
        print(f"  Doc {d_id} status: {status}")
        if status == "READY":
            break
        elif status == "FAILED":
            print(f"  Doc processing FAILED! Response: {doc_data}")
            exit(1)
        time.sleep(3)

user_id = jwt_data.get('userId')
print(f"\nSUCCESS! User ID is: {user_id}")
print(f"Run the eval script with: python rag-service/eval/run_evaluation.py --user_id {user_id}")
