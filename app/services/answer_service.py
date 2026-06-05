"""Answer service — grounded RAG answer generation using Groq LLM."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are SiteMind, a website intelligence analyst. You answer questions about a website using ONLY the evidence snippets provided below. Follow these rules:

1. Answer based strictly on the provided evidence. Do not use prior knowledge.
2. If the evidence does not contain enough information to answer, say "I cannot answer this question based on the available evidence."
3. Include citations in your answer by referencing the source URL in brackets like [source_url].
4. Every factual claim must be backed by a citation.
5. Be concise and specific.
6. Rate your confidence in the answer from 0.0 to 1.0.

Return your response as JSON with keys: "answer" (string), "confidence" (float 0-1), "citations" (list of strings with source URLs used)."""


async def generate_answer(
    session: AsyncSession,
    site_id: uuid.UUID,
    question: str,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate a grounded answer from evidence using Groq."""
    settings = get_settings()

    if not evidence:
        return {
            "answer": "I cannot answer this question based on the available evidence.",
            "confidence": 0.0,
            "citations": [],
        }

    evidence_text = "\n\n".join(
        [
            f"[Source: {e.get('source_url', 'unknown')} | Type: {e.get('artifact_type', 'unknown')}]\n{e.get('snippet', '')}"
            for i, e in enumerate(evidence)
        ]
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Question: {question}\n\nEvidence:\n{evidence_text}\n\nAnswer the question using ONLY the evidence above. Return JSON.",
        },
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 1024,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            result = json.loads(content)
        except Exception as exc:
            logger.warning("Answer generation failed: %s", exc)
            result = {
                "answer": "I could not generate an answer due to a processing error.",
                "confidence": 0.0,
                "citations": [],
            }

    return result


async def close_answer_client() -> None:
    pass
