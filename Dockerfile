# ============================================
# AI Tech & Delivery Review Agent
# Multi-stage Dockerfile for Production
# ============================================

# --------------------------------------------
# Stage 1: Builder
# --------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --------------------------------------------
# Stage 2: Development
# --------------------------------------------
FROM builder as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    httpx \
    black \
    isort \
    flake8

WORKDIR /app
COPY . .

# Override command for development
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

# --------------------------------------------
# Stage 3: Production
# --------------------------------------------
FROM python:3.11-slim as production

# Labels
LABEL maintainer="AI Review Agent Team"
LABEL version="1.0.0"
LABEL description="AI-powered project review system"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app \
    DATA_DIR=/app/data \
    UPLOADS_DIR=/app/uploads \
    REPORTS_DIR=/app/reports \
    CHROMA_DB=/app/chroma_db

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR ${APP_HOME}

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appgroup . .

# Create required directories
RUN mkdir -p ${DATA_DIR} ${UPLOADS_DIR} ${REPORTS_DIR} ${CHROMA_DB} && \
    chown -R appuser:appgroup ${APP_HOME}

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
