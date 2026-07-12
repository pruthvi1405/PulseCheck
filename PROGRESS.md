# PulseCheck Build Progress

## Phase 0 — GitHub API access + test repo — DONE (2026-07-12)

- `.env` holds `GITHUB_TOKEN` and `OPENAI_KEY` (not committed; see `.gitignore`).
- `.gitignore` added, covering `.env`, `.venv/`, `*.pem`, `__pycache__/`, `*.pyc`.
- `test_github_access.py` added: stdlib-only script that authenticates against
  the GitHub API and optionally checks access to a specific repo.
  - `python3 test_github_access.py` → confirms the token authenticates.
  - `python3 test_github_access.py owner/repo` → also confirms repo access.
- Verified token authenticates as `pruthvi1405`.
- Test repo selected: **`pruthvi1405/UnionFind`** (existing private repo) — confirmed accessible with current token.
- Note: an earlier token/key pair was accidentally exposed in a terminal
  transcript during setup and was rotated; old credentials should stay revoked.

## Phase 1 — GitHub App registration + webhook scaffold — NOT STARTED

