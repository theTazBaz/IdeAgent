"""
pipeline/llm.py
===============
One place for every Groq chat call, with retries and friendly errors.

    text = llm.chat(prompt, temperature=0.1)

Transient failures (rate limits, timeouts, connection drops, 5xx) are retried
with backoff, honouring the server's Retry-After. Anything else — or running
out of attempts — raises LLMError with a message that is safe to show a user
and an HTTP status the API can return.
"""
from __future__ import annotations

import os
import random
import re
import time

import groq
from groq import Groq

from pipeline import config

MAX_ATTEMPTS = 4          # total tries per call
MAX_WAIT_S = 30.0         # never sleep longer than this between tries
REQUEST_TIMEOUT_S = 60.0

_client: Groq | None = None


class LLMError(Exception):
    """A Groq failure with a user-presentable message and an HTTP status."""

    def __init__(self, user_message: str, status_code: int = 502, retry_after: float | None = None):
        super().__init__(user_message)
        self.user_message = user_message
        self.status_code = status_code
        self.retry_after = retry_after


def get_client() -> Groq:
    """Shared Groq client. Retries are handled here, so the SDK's own are off."""
    global _client
    if _client is None:
        key = os.environ.get("GROQ_API_KEY") or config.GROQ_API_KEY
        if not key:
            raise LLMError("The server has no GROQ_API_KEY configured.", status_code=500)
        _client = Groq(api_key=key, max_retries=0, timeout=REQUEST_TIMEOUT_S)
    return _client


def _retry_after(exc: Exception) -> float | None:
    """Seconds the server asked us to wait, from the Retry-After header."""
    resp = getattr(exc, "response", None)
    value = resp.headers.get("retry-after") if resp is not None else None
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def _backoff(attempt: int, server_hint: float | None) -> float:
    """Wait before retry number `attempt` (1-based)."""
    if server_hint is not None:
        return server_hint + random.uniform(0, 0.5)
    return min(MAX_WAIT_S, 2 ** attempt) + random.uniform(0, 0.5)


def chat(prompt: str, *, temperature: float = 0.1, client: Groq | None = None) -> str:
    """Send one user prompt and return the reply text with any <think> block removed."""
    client = client or get_client()
    last: LLMError | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            text = resp.choices[0].message.content or ""
            return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()

        # ---- not worth retrying ----------------------------------------
        except groq.AuthenticationError:
            raise LLMError("The Groq API key was rejected. Check GROQ_API_KEY on the server.", 500)
        except groq.PermissionDeniedError:
            raise LLMError("The Groq API key is not allowed to use this model.", 500)
        except groq.NotFoundError:
            raise LLMError(f"The model {config.LLM_MODEL!r} is not available on Groq. Update LLM_MODEL in config.py.", 500)
        except groq.BadRequestError as exc:
            raise LLMError(f"Groq rejected the request: {str(exc)[:200]}", 502)

        # ---- transient: retry ------------------------------------------
        except groq.RateLimitError as exc:
            hint = _retry_after(exc)
            last = LLMError("The AI service is rate-limited right now. Please try again in a moment.", 429, hint)
            if hint is not None and hint > MAX_WAIT_S:
                raise last  # waiting that long inside a request is pointless
        except (groq.APITimeoutError, groq.APIConnectionError):
            hint = None
            last = LLMError("Could not reach the AI service (timed out). Please try again.", 504)
        except groq.InternalServerError as exc:
            hint = _retry_after(exc)
            last = LLMError("The AI service had an internal error. Please try again.", 502, hint)
        except groq.APIStatusError as exc:   # any other HTTP status
            raise LLMError(f"Unexpected response from the AI service (HTTP {exc.status_code}).", 502)

        if attempt == MAX_ATTEMPTS:
            break
        wait = _backoff(attempt, hint)
        print(f"       ⏳ Groq: {last.user_message} Retrying in {wait:.1f}s (attempt {attempt}/{MAX_ATTEMPTS}) …")
        time.sleep(wait)

    raise last  # type: ignore[misc]
