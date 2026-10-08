import math
import re


SEPARATORS = [
    "\n\n",
    "\n",
    ". ",
    "? ",
    "! ",
    " ",
]


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def get_last_n_tokens(
    text: str,
    n: int,
) -> str:
    if not text or n <= 0:
        return ""

    words = text.split()

    words_needed = math.ceil(n / 1.3)

    return " ".join(
        words[-words_needed:]
    )


def split_by_separator(
    text: str,
    separator: str,
    max_tokens: int,
) -> list[dict]:
    parts = text.split(separator)

    chunks = []

    current_parts = []
    current_start = 0

    for index, part in enumerate(parts):
        if not part:
            continue

        if current_parts:
            candidate = (
                separator.join(current_parts)
                + separator
                + part
            )
        else:
            candidate = part

        if estimate_tokens(candidate) <= max_tokens:
            current_parts.append(part)
            continue

        if current_parts:
            chunk_text = separator.join(
                current_parts
            ).strip()

            start_char = current_start

            end_char = (
                start_char
                + len(chunk_text)
            )

            chunks.append(
                {
                    "text": chunk_text,
                    "startChar": start_char,
                    "endChar": end_char,
                }
            )

            current_start = (
                end_char
                + len(separator)
            )

            current_parts = [part]

        else:
            chunks.append(
                {
                    "text": part.strip(),
                    "startChar": current_start,
                    "endChar": (
                        current_start
                        + len(part)
                    ),
                }
            )

            current_start += (
                len(part)
                + len(separator)
            )

    if current_parts:
        chunk_text = separator.join(
            current_parts
        ).strip()

        chunks.append(
            {
                "text": chunk_text,
                "startChar": current_start,
                "endChar": (
                    current_start
                    + len(chunk_text)
                ),
            }
        )

    return chunks


def recursive_split(
    text: str,
    separators: list[str],
    max_tokens: int,
    start_offset: int = 0,
) -> list[dict]:
    text = text.strip()

    if not text:
        return []

    if estimate_tokens(text) <= max_tokens:
        return [
            {
                "text": text,
                "startChar": start_offset,
                "endChar": (
                    start_offset
                    + len(text)
                ),
            }
        ]

    for separator_index, separator in enumerate(
        separators
    ):
        if separator not in text:
            continue

        parts = text.split(separator)

        if len(parts) <= 1:
            continue

        raw_chunks = split_by_separator(
            text,
            separator,
            max_tokens,
        )

        results = []

        remaining_separators = separators[
            separator_index + 1:
        ]

        for chunk in raw_chunks:
            if (
                estimate_tokens(chunk["text"])
                <= max_tokens
            ):
                results.append(chunk)
                continue

            if remaining_separators:
                nested_chunks = recursive_split(
                    chunk["text"],
                    remaining_separators,
                    max_tokens,
                    chunk["startChar"],
                )

                results.extend(
                    nested_chunks
                )
            else:
                results.append(chunk)

        return results

    return [
        {
            "text": text,
            "startChar": start_offset,
            "endChar": (
                start_offset
                + len(text)
            ),
        }
    ]


def add_overlap(
    chunks: list[dict],
    overlap_tokens: int,
) -> list[dict]:
    if (
        not chunks
        or overlap_tokens <= 0
        or len(chunks) == 1
    ):
        return chunks

    results = [chunks[0].copy()]

    for index in range(1, len(chunks)):
        previous = results[-1]
        current = chunks[index].copy()

        overlap = get_last_n_tokens(
            previous["text"],
            overlap_tokens,
        )

        if overlap:
            current["text"] = (
                overlap
                + "\n"
                + current["text"]
            )

        results.append(current)

    return results


def chunk_document(
    text: str,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
    min_chunk_tokens: int = 50,
) -> list[dict]:
    if not text or not text.strip():
        return []

    raw_chunks = recursive_split(
        text,
        SEPARATORS,
        max_tokens,
    )

    chunks_with_overlap = add_overlap(
        raw_chunks,
        overlap_tokens,
    )

    chunks = []

    for index, chunk in enumerate(
        chunks_with_overlap
    ):
        token_estimate = estimate_tokens(
            chunk["text"]
        )

        if token_estimate < min_chunk_tokens:
            continue

        chunks.append(
            {
                "text": chunk["text"],
                "index": index,
                "tokenEstimate": token_estimate,
                "metadata": {
                    "startChar": chunk["startChar"],
                    "endChar": chunk["endChar"],
                },
            }
        )

    return chunks
