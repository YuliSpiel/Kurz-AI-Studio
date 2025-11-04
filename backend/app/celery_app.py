"""
Celery application instance for distributed task execution.
"""
from celery import Celery
from app.config import settings

# Create Celery instance
celery = Celery(
    "autoshorts",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.plan",
        "app.tasks.designer",
        "app.tasks.composer",
        "app.tasks.voice",
        "app.tasks.director",
        "app.tasks.recover",
    ]
)

# Celery configuration
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Auto-retry configuration
celery.conf.task_autoretry_for = (Exception,)
celery.conf.task_retry_kwargs = {"max_retries": 3}
celery.conf.task_retry_backoff = True
celery.conf.task_retry_backoff_max = 600  # 10 minutes max backoff
celery.conf.task_retry_jitter = True


if __name__ == "__main__":
    celery.start()
