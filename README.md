# PulseCheck

A GitHub App that automatically reviews pull requests: on `opened`/`synchronize`
events it fetches the changed files, lints them with ESLint, and posts inline
review comments back to the PR.

## How it works

1. GitHub delivers a signed `pull_request` webhook to `app.py`.
2. The signature is verified against `WEBHOOK_SECRET` (HMAC-SHA256 over the
   raw request body, compared against the `X-Hub-Signature-256` header).
3. `auth_test.py` mints a JWT from the App's private key, exchanges it for
   an installation access token, and fetches the PR's changed files.
4. For each lintable file (`.ts`, `.tsx`, `.js`, `.jsx`), `helper.py` fetches
   its content at the PR's head commit and runs it through ESLint
   (`eslint-baseline.json` config).
5. Any lint messages are posted as a single review with inline comments via
   `helper.post_review`.

## Setup

Install dependencies:

```
pip install -r requirements.txt
npm install
```

Create a `.env` with:

```
GITHUB_TOKEN=          # personal access token, used for local API checks
OPENAI_KEY=            # reserved for future AI-based review logic
NGROK_AUTHTOKEN=       # for exposing the local server during development
WEBHOOK_SECRET=        # must match the GitHub App's Webhook secret
GITHUB_APP_ID=         # the App's ID (see App settings)
PRIVATE_KEY_PATH=      # path to the App's downloaded .pem private key
```

Run the server:

```
python3 app.py
```

Expose it publicly (e.g. via ngrok) and set that URL + `/webhook` as the
GitHub App's Webhook URL.

## GitHub App configuration

- Webhook: Active, SSL verification enabled, URL pointed at your tunnel.
- Permissions needed: Pull requests (read & write), Contents (read).
- Subscribe to the `Pull request` event.
- Install the App on the test repo you want reviewed.

## Scripts

- `test_github_access.py` — verifies `GITHUB_TOKEN` authenticates and
  (optionally) has access to a given `owner/repo`.
- `auth_test.py` — standalone check of the App-auth flow (JWT →
  installation token → PR file list); also importable by `app.py`.

## Notes

- ngrok's free tier issues a new URL on every restart — update the
  Webhook URL in the App settings each time you restart the tunnel.
- See `PROGRESS.md` for build-phase history.
