# AI Networking Copilot (SWE + MBA Job Seeker)

An MVP backend for an AI-powered networking assistant that:

- creates job-search **campaigns** (resume + JD + target company)
- tracks **contacts** and **interactions** (Gmail sync per-contact)
- drafts personalized **outreach** + **follow-ups**
- suggests **next best actions**
- schedules **follow-up reminders** (Google Calendar)

## Quickstart (local)

### 1) Create a virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### 2) Configure env

Copy `.env.example` to `.env` and fill values.

### 3) Run API

```bash
uvicorn app.main:app --reload
```

Open:

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Dev auth shortcut

In `ENVIRONMENT=dev`, you can call authenticated endpoints by passing:

- `X-Debug-User: you@example.com`

### Demo API key (no OAuth)

If you want to deploy without Google OAuth (e.g., day-1 demo), set:

- `DEMO_API_KEY` (random string)
- `DEMO_USER_EMAIL` (your email)

Then call authenticated endpoints with:

- `X-Api-Key: <your DEMO_API_KEY>`

## Google OAuth (Gmail + Calendar)

You’ll need a Google Cloud OAuth client with:

- Authorized redirect URI: `http://localhost:8000/integrations/google/callback`
- Scopes: Gmail readonly + Calendar events

Then set:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`

## Scalability notes (built-in)

- Postgres-ready schema via SQLAlchemy models (`DATABASE_URL`)
- Token storage for per-user Google integrations
- Background worker hook points (email sync + follow-up scheduling)
- Docker + Compose templates included for local/prod parity (`docker-compose.yml`)

## Docker (local/prod parity)

```bash
docker compose up --build
```

This runs:

- API on `http://localhost:8000`
- Postgres on `localhost:5432`
- Redis on `localhost:6379` (reserved for background jobs)

## CI/CD

GitHub Actions workflows:

- `ci.yml`: lint + tests on PRs
- `docker.yml`: build container and publish to GHCR (`ghcr.io/<owner>/<repo>`)

## Pushing to GitHub

This workspace has no remote configured yet. Once you create a GitHub repo:

```bash
git remote add origin <YOUR_REPO_URL>
git add -A
git commit -m "Initial MVP: API + Google integrations + CI"
git push -u origin main
```
