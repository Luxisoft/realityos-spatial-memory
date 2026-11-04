#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"
local_progress 0 2 'Checking Docker'
assert_local_docker
local_progress 1 2 'Stopping local services'
local_compose down
local_progress 2 2 'Local services stopped; database and queue volumes are preserved'
