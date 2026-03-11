#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$PWD}"
OWNER="${2:-}"
NAME="${3:-}"

cd "${REPO_DIR}"
if [[ ! -d .git ]]; then
  git init
fi

git add .
git commit -m "chore: standalone OpenStoryline automation pack" || true

if [[ -n "${OWNER}" && -n "${NAME}" ]]; then
  REMOTE_URL="https://github.com/${OWNER}/${NAME}.git"
  git remote remove origin >/dev/null 2>&1 || true
  git remote add origin "${REMOTE_URL}"
  git branch -M main
  git push -u origin main
  echo "Pushed to ${REMOTE_URL}"
  exit 0
fi

if command -v gh >/dev/null 2>&1; then
  gh repo create --source . --public --push
  exit 0
fi

echo "No OWNER/NAME provided and gh CLI not available."
echo "Run: bash scripts/publish_github.sh <repo_dir> <owner> <repo>"
