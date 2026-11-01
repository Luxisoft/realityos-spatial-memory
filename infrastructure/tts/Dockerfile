FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app HF_HOME=/models TTS_CPU_THREADS=2
WORKDIR /app
COPY infrastructure/tts/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
COPY backend/app/tts_contracts.py ./app/tts_contracts.py
COPY backend/app/providers/seamless_service.py ./app/providers/seamless_service.py
COPY scripts/benchmark_tts.py ./benchmark_tts.py
RUN python -c "from transformers import AutoProcessor, SeamlessM4Tv2ForTextToSpeech; from app.providers.seamless_service import create_app"
RUN useradd --system --uid 10002 tts && mkdir /models && chown tts /models
USER tts
EXPOSE 8091
CMD ["uvicorn", "app.providers.seamless_service:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8091", "--workers", "1", "--no-access-log"]
