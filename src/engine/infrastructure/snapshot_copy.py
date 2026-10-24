"""Isolated copies of normalized runtime containers, without atomic deepcopy overhead.

Ownership: infrastructure copy primitive, not a quote parser or projection.
Unknown objects retain their own deepcopy protocol and cycles/aliases are kept.
"""
import copy
from collections import deque
from dataclasses import dataclass
from collections.abc import Mapping as _Mapping
from types import MappingProxyType as _MappingProxyType

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


def snapshot_without_fields(value, fields):
    """Clone a root mapping except discarded fields, retaining root aliases.

    This has the same ownership as deepcopy followed by root pop. It avoids
    traversing data which the caller already discards, without projecting
    nested operating inputs or replacing unknown objects' copy protocol.
    """
    if type(value) is not dict:
        result = copy.deepcopy(value)
        for key in fields:
            result.pop(key, None)
        return result
    result = {}
    memo = {id(value): result}
    for key, item in value.items():
        if key not in fields:
            result[snapshot_copy(key, memo)] = snapshot_copy(item, memo)
    return result


class FrozenMapping(_Mapping):
    """Owned recursive snapshot; foreign read-only views remain untrusted."""
    __slots__ = ('_values', '_shareable')

    def __init__(self, values):
        children = {str(key): _freeze_owned(item) for key, item in values.items()}
        object.__setattr__(self, '_values', _MappingProxyType(
            {key: item for key, (item, _) in children.items()}))
        object.__setattr__(self, '_shareable', all(owned for _, owned in children.values()))

    def __setattr__(self, name, value):
        raise TypeError('immutable_async_snapshot')

    def __delattr__(self, name):
        raise TypeError('immutable_async_snapshot')

    def __getitem__(self, key):
        return self._values[key]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)


def _freeze_owned(value):
    if type(value) in (str, int, float, bool, bytes, complex, type(None)):
        return value, True
    if type(value) is FrozenMapping and value._shareable:
        return value, True
    if isinstance(value, _Mapping):
        frozen = FrozenMapping(value)
        return frozen, frozen._shareable
    if isinstance(value, (list, tuple, set, frozenset)):
        children = [_freeze_owned(item) for item in value]
        items = (item for item, _ in children)
        frozen = frozenset(items) if isinstance(value, (set, frozenset)) else tuple(items)
        return frozen, all(owned for _, owned in children)
    # A copied custom object can still be mutable. Copy it again at each
    # ownership boundary; it must never mark its parent safe for sharing.
    return copy.deepcopy(value), False


def immutable_mapping(value):
    """Freeze once, then share only owned recursively immutable snapshots."""
    return _freeze_owned(value if isinstance(value, _Mapping) else dict(value or {}))[0]
