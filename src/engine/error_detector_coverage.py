"""Compatibility wrapper for :mod:`src.engine.monitoring.error_detector_coverage`."""

from __future__ import annotations

from src.engine.monitoring import error_detector_coverage as _impl

for _name in dir(_impl):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_impl, _name)
