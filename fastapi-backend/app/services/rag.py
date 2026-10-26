import os
import time

from app.services.chunking import estimate_tokens


from app.config.prompts import RAG_SYSTEM_PROMPT
from app.lib.http.openai_client import openai_post_with_retry
from app.utils.logger import logger


CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.1")


CONTEXT_TOKEN_BUDGET = 3500


def is_redundant(
    candidate: dict,
    selected: list[dict],
) -> bool:
    return any(
        chunk["documentId"] == candidate["documentId"]
        and abs(
            chunk["chunkIndex"]
            - candidate["chunkIndex"]
        ) <= 1
        for chunk in selected
    )


def assemble_context(
    search_results: list[dict],
) -> dict:
    selected = []
    total_tokens = 0

    for result in search_results:

        if is_redundant(
            result,
            selected,
        ):
            continue

        token_count = result.get(
            "tokenCount",
            estimate_tokens(result["content"]),
        )

        if (
            total_tokens + token_count
            > CONTEXT_TOKEN_BUDGET
        ):
            break

        selected.append(result)
        total_tokens += token_count

    citations = []

    for index, chunk in enumerate(
        selected,
        start=1,
    ):
        citations.append({
            "index": index,
            "chunkId": chunk["chunkId"],
            "documentId": chunk["documentId"],
            "documentTitle": chunk["documentTitle"],
            "chunkIndex": chunk["chunkIndex"],
            "score": chunk["score"],
        })

    context_parts = []

    for index, chunk in enumerate(
        selected,
        start=1,
    ):
        context_parts.append(
            f'[Source {index}: '
            f'"{chunk["documentTitle"]}", '
            f'Section {chunk["chunkIndex"] + 1}]\n'
            f'{chunk["content"]}'
        )

    context_text = "\n\n---\n\n".join(
        context_parts
    )

    return {
        "chunks": selected,
        "contextText": context_text,
        "totalTokens": total_tokens,
        "citations": citations,
    }


def generate_rag_response(
    question: str,
    context: dict,
    conversation_history: list[dict] | None = None,
    user_id: str | None = None,
    conversation_id: str | None = None,
    correlation_id: str | None = None,
) -> dict:

    messages = [
        {
            "role": "system",
            "content": RAG_SYSTEM_PROMPT,
        }
    ]

    if conversation_history:
        recent = conversation_history[-10:]
        messages.extend(recent)

    if context["chunks"]:
        user_content = "\n".join([
            "Here is the relevant context "
            "from my documents:",
            "",
            context["contextText"],
            "",
            "---",
            "",
            f"My question: {question}",
        ])
    else:
        user_content = "\n".join([
            "No relevant context was found "
            "in my documents for this question.",
            "",
            f"My question: {question}",
        ])

    messages.append({
        "role": "user",
        "content": user_content,
    })

    start_time = time.perf_counter()

    response = openai_post_with_retry(
        "/api/chat",
        {
            "model": CHAT_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 1500,
            },
        },
    )

    result = response.json()

    answer = result["message"]["content"]

    usage = result.get("usage") or {
        "prompt_tokens": result.get("prompt_eval_count", 0),
        "completion_tokens": result.get("eval_count", 0),
        "total_tokens": (
            result.get("prompt_eval_count", 0)
            + result.get("eval_count", 0)
        ),
    }

    prompt_tokens = usage.get(
        "prompt_tokens",
        0,
    )

    completion_tokens = usage.get(
        "completion_tokens",
        0,
    )

    total_tokens = usage.get(
        "total_tokens",
        prompt_tokens + completion_tokens,
    )

    cost_usd = 0.0

    duration = int(
        (time.perf_counter() - start_time) * 1000
    )

    logger.info(
        "RAG response generated | "
        "correlation_id=%s conversation_id=%s "
        "model=%s context_chunks=%s "
        "prompt_tokens=%s completion_tokens=%s "
        "cost_usd=%.6f duration_ms=%s",
        correlation_id,
        conversation_id,
        CHAT_MODEL,
        len(context["chunks"]),
        prompt_tokens,
        completion_tokens,
        cost_usd,
        duration,
    )

    return {
        "answer": answer,
        "citations": context["citations"],
        "tokensUsed": {
            "prompt": prompt_tokens,
            "completion": completion_tokens,
            "total": total_tokens,
        },
        "costUsd": cost_usd,
        "model": CHAT_MODEL,
    }
