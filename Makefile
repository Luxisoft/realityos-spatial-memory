.DEFAULT_GOAL := help

help:
	@printf '%s\n' 'make install | lint | test | api | migrate | seed | compose-up'

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e 'backend[dev]'

lint:
	.venv/bin/ruff check backend tests

test:
	.venv/bin/pytest -q

api:
	.venv/bin/uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

migrate:
	.venv/bin/alembic -c backend/alembic.ini upgrade head

seed:
	.venv/bin/python scripts/seed_demo.py

compose-up:
	docker compose --env-file .env -f infrastructure/docker-compose.yml up --build
