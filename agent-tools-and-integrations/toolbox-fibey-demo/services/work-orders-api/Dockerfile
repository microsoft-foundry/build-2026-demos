FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml ./
COPY server.py ./
COPY data/ ./data/

RUN uv sync --no-dev

EXPOSE 8002

CMD ["uv", "run", "python", "server.py"]
