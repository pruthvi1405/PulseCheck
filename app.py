from auth_test import generate_jwt, get_installation_id, get_installation_token, get_pr_files
from fastapi import FastAPI, Request, HTTPException
from helper import fetch_file_content, post_review, run_eslint
from llm_review import call_llm_review
import uvicorn
import hmac, hashlib, json
from dotenv import load_dotenv
import os


load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

LINTABLE_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx")

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
        owner = payload["repository"]["owner"]["login"]
        repo = payload["repository"]["name"]
        pr_number = payload["number"]
        commit_sha = payload["pull_request"]["head"]["sha"]

        print(f"PR #{pr_number} needs review: {payload['pull_request']['title']}", flush=True)
        token = generate_jwt()
        installation_id = get_installation_id(token, owner, repo)
        access_token = get_installation_token(token, installation_id)
        files = get_pr_files(access_token, owner, repo, pr_number)

        review_comments = []
        for f in files:
            if f["status"] == "removed" or not f["filename"].endswith(LINTABLE_EXTENSIONS):
                continue
            try:
                llm_issues = call_llm_review(f["filename"], f.get("patch", ""))
            except Exception as e:
                print(f"  {f['filename']}: LLM review skipped due to error ({e})", flush=True)
                llm_issues = []
            for issue in llm_issues:
                review_comments.append({
                    "path": f["filename"],
                    "line": issue["line"],
                    "side": "RIGHT",
                    "body": f"🤖 **AI review ({issue['severity']})**: {issue['comment']}",
                })
            try:
                content = fetch_file_content(access_token, owner, repo, f["filename"], commit_sha)
                messages = run_eslint(content, f["filename"])
            except Exception as e:
                print(f"  {f['filename']}: lint skipped due to error ({e})", flush=True)
                messages = []
            for m in messages:
                review_comments.append({
                    "path": f["filename"],
                    "line": m["line"],
                    "side": "RIGHT",
                    "body": f"**{m['ruleId']}**: {m['message']}",
                })

            print(f"  {f['filename']}: {len(messages)} issue(s)", flush=True)
        post_review(access_token, owner, repo, pr_number, commit_sha, review_comments)
        print(f"Posted {len(review_comments)} comment(s) to PR #{pr_number}", flush=True)
    else:
        print(f"Ignoring event: {event_type} / action: {payload.get('action')}", flush=True)
    return {"status": "received"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)