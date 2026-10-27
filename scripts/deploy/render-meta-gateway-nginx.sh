#!/usr/bin/env bash
set -euo pipefail

template_path=${1:?Usage: render-meta-gateway-nginx.sh TEMPLATE OUTPUT}
output_path=${2:?Usage: render-meta-gateway-nginx.sh TEMPLATE OUTPUT}
gateway_hostname=${META_GATEWAY_HOSTNAME:?META_GATEWAY_HOSTNAME is required}
gateway_port=${META_GATEWAY_PORT:-9088}

if [[ ! "$gateway_hostname" =~ ^[a-z0-9.-]+$ ]] || [[ "$gateway_hostname" != *.* ]]; then
  echo "META_GATEWAY_HOSTNAME must be a lowercase DNS hostname." >&2
  exit 2
fi
if [[ ! "$gateway_port" =~ ^[0-9]{2,5}$ ]] || (( gateway_port < 1 || gateway_port > 65535 )); then
  echo "META_GATEWAY_PORT must be a valid TCP port." >&2
  exit 2
fi

sed \
  -e "s/__META_GATEWAY_HOSTNAME__/${gateway_hostname}/g" \
  -e "s/__META_GATEWAY_PORT__/${gateway_port}/g" \
  "$template_path" > "$output_path"
