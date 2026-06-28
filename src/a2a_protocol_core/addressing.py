"""
FAS-1 ``pay:`` URI addressing.

The single source of truth for the ``pay:`` address grammar used across the
A2A protocol surface. Kept dependency-free (stdlib only) so it can be imported
anywhere — validators, schemas, clients.
"""

from __future__ import annotations

import re

# pay:<label>(.<label>)*  — labels are lowercase alphanumeric + hyphen,
# 1..63 chars, no leading hyphen. Total length capped at 128.
PAY_URI_PATTERN = re.compile(r"^pay:[a-z0-9][a-z0-9\-]{0,62}(\.[a-z0-9][a-z0-9\-]{0,62})*$")

MAX_PAY_URI_LENGTH = 128


def is_valid_pay_uri(value: str) -> bool:
    """Return True if ``value`` is a syntactically valid ``pay:`` URI."""
    return bool(PAY_URI_PATTERN.match(value)) and len(value) <= MAX_PAY_URI_LENGTH


def assert_valid_pay_uri(value: str) -> str:
    """Return ``value`` if valid, else raise ``ValueError``."""
    if not is_valid_pay_uri(value):
        raise ValueError(f"Invalid pay: URI format: {value}")
    return value
