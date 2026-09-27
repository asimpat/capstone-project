from app.queues.dead_letter_queue import dead_letter_queue


def on_job_success(job, connection, result, *args, **kwargs):
    print(
        f"[JOB COMPLETED] "
        f"job_id={job.id}, "
        f"result={result}"
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
    print(
        f"[JOB FAILED] "
        f"job_id={job.id}, "
        f"error={exc_value}"
    )

    dead_letter_queue.enqueue(
        "app.jobs.tasks.record_dead_letter",
        job.id,
        str(exc_value),
    )


def on_job_stopped(job, connection, *args, **kwargs):
    print(
        f"[JOB STOPPED] "
        f"job_id={job.id}"
    )
