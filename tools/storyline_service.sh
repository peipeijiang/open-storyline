#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  storyline_service.sh start [project_dir] [conda_env]
  storyline_service.sh stop [project_dir]
  storyline_service.sh status [project_dir]

Defaults:
  project_dir = current directory
  conda_env   = storyline
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

ACTION="$1"
PROJECT_DIR="${2:-$(pwd)}"
CONDA_ENV="${3:-storyline}"

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Project directory not found: $PROJECT_DIR" >&2
  exit 1
fi

find_listeners() {
  lsof -tiTCP:7860 -sTCP:LISTEN -n -P 2>/dev/null || true
  lsof -tiTCP:8001 -sTCP:LISTEN -n -P 2>/dev/null || true
}

check_ports() {
  local web mcp
  web=$(lsof -tiTCP:7860 -sTCP:LISTEN -n -P 2>/dev/null | head -n1 || true)
  mcp=$(lsof -tiTCP:8001 -sTCP:LISTEN -n -P 2>/dev/null | head -n1 || true)
  if [[ -n "$web" && -n "$mcp" ]]; then
    return 0
  fi
  return 1
}

case "$ACTION" in
  start)
    if check_ports; then
      echo "OpenStoryline is already running on ports 7860 and 8001"
      exit 0
    fi

    # Use login shell to ensure conda function is available.
    (
      source /opt/anaconda3/etc/profile.d/conda.sh
      conda activate "$CONDA_ENV"
      cd "$PROJECT_DIR"
      nohup bash run.sh > run.log 2>&1 &
      echo $! > .storyline_service.pid
    )

    sleep 3
    if check_ports; then
      echo "Started successfully"
      echo "Web: http://127.0.0.1:7860"
      echo "MCP: http://127.0.0.1:8001"
      exit 0
    fi

    echo "Failed to start; inspect $PROJECT_DIR/run.log" >&2
    exit 1
    ;;

  stop)
    mapfile -t pids < <(find_listeners | awk '!seen[$0]++')
    if [[ ${#pids[@]} -eq 0 ]]; then
      echo "No listeners found on ports 7860/8001"
      exit 0
    fi

    kill "${pids[@]}" || true
    sleep 1
    echo "Stopped PIDs: ${pids[*]}"
    ;;

  status)
    web_pid=$(lsof -tiTCP:7860 -sTCP:LISTEN -n -P 2>/dev/null | head -n1 || true)
    mcp_pid=$(lsof -tiTCP:8001 -sTCP:LISTEN -n -P 2>/dev/null | head -n1 || true)

    if [[ -z "$web_pid" && -z "$mcp_pid" ]]; then
      echo "Status: stopped"
      exit 1
    fi

    echo "Status: running"
    [[ -n "$web_pid" ]] && echo "Web PID: $web_pid (port 7860)"
    [[ -n "$mcp_pid" ]] && echo "MCP PID: $mcp_pid (port 8001)"
    if command -v curl >/dev/null 2>&1; then
      code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://127.0.0.1:7860/ || true)
      echo "Web GET / HTTP code: ${code:-N/A}"
    fi
    ;;

  *)
    usage
    exit 1
    ;;
esac
