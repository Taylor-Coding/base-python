from app.integrations.celery_app import celery_app
from app.integrations.s3 import upload_file


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_and_upload_file(self, file_bytes: bytes, filename: str, content_type: str = "application/octet-stream") -> dict:
    try:
        key = upload_file(file_bytes, filename, content_type)
        return {"status": "uploaded", "key": key}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def cleanup_temp_files(keys: list[str]) -> dict:
    from app.integrations.s3 import delete_file

    deleted = []
    for key in keys:
        delete_file(key)
        deleted.append(key)
    return {"status": "cleaned", "deleted": deleted}
