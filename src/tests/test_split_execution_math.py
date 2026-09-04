from __future__ import annotations

from src.trading.order.split_execution_math import split_qty, split_qty_by_weights


def test_split_qty_conserves_quantity_and_clips_leg_count() -> None:
    assert split_qty(10, 2, 0.4) == [4, 6]
    assert split_qty(2, 3, 0.5) == [1, 1]
    assert split_qty(1, 3, 0.5) == [1]


def test_weighted_split_is_deterministic_and_quantity_preserving() -> None:
    assert split_qty_by_weights(20, 3, [0.5, 0.25, 0.25]) == [10, 5, 5]
    result = split_qty_by_weights(11, 3, [1, 1, 1])
    assert result == [4, 4, 3]
    assert sum(result) == 11
