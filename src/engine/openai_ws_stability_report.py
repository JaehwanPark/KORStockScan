"""Compatibility wrapper for :mod:`src.engine.ai.openai_ws_stability_report`."""

from __future__ import annotations

import sys
import types

from src.engine.ai import openai_ws_stability_report as _impl


# Keep wrappers mutable for test monkeypatches that set `DATA_DIR` on this legacy path.
_DATA_DIR = _impl.DATA_DIR


class _OpenAIWsCompatibilityModule(types.ModuleType):
    def __getattr__(self, name: str):
        if name == "DATA_DIR":
            return _impl.DATA_DIR
        try:
            return getattr(_impl, name)
        except AttributeError as exc:  # pragma: no cover
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value):
        if name == "DATA_DIR":
            _impl.DATA_DIR = value
        super().__setattr__(name, value)

    def __dir__(self):
        return sorted(set(super().__dir__() + list(vars(_impl).keys())))


sys.modules[__name__].__class__ = _OpenAIWsCompatibilityModule
# Keep `DATA_DIR` defined so monkeypatch sees and edits the expected symbol.
DATA_DIR = _DATA_DIR

# Preserve a legacy-compat import surface with explicit named exports.
for _name in dir(_impl):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_impl, _name)

if __name__ == "__main__":
    raise SystemExit(_impl.main())
