#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"
assert_local_docker
local_compose down
echo 'Stopped. Local database and queue volumes are preserved.'
