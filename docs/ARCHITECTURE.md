# Architecture Notes

## Layers

**Sensor layer** (`sensor_simulators/`): five independent async loops,
each modelling a different physical sensor with its own sampling
frequency (`sensor_simulators/config.py`):

| Sensor | Type | Default interval |
|---|---|---|
| RFID badge reader | identity | 8s |
| Temperature | ambient | 4s |
| Humidity | ambient | 6s |
| Occupancy/motion (PIR) | ambient | 5s |
| Door contact | ambient | 10s |

Each posts one reading at a time to the fog node over HTTP
(`POST /ingest/{sensor_type}`). Real hardware would more likely use
MQTT for this hop; HTTP was chosen here for simplicity — worth a line
in the report's design-decisions/future-work section.

**Fog layer** (`fog_node/main.py`): a single FastAPI process that:
1. Accepts readings from sensors, validates them (pydantic schema).
2. Buffers them in memory, tagging each with `fog_node_id` and
   `received_at`.
3. Applies a small amount of local (edge) processing: ambient readings
   that changed by less than `TEMPERATURE_NOISE_BAND_C` since the last
   reading from the same device are flagged as noise in the payload
   (`raw.fog_flag = "within_noise_band"`) rather than being dropped —
   they're still forwarded and stored, just annotated, so nothing is
   silently lost, but a dashboard/report can distinguish signal from
   noise.
4. On a fixed timer (`DISPATCH_INTERVAL_SECONDS`), flushes the buffer as
   one batch POST to the backend's ingestion endpoint, with retry +
   re-buffering on failure so a temporary backend outage doesn't lose
   data.

This is the core "why have a fog node at all" argument for the report:
it decouples sensor sampling rate from cloud request rate (5 sensors
firing every few seconds becomes one batched request every
`DISPATCH_INTERVAL_SECONDS`), and it's a natural place to put filtering/
aggregation logic that shouldn't have to round-trip to the cloud.

**Cloud/backend layer** (`backend/`, Django + DRF):
- `sensors.views.SensorIngestView` — machine-to-machine endpoint, shared
  API key auth (`sensors/authentication.py`), accepts a batch of
  readings and enqueues each one on Celery (`sensors/tasks.py:
  process_sensor_reading`), returning `202 Accepted` immediately.
- A separate Celery worker process consumes the queue, resolves the
  employee (if any), applies threshold rules (temperature/humidity),
  persists a `SensorEvent`, and raises an `Alert` if a threshold was
  crossed.
- The rest of the API (`employees`, `attendance`, `alerts`, `dashboard`,
  `scanner`) is JWT-authenticated and unchanged from the original
  design, serving the frontend dashboard.

## Why this counts as "scalable"

The naive version of this system would have the ingestion endpoint
write directly to the database inside the request/response cycle. That
ties API latency to DB write latency and to however much business logic
(alert rules, employee lookups) runs per reading — and it means the
only way to handle more sensor throughput is to give the single web
process more CPU.

Putting a queue (Redis + Celery) between "accept the reading" and
"process the reading" means:
- The ingestion endpoint's response time is ~constant regardless of
  sensor volume (`Response 202` doesn't wait for the DB write).
- Celery workers can be scaled horizontally and independently of the
  web process — `celery -A smartoffice worker` can run as many replicas
  as needed, e.g. in a separate autoscaling group/ECS service in a real
  deployment.
- A burst of readings (e.g. many sensors reporting at once) queues up
  rather than causing web-process request timeouts.

For a cloud deployment, `REDIS_URL` would point at a managed Redis
(e.g. AWS ElastiCache), `DATABASE_URL` at a managed Postgres (e.g. RDS —
already supported in `backend/smartoffice/settings.py`), and the web/
worker processes would run as separate autoscaled services.

## Data model changes from the original design

`sensors.models.SensorEvent` was extended to support ambient sensors
that aren't tied to one employee:
- `employee` made nullable (was previously required, which would have
  crashed on invalid-RFID events with no resolved employee).
- Added `value` (float), `unit`, `fog_node_id`, `recorded_at`.
- `recorded_at` (set by the fog node, when the sensor captured the
  reading) vs. `timestamp` (set by the backend, when it was stored) —
  the gap between the two is the sensor→fog→cloud latency, which is
  worth graphing in the report if you want to discuss latency/
  performance.

## Known simplifications (good "future work" material for the report)

- Fog node authentication with the backend is a single shared API key,
  not per-device credentials/certificates (e.g. mutual TLS via AWS IoT
  Core would be the production-grade version).
- The fog node buffer is in-memory and single-process; a fog node
  restart loses whatever hasn't been dispatched yet. A production
  version might persist the buffer or use a local durable queue.
- Only one fog node is modelled by default (`FOG_NODE_ID=fog-01`); the
  code supports running several (each `SensorEvent.fog_node_id` traces
  which one forwarded it), but they're not orchestrated here.
- Sensor→fog transport is plain HTTP; MQTT (with QoS, retained
  messages) is more typical for real IoT sensor fleets and would be
  worth discussing as an alternative.
