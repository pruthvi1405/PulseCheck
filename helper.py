import json
import os
import subprocess
import tempfile
import requests

import time

def fetch_file_content(access_token, owner, repo, path, ref, retries=2):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github.raw+json"}
    for attempt in range(retries + 1):
        resp = requests.get(url, headers=headers, params={"ref": ref})
        if resp.status_code < 500:
            resp.raise_for_status()
            return resp.text
        if attempt < retries:
            time.sleep(1 * (attempt + 1))  # backoff: 1s, then 2s
    resp.raise_for_status()  # out of retries, raise the last error

def run_eslint(file_content: str, filename: str):
    with tempfile.NamedTemporaryFile(mode="w", suffix=os.path.splitext(filename)[1], delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name

    project_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_dir, "eslint-baseline.json")

    result = subprocess.run(
        ["npx", "eslint", "--format", "json", "--no-eslintrc", "--config", config_path, tmp_path],
        capture_output=True, text=True,
        cwd=project_dir,
    )
    os.unlink(tmp_path)

    if result.returncode not in (0, 1):
        print(f"    [eslint error] returncode={result.returncode} stderr={result.stderr}", flush=True)
        return []

    if not result.stdout:
        return []
    parsed = json.loads(result.stdout)
    return parsed[0]["messages"] if parsed else []

def post_review(access_token, owner, repo, pr_number, commit_sha, comments):
    if not comments:
        return  # nothing to post, PR is clean

    resp = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        json={
            "commit_id": commit_sha,
            "event": "COMMENT",  # use "REQUEST_CHANGES" or "APPROVE" instead if you want that behavior
            "body": "PulseCheck automated review",
            "comments": comments,
        },
    )
    resp.raise_for_status()
    return resp.json()