"""Operator-directed live execution for source-qualified widget signals."""

__all__ = ["EXECUTION_AUTHORITY", "WidgetSignalAutoTrader"]


def __getattr__(name: str):
    # Diagnostic submodules must not initialize the live engine or its broker
    # configuration just to inspect an observation receipt. Preserve exports.
    if name in __all__:
        from src.trading.widget_auto_trade import engine

        return getattr(engine, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
