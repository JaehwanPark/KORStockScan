"""Offline/shared adaptive exit primitives; no broker or activation authority."""

from .decision import evaluate_exit
from .reducer import reduce_event

__all__ = ["evaluate_exit", "reduce_event"]
