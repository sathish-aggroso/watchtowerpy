from app.celery_config import celery_app
from app.tasks.screenshot_tasks import fetch_url_sync


@celery_app.task(bind=True, name="app.tasks.fetch_url")
def fetch_url(self, url: str):
    return fetch_url_sync(url)
