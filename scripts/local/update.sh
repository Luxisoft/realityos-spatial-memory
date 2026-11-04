#!/usr/bin/env bash
# Fast updates never build/pull an image, download models or probe live providers.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"

local_update_value() {
  local key="$1" line value=''
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" == "$key="* ]] || continue
    value=${line#*=}; value=${value%$'\r'}
    if [[ "$value" == \"*\" || "$value" == \'*\' ]]; then value=${value:1:-1}; fi
  done < "$local_env"
  printf '%s' "$value"
}

local_update_preflight() {
  [[ -f "$local_env" ]] || { echo 'No local installation found. Run scripts/local/start.sh first.' >&2; return 1; }
  local mode="${1:-update}" key value service id state project found image running health realm installed hash
  for key in ENVIRONMENT LOCAL_LOGIN_ENABLED LOCAL_EVALUATION_ENABLED META_MODE FACE_ENGINE; do
    value=$(local_update_value "$key")
    case "$key=$value" in ENVIRONMENT=local|LOCAL_LOGIN_ENABLED=true|LOCAL_EVALUATION_ENABLED=true|META_MODE=live|FACE_ENGINE=insightface) ;;
      *) echo "Invalid local setting: $key. No services were stopped." >&2; return 1;; esac
  done
  for key in POSTGRES_PASSWORD JWT_SECRET DEVICE_CREDENTIAL_PEPPER STORAGE_ENCRYPTION_KEY MODEL_API_KEY; do
    [[ -n "$(local_update_value "$key")" ]] || { echo "Missing $key in .env.local. Run scripts/local/start.sh first." >&2; return 1; }
  done
  value=$(local_update_value LOCAL_HTTP_PORT)
  [[ "$value" =~ ^[0-9]{4,5}$ ]] && (( 10#$value >= 1024 && 10#$value <= 65535 )) || { echo 'LOCAL_HTTP_PORT must be between 1024 and 65535.' >&2; return 1; }
  for key in META_API_BASE_URL META_GATEWAY_BASE_URL; do
    value=$(local_update_value "$key")
    [[ "$value" != *realityos.luxisoft.com* && "$value" != *meta.luxisoft.com* ]] || { echo 'Production URLs are forbidden in the local runtime.' >&2; return 1; }
  done
  if [[ "$mode" != recover ]]; then
    for key in backend/app backend/alembic backend/alembic.ini backend/schema backend/pyproject.toml scripts/local/bootstrap.py simulator/database simulator/media; do
      [[ -e "$local_root/$key" ]] || { echo "Missing repository source: $key. Finish updating the checkout first." >&2; return 1; }
    done
  fi
  assert_local_docker
  local template='{{index .Config.Labels `com.docker.compose.project`}}|{{index .Config.Labels `com.docker.compose.service`}}|{{.Image}}|{{.State.Running}}|{{if .State.Health}}{{.State.Health.Status}}{{end}}|{{range .Config.Env}}{{if or (eq . `ENVIRONMENT=local`) (eq . `LOCAL_LOGIN_ENABLED=true`) (eq . `LOCAL_EVALUATION_ENABLED=true`)}}{{.}};{{end}}{{end}}'
  local compose=(compose --project-name realityos-local --env-file "$local_env" --file "$local_root/infrastructure/docker-compose.local.yml")
  local_update_image=''
  local_update_worker=''; local_update_worker_running=false
  local -a services=(api worker postgres redis)
  [[ "$mode" != recover ]] || services=(worker)
  for service in "${services[@]}"; do
    id=$(local_docker "${compose[@]}" ps --all --quiet "$service")
    [[ -n "$id" && ! "$id" =~ [[:space:]] ]] || { echo "Local $service is not installed. Run scripts/local/start.sh first." >&2; return 1; }
    state=$(local_docker inspect --type container --format "$template" "$id")
    IFS='|' read -r project found image running health realm <<< "$state"
    [[ "$project" == realityos-local && "$found" == "$service" ]] || { echo 'Refusing a container outside the local installation.' >&2; return 1; }
    if [[ "$service" == postgres || "$service" == redis ]]; then
      [[ "$running/$health" == true/healthy ]] || { echo "Local $service must be running and healthy. Start the existing local stack first; no services were stopped." >&2; return 1; }
    else
      for key in ENVIRONMENT=local LOCAL_LOGIN_ENABLED=true LOCAL_EVALUATION_ENABLED=true; do
        [[ "$realm" == *"$key;"* ]] || { echo 'The installed API/worker is not in the local evaluation realm.' >&2; return 1; }
      done
      [[ -z "$local_update_image" || "$local_update_image" == "$image" ]] || { echo 'Installed API and worker use different images. Run the full local installer first.' >&2; return 1; }
      local_update_image="$image"
      if [[ "$service" == worker ]]; then local_update_worker="$id"; local_update_worker_running="$running"; fi
    fi
  done
  [[ "$mode" != recover ]] || return 0
  [[ "$local_update_image" =~ ^sha256:[a-f0-9]{64}$ ]] || { echo 'The installed local image ID is invalid.' >&2; return 1; }
  installed=$(local_docker image inspect --format '{{.Id}}' "$local_update_image" 2>/dev/null) || installed=''
  [[ "$installed" == "$local_update_image" ]] || { echo 'Local image is missing. Run scripts/local/start.sh first.' >&2; return 1; }
  hash=$(sed 's/\r$//' "$local_root/backend/pyproject.toml" | sha256sum); hash=${hash%% *}
  local_docker run --rm --interactive --pull never --network none --read-only --entrypoint python "$local_update_image" - "$hash" < "$local_root/scripts/local/check_update_image.py"
}

update_local_runtime() (
  # A subshell restores the caller's image pin and traps after success/failure.
  local pause_attempted=false update_token
  update_token=$(tr -d - < /proc/sys/kernel/random/uuid)
  trap 'result=$?; if (( result != 0 )) && [[ "$pause_attempted" == true ]]; then
    running=$(local_docker inspect --type container --format "{{.State.Running}}" "$local_update_worker" 2>/dev/null) || running=""
    if [[ "$running" == true ]]; then
      local_docker exec --interactive "$local_update_worker" python - resume "$update_token" < "$local_root/scripts/local/check_update_worker.py" || echo "[ERROR] Worker recovery could not be confirmed. After confirming no other update is running, run scripts/local/update.sh --resume-worker before retrying." >&2
    fi
    echo "[ERROR] Update incomplete. PostgreSQL/Redis services and volumes were preserved. No additional processes were stopped; resolve the reported error before retrying." >&2
  fi' EXIT
  local_progress 0 5 'Checking the installed local runtime'
  local_update_preflight
  local_compose config --quiet
  if [[ "$local_update_worker_running" == true ]]; then
    echo '[INFO] Checking that the worker has no active processing before pausing its consumer.'
    pause_attempted=true
    local_docker exec --interactive "$local_update_worker" python - prepare "$update_token" < "$local_root/scripts/local/check_update_worker.py"
  fi
  local_progress 1 5 'Stopping API and worker together'
  local_compose stop api worker
  local_progress 2 5 'Applying database updates and starting API'
  local_compose up -d --no-build --pull never --no-deps --force-recreate --wait --wait-timeout 180 api
  local_progress 3 5 'Starting worker with the same installed image'
  local_compose up -d --no-build --pull never --no-deps --force-recreate --wait --wait-timeout 60 worker
  local_progress 4 5 'Queuing only pending local publications'
  local_compose exec -T api python /scripts/local/bootstrap.py --queue
  local_progress 5 5 'Local update completed'
  echo '[SUCCESS] Code and local data revisions are current. PostgreSQL, Redis, credentials and installed models were preserved.'
)

resume_local_worker() {
  local_update_preflight recover
  if [[ "$local_update_worker_running" != true ]]; then echo '[INFO] Worker is stopped; rerun the regular updater to start it.'; return; fi
  local_docker exec --interactive "$local_update_worker" python - recover < "$local_root/scripts/local/check_update_worker.py"
  echo '[SUCCESS] Worker consumer recovery completed. No services were stopped or recreated.'
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  case "$*" in '') update_local_runtime;; --resume-worker) resume_local_worker;; *) echo 'Usage: scripts/local/update.sh [--resume-worker]' >&2; exit 2;; esac
fi
