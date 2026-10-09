# Builds the Five Desks OpenEnv server. Arena runs linux/amd64 only.
FROM python:3.12-slim

WORKDIR /app/env

COPY pyproject.toml openenv.yaml ./
COPY five_desks ./five_desks
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "openenv @ git+https://github.com/meta-pytorch/OpenEnv.git@86a180ede21e044f7929b9a7783ad83aa67d83a3" pydantic fastapi "uvicorn[standard]"

ENV PYTHONPATH="/app/env" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "five_desks.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
