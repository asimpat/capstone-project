import logging
import sys
import os


class SensitiveDataFilter(logging.Filter):
    """
    Prevent sensitive information from appearing in logs.
    """

    SENSITIVE_FIELDS = {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "api_key",
        "secret",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        message = str(record.msg)

        for field in self.SENSITIVE_FIELDS:
            if field.lower() in message.lower():
                record.msg = "[REDACTED]"
                record.args = ()

        return True


def setup_logger():
    environment = os.getenv("ENVIRONMENT", "development")

    logger = logging.getLogger("docuchat")

    if logger.handlers:
        return logger

    logger.setLevel(
        logging.INFO if environment == "production"
        else logging.DEBUG
    )

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )

    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    logger.addHandler(handler)

    return logger


logger = setup_logger()
