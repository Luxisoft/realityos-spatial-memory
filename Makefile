.DEFAULT_GOAL := help

help:
	@printf '%s\n' 'make install | lint | test | api | migrate | seed | compose-up | gateway-api | runtime-dirs'

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e 'backend[dev]'
	.venv/bin/pip install -e 'meta-gateway[dev]'

lint:
	.venv/bin/ruff check backend tests meta-gateway gateway-tests

test:
	.venv/bin/pytest -q tests gateway-tests

api:
	.venv/bin/uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

migrate:
	.venv/bin/alembic -c backend/alembic.ini upgrade head

seed:
	.venv/bin/python scripts/seed_demo.py

compose-up:
	docker compose --env-file .env -f infrastructure/docker-compose.yml up --build

gateway-api:
	.venv/bin/uvicorn realityos_meta_gateway.main:app_factory --app-dir meta-gateway --factory --host 127.0.0.1 --port 9088

runtime-dirs:
	sh scripts/setup_runtime_dirs.sh
