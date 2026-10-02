import re


SCRIPT_PATTERN = re.compile(
    r"<script\b[^>]*>.*?</script>",
    re.IGNORECASE | re.DOTALL,
)

HTML_TAG_PATTERN = re.compile(
    r"<[^>]+>"
)


def sanitize_string(value: str) -> str:
    """
    Remove script blocks and HTML tags from a string.
    """
    value = SCRIPT_PATTERN.sub("", value)
    value = HTML_TAG_PATTERN.sub("", value)

    return value.strip()


def sanitize_text_fields(data: dict, fields: list[str]) -> dict:
    """
    Sanitize selected string fields.
    """
    cleaned = data.copy()

    for field in fields:
        value = cleaned.get(field)

        if isinstance(value, str):
            cleaned[field] = sanitize_string(value)

    return cleaned
