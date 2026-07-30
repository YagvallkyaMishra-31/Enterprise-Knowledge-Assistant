import requests
import uuid
import json
import sseclient
import time

BASE_URL = "http://localhost:8080"

def print_curl(method, url, headers=None, json_body=None):
    curl = f"curl -X {method} {url}"
    if headers:
        for k, v in headers.items():
            if k.lower() != "authorization": # hide token
                curl += f' -H "{k}: {v}"'
            else:
                curl += f' -H "Authorization: Bearer <token>"'
    if json_body:
        curl += f" -d '{json.dumps(json_body)}'"
    print(f"\nExecuting: {curl}")

def register_and_login(email, name):
    reg_body = {"email": email, "password": "password123", "fullName": name}
    r = requests.post(f"{BASE_URL}/api/auth/register", json=reg_body)
    return r.json().get("accessToken")

# Setup users
u1_email = f"user1_{uuid.uuid4().hex[:8]}@example.com"
u2_email = f"user2_{uuid.uuid4().hex[:8]}@example.com"

token1 = register_and_login(u1_email, "User One")
token2 = register_and_login(u2_email, "User Two")

headers1 = {"Authorization": f"Bearer {token1}"}
headers1_json = {"Authorization": f"Bearer {token1}", "Content-Type": "application/json"}
headers2_json = {"Authorization": f"Bearer {token2}", "Content-Type": "application/json"}

print("\n--- a. POST /api/chat/sessions - real response ---")
print_curl("POST", f"{BASE_URL}/api/chat/sessions", headers1_json, {"title": "My Session"})
resp = requests.post(f"{BASE_URL}/api/chat/sessions", headers=headers1_json, json={"title": "My Session"})
print(f"HTTP {resp.status_code}\n{json.dumps(resp.json(), indent=2)}")
session_id = resp.json()["id"]

print("\n--- Uploading real document context ---")
# Upload a document
files = {'file': ('fact.txt', 'The secret code word for the project is FLAMINGO.', 'text/plain')}
upload_resp = requests.post(f"{BASE_URL}/api/documents", headers=headers1, files=files)
doc_id = upload_resp.json()["id"]
print(f"Uploaded document {doc_id}. Waiting for READY state...")
while True:
    time.sleep(1)
    status_resp = requests.get(f"{BASE_URL}/api/documents/{doc_id}", headers=headers1)
    status = status_resp.json()["uploadStatus"]
    if status == "READY":
        print("Document is READY and embedded!")
        break
    elif status == "FAILED":
        print("Document failed processing!")
        exit(1)

print("\n--- b. POST /api/chat/sessions/{id}/ask (Grounded) ---")
print_curl("POST", f"{BASE_URL}/api/chat/sessions/{session_id}/ask", headers1_json, {"question": "What is the secret code word for the project?"})
resp_sse = requests.post(f"{BASE_URL}/api/chat/sessions/{session_id}/ask", headers=headers1_json, json={"question": "What is the secret code word for the project?"}, stream=True)
print(f"HTTP {resp_sse.status_code}")
client = sseclient.SSEClient(resp_sse)
for event in client.events():
    print(f"Event: {event.event} | Data: {event.data}")
    if json.loads(event.data)["type"] == "done":
        break

print("\n--- c. GET /api/chat/sessions/{id}/messages ---")
print_curl("GET", f"{BASE_URL}/api/chat/sessions/{session_id}/messages", headers1_json)
resp_msgs = requests.get(f"{BASE_URL}/api/chat/sessions/{session_id}/messages", headers=headers1_json)
print(f"HTTP {resp_msgs.status_code}\n{json.dumps(resp_msgs.json(), indent=2)}")

print("\n--- e. Unrelated question - empty sources + fallback ---")
resp_unrelated = requests.post(f"{BASE_URL}/api/chat/sessions/{session_id}/ask", headers=headers1_json, json={"question": "What is the distance to the moon?"}, stream=True)
print(f"HTTP {resp_unrelated.status_code}")
unrelated_client = sseclient.SSEClient(resp_unrelated)
for event in unrelated_client.events():
    print(f"Event: {event.event} | Data: {event.data}")
    if json.loads(event.data)["type"] == "done":
        break

print("\n--- f. Second user's token against first user's session ---")
resp_iso_get = requests.get(f"{BASE_URL}/api/chat/sessions/{session_id}/messages", headers=headers2_json)
print(f"GET /messages HTTP {resp_iso_get.status_code}")
resp_iso_post = requests.post(f"{BASE_URL}/api/chat/sessions/{session_id}/ask", headers=headers2_json, json={"question": "Hack"})
print(f"POST /ask HTTP {resp_iso_post.status_code}")

print("\n--- d. 11 rapid requests - real 429 on the 11th ---")
# 1st request was b, 2nd was e, so we need 9 more to hit 11 total. Let's just blast 11 to be sure.
for i in range(11):
    r = requests.post(f"{BASE_URL}/api/chat/sessions/{session_id}/ask", headers=headers1_json, json={"question": "Rapid fire!"}, stream=True)
    print(f"Request {i+1}: HTTP {r.status_code}")
    if r.status_code == 429:
        print(f"429 received: {r.text}")
        break

