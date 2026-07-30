import requests
BASE_URL = "http://localhost:8080"
import uuid
u = "u" + uuid.uuid4().hex[:8] + "@x.com"
u2 = "u2" + uuid.uuid4().hex[:8] + "@x.com"
t1 = requests.post(f"{BASE_URL}/api/auth/register", json={"email":u, "password":"password123", "fullName":"u"}).json()["accessToken"]
t2 = requests.post(f"{BASE_URL}/api/auth/register", json={"email":u2, "password":"password123", "fullName":"u2"}).json()["accessToken"]
sid = requests.post(f"{BASE_URL}/api/chat/sessions", headers={"Authorization": f"Bearer {t1}", "Content-Type": "application/json"}, json={"title":"t"}).json()["id"]
r = requests.get(f"{BASE_URL}/api/chat/sessions/{sid}/messages", headers={"Authorization": f"Bearer {t2}"})
print(r.status_code)
print(r.text)
