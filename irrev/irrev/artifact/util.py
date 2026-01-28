"""
Small utilities for the artifact subsystem.

This module intentionally avoids third-party dependencies.
"""

from __future__ import annotations

import os
import time


_CROCKFORD32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode_crockford_base32(value: int, length: int) -> str:
    chars: list[str] = []
    for _ in range(length):
        chars.append(_CROCKFORD32[value & 31])
        value >>= 5
    return "".join(reversed(chars))


def new_ulid(*, timestamp_ms: int | None = None) -> str:
    """
    Generate a ULID (26 chars, Crockford base32).

    ULID = 48-bit millisecond timestamp + 80-bit randomness.
    """
    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)

    if not (0 <= timestamp_ms < (1 << 48)):
        raise ValueError("timestamp_ms out of range for ULID")

    randomness = int.from_bytes(os.urandom(10), "big")
    value = (timestamp_ms << 80) | randomness
    return _encode_crockford_base32(value, 26)

