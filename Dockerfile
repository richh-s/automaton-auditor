FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (cache layer)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY . .

# Environment variables (override at runtime)
ENV OPENAI_API_KEY=""
ENV LANGCHAIN_API_KEY=""
ENV LANGCHAIN_TRACING_V2="false"

ENTRYPOINT ["uv", "run", "python", "main.py"]
CMD ["--help"]
