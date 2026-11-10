"""Small boundary helpers: never turn missing sensors into plausible zeros."""

import math
from typing import Any


def number(value: Any, maximum: float | None = None) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(result) or result < 0 or (maximum is not None and result > maximum):
        return None
    return result


def ratio(used: float | int | None, total: float | int | None) -> float | None:
    if used is None or total is None or total <= 0:
        return None
    return number(used / total * 100, 100)


def text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[:256]
    return str(value)[:256]
