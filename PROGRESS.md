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

## Phase 2 — App-auth flow + automated ESLint review — DONE (2026-07-13)

- `auth_test.py` added: generates a JWT from the App's private key
  (`PRIVATE_KEY_PATH`, `GITHUB_APP_ID`), exchanges it for an installation
  access token, and fetches a PR's changed files.
- `helper.py` added: fetches file content at a given commit (with retry/
  backoff on 5xx), runs it through ESLint (`eslint-baseline.json`, TS/React
  config) via a temp file + `npx eslint`, and posts results as a single PR
  review with inline comments.
- `app.py` webhook handler now drives the full pipeline on `pull_request`
  `opened`/`synchronize`: install-token exchange → fetch changed lintable
  files (`.ts`/`.tsx`/`.js`/`.jsx`) → lint → post review comments.
- Added `package.json` / ESLint toolchain (`node_modules/` gitignored) and
  populated `requirements.txt` (fastapi, uvicorn, python-dotenv, requests,
  PyJWT, cryptography) — was previously committed empty.
- Added `README.md` documenting setup, required `.env` vars, and the
  review pipeline.
- `OPENAI_KEY` is present in `.env` but not yet used — reserved for a
  future AI-based review step beyond plain ESLint.

## Phase 3 — LLM-based review step — DONE (2026-07-13)

- `llm_review.py` added: sends each changed file's diff (annotated with
  real line numbers via `parse_diff_with_line_numbers`) to `gpt-4o-mini`,
  prompted to flag only genuine logic/edge-case/bug issues (medium/high
  severity) and explicitly ignore style/lint-catchable issues.
- `app.py` now runs the LLM review alongside ESLint per file and merges
  both into the same posted review; either step failing is caught and
  logged independently so one doesn't block the other.
- `.env`'s `OPENAI_KEY` was renamed to `OPENAI_API_KEY` to match what
  `llm_review.py` reads; `requirements.txt` updated with `openai`.

