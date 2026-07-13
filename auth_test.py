import jwt
import time
import os
from dotenv import load_dotenv
import requests

load_dotenv()

APP_ID = os.getenv("GITHUB_APP_ID")
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")

def generate_jwt():
    with open(PRIVATE_KEY_PATH, "r") as f:
        private_key = f.read()

    now = int(time.time())
    payload = {
        "iat": now - 60,       # issued-at, backdated 60s to allow for clock drift
        "exp": now + (9 * 60), # expires in 9 minutes (GitHub caps this at 10)
        "iss": APP_ID,         # who's asking — your App ID
    }
    return jwt.encode(payload, private_key, algorithm="RS256")

def get_installation_id(jwt_token, owner, repo):
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/installation",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        },
    )
    resp.raise_for_status()
    return resp.json()["id"]

def get_installation_token(jwt_token, installation_id):
    resp = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        },
    )
    resp.raise_for_status()
    return resp.json()["token"]

def get_pr_files(access_token, owner, repo, pr_number):
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        },
    )
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    jwt_token = generate_jwt()
    installation_id = get_installation_id(jwt_token, "pruthvi1405", "UnionFind")
    print("Installation ID:", installation_id)

    access_token = get_installation_token(jwt_token, installation_id)
    files = get_pr_files(access_token, "pruthvi1405", "UnionFind", 2)
    for f in files:
        print(f["filename"], "-", f["status"], f"(+{f['additions']}/-{f['deletions']})")