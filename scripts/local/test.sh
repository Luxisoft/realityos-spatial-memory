#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"
assert_local_docker
local_compose ps
local_compose exec -T api python /scripts/local/check_runtime.py --providers
local_compose exec -T api python -c "import json, urllib.request; x=json.load(urllib.request.urlopen('http://localhost:8000/v1/auth/local-accounts')); print('Available local accounts:', len(x['accounts']))"
