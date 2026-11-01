.DEFAULT_GOAL := help

help:
	@printf '%s\n' 'make install | lint | test | architecture-check | format-check | android-check | api | migrate | seed | compose-up | gateway-api | runtime-dirs'

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

architecture-check:
	.venv/bin/python scripts/check_structure.py

format-check:
	.venv/bin/ruff format --check backend/app/http backend/app/providers backend/app/processing backend/app/social_features backend/app/routes.py backend/app/meta.py backend/app/services.py backend/app/social.py tests/social tests/test_architecture_contract.py tests/conftest.py scripts/check_structure.py
	npm --prefix frontend run format:check
	npm --prefix display-webapp run format:check
	cd android && ./gradlew :app:ktlintCheck

android-check:
	cd android && ./gradlew :app:ktlintCheck :app:testDebugUnitTest :app:lintDebug :app:assembleDebug :app:assembleRelease

.PHONY: architecture-check format-check android-check

# Windows PowerShell launchers use an independent .env.local and Docker project.
local-help:
	@printf '%s\n' 'See docs/LOCAL_WINDOWS.md. Windows: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Start-RealityOS.ps1'

.PHONY: local-help
