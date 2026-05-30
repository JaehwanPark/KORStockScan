"""Compatibility wrapper for :mod:`src.engine.monitoring.system_metric_sampler`."""

from __future__ import annotations

from src.engine.monitoring import system_metric_sampler as _impl

for _name in dir(_impl):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_impl, _name)

if __name__ == "__main__":
    raise SystemExit(main())
