#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:?project dir required}"
shift

python "$(cd "$(dirname "$0")/.." && pwd)/tools/storyline_batch_instruction.py"   --project-root "${PROJECT_DIR}"   "$@"
