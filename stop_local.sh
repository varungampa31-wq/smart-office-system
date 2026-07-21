#!/usr/bin/env bash
# Stops everything started by run_local.sh.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT_DIR/.pids"

for name in simulator fog_node backend celery; do
  pidfile="$PID_DIR/$name.pid"
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $name (pid $pid)..."
      kill "$pid" 2>/dev/null
    fi
    rm -f "$pidfile"
  fi
done

if command -v redis-cli >/dev/null 2>&1; then
  redis-cli shutdown nosave >/dev/null 2>&1 || true
fi

echo "Done."
