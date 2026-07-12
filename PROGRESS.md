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

## Phase 1 — GitHub App registration + webhook scaffold — DONE (2026-07-12)

- GitHub App `pruthvi1405` registered (App ID 4280798), installed on
  `pruthvi1405/UnionFind`.
- Webhook URL set to an ngrok tunnel (`.../webhook`) with SSL verification
  enabled; note ngrok free-tier URLs rotate on restart and must be re-saved
  in the App's Webhook settings each time.
- `app.py` added: FastAPI server with a `/webhook` endpoint that verifies
  `X-Hub-Signature-256` via HMAC-SHA256 (using `WEBHOOK_SECRET` from `.env`)
  before parsing the payload, and logs `pull_request` `opened`/`synchronize`
  events.
- Debugging note: initial 401s were caused by the Webhook secret field on
  the App settings page not actually persisting (UI accepted the save but
  the field came back empty on reload) — re-entering it and saving fixed
  delivery. Confirmed end-to-end with a real PR event (PR #2) processed
  with `200 OK`.

## Phase 2 — not yet defined in the build guide

