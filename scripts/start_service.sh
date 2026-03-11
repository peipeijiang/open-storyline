#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"
PROJECT_DIR="${2:-$PWD/FireRed-OpenStoryline}"
CONDA_ENV="${3:-storyline}"

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
bash "${SCRIPT_DIR}/tools/storyline_service.sh" "${ACTION}" "${PROJECT_DIR}" "${CONDA_ENV}"
