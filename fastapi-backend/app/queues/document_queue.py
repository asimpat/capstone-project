from rq import Retry

from app.queue import queue
from app.jobs.callbacks import (
    on_job_success,
    on_job_failure,
    on_job_stopped,
)


def queue_document_for_processing(document_id: str):
    return queue.enqueue(
        "app.jobs.tasks.process_document",
        document_id,
        retry=Retry(
            max=3,
            interval=[2, 4, 8],
        ),
        on_success=on_job_success,
        on_failure=on_job_failure,
        on_stopped=on_job_stopped,
    )
