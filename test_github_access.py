#!/usr/bin/env python3
"""Phase 0 check: confirm the GitHub PAT in .env works, and optionally verify
access to a specific test repo.

Usage:
    python3 test_github_access.py                 # just verify the token
    python3 test_github_access.py owner/repo       # also check repo access
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def load_env(path=".env"):
    env = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        env[key.strip()] = value
    return env


def api_get(path, token):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    env = load_env()
    token = env.get("GITHUB_TOKEN")
    if not token:
        print("FAIL: GITHUB_TOKEN not set in .env")
        sys.exit(1)

    try:
        user = api_get("/user", token)
    except urllib.error.HTTPError as e:
        print(f"FAIL: token rejected by GitHub API ({e.code} {e.reason})")
        sys.exit(1)

    print(f"OK: token authenticated as '{user['login']}'")

    if len(sys.argv) > 1:
        repo = sys.argv[1]
        try:
            info = api_get(f"/repos/{repo}", token)
        except urllib.error.HTTPError as e:
            print(f"FAIL: cannot access repo '{repo}' ({e.code} {e.reason})")
            sys.exit(1)
        print(f"OK: token can access '{info['full_name']}' (private={info['private']})")


if __name__ == "__main__":
    main()
