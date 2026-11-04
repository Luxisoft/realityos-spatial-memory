FROM python:3.13-slim-trixie AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
COPY scripts /scripts
# Dependencies are installed into the image's own Python environment as root.
RUN apt-get update \
    && apt-get install --no-install-recommends -y ffmpeg g++ \
    && pip install --no-cache-dir --root-user-action=ignore ".[faces]" \
    && apt-get purge -y g++ \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
# Bake InsightFace weights so api/worker start fast without a model download.
RUN python -c "from insightface.app import FaceAnalysis; app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider']); app.prepare(ctx_id=0)"
COPY simulator/social-directory/source /simulator/social-directory/source
COPY simulator/local /simulator/local
COPY simulator/profiles /simulator/profiles
COPY simulator/workspaces /simulator/workspaces
COPY simulator/real-scenes /simulator/real-scenes

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
