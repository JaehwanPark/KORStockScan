"""Compatibility wrapper for :mod:`src.engine.swing.ml_predictor`."""

from __future__ import annotations

from src.engine.swing import ml_predictor as _impl

for _name in dir(_impl):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_impl, _name)
