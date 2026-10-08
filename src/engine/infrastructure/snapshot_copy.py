"""Isolated copies of normalized runtime containers, without atomic deepcopy overhead.

Ownership: infrastructure copy primitive, not a quote parser or projection.
Unknown objects retain their own deepcopy protocol and cycles/aliases are kept.
"""
import copy
from collections import deque

_ATOMIC = frozenset((str, int, float, bool, bytes, type(None)))


def snapshot_copy(value, memo=None):
    kind = type(value)
    if kind in _ATOMIC:
        return value
    if memo is None:
        memo = {}
    ident = id(value)
    if ident in memo:
        return memo[ident]
    if kind is dict:
        result = value.copy()
        memo[ident] = result
        for key, item in value.items():
            # Normalized field names are strings. Nonstandard keys use the
            # complete deepcopy protocol, including key isolation.
            if type(key) not in _ATOMIC:
                del result[key]
                result[snapshot_copy(key, memo)] = snapshot_copy(item, memo)
            elif type(item) not in _ATOMIC:
                result[key] = snapshot_copy(item, memo)
        return result
    if kind is list or kind is deque:
        result = [] if kind is list else deque(maxlen=value.maxlen)
        memo[ident] = result
        result.extend(item if type(item) in _ATOMIC else snapshot_copy(item, memo)
                      for item in value)
        return result
    return copy.deepcopy(value, memo)
