FROM python:3.13-slim-trixie AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/install_dependencies.py /build/install_dependencies.py
# Dependencies are installed into the image's own Python environment as root.
# This layer depends only on package metadata, not application code or fixtures.
RUN apt-get update \
    && apt-get install --no-install-recommends -y ffmpeg g++ \
    && python /build/install_dependencies.py \
    && apt-get purge -y g++ \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /build
# Bake InsightFace weights so api/worker start fast without a model download.
RUN python -c "from insightface.app import FaceAnalysis; app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider']); app.prepare(ctx_id=0)"
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
COPY backend/schema ./schema
# Preserve the installed distribution metadata without resolving dependencies again.
RUN pip install --no-index --no-deps --no-build-isolation --root-user-action=ignore ".[faces]"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Only the local build includes evaluation SQL and graphic test resources.
FROM base AS local
COPY scripts/local /scripts/local
COPY simulator/database /simulator/database
COPY simulator/media /simulator/media

# The default artifact is safe to use for server releases.
FROM base AS server
