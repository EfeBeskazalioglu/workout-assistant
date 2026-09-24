# Workout Assistant

An AI fitness assistant that turns plain-language workout logs into structured, validated records.

*"benched 135 lbs for 5 reps"* → `{exercise: "bench press", reps: 5, weight: 135, unit: "lb"}`

**Status:** Phase 1 (LLM service) is nearly complete. Next: tests, evals, CI and a live deployment.

## How it works

```
POST text → FastAPI → LLM (via Instructor, JSON schema mode) → Pydantic validation → SQLite
```

- **Schema-constrained output:** the model must answer in a Pydantic schema, enforced by [Instructor](https://python.useinstructor.com/) in JSON schema mode. It can't return free text or broken JSON.
- **Two-layer schema:** the model only sees `WorkoutLLM` (the exercises). The application model `WorkoutRecord` adds fields the model should never invent, like the workout date, and runs checks such as "at least one exercise" after the model answers.
- **Constrained fields:** units are an enum (`kg` / `lb`), exercise names are normalised, and missing values stay `null` instead of being guessed.
- **Provider-agnostic:** works with any OpenAI-compatible endpoint, configured through three environment variables. It currently runs on [Groq](https://groq.com) with `openai/gpt-oss-20b` (under 1 s per call).
- **Logging:** every LLM call is logged with its duration; failures are logged with the upstream error, which is never sent to the client.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/parse` | Parse a log into a structured record, without saving it |
| `POST` | `/workouts` | Parse a log and save it |
| `GET` | `/workouts` | List all saved workouts with their exercises |

Request body for both `POST` endpoints:

```json
{"text": "3x8 squat at 60kg, then 3x10 bench at 40kg"}
```

### Error codes

| Code | When | Why this code |
|---|---|---|
| `422` | The input has no recognisable exercise (e.g. *"chest day felt strong"*) | The client can fix it by sending a more specific log |
| `503` + `Retry-After` | The LLM provider timed out or hit its rate limit | The problem is on the server side and temporary; the same request may succeed later |

## Failure log

[`failures.md`](failures.md) is the core of this project. It records every way the model broke across runs, with the input, the output, and whether the issue is closed. It currently tracks 15 failure modes. Examples:

- A schema constraint (`min_length=1`) pushed the model to *hallucinate* a fake exercise instead of honestly returning an empty list. The fix was to move that check from the LLM-facing schema to the application model.
- Calls took 30–50 s. Switching providers didn't help; measuring did: Instructor's default tool-calling mode was silently retrying because the model kept renaming schema fields. JSON schema mode brought calls under 1 s.
- `temperature=0` did not make the output deterministic: the same input sometimes dropped a field it had filled in on another run.

The rule this project follows: fix failures in the schema and the code, not by adding more instructions to the prompt.

## Known limitations

- **Turkish exercise names** ("mekik" = sit-up) are not mapped to standard names (failure A1). Planned: retrieval over a known exercise list.
- **Fields are sometimes dropped** even when stated in the input (A5). Planned: measured as a rate in the eval set.
- **Rate limit:** the free Groq tier allows about 11 requests per minute. Near the limit, requests slow down to 4–5 s while the SDK retries; past it, the API returns `503` (D4).
- **Storage** is a local SQLite file. Planned: Postgres with migrations.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create your environment file and fill it in. Get a free Groq API key at [console.groq.com/keys](https://console.groq.com/keys).

   ```bash
   cp .env.example .env
   ```

   ```
   LLM_API_KEY=your-groq-key
   LLM_BASE_URL=https://api.groq.com/openai/v1
   LLM_MODEL=openai/gpt-oss-20b
   ```

   Optional: `TIMEOUT` (seconds per LLM call, default 15).

3. Start the server:

   ```bash
   fastapi dev main.py
   ```

4. Open the interactive docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) and try the endpoints.

Settings are read once at startup, so restart the server after changing `.env`.

## Next Steps

- LLM parsing into validated structured data
- FastAPI service with error handling and logging
- Storage in SQLite
- Tests with a mocked LLM, run in CI on every pull request
- Eval set built from real logs, with per-field accuracy reported as a rate
- Postgres (Neon) with Alembic migrations-  Web UI and a live deployment
- Retrieval over a known exercise list and an agent that answers questions about your training history

## Stack

Python · FastAPI · Pydantic · pydantic-settings · Instructor · OpenAI SDK · SQLAlchemy · SQLite
