from app.queues.dead_letter_queue import dead_letter_queue
from app.utils.logger import logger


def on_job_success(job, connection, result, *args, **kwargs):
    logger.info(
        "Job completed | job_id=%s result=%s",
        job.id,
        result,
    )


def on_job_failure(
    job,
    connection,
    exc_type,
    exc_value,
    traceback,
    *args,
    **kwargs,
):
    logger.error(
        "Job failed | job_id=%s error=%s",
        job.id,
        exc_value,
    )

    dead_letter_queue.enqueue(
        "app.jobs.tasks.record_dead_letter",
        job.id,
        str(exc_value),
    )


def on_job_stopped(job, connection, *args, **kwargs):
    logger.warning(
        "Job stopped | job_id=%s",
        job.id,
    )
