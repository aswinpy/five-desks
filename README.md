# Five Desks — OpenEnv Arena environment (masapasa)

One OpenEnv image covering the five domains where no arena run has scored yet:
finance, natural science, math, cybersecurity, media.

- Procedural tasks from fixed seeds (deterministic, no assets to download)
- Small virtual workspace per episode: agent uses `grep` / `read` / `calc`, then `answer`
- Deterministic verifier, partial credit on multi-part finance answers
- Short observations, forgiving schema, `MAX_STEPS=8`

## Layout

- `five_desks/models.py` — action / observation schemas
- `five_desks/generators.py` — deterministic task generators + verifiers
- `five_desks/server/` — OpenEnv environment + FastAPI app + Dockerfile
- `five_desks/client.py` — typed client
- `dataset/` — `tasks.jsonl` + README card (publish as HF dataset)
- `submission/submission.json` — arena request template (show human before sending)
- `tests/` — oracle / wrong / partial / finish-path checks

## Local checks (no Docker needed)

```sh
uv run --python 3.12 --project . pytest -q
uv run --python 3.12 --project . python -m five_desks.server.app --port 8000 &
uv run --python 3.12 --project . openenv validate --url http://localhost:8000
```

Pinned OpenEnv revision: `86a180ede21e044f7929b9a7783ad83aa67d83a3`

## Build (GitHub Actions, linux/amd64 — no local Docker needed)

See `.github/workflows/build.yml`. It builds
`ghcr.io/<owner>/five-desks:v1`, pushes, makes visibility public manually,
then anonymously pulls + replays every task.
