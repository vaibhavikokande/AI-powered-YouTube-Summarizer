from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ai_youtube_summarizer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    # Explicit module import rather than autodiscover_tasks() — autodiscover
    # looks for a submodule literally named "tasks" inside each listed
    # package (i.e. app.tasks.tasks), which isn't our layout.
    include=["app.tasks.content_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # A single retry policy for transient infra failures (DB/broker
    # connection blips) at the task level — distinct from the LLM-call-level
    # retry already in app/agents/llm_provider.py, which handles provider
    # rate limits/timeouts specifically.
    task_default_retry_delay=10,
    task_acks_late=True,
)
