FROM python:3.12-slim

WORKDIR /app

COPY src/fibey/gateway/ ./src/fibey/gateway/
COPY src/fibey/__init__.py ./src/fibey/__init__.py

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    httpx \
    azure-identity \
    python-dotenv

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "fibey.gateway.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
