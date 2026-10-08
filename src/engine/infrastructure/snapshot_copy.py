"""Isolated copies of normalized runtime containers, without atomic deepcopy overhead.

Ownership: infrastructure copy primitive, not a quote parser or projection.
Unknown objects retain their own deepcopy protocol and cycles/aliases are kept.
"""
import copy
from collections import deque
from dataclasses import dataclass

_ATOMIC = frozenset((str, int, float, bool, bytes, type(None)))


class FrozenSnapshotList(tuple):
    """Immutable owned row list, restored as a list for existing consumers."""

    def __deepcopy__(self, memo):
        return materialize_history(self)


@dataclass(frozen=True, slots=True)
class FrozenSnapshotDeque:
    """Preserve the full tape's container contract and original capacity."""
    rows: tuple
    maxlen: int | None

    def __deepcopy__(self, memo):
        return materialize_history(self)


class FrozenSnapshotDict(dict):
    """Ingress-owned immutable history row; consumers receive mutable copies."""
    def _immutable(self, *args, **kwargs):
        raise TypeError('immutable_snapshot_record')
    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _immutable

    def __deepcopy__(self, memo):
        return materialize_history(self)


def freeze_history(value):
    """Freeze under the owner lock; only already immutable records are shared."""
    kind = type(value)
    if kind in _ATOMIC or kind in (FrozenSnapshotDict, FrozenSnapshotList, FrozenSnapshotDeque):
        return value
    if kind is dict:
        return FrozenSnapshotDict({k: freeze_history(v) for k, v in value.items()})
    if kind is deque:
        return FrozenSnapshotDeque(tuple(freeze_history(v) for v in value), value.maxlen)
    if kind is list:
        return FrozenSnapshotList(freeze_history(v) for v in value)
    if kind is tuple:
        return tuple(freeze_history(v) for v in value)
    # Private copies of nonstandard objects are not shared with ingress.
    return copy.deepcopy(value)


def materialize_history(value):
    kind = type(value)
    if kind in _ATOMIC:
        return value
    if kind is FrozenSnapshotDict:
        return {k: materialize_history(v) for k, v in value.items()}
    if kind is FrozenSnapshotList:
        return [materialize_history(v) for v in value]
    if kind is FrozenSnapshotDeque:
        return deque((materialize_history(v) for v in value.rows), maxlen=value.maxlen)
    if kind is tuple:
        return tuple(materialize_history(v) for v in value)
    return copy.deepcopy(value)


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
