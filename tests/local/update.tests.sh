#!/usr/bin/env bash
# Run the real Bash updater against a fake Docker executable/function only.
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
test_root="$(mktemp -d)/RealityOS update tests"
mkdir -p "$test_root"/{scripts/local,backend/{app,alembic,schema},simulator/{database,media},infrastructure}
cleanup() { rm -rf -- "${test_root%/*}"; }
trap cleanup EXIT
cp "$repo_root/scripts/local/"{update.sh,common.sh,console.sh,check_update_image.py,check_update_worker.py} "$test_root/scripts/local/"
touch "$test_root/backend/alembic.ini" "$test_root/scripts/local/bootstrap.py"
printf '[project]\r\nname="local-check"\r\n' > "$test_root/backend/pyproject.toml"
cp "$repo_root/.env.local.example" "$test_root/.env.local"
for key in POSTGRES_PASSWORD JWT_SECRET DEVICE_CREDENTIAL_PEPPER STORAGE_ENCRYPTION_KEY MODEL_API_KEY; do
  sed -i "s/^$key=$/$key=local-test-value/" "$test_root/.env.local"
done
cp "$test_root/.env.local" "$test_root/environment-original"
printf 'do not change server configuration' > "$test_root/.env"
export FAKE_LOG="$test_root/docker.log" FAKE_STATE="$test_root/worker-state" FAKE_SCENARIO='' FAKE_IMAGE="sha256:$(printf 'a%.0s' {1..64})"
export FAKE_HASH="$(sed 's/\r$//' "$test_root/backend/pyproject.toml" | sha256sum | cut -d' ' -f1)"
export MODEL_API_KEY=external-private-key REALITYOS_LOCAL_IMAGE=external-untrusted-image:latest
unset DOCKER_HOST DOCKER_CONTEXT

docker() {
  printf 'pin=%s key=%s | %s\n' "${REALITYOS_LOCAL_IMAGE:-}" "${MODEL_API_KEY:-}" "$*" >> "$FAKE_LOG"
  case "$1" in
    context) if [[ "$FAKE_SCENARIO" == remote ]]; then echo ssh://production; else echo unix:///fake/docker.sock; fi;;
    info) echo linux/amd64;;
    image) [[ "$FAKE_SCENARIO" != missing-image ]] || return 1; echo "$FAKE_IMAGE";;
    inspect)
      if [[ "$5" == '{{.State.Running}}' ]]; then cat "$FAKE_STATE"; return; fi
      local service="${!#}" image="$FAKE_IMAGE" health=healthy running=true realm='ENVIRONMENT=local;LOCAL_LOGIN_ENABLED=true;LOCAL_EVALUATION_ENABLED=true;'
      service=${service#id-}
      if [[ "$FAKE_SCENARIO" == mixed-images && "$service" == worker ]]; then image="sha256:$(printf 'b%.0s' {1..64})"; fi
      if [[ "$FAKE_SCENARIO" == database-unhealthy && "$service" == postgres ]]; then health=unhealthy; fi
      if [[ "$FAKE_SCENARIO" == server-realm ]]; then realm='ENVIRONMENT=production;'; fi
      if [[ "$FAKE_SCENARIO" == stopped-worker && "$service" == worker ]]; then running=false; fi
      echo "realityos-local|$service|$image|$running|$health|$realm";;
    run)
      local body
      body=$(cat)
      [[ "$body" == *'def verify_image'* && "${!#}" == "$FAKE_HASH" ]] || { echo 'ERROR: probe input/hash is invalid'; return 8; }
      [[ "$FAKE_SCENARIO" != dependencies ]] || { echo 'Dependencies changed. Run the full local installer first.'; return 8; };;
    exec)
      local body
      body=$(cat)
      [[ -n "$body" && ( "${!#}" == recover || "${!#}" =~ ^[a-f0-9]{32}$ ) && "$3" == id-worker ]] || { echo 'ERROR: invalid worker probe'; return 8; }
      if [[ "$6" == prepare && ( "$FAKE_SCENARIO" == worker-* || "$FAKE_SCENARIO" == resume-failed ) ]]; then echo 'ERROR: worker busy or status unavailable'; return 8; fi
      if [[ "$6" == resume && "$FAKE_SCENARIO" == resume-failed ]]; then echo 'ERROR: restore unavailable'; return 8; fi;;
    compose)
      local command="${8:-}" service="${!#}"
      if [[ "${2:-}" == version ]]; then return 0; fi
      if [[ "$command" == ps ]]; then [[ "$FAKE_SCENARIO" == "missing-$service" ]] || echo "id-$service"; return 0; fi
      if [[ "$command" == config && "$FAKE_SCENARIO" == config-failed ]]; then echo 'ERROR: invalid Compose configuration'; return 7; fi
      if [[ "$command" == stop && "$FAKE_SCENARIO" == stop-failed ]]; then echo 'ERROR: simulated partial stop failure'; return 7; fi
      if [[ "$command" == stop ]]; then echo false > "$FAKE_STATE"; fi
      if [[ "$command" == up && "$FAKE_SCENARIO" == "failed-$service" ]] || [[ "$command" == exec && "$FAKE_SCENARIO" == queue-failed ]]; then echo 'ERROR: simulated startup failure'; return 7; fi;;
    *) echo 'ERROR: unexpected Docker command'; return 9;;
  esac
}
export -f docker
fail() { echo "FAIL: $*" >&2; exit 1; }
run_case() {
  export FAKE_SCENARIO="$1"
  local expected="${2:-}" mode="${3:-}" output result
  local -a arguments=()
  [[ -z "$mode" ]] || arguments+=("$mode")
  : > "$FAKE_LOG"
  echo true > "$FAKE_STATE"
  if output=$(bash "$test_root/scripts/local/update.sh" "${arguments[@]}" 2>&1); then result=0; else result=$?; fi
  if [[ -n "$expected" ]]; then
    [[ "$result" != 0 && "$output" == *"$expected"* ]] || fail "$1: expected failure '$expected', got ($result) $output"
  else [[ "$result" == 0 ]] || fail "$1: $output"; fi
  if [[ "$1" == resume-failed ]]; then [[ "$output" == *'--resume-worker'* ]] || fail 'Recovery guidance was hidden.'; fi
  [[ "$(cat "$test_root/.env")" == 'do not change server configuration' ]] || fail 'Server configuration changed.'
  [[ "$MODEL_API_KEY" == external-private-key && "$REALITYOS_LOCAL_IMAGE" == external-untrusted-image:latest ]] || fail 'Caller environment changed.'
  ! grep -Eq 'external-private-key|external-untrusted-image| --providers| build | pull | down ' "$FAKE_LOG" || fail 'External settings/heavy operation reached Docker.'
  if grep -q ' | run ' "$FAKE_LOG"; then
    grep -q 'run --rm --interactive --pull never --network none --read-only --entrypoint python' "$FAKE_LOG" || fail 'Image probe was not isolated.'
  fi
}

