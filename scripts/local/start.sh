#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"
assert_local_docker
umask 077
[[ -f "$local_env" ]] || cp "$local_root/.env.local.example" "$local_env"
chmod 600 "$local_env"
for key in POSTGRES_PASSWORD JWT_SECRET DEVICE_CREDENTIAL_PEPPER STORAGE_ENCRYPTION_KEY; do
  if grep -qx "$key=" "$local_env"; then
    secret="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
    sed -i "s/^$key=\$/$key=$secret/" "$local_env"
  fi
done
if grep -qx 'MODEL_API_KEY=' "$local_env"; then
  read -r -s -p 'Your Meta MODEL_API_KEY (hidden): ' local_meta_key
  printf '\n'
  [[ -n "$local_meta_key" && "$local_meta_key" != *$'\r'* ]] || { echo 'A Meta key is required.' >&2; exit 1; }
  # Compose single-quoted values preserve dollar signs, slashes and backslashes.
  [[ "$local_meta_key" != *"'"* ]] || { echo 'Set MODEL_API_KEY directly in the private .env.local file.' >&2; exit 1; }
  sed -i '/^MODEL_API_KEY=$/d' "$local_env"
  printf "MODEL_API_KEY='%s'\n" "$local_meta_key" >> "$local_env"
  unset local_meta_key
fi
[[ "$(local_docker info --format '{{.NCPU}}')" -ge 4 && "$(local_docker info --format '{{.MemTotal}}')" -ge 7900000000 ]] || { echo 'Allocate at least 4 CPUs and 8 GiB RAM to Docker.' >&2; exit 1; }
echo 'Building the local runtime. The first build downloads dependencies and InsightFace weights.'
local_compose build api
local_compose run --rm --no-deps api python /scripts/local/check_runtime.py --providers
local_compose up -d --wait --wait-timeout 3600
local_compose exec -T api python /scripts/local/bootstrap.py --queue
echo 'Ready: http://localhost:8080/docs. Install the local Android APK and select an account.'
echo 'Restarting preserves all edits and deletions. Meta indexing continues in the worker.'
