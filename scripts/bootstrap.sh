#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-$PWD}"
CONDA_ENV="${2:-storyline}"
REPO_URL="${3:-https://github.com/FireRedTeam/FireRed-OpenStoryline.git}"
BRANCH="${4:-main}"
PROJECT_DIR="${WORKSPACE}/FireRed-OpenStoryline"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required." >&2
  exit 1
fi
if ! command -v conda >/dev/null 2>&1; then
  echo "conda is required." >&2
  exit 1
fi

mkdir -p "${WORKSPACE}"

if [[ ! -d "${PROJECT_DIR}/.git" ]]; then
  git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${PROJECT_DIR}"
fi

source "$(conda info --base)/etc/profile.d/conda.sh"
if ! conda env list | awk '{print $1}' | grep -qx "${CONDA_ENV}"; then
  conda create -n "${CONDA_ENV}" python=3.11 -y
fi
conda activate "${CONDA_ENV}"

cd "${PROJECT_DIR}"
if [[ -f build_env.sh ]]; then
  bash build_env.sh || true
fi
if [[ -f requirements.txt ]]; then
  pip install -r requirements.txt
fi

echo "Bootstrap completed."
echo "Project: ${PROJECT_DIR}"
echo "Env: ${CONDA_ENV}"