for iteration in 1 2; do
  run_case success
  mapfile -t mutations < <(grep ' | compose ' "$FAKE_LOG" | grep -E ' (stop|up|exec) ')
  [[ ${#mutations[@]} == 4 && "${mutations[0]}" == *' stop api worker' && "${mutations[1]}" == *' api' && "${mutations[2]}" == *' worker' && "${mutations[3]}" == *' --queue' ]] || fail 'Wrong mutation order.'
  for index in 1 2; do
    [[ "${mutations[$index]}" == "pin=$FAKE_IMAGE "* ]] || fail 'Installed image was not pinned.'
    [[ "${mutations[$index]}" == *'--no-build --pull never --no-deps --force-recreate --wait'* ]] || fail 'Unsafe recreation flags.'
  done
  cmp -s "$test_root/.env.local" "$test_root/environment-original" || fail 'Local credentials changed.'
done
run_case stopped-worker
! grep -q ' | exec ' "$FAKE_LOG" || fail 'Retry tried to execute a guard in a stopped worker.'
for case in dependencies missing-image mixed-images database-unhealthy server-realm remote missing-api missing-worker missing-postgres missing-redis config-failed worker-busy worker-unknown resume-failed; do
  case "$case" in
    dependencies) expected='Dependencies changed';; missing-image) expected='Local image is missing';; mixed-images) expected='different images';;
    database-unhealthy) expected='must be running and healthy';; server-realm) expected='local evaluation realm';; remote) expected='Remote endpoints are refused';;
    config-failed) expected='Docker could not complete';; worker-*|resume-failed) expected='worker busy or status unavailable';; *) expected='not installed';;
  esac
  run_case "$case" "$expected"
  ! grep ' | compose ' "$FAKE_LOG" | grep -Eq ' (stop|up|exec) ' || fail "$case stopped a service during preflight."
  if [[ "$case" == worker-* || "$case" == resume-failed ]]; then [[ "$(tail -n1 "$FAKE_LOG")" == *' python - resume '* ]] || fail 'Rejected pause was not resumed.'; fi
done
for case in failed-api failed-worker queue-failed stop-failed; do
  run_case "$case" 'Update incomplete'
  if [[ "$case" == stop-failed ]]; then [[ "$(tail -n1 "$FAKE_LOG")" == *' | exec --interactive id-worker python - resume '* ]] || fail 'Partial stop failure did not resume its old worker.'
  else [[ "$(tail -n1 "$FAKE_LOG")" == *' | inspect '* ]] || fail 'Recovery tried to execute in a stopped old worker.'; fi
  [[ $(grep -c ' stop api worker$' "$FAKE_LOG") == 1 ]] || fail 'A failed update stopped a worker that could be processing new jobs.'
  if [[ "$case" == failed-api ]]; then ! grep -q ' up .* worker$' "$FAKE_LOG" || fail 'Worker started before API readiness.'; fi
done
run_case dependencies '' --resume-worker
! grep -Eq ' \| (run|image) | (stop|up|config) ' "$FAKE_LOG" || fail 'Explicit recovery checked dependencies or changed services.'
[[ "$(tail -n1 "$FAKE_LOG")" == *' python - recover' ]] || fail 'Explicit recovery did not call its guard.'
run_case stopped-worker '' --resume-worker
! grep -q ' | exec ' "$FAKE_LOG" || fail 'Recovery tried to execute in a stopped worker.'
printf '\nREALITYOS_LOCAL_IMAGE=malicious\n' >> "$test_root/.env.local"
run_case reserved-image 'forbidden in .env.local'
[[ ! -s "$FAKE_LOG" ]] || fail 'Reserved image reached Docker.'
cp "$test_root/environment-original" "$test_root/.env.local"
export DOCKER_HOST=ssh://production
run_case remote-host 'Remote endpoints are refused'
! grep -Eq ' (info|stop|up|exec) ' "$FAKE_LOG" || fail 'Remote host reached engine operations.'
unset DOCKER_HOST
rm "$test_root/.env.local"
run_case not-installed 'start.sh first'
[[ ! -s "$FAKE_LOG" ]] || fail 'First installation reached Docker.'
echo '26 Bash fast-update scenarios passed; all Docker commands were simulated.'
