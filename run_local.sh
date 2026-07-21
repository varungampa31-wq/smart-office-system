#!/usr/bin/env bash
# Starts every service as a plain local background process: no Docker.
# Mirrors exactly what you'd run in 5 separate terminals -- this script
# just does it for you and logs each service to logs/*.log.
#
# Usage:
#   ./run_local.sh          # starts Redis (if installed) + Celery worker + Django + fog node + simulators
#   ./run_local.sh --no-redis   # skips Redis/Celery, runs tasks in-process instead (simpler, less "real")
#
# Stop everything with: ./stop_local.sh

set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
LOG_DIR="$ROOT_DIR/logs"
PID_DIR="$ROOT_DIR/.pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

USE_REDIS=1
if [[ "$1" == "--no-redis" ]]; then
  USE_REDIS=0
fi

# ---------------------------------------------------------------------------
# 1. Virtualenv + dependencies (one shared venv for backend + fog_node +
#    sensor_simulators keeps this script simple; feel free to split them
#    into per-service venvs if you prefer).
# ---------------------------------------------------------------------------
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Creating virtualenv at $VENV_DIR ..."
  python3 -m venv "$VENV_DIR"
fi

PIP="$VENV_DIR/bin/pip"
PY="$VENV_DIR/bin/python"

echo "Installing dependencies (first run only takes a while)..."
"$PIP" install -q --upgrade pip
"$PIP" install -q -r "$ROOT_DIR/backend/requirements.txt"
"$PIP" install -q -r "$ROOT_DIR/fog_node/requirements.txt"
"$PIP" install -q -r "$ROOT_DIR/sensor_simulators/requirements.txt"

# ---------------------------------------------------------------------------
# 2. Env files (copy the examples if you haven't already)
# ---------------------------------------------------------------------------
[[ -f "$ROOT_DIR/backend/.env" ]] || cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
[[ -f "$ROOT_DIR/fog_node/.env" ]] || cp "$ROOT_DIR/fog_node/.env.example" "$ROOT_DIR/fog_node/.env"
[[ -f "$ROOT_DIR/sensor_simulators/.env" ]] || cp "$ROOT_DIR/sensor_simulators/.env.example" "$ROOT_DIR/sensor_simulators/.env"

# ---------------------------------------------------------------------------
# 3. Redis + Celery worker (the ingestion queue), unless --no-redis
# ---------------------------------------------------------------------------
if [[ "$USE_REDIS" -eq 1 ]]; then
  if ! command -v redis-server >/dev/null 2>&1; then
    echo "redis-server not found. Install it (e.g. 'sudo apt install redis-server')"
    echo "or re-run this script with --no-redis to skip the real queue."
    exit 1
  fi

  if ! redis-cli ping >/dev/null 2>&1; then
    echo "Starting redis-server..."
    redis-server --daemonize yes --port 6379
    sleep 1
  fi

  export CELERY_TASK_ALWAYS_EAGER=False
  echo "Starting Celery worker..."
  (cd "$ROOT_DIR/backend" && nohup "$VENV_DIR/bin/celery" -A smartoffice worker --loglevel=info --concurrency=2 \
    > "$LOG_DIR/celery.log" 2>&1 & echo $! > "$PID_DIR/celery.pid")
else
  echo "Running WITHOUT Redis/Celery: tasks will run synchronously in-process."
  export CELERY_TASK_ALWAYS_EAGER=True
fi

# ---------------------------------------------------------------------------
# 4. Django backend: migrate, seed demo employees, run dev server
# ---------------------------------------------------------------------------
echo "Running migrations + seeding demo employees..."
(cd "$ROOT_DIR/backend" && "$PY" manage.py migrate)
(cd "$ROOT_DIR/backend" && "$PY" manage.py seed_demo)

echo "Starting Django backend on http://localhost:8000 ..."
(cd "$ROOT_DIR/backend" && nohup "$PY" manage.py runserver 0.0.0.0:8000 --noreload \
  > "$LOG_DIR/backend.log" 2>&1 & echo $! > "$PID_DIR/backend.pid")
sleep 2

# ---------------------------------------------------------------------------
# 5. Fog node (FastAPI)
# ---------------------------------------------------------------------------
echo "Starting fog node on http://localhost:9000 ..."
(cd "$ROOT_DIR" && BACKEND_URL="http://localhost:8000" nohup "$PY" -m uvicorn fog_node.main:app --host 0.0.0.0 --port 9000 \
  > "$LOG_DIR/fog_node.log" 2>&1 & echo $! > "$PID_DIR/fog_node.pid")
sleep 2

# ---------------------------------------------------------------------------
# 6. Sensor simulators (5 sensor types, async loops)
# ---------------------------------------------------------------------------
echo "Starting sensor simulators..."
(cd "$ROOT_DIR" && FOG_NODE_URL="http://localhost:9000" nohup "$PY" -m sensor_simulators.simulator \
  > "$LOG_DIR/simulator.log" 2>&1 & echo $! > "$PID_DIR/simulator.pid")

echo ""
echo "All services started."
echo "  Backend API:   http://localhost:8000/api/"
echo "  Django admin:  http://localhost:8000/admin/"
echo "  Fog node:      http://localhost:9000/health  and  /stats"
echo "  Frontend:      open total_frontend/frontend/index.html in a browser"
echo ""
echo "Logs are in $LOG_DIR/*.log. Stop everything with ./stop_local.sh"
