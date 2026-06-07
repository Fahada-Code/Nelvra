import os

from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

app = Celery(
    "nelvra",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "workers.quality_evaluator",
        "workers.drift_detector",
        "workers.alert_dispatcher",
        "workers.prompt_optimizer",
    ],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # These are fire-and-forget side-effect tasks — nobody reads their return
    # value. Ignoring results avoids the result backend entirely on enqueue,
    # which otherwise blocks the caller retrying Redis when it's unreachable.
    task_ignore_result=True,
    # Fail fast on enqueue so a slow/unreachable broker never hangs an API
    # request; the producer (api/tasks.py) catches the error and skips the task.
    task_publish_retry=False,
    broker_connection_retry_on_startup=False,
    broker_transport_options={"socket_connect_timeout": 2, "socket_timeout": 2},
    beat_schedule={
        "check-alerts-every-minute": {
            "task": "workers.alert_dispatcher.check_all_alerts",
            "schedule": 60.0,
        },
        "detect-drift-hourly": {
            "task": "workers.drift_detector.detect_all_drift",
            "schedule": 3600.0,
        },
        "refresh-prompt-stats-hourly": {
            "task": "workers.drift_detector.refresh_all_prompt_stats",
            "schedule": 3600.0,
        },
    },
)
