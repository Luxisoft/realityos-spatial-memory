#!/usr/bin/env sh

# Creates private, Git-ignored runtime storage under the deployed project.
# This directory is intentionally not a Docker volume and is used only to stage
# consented manual test photos before the explicit importer is invoked.
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
staging_dir="$project_root/.runtime/manual-captures/incoming"

install -d -m 0750 "$staging_dir"
chmod 0750 "$project_root/.runtime" "$project_root/.runtime/manual-captures" "$staging_dir"
printf '%s\n' "Private manual-photo staging directory ready: $staging_dir"
