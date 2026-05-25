"""Compatibility wrapper for :mod:`src.engine.monitoring.server_report_comparison`."""

from __future__ import annotations

from src.engine.monitoring import server_report_comparison as _impl

for _name in dir(_impl):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_impl, _name)


if __name__ == "__main__":
    raise SystemExit(_impl.main())
