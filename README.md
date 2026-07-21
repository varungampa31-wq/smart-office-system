# Smart Office — Fog & Edge Computing Project

An attendance/access-control "smart office" system built for a Fog and
Edge Computing module. Three layers, matching the assignment brief:

```
sensor_simulators/  --HTTP-->  fog_node/  --HTTP batch-->  backend/  (Django + Celery/Redis queue)
   (5 sensor types,              (buffers, does light        (validates, enqueues, persists,
    configurable frequency)       edge processing, batches     raises alerts, serves the
                                   on a timer)                  dashboard/REST API)
```

- **`sensor_simulators/`** — five independent async "sensors" (RFID badge
  reader, temperature, humidity, occupancy/motion, door contact), each
  generating readings on its own configurable interval and posting them
  to the fog node.
- **`fog_node/`** — a small FastAPI service that buffers incoming
  readings, tags them with a fog node ID, does light local processing
  (flags near-duplicate ambient readings as noise), and periodically
  dispatches a batch to the cloud backend (configurable dispatch rate).
- **`backend/`** — Django + Django REST Framework. Human users (the
  frontend, JWT-authenticated) hit the normal CRUD/dashboard API. The
  fog node hits a separate API-key-authenticated ingestion endpoint,
  which enqueues each reading on Celery/Redis instead of writing to the
  database inline — that's the "scalable" part: the web process stays
  fast regardless of DB/worker load, and you can run more worker
  processes independently of the web process as sensor volume grows.
- **`total_frontend/`** — plain HTML/CSS/JS dashboard, employee,
  attendance, alerts, and scanner pages that call the Django REST API.

See `docs/ARCHITECTURE.md` for more detail (useful for the report).

## Running everything locally (no Docker)

You need Python 3.10+ and, for the real queue, Redis (`sudo apt install
redis-server` on Ubuntu/Debian, `brew install redis` on macOS). If you
don't want to install Redis, you can still run everything with tasks
processed synchronously in-process (see `--no-redis` below) — it just
means you're not exercising the actual queue.

### Option A — one command

```bash
./run_local.sh            # sets up a venv, installs deps, starts everything
# or, without Redis/Celery:
./run_local.sh --no-redis

./stop_local.sh           # stops everything the script started
```

This creates `.venv/`, installs each service's `requirements.txt` into
it, copies each `.env.example` to `.env` (edit these if you want to
change ports, frequencies, thresholds, etc.), runs migrations, seeds 5
demo employees with known RFID tags, and starts:

- Redis (if not using `--no-redis`)
- a Celery worker (`celery -A smartoffice worker`)
- the Django backend on `http://localhost:8000`
- the fog node on `http://localhost:9000`
- the 5 sensor simulators

Logs are written to `logs/*.log`. Then open
`total_frontend/frontend/index.html` in a browser (or serve the
`total_frontend` folder with any static file server) to use the
dashboard/employees/attendance/alerts/scanner pages.

### Option B — five terminals (equivalent, more visible for a demo)

```bash
# 1) Redis
redis-server --port 6379

# 2) Celery worker
cd backend
cp .env.example .env        # first time only
python -m venv ../.venv && ../.venv/bin/pip install -r requirements.txt   # first time only
../.venv/bin/celery -A smartoffice worker --loglevel=info

# 3) Django backend
cd backend
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py seed_demo
../.venv/bin/python manage.py runserver 0.0.0.0:8000

# 4) Fog node
cd fog_node
cp .env.example .env        # first time only
../.venv/bin/pip install -r requirements.txt   # first time only
../.venv/bin/uvicorn fog_node.main:app --host 0.0.0.0 --port 9000

# 5) Sensor simulators
cd sensor_simulators
cp .env.example .env        # first time only
../.venv/bin/pip install -r requirements.txt   # first time only
../.venv/bin/python -m sensor_simulators.simulator
```

### Verifying it's working

```bash
curl http://localhost:9000/health          # fog node
curl http://localhost:9000/stats           # buffered/dispatched counters
curl http://localhost:8000/admin/          # Django admin
```

**Frontend login**: `seed_demo` (run automatically by `run_local.sh`,
or manually via `python manage.py seed_demo`) creates a demo login for
`total_frontend/frontend/index.html`:

```
username: admin
password: admin123
```

This is a separate concept from the seeded *Employees* (`EMP001`…
`EMP005`) — the login is a Django `User` account (who's allowed to use
the dashboard), Employees are what sensors track (who gets scanned/
checked in). Nothing links the two, so don't expect an employee's RFID
tag to work as a login, or vice versa. Change/remove the demo admin
password before anything beyond local coursework use.

Within a few seconds of starting the simulators you should see
`SensorEvent` rows and (occasionally, since the temperature/humidity/
RFID simulators are tuned to trigger it sometimes but not constantly)
`Alert` rows appear — check via `/admin/`, `/api/sensors/sensors/`, or
`/api/sensors/stats/`.

### Human-triggered scanning (separate from the fog pipeline)

`total_frontend/frontend/scanner.html` still works as before — it's a
manual "badge scan" button hitting `POST /api/scanner/scan/` for demo/
testing convenience, independent of the autonomous sensor simulators.
Use the seeded RFID tags (`RFID-A1001` … `RFID-A1005`, see
`backend/employees/management/commands/seed_demo.py`) or add your own
employees via `/admin/`.

## What changed vs. the original zip

If you're comparing against what you had before, the short version:

- **Fixed bugs**: `SensorEvent.employee` was a required FK but code tried
  to save `employee=None` for invalid scans (would crash); `Alert`
  choices were missing `MULTIPLE_SCAN`, which the code already used;
  `scanner/views.py` wrote `sensor_type` values that didn't match any
  defined choice; `seed_demo` created Employee records but no Django
  User, so the frontend login page had no credentials that would work.
- **Added**: the fog node, the 5 sensor simulators, the Celery/Redis
  ingestion queue, the API-key-authenticated ingestion endpoint, a
  sensor-stats aggregation endpoint, and `run_local.sh`/`stop_local.sh`.
- **Unchanged**: the employees/attendance/alerts/dashboard CRUD API and
  the frontend pages behave exactly as before.

## Still on you before submission

- **Deployment to a public cloud** is not done here (this project only
  covers running everything locally). The brief requires this — put the
  Django backend, fog node, and simulators on cloud VM(s)/services and
  update `BACKEND_URL`/`FOG_NODE_URL` accordingly.
- **The 8-page report and demo video/slides.**
- Consider swapping SQLite for Postgres for anything beyond local
  testing (`DATABASE_URL` in `backend/.env.example` is already wired up
  for this — see `backend/smartoffice/settings.py`).
