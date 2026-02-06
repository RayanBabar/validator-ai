# Use official Python runtime
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (gcc/libpq for psycopg if needed, though binary wheels usually suffice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
#just for check
# Install uv for fast dependency management
RUN pip install uv

# Copy project files (DO NOT copy .env - use runtime env vars or Docker secrets)
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY app.py ./
COPY .env ./

# Install dependencies using uv
RUN uv sync

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "--", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
