"""Tests for the bounded-retry helper used by every idempotent HTTP leg."""

from __future__ import annotations

import pytest
import requests

from a2a_protocol_core import _retry
from a2a_protocol_core._retry import get_with_retries


class _Resp:
    def __init__(self, status_code):
        self.status_code = status_code


class _Session:
    def __init__(self, outcomes):
        # each outcome: an int status, or an Exception instance to raise
        self._outcomes = list(outcomes)
        self.calls = 0

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls += 1
        out = self._outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return _Resp(out)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    slept = []
    monkeypatch.setattr(_retry.time, "sleep", slept.append)
    return slept


def test_success_first_try():
    http = _Session([200])
    assert get_with_retries(http, "u", timeout=1).status_code == 200
    assert http.calls == 1


def test_retries_transient_status_then_succeeds(_no_sleep):
    http = _Session([503, 502, 200])
    assert get_with_retries(http, "u", timeout=1).status_code == 200
    assert http.calls == 3
    assert _no_sleep == [0.5, 1.0]  # exponential, deterministic, no jitter


def test_retries_connection_error_then_succeeds():
    http = _Session([requests.ConnectionError("reset"), 402])
    assert get_with_retries(http, "u", timeout=1).status_code == 402
    assert http.calls == 2


def test_exhausted_retries_returns_last_response():
    http = _Session([503, 503, 503])
    assert get_with_retries(http, "u", timeout=1, retries=2).status_code == 503
    assert http.calls == 3  # bounded: retries + 1 attempts, then the answer stands


def test_exhausted_retries_raises_last_connection_error():
    http = _Session([requests.ConnectionError("a"), requests.Timeout("b"), requests.ConnectionError("c")])
    with pytest.raises(requests.ConnectionError):
        get_with_retries(http, "u", timeout=1, retries=2)
    assert http.calls == 3


@pytest.mark.parametrize("status", [400, 401, 402, 404, 422, 500])
def test_real_answers_are_not_retried(status):
    http = _Session([status])
    assert get_with_retries(http, "u", timeout=1).status_code == status
    assert http.calls == 1
