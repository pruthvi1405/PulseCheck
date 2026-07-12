from fastapi import FastAPI, Request, HTTPException
import uvicorn
import hmac, hashlib, json
from dotenv import load_dotenv
import os

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    print(">>> webhook hit", flush=True)
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
    else:
        form = await request.form()
        payload = json.loads(form["payload"])

    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "pull_request" and payload.get("action") in ("opened", "synchronize"):
        print(f"PR #{payload['number']} needs review: {payload['pull_request']['title']}", flush=True)
    else:
        print(f"Ignoring event: {event_type} / action: {payload.get('action')}", flush=True)

    return {"status": "received"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)