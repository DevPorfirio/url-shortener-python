from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "url_shortener",
    broker=str(settings.celery_broker_url),
    backend=str(settings.celery_result_backend),
)

celery_app.conf.update(
    task_default_queue=settings.celery_default_queue,
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)


@celery_app.task(name="health.ping")
def ping() -> str:  # pragma: no cover - simple connectivity check
    return "pong"
