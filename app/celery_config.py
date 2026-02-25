import os
from celery import Celery

broker_url = os.environ.get("CELERY_BROKER_URL", "sqla+sqlite:///./db/celery_broker.db")
result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND", "db+sqlite:///./db/celery_results.db"
)

celery_app = Celery(
    "checkdiff",
    broker=broker_url,
    backend=result_backend,
    include=[
        "app.tasks.screenshot_tasks",
        "app.tasks.check_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=180,
    task_soft_time_limit=150,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
    result_expires=3600,
)
