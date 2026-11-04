#!/usr/bin/env bash
# This suite uses fake Docker output and disposable credentials only.
set -euo pipefail
source "$(dirname -- "$0")/../../scripts/local/common.sh"
console_test_root="$(mktemp -d)"
local_env="$console_test_root/.env.local"
cleanup() { rm -f -- "$local_env"; rmdir -- "$console_test_root"; }
trap cleanup EXIT
cat > "$local_env" <<'ENV'
MODEL_API_KEY='fake-private-key'
DEVICE_CREDENTIAL_PEPPER="fake-$$pepper"
ENV
fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }

output=$(local_console_summary <<'LOG'
#13 [9/14] RUN apt-get update && pip install .
#13 101.1 Downloading opencv_python_headless.whl.metadata (19 kB)
#13 101.8 Collecting stringzilla>=3.10.4
#13 102.5 INFO: pip is looking at multiple versions of kombu[redis]
WARNING: fake-private-key fake-$pepper needs attention
#19 exporting to image
#19 exporting layers
api: Up 1 minute (healthy)
LOG
)
[[ "$output" == *'Installing system and Python dependencies.'* ]] || fail 'Missing build summary.'
[[ "$output" != *Collecting* && "$output" != *Downloading* && "$output" != *kombu* ]] || fail 'Verbose package output was displayed.'
[[ "$output" != *fake-* && "$output" == *'[WARNING]'*'[redacted] [redacted]'* ]] || fail 'Secrets were not redacted.'
[[ $(printf '%s\n' "$output" | grep -c 'Exporting the backend image') == 1 ]] || fail 'Duplicate phase messages.'
[[ "$output" == *'[INFO] api: Up 1 minute (healthy)'* ]] || fail 'Compact service status was lost.'

docker() { printf '%s\n' 'ERROR: failed to download using fake-private-key'; return 7; }
if output=$(local_compose build api 2>&1); then
  fail 'Docker failure was swallowed.'
else
  [[ $? == 7 ]] || fail 'Docker exit code changed.'
fi
[[ "$output" == *'[ERROR]'* && "$output" != *fake-private* ]] || fail 'Error was hidden or leaked credentials.'
[[ "$output" != *SUCCESS* && "$output" != *'100%'* ]] || fail 'Failed work was marked complete.'

docker() { printf '%s\n' 'Collecting a-package' '{"models_available":["muse-spark-1.3"]}'; }
output=$(local_compose run api)
[[ "$output" == '[INFO] Meta API: the required models are available.' ]] || fail 'Provider summary changed.'
output=$(local_progress 3 10 'Building the backend image')
[[ "$output" == '[INFO] [######--------------] 30% | Building the backend image (3/10 steps complete)' ]] || fail 'Incorrect stage progress.'
output=$(local_progress 10 10 'Local setup completed')
[[ "$output" == '[SUCCESS] [####################] 100%'* ]] || fail 'Missing completion.'
if local_progress 11 10 'Invalid' >/dev/null 2>&1; then fail 'Invalid progress was accepted.'; fi
echo '6 Bash console regression cases passed: summaries, redaction, errors, provider status and progress.'
