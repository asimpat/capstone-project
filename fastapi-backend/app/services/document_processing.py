from pathlib import Path


SUPPORTED_FORMATS = {
    "txt": "text",
    "md": "markdown",
    "pdf": "pdf",
}


def detect_format(filename: str) -> str:
    extension = Path(filename).suffix.lower().lstrip(".")

    if extension not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported file format: .{extension}"
        )

    return SUPPORTED_FORMATS[extension]


def extract_text(
    content: bytes | str,
    format: str,
) -> dict:
    if format == "text":
        text = (
            content
            if isinstance(content, str)
            else content.decode("utf-8")
        )

        return {
            "text": text,
        }

    if format == "markdown":
        raw = (
            content
            if isinstance(content, str)
            else content.decode("utf-8")
        )

        return {
            "text": strip_markdown(raw),
        }

    if format == "pdf":
        return extract_pdf_text(content)

    raise ValueError(
        f"Unsupported format: {format}"
    )


def extract_pdf_text(
    content: bytes | str,
) -> dict:
    import fitz

    if isinstance(content, str):
        import base64

        buffer = base64.b64decode(content)
    else:
        buffer = content

    pdf = fitz.open(
        stream=buffer,
        filetype="pdf",
    )

    pages = []

    for page in pdf:
        pages.append(page.get_text())

    page_count = len(pdf)

    pdf.close()

    text = "\n\n".join(pages)

    return {
        "text": clean_extracted_text(text),
        "pageCount": page_count,
    }


def strip_markdown(text: str) -> str:
    import re

    text = re.sub(
        r"#{1,6}\s+",
        "",
        text,
    )

    text = re.sub(
        r"\*{1,3}(.*?)\*{1,3}",
        r"\1",
        text,
    )

    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text,
    )

    text = re.sub(
        r"`{1,3}[^`]*`{1,3}",
        "",
        text,
    )

    text = re.sub(
        r"^[\-\*+]\s+",
        "",
        text,
        flags=re.MULTILINE,
    )

    return text.strip()


def clean_extracted_text(text: str) -> str:
    import re

    text = text.replace(
        "\r\n",
        "\n",
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    text = re.sub(
        r"\s{3,}",
        " ",
        text,
    )

    return text.strip()
