.DEFAULT_GOAL := help

help:
	@printf '%s\n' 'make install | lint | test | docs-check | architecture-check | format-check | android-check | api | migrate | seed | compose-up | gateway-api | runtime-dirs'

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

compose-up: local-start

gateway-api:
	.venv/bin/uvicorn realityos_meta_gateway.main:app_factory --app-dir meta-gateway --factory --host 127.0.0.1 --port 9088

runtime-dirs:
	sh scripts/setup_runtime_dirs.sh

architecture-check:
	.venv/bin/python scripts/check_structure.py

docs-check:
	python3 scripts/check_docs.py
	python3 scripts/build_api_docs.py --check
	node scripts/check_postman_scripts.cjs

postman-runtime-check:
	node scripts/check_postman_runtime.cjs

format-check:
	.venv/bin/ruff format --check backend/app/http backend/app/providers backend/app/processing backend/app/social_features backend/app/routes.py backend/app/meta.py backend/app/services.py backend/app/social.py tests/social tests/test_architecture_contract.py tests/conftest.py scripts/check_structure.py
	cd android && ./gradlew :app:ktlintCheck

android-check:
	cd android && ./gradlew :app:ktlintCheck :app:testDebugUnitTest :app:lintDebug :app:assembleDebug :app:assembleRelease

.PHONY: docs-check postman-runtime-check architecture-check format-check android-check

# Primary localhost installation; Windows uses the PowerShell launcher.
local-help:
	@printf '%s\n' 'See docs/en/deployment/DEPLOYMENT_LOCALHOST.md. Windows: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Start-RealityOS.ps1'

.PHONY: local-help

local-start:
	bash scripts/local/start.sh

local-stop:
	bash scripts/local/stop.sh

local-test:
	bash scripts/local/test.sh

.PHONY: local-start local-stop local-test compose-up
