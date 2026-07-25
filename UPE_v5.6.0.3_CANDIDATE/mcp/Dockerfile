FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OPENAI_AGENTS_DISABLE_TRACING=1 \
    OPENAI_AGENTS_DONT_LOG_MODEL_DATA=1 \
    OPENAI_AGENTS_DONT_LOG_TOOL_DATA=1

WORKDIR /app

RUN pip install --no-cache-dir uv
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv sync --no-dev

EXPOSE 8000
CMD ["uv", "run", "upe-review-mcp"]
