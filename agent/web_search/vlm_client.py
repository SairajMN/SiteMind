"""Vision Language Model (VLM) client — uses free APIs from .env.

Supports: Groq (LLaVA), OpenRouter (various vision models), and Inception API.
Falls back through providers if one fails.
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# ── helpers ──────────────────────────────────────────────────────────

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _image_b64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def _build_messages(
    system_prompt: str,
    user_text: str,
    image_b64: str | None = None,
) -> list[dict[str, Any]]:
    """Build a chat message list, optionally including a base64 image."""
    content: list[dict[str, Any]] = []

    if system_prompt:
        content.append({"type": "text", "text": system_prompt})

    # Image first (if provided)
    if image_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
        })

    # User text
    content.append({"type": "text", "text": user_text})

    return [
        {"role": "user", "content": content},
    ]


# ── provider clients ─────────────────────────────────────────────────

async def _call_groq_vision(
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str | None:
    """Call Groq API with vision model (LLaVA / multimodal)."""
    api_key = _env("GROQ_API_KEY")
    if not api_key:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info("Groq vision (%s) succeeded", model)
            return content
    except Exception as exc:
        logger.warning("Groq vision (%s) failed: %s", model, exc)
        return None


async def _call_openrouter_vision(
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str | None:
    """Call OpenRouter API with vision model."""
    api_key = _env("OPENROUTER_API_KEY")
    if not api_key:
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://sitemind.app",
        "X-Title": "SiteMind",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info("OpenRouter vision (%s) succeeded", model)
            return content
    except Exception as exc:
        logger.warning("OpenRouter vision (%s) failed: %s", model, exc)
        return None


async def _call_inception_vision(
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str | None:
    """Call Inception API with vision model."""
    api_key = _env("INCEPTION_API_KEY")
    if not api_key:
        return None

    url = "https://api.inceptionlabs.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info("Inception vision (%s) succeeded", model)
            return content
    except Exception as exc:
        logger.warning("Inception vision (%s) failed: %s", model, exc)
        return None


# ── text-only LLM (for planning / formatting without vision) ─────────

async def _call_groq_text(
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str | None:
    """Call Groq with a text-only model."""
    api_key = _env("GROQ_API_KEY")
    if not api_key:
        return None
    # Strip images for text-only models
    clean_messages = []
    for msg in messages:
        if isinstance(msg.get("content"), list):
            texts = [c["text"] for c in msg["content"] if c.get("type") == "text"]
            clean_messages.append({"role": msg["role"], "content": "\n".join(texts)})
        else:
            clean_messages.append(msg)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": clean_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning("Groq text (%s) failed: %s", model, exc)
        return None


# ── public API ───────────────────────────────────────────────────────

# Free vision-capable models
VISION_MODELS = [
    # Groq vision models
    ("groq", "llama-3.2-11b-vision-preview"),
    # OpenRouter free vision models
    ("openrouter", "openai/gpt-4o-mini"),
]

# Text-only models for fallback / planning (all verified working on Groq)
TEXT_MODELS = [
    ("groq", "llama-3.1-8b-instant"),
    ("groq", "llama-3.3-70b-versatile"),
]


async def analyze_with_vlm(
    image_bytes: bytes | None,
    page_text: str,
    extraction_instructions: str,
) -> dict[str, Any]:
    """Analyze a screenshot + text using VLM. Extracts structured data.

    Returns dict with at least:
      { "extracted": [ { "name", "price", "rating", "specs", ... } ],
        "summary": "...",
        "source": "groq/llava-v1.5-7b-4096-preview" }
    """
    system_prompt = (
        "You are a web data extraction expert. "
        "Analyze the screenshot and page text to extract structured information. "
        "Return your answer as JSON with keys: 'extracted' (list of items found), "
        "'summary' (a brief summary of findings). "
        "Each item should have: name, price (if visible), rating (if visible), "
        "specs (key features), and source_url if available."
    )

    user_text = (
        f"Extraction instructions: {extraction_instructions}\n\n"
        f"Page text content:\n{page_text[:6000]}\n\n"
        "Extract the structured data as JSON."
    )

    image_b64 = _image_b64(image_bytes) if image_bytes else None
    messages = _build_messages(system_prompt, user_text, image_b64)

    last_error: str | None = None

    # Try vision models first
    for provider, model in VISION_MODELS:
        if not image_bytes and "vision" not in model and "vl" not in model:
            continue  # skip vision models when no image

        if provider == "groq":
            result = await _call_groq_vision(model, messages)
        elif provider == "openrouter":
            result = await _call_openrouter_vision(model, messages)
        elif provider == "inception":
            result = await _call_inception_vision(model, messages)
        else:
            continue

        if result:
            return _parse_vlm_result(result, f"{provider}/{model}")

        last_error = f"{provider}/{model} failed"

    # Fallback: try text-only models with just page text
    text_messages = [{"role": "user", "content": f"{system_prompt}\n\n{user_text}"}]
    for provider, model in TEXT_MODELS:
        if provider == "groq":
            result = await _call_groq_text(model, text_messages)
        else:
            continue

        if result:
            return _parse_vlm_result(result, f"{provider}/{model}")

        last_error = f"{provider}/{model} failed"

    logger.error("All VLM/text models failed. Last error: %s", last_error)
    return {
        "extracted": [],
        "summary": "Failed to analyze page content.",
        "source": "none",
        "error": last_error,
    }


async def analyze_text_with_llm(
    user_prompt: str,
    system_prompt: str | None = None,
) -> str | None:
    """Send a text-only prompt to available LLM for planning/formatting."""
    messages = _build_messages(system_prompt or "", user_prompt, None)

    for provider, model in TEXT_MODELS:
        if provider == "groq":
            result = await _call_groq_text(model, messages)
        else:
            continue
        if result:
            return result

    # Fallback to vision models in text mode
    for provider, model in VISION_MODELS:
        if provider == "groq":
            result = await _call_groq_vision(model, messages)
        elif provider == "openrouter":
            result = await _call_openrouter_vision(model, messages)
        elif provider == "inception":
            result = await _call_inception_vision(model, messages)
        else:
            continue
        if result:
            return result

    return None


def _parse_vlm_result(raw: str, source: str) -> dict[str, Any]:
    """Try to parse JSON from VLM response."""
    import re

    # Try to extract JSON block
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if json_match:
        raw = json_match.group(1)

    try:
        import json as j
        data = j.loads(raw)
        if isinstance(data, dict):
            data.setdefault("extracted", [])
            data.setdefault("summary", "")
            data["source"] = source
            return data
    except Exception:
        pass

    # Fallback: extract list items
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    items = []
    for line in lines:
        if line.startswith("- ") or line.startswith("* ") or line[0].isdigit():
            items.append({"name": line, "source": source})

    return {
        "extracted": items,
        "summary": raw[:500],
        "source": source,
        "raw": raw[:1000],
    }