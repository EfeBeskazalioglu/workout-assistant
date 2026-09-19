# Workout Assistant

An AI fitness assistant that tracks sets, reps and weights from plain-language workout logs.

**Status:** in development. Phase 1 is the LLM parsing service.

## What works now

`parser.py` turns a free-text log such as *"benched 135 lbs for 5 reps"* into a validated, structured workout record:

- **Schema-constrained output:** the model must answer in a Pydantic schema, enforced by [Instructor](https://github.com/instructor-ai/instructor). It can't return free text or broken JSON.
- **Two-layer schema:** the model only sees `WorkoutLog` (exercises). The application record `WorkoutRecord` adds fields the model should never invent, like the workout date, and runs checks such as "at least one exercise", after the model answers.
- **Constrained fields:** units are an enum (`kg` / `lb`), exercise names are normalised, and missing values stay `null` instead of being guessed.
- **Model:** any OpenAI-compatible endpoint. It currently uses a free model through [OpenRouter](https://openrouter.ai).

## Failure log

[`failures.md`](failures.md) is the core of this project. It records every way the model broke across runs, with the input, the output, and whether the issue is closed. It currently tracks 12 failure modes. Examples:

- A schema constraint (`min_length=1`) pushed the model to *hallucinate* a fake exercise instead of honestly returning an empty list. The fix was to move that check from the LLM-facing schema to the application model.
- `temperature=0` did not make the output deterministic: the same input sometimes dropped a field it had filled in on another run.
- Turkish exercise names ("mekik" = sit-up) are still not mapped to standard names. This one is still open and planned for the retrieval phase.

The rule this project follows: fix failures in the schema and the code, not by adding more instructions to the prompt.

## Roadmap

- [x] Phase 1: LLM parsing into validated structured data
- [ ] Eval set: fixed test inputs, several runs each, with per-field accuracy reported as a rate
- [ ] Retrieval over a known exercise list, to map names like "mekik" to "sit-up" (failure A1)
- [ ] FastAPI endpoint, with a timeout based on the measured latency (failure D2)
- [ ] Storage: SQLite, then Postgres

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
OPENROUTER_API_KEY=your-key-here
```

Run the sample inputs:

```bash
python parser.py
```

## Stack

Python · Pydantic · Instructor · OpenAI SDK (via OpenRouter)
