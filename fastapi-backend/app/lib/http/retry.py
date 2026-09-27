import time

import httpx


def is_retryable(error: Exception) -> bool:
    if isinstance(error, httpx.TimeoutException):
        return True

    if isinstance(error, httpx.RequestError):
        return True

    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code

        return (
            status == 408
            or status == 429
            or status >= 500
        )

    return False


def with_retry(
    operation,
    max_attempts: int = 3,
    base_delay: float = 1.0,
):
    last_error = None

    for attempt in range(1, max_attempts + 1):

        try:
            return operation()

        except Exception as error:
            last_error = error

            if not is_retryable(error):
                raise

            if attempt == max_attempts:
                raise

            retry_after = None

            if isinstance(error, httpx.HTTPStatusError):
                retry_after = error.response.headers.get(
                    "Retry-After"
                )

            if retry_after:
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = base_delay * (2 ** (attempt - 1))
            else:
                delay = base_delay * (2 ** (attempt - 1))

            print(
                f"Attempt {attempt} failed. "
                f"Retrying in {delay}s..."
            )

            time.sleep(delay)

    raise last_error
