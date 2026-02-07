FROM python:3.12-slim AS base

# Create image directory
RUN mkdir /images

WORKDIR /app

# Copy source files BEFORE pip install (required for editable install)
COPY src/ ./src/
COPY pyproject.toml .
COPY scripts/ ./scripts/

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Install fonts for text overlay feature
RUN bash scripts/install_fonts.sh

# Install PIP Dependencies
# Note: src/ must exist before this step for editable install
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -e .

# NO .env or alembic.ini copied - these come from volume mounts at runtime!

# App stage - for aiproxysrv-app
FROM base AS app

EXPOSE 5050
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5050", \
       "--timeout", "180", \
       "--limit-request-field_size", "32768", \
       "wsgi:app"]
