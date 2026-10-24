"""Pure numeric conversion shared by Main and its state/scale-in consumers."""

import math


def safe_float(value, default=0.0):
    """Return a finite float, or the caller's unchanged default on invalid input."""
    try:
        if value is None:
            return default
        if isinstance(value, str) and value.strip().lower() in {
            "",
            "nan",
            "nat",
            "none",
            "inf",
            "+inf",
            "-inf",
        }:
            return default
        numeric = float(value)
        if not math.isfinite(numeric):
            return default
        return numeric
    except Exception:
        return default
