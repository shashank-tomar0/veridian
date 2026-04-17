from celery import Celery
from backend.config import settings

celery_app = Celery(
    "veridian_workers",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "workers.tasks.analyze",
        "workers.tasks.text",
        "workers.tasks.image",
        "workers.tasks.audio",
        "workers.tasks.video",
        "workers.tasks.verify",
        "workers.tasks.receipt"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True, # Critical for dead-letter processing
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60, # exponential backoff starts at 60s
)
