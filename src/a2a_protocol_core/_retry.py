"""
Bounded, deterministic retry for idempotent HTTP legs.

Agent runtimes call these endpoints over flaky networks; a transient connection
reset or a 502 from a proxy should not fail a whole pay/screen flow. Retries
are DELIBERATELY narrow:

- GET only, and only legs that are idempotent by contract. The x402 settle leg
  qualifies: the server checks idempotency BEFORE verification, so re-sending
  the same settled tx proof returns the recorded outcome rather than
  double-settling.
- Connection errors / timeouts and 502/503/504 only. A 4xx or a 500 is a real
  answer and is returned/raised immediately — retrying it would just repeat it.
- Fixed attempt count, exponential backoff, no jitter — deterministic, like
  everything else in this package.
"""

from __future__ import annotations

import time
from typing import Optional

import requests

RETRYABLE_STATUS = frozenset({502, 503, 504})
DEFAULT_RETRIES = 2  # total attempts = retries + 1
DEFAULT_BACKOFF = 0.5  # seconds; doubles per attempt


def get_with_retries(
    session: requests.Session,
    url: str,
    *,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: int,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
) -> requests.Response:
    """GET with bounded retries on transient failures (see module docstring)."""
    attempt = 0
    while True:
        try:
            resp = session.get(url, params=params, headers=headers, timeout=timeout)
        except (requests.ConnectionError, requests.Timeout):
            if attempt >= retries:
                raise
            time.sleep(backoff * (2**attempt))
            attempt += 1
            continue
        if resp.status_code in RETRYABLE_STATUS and attempt < retries:
            time.sleep(backoff * (2**attempt))
            attempt += 1
            continue
        return resp
