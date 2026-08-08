"""Observation/research-only micro-reversion namespace.

Keep this package initializer free of eager imports.  In particular, a future
market-data producer must be able to import ``observation_adapter`` without
loading detector, journal, replay, AI, broker, or order dependencies.

Consumers import the concrete owner module directly.  Nothing in this package
is connected to a trading-decision consumer by default.
"""

__all__: tuple[str, ...] = ()
