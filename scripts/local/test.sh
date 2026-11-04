#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"
local_progress 0 4 'Checking Docker'
assert_local_docker
local_progress 1 4 'Checking service status'
local_compose ps --format '{{.Service}}: {{.Status}}'
local_progress 2 4 'Checking model availability'
local_compose exec -T api python /scripts/local/check_runtime.py --providers
local_progress 3 4 'Checking local account availability'
local_compose exec -T api python -c "import json, urllib.request; x=json.load(urllib.request.urlopen('http://localhost:8000/v1/auth/local-accounts')); print('Available local accounts:', len(x['accounts']))"
local_progress 4 4 'Local diagnostics completed'
