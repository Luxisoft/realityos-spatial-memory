FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY meta-gateway/pyproject.toml ./pyproject.toml
COPY meta-gateway/realityos_meta_gateway ./realityos_meta_gateway
RUN python -m pip install --upgrade pip && python -m pip install .

RUN useradd --system --create-home --uid 10001 gateway
USER gateway
EXPOSE 8080
CMD ["uvicorn", "realityos_meta_gateway.main:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8080"]
