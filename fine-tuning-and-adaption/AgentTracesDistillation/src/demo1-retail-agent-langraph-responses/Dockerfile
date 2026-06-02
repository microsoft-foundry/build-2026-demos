FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
COPY . user_agent/
WORKDIR /app/user_agent
RUN uv pip install --system --prerelease=allow -r requirements.txt
EXPOSE 8088
CMD ["python", "main.py"]
