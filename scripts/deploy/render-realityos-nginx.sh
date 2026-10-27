#!/usr/bin/env bash
set -euo pipefail

template_path=${1:?Usage: render-realityos-nginx.sh TEMPLATE OUTPUT}
output_path=${2:?Usage: render-realityos-nginx.sh TEMPLATE OUTPUT}
hostname=${REALITYOS_HOSTNAME:?REALITYOS_HOSTNAME is required}
proxy_port=${REALITYOS_PROXY_PORT:-8090}

if [[ ! "$hostname" =~ ^[a-z0-9.-]+$ ]] || [[ "$hostname" != *.* ]]; then
  echo "REALITYOS_HOSTNAME must be a lowercase DNS hostname." >&2
  exit 2
fi
if [[ ! "$proxy_port" =~ ^[0-9]{2,5}$ ]] || (( proxy_port < 1 || proxy_port > 65535 )); then
  echo "REALITYOS_PROXY_PORT must be a valid TCP port." >&2
  exit 2
fi

sed \
  -e "s/__REALITYOS_HOSTNAME__/${hostname}/g" \
  -e "s/__REALITYOS_PROXY_PORT__/${proxy_port}/g" \
  "$template_path" > "$output_path"
