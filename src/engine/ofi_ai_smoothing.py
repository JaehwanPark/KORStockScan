"""Compatibility wrapper for :mod:`src.engine.lifecycle.ofi_ai_smoothing`."""

from __future__ import annotations

from src.engine.lifecycle import ofi_ai_smoothing as _impl

for _name in dir(_impl):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_impl, _name)
