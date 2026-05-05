"""OpenAI-compatible LibreChat proxy with TRACE scoring.

This is a small hosted prototype, not a new SDK surface. LibreChat sends
OpenAI-style chat requests to this service. The service calls OpenRouter with
free-model defaults, scores the assistant answer with TRACE, and returns the
original chat response with `latence_trace` metadata attached.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request

from latence import AsyncLatence

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

app = FastAPI(title="Latence TRACE LibreChat Prototype")


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise HTTPException(status_code=500, detail=f"{name} is not configured")
    return value


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> dict[str, Any]:
    body = await request.json()
    messages = body.get("messages") or []
    body.setdefault(
        "model",
        os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
    )

    async with httpx.AsyncClient(timeout=60.0) as http:
        upstream = await http.post(
            OPENROUTER_URL,
            json=body,
            headers={
                "Authorization": f"Bearer {_required_env('OPENROUTER_API_KEY')}",
                "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "https://latence.ai"),
                "X-Title": os.environ.get("OPENROUTER_APP_NAME", "Latence TRACE Demo"),
            },
        )
    if upstream.status_code >= 400:
        raise HTTPException(status_code=upstream.status_code, detail=upstream.text)

    response = upstream.json()
    answer = _assistant_text(response)
    context = _context_from_messages(messages)
    query = _last_user_message(messages)

    if answer and context:
        async with AsyncLatence() as trace:
            score = await trace.grounding.rag(
                query=query,
                response_text=answer,
                raw_context=context,
            )
        response["latence_trace"] = score.model_dump(mode="json", exclude_none=True)

    return response


def _assistant_text(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    return content if isinstance(content, str) else ""


def _last_user_message(messages: list[dict[str, Any]]) -> str | None:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content")
            return content if isinstance(content, str) else None
    return None


def _context_from_messages(messages: list[dict[str, Any]]) -> list[str] | None:
    chunks = [
        content
        for message in messages
        if message.get("role") == "system"
        and isinstance((content := message.get("content")), str)
        and content
    ]
    return chunks or None

