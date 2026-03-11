#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:?project dir required}"
shift

BASE_URL="${BASE_URL:-http://127.0.0.1:7860}"
OUTPUT_JSON="${OUTPUT_JSON:-/tmp/storyline_run.json}"

python "$(cd "$(dirname "$0")/.." && pwd)/tools/storyline_workflow.py"   --base-url "${BASE_URL}"   "$@"   --output-json "${OUTPUT_JSON}"
