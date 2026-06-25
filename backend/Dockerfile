FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:${PATH}"

# Copy requirements
COPY pyproject.toml uv.lock ./

# Build dependencies
RUN uv sync --no-dev --frozen

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY app/ /app/app

# Expose backend port
EXPOSE 8000

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="."

# Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
