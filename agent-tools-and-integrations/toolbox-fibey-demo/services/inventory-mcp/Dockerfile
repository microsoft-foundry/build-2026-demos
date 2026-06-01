FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./pyproject.toml
RUN uv sync --no-dev

COPY server.py ./server.py
COPY data ./data

EXPOSE 8001

CMD ["uv", "run", "python", "server.py"]
