#!/usr/bin/env bash
# Shell helpers deliberately never source an environment file as executable code.
set -euo pipefail
export LC_ALL=C
local_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
local_env="$local_root/.env.local"
local_update_image=''
source "$local_root/scripts/local/console.sh"
local_docker() (
  if [[ -f "$local_env" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      if [[ "$line" =~ ^[[:space:]]*([A-Z][A-Z0-9_]*)= ]]; then
        key="${BASH_REMATCH[1]}"
        [[ "$key" != DOCKER_* && "$key" != COMPOSE_* && "$key" != REALITYOS_LOCAL_IMAGE ]] || { echo 'DOCKER_* / COMPOSE_* / REALITYOS_LOCAL_IMAGE are forbidden in .env.local.' >&2; exit 1; }
        unset "$key"
      fi
    done < "$local_env"
  fi
  unset REALITYOS_LOCAL_IMAGE
  if [[ -n "$local_update_image" ]]; then
    [[ "$local_update_image" =~ ^sha256:[a-f0-9]{64}$ ]] || { echo 'Invalid internal local image pin.' >&2; exit 1; }
    export REALITYOS_LOCAL_IMAGE="$local_update_image"
  fi
  docker "$@"
)
local_compose() {
  local result
  if local_docker compose --project-name realityos-local --env-file "$local_env" --file "$local_root/infrastructure/docker-compose.local.yml" "$@" 2>&1 | local_console_summary; then
    return 0
  else
    result=$?
    printf '[ERROR] Docker could not complete the local operation (exit code %d).\n' "$result" >&2
    return "$result"
  fi
}
assert_local_docker() {
  [[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || { echo 'Linux x64 required; Windows uses Start-RealityOS.ps1.' >&2; exit 1; }
  command -v docker >/dev/null || { echo 'Install Docker Engine and the Compose plugin first.' >&2; exit 1; }
  local endpoint
  for endpoint in "${DOCKER_HOST:-unix:///var/run/docker.sock}" "$(local_docker context inspect --format '{{.Endpoints.docker.Host}}')"; do
    case "$endpoint" in unix://*|tcp://localhost:*|tcp://127.0.0.1:*|tcp://\[::1\]:*) ;; *) echo 'Select a local Docker context. Remote endpoints are refused.' >&2; exit 1;; esac
  done
  [[ "$(local_docker info --format '{{.OSType}}/{{.Architecture}}')" =~ ^linux/(x86_64|amd64)$ ]] || { echo 'Docker must run Linux x64 containers.' >&2; exit 1; }
  local_docker compose version >/dev/null
}
