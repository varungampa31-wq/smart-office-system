"""
Celery application for the smartoffice project.

This is the queue that decouples "receive a sensor reading from the fog
node" from "process and persist it". In a real deployment the broker
(REDIS_URL) would be something like AWS ElastiCache for Redis, and you'd
run one or more `celery -A smartoffice worker` processes that can be
scaled independently of the web process (e.g. in their own autoscaling
group / ECS service) -- that's the "scalable backend" story for the
report: the API layer stays thin and fast, the worker layer scales with
sensor throughput.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartoffice.settings")

app = Celery("smartoffice")

# Read CELERY_* settings from Django settings.py (see the "Fog / edge
# ingestion & scalability" section at the bottom of that file).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in each installed app (sensors/tasks.py, etc).
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
