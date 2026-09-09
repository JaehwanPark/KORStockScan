from copy import deepcopy

import pytest

from src.trading.order.adaptive_exit.source import record_first_fill_observation

FIELD = "adaptive_exit_first_fill_observation"


def observe(record, old, new, second):
    record_first_fill_observation(
        record,
        previous_filled_qty=old,
        filled_qty=new,
        observed_at=f"2026-09-09T09:00:{second:02d}+09:00",
    )


def test_first_clock_is_immutable_across_partial_fill_and_recovery():
    record = {}
    observe(record, 0, 0, 0)
    observe(record, 0, 3, 2)
    persisted = deepcopy(record)
    observe(persisted, 3, 10, 8)
    assert persisted[FIELD]["first_observed_at"].endswith("02+09:00")
    assert persisted[FIELD]["last_zero_observed_at"].endswith("00+09:00")
    assert persisted[FIELD]["timestamp_provenance"] == (
        "broker_reconciliation_observation_not_exchange_fill_time"
    )


def test_existing_filled_inventory_never_gets_a_new_first_clock():
    record = {}
    observe(record, 3, 10, 8)
    observe(record, 10, 10, 9)
    assert record[FIELD]["first_observed_at"] is None
    assert record[FIELD]["status"] == "legacy_first_fill_unavailable"


@pytest.mark.parametrize(
    "old,new,ts",
    [
        (True, 2, "2026-09-09T09:00:01+09:00"),
        (2, 1, "2026-09-09T09:00:01+09:00"),
        (0, 1, "2026-09-09T09:00:01"),
        (0, 1, "invalid"),
    ],
)
def test_invalid_observation_is_not_repaired_by_a_later_fill(old, new, ts):
    record = {}
    record_first_fill_observation(
        record, previous_filled_qty=old, filled_qty=new, observed_at=ts
    )
    observe(record, 0, 1, 9)
    assert record[FIELD]["status"] == "observation_contract_invalid"
    assert record[FIELD]["first_observed_at"] is None


def test_backward_clock_keeps_original_and_marks_gap():
    record = {}
    observe(record, 0, 1, 2)
    observe(record, 1, 2, 1)
    assert record[FIELD]["first_observed_at"].endswith("02+09:00")
    assert record[FIELD]["status"] == "observation_contract_invalid"


def test_corrupt_original_metadata_is_preserved():
    record = {FIELD: "corrupt"}
    observe(record, 0, 1, 2)
    assert record[FIELD] == "corrupt"


def test_clock_regression_after_later_partial_fill_is_not_hidden_by_first_time():
    record = {}
    observe(record, 0, 1, 2)
    observe(record, 1, 3, 8)
    observe(record, 3, 4, 7)
    assert record[FIELD]["status"] == "observation_contract_invalid"
    assert record[FIELD]["first_observed_at"].endswith("02+09:00")
