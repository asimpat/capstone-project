from fastapi import Request


def add_rate_limit_headers(
    request: Request,
    response,
    result: dict,
):
    response.headers["RateLimit-Limit"] = str(
        result["limit"]
    )

    response.headers["RateLimit-Remaining"] = str(
        result["remaining"]
    )

    response.headers["RateLimit-Reset"] = str(
        result["reset"]
    )
