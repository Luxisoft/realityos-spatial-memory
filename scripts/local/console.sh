#!/usr/bin/env bash
# Concise English output. Percentages count completed steps, not elapsed time.
local_progress() {
  local completed="$1" total="$2" status="$3" filled percent level=INFO bar status_padding
  (( total > 0 && completed >= 0 && completed <= total )) || { echo '[ERROR] Invalid progress step count.' >&2; return 1; }
  percent=$((100 * completed / total))
  filled=$((20 * completed / total))
  printf -v bar '%*s' "$filled" ''; bar=${bar// /#}
  printf -v status_padding '%*s' "$((20 - filled))" ''
  bar+=${status_padding// /-}
  (( completed < total )) || level=SUCCESS
  printf '[%s] [%s] %d%% | %s (%d/%d steps complete)\n' "$level" "$bar" "$percent" "$status" "$completed" "$total"
}

local_console_summary() {
  local line key value secret message level lower
  local -a secrets=()
  local -A seen=()
  # Read values as data, never source the private environment file.
  if [[ -f "$local_env" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      [[ "$line" =~ ^([A-Z][A-Z0-9_]*)=(.*)$ ]] || continue
      key=${BASH_REMATCH[1]}; value=${BASH_REMATCH[2]%$'\r'}
      [[ "$key" =~ PASSWORD|TOKEN|SECRET|KEY|PEPPER ]] || continue
      if [[ "$value" == \"*\" ]]; then
        value=${value:1:-1}
        value=${value//\\\"/\"}; value=${value//\\\\/\\}; value=${value//\$\$/\$}
      elif [[ "$value" == \'*\' ]]; then
        value=${value:1:-1}
      fi
      [[ -z "$value" ]] || secrets+=("$value")
    done < "$local_env"
  fi
  while IFS= read -r line || [[ -n "$line" ]]; do
    message=''; level=INFO; lower=${line,,}
    if [[ "$lower" =~ (^|[^a-z])(warning|warn:|error|failed|denied:|unauthorized:)([^a-z]|$) ]]; then
      level=ERROR
      [[ ! "$lower" =~ (^|[^a-z])(warning|warn:)([^a-z]|$) ]] || level=WARNING
      message=$line
    elif [[ "$line" =~ ^#[0-9]+.*load\ (build\ definition|metadata|build\ context) ]]; then
      message='Preparing the backend build context and base image.'
    elif [[ "$line" =~ ^#[0-9]+.*RUN\ apt-get ]]; then
      message='Installing system and Python dependencies.'
    elif [[ "$line" =~ ^#[0-9]+.*RUN\ python.*FaceAnalysis ]]; then
      message='Preparing computer vision models.'
    elif [[ "$line" =~ ^#[0-9]+.*COPY\ simulator/ ]]; then
      message='Copying the existing local scenarios.'
    elif [[ "$line" =~ ^#[0-9]+\ exporting ]]; then
      message='Exporting the backend image. This can take several minutes.'
    elif [[ "$line" =~ ^(api|worker|postgres|redis):\ |^Available\ local\ accounts:\ [0-9]+$ ]]; then
      message=$line
    elif [[ "$line" == \{* && "$line" == *models_available* ]]; then
      message='Meta API: the required models are available.'
    fi
    [[ -n "$message" ]] || continue
    for secret in "${secrets[@]}"; do message=${message//"$secret"/'[redacted]'}; done
    (( ${#message} <= 300 )) || message="${message:0:297}..."
    [[ -z "${seen["$level $message"]:-}" ]] || continue
    seen["$level $message"]=1
    printf '[%s] %s\n' "$level" "$message"
  done
}
