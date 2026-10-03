"""Pure offline identity and chronological validation for entry calibration.

Owned by scalping postclose producers; this module has no runtime/order calls.
"""

from datetime import datetime, timedelta, timezone
from collections import defaultdict
from collections.abc import Sequence
import json
import tempfile

KST = timezone(timedelta(hours=9))
NEW_LOGIC_SOURCE_DATE = "2026-10-02"
OPPORTUNITY_IDENTITY_VERSION = "native_scanner_or_fixed_watch_v2"


class FrozenRows(Sequence):
    """Disk-backed compact rows; keep one source partition in memory at a time."""

    def __init__(self):
        self._file = tempfile.TemporaryFile(mode="w+b")
        self._offsets = []

    def append(self, row):
        self._file.seek(0, 2)
        self._offsets.append(self._file.tell())
        self._file.write(json.dumps(row, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode() + b"\n")

    def __len__(self):
        return len(self._offsets)

    def extend(self, rows):
        for row in rows:
            self.append(row)

    def __eq__(self, other):
        if not isinstance(other, Sequence):
            return NotImplemented
        return len(self) == len(other) and all(left == right for left, right in zip(self, other))

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        self._file.seek(self._offsets[index])
        return json.loads(self._file.readline())

    def __del__(self):
        self._file.close()


def source_identifier(value):
    """Keep native string identities; null spellings are never provenance."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    return (value if value.lower() not in {
        "", "-", "none", "null", "nan", "n/a", "unknown", "undefined",
    } else None)


def source_identifiers(value):
    values = value if isinstance(value, (list, tuple, set)) else [value]
    return sorted({identity for item in values if (identity := source_identifier(item))})


def opportunity_identity(row):
    values = tuple(source_identifier(row.get(key)) for key in (
        "source_date", "stock_code", "effective_venue", "session_bucket",
    ))
    if row.get("watch_origin") == "MAIN_FIXED_WATCH":
        lineage = tuple(source_identifier(row.get(key)) for key in (
            "watch_origin", "watch_admission_id", "watch_generation_id",
        ))
    else:
        lineage = (source_identifier(row.get("scanner_promotion_id")),)
    if any(value is None for value in (*values, *lineage)):
        raise ValueError("opportunity_lineage_missing")
    if datetime.fromisoformat(values[0]).date().isoformat() != values[0]:
        raise ValueError("opportunity_date_invalid")
    return (*values, *lineage)


def decision_time(row):
    value = datetime.fromisoformat(row["decision_ts"])
    if value.tzinfo is None or value.astimezone(KST).date().isoformat() != row["source_date"]:
        raise ValueError("decision_clock_invalid")
    return value


def observation_end(row):
    # Fixed ten-minute CF is the current owner. Explicit larger windows are
    # respected; a shorter claim cannot shorten the registered observation.
    end = decision_time(row) + timedelta(minutes=10)
    for path in (row.get("entry_quality_path") or {}, row.get("ai_stage_path") or {}):
        stamp = path.get("window_end") or path.get("observation_end")
        if stamp:
            parsed = datetime.fromisoformat(stamp)
            if parsed.tzinfo is None:
                raise ValueError("observation_clock_invalid")
            end = max(end, parsed)
    return end


def chronological_split(rows, *, training_through_date=None):
    """Split identities before labels, then purge overlapping observation windows."""
    groups, excluded = defaultdict(list), []
    seen, conflicted = {}, set()
    for row in rows:
        trace = row.get("decision_trace_id") or row.get("evaluation_key")
        try:
            identity = opportunity_identity(row)
            decision_time(row)
            observation_end(row)
            if not isinstance(trace, str) or not trace:
                raise ValueError("attempt_identity_missing")
        except (ValueError, TypeError, KeyError) as exc:
            excluded.append({"attempt_id": trace, "reason": str(exc)})
            continue
        if trace in seen:
            if row != seen[trace][1]:
                conflicted.add(trace)
            continue
        seen[trace] = (identity, row)
    for trace, (identity, row) in seen.items():
        if trace in conflicted:
            excluded.append({"attempt_id": trace, "reason": "attempt_identity_conflict"})
        else:
            groups[identity].append(row)
    dates = sorted({key[0] for key in groups})
    if not dates:
        return [], [], {"version": "chronological_opportunity_purge_v1", "exclusions": excluded}
    if training_through_date:
        train_ids = {key for key in groups if key[0] <= training_through_date}
        hold_ids = set(groups) - train_ids
        basis = "explicit_forward_boundary"
    elif len(dates) > 1:
        train_ids = {key for key in groups if key[0] < dates[-1]}
        hold_ids = set(groups) - train_ids
        basis = "last_source_date"
    else:
        ordered = sorted(groups, key=lambda key: (min(decision_time(r) for r in groups[key]), key))
        boundary = max(1, int(len(ordered) * .7))
        train_ids, hold_ids = set(ordered[:boundary]), set(ordered[boundary:])
        basis = "same_day_70_30_opportunities"
    hold_start = min((decision_time(r) for key in hold_ids for r in groups[key]), default=None)
    purged = {key for key in train_ids if hold_start is not None
              and max(observation_end(r) for r in groups[key]) >= hold_start}
    train_ids -= purged
    train = sorted((r for key in train_ids for r in groups[key]), key=lambda r: (decision_time(r), str(r.get("decision_trace_id") or r.get("evaluation_key"))))
    held = sorted((r for key in hold_ids for r in groups[key]), key=lambda r: (decision_time(r), str(r.get("decision_trace_id") or r.get("evaluation_key"))))
    manifest = {"version": "chronological_opportunity_purge_v1", "basis": basis,
                "train_opportunity_ids": [list(key) for key in sorted(train_ids)],
                "holdout_opportunity_ids": [list(key) for key in sorted(hold_ids)],
                "purged_opportunity_ids": [list(key) for key in sorted(purged)],
                "train_observation_end": max((observation_end(r) for r in train), default=None).isoformat() if train else None,
                "holdout_start": hold_start.isoformat() if hold_start else None,
                "exclusions": excluded}
    return train, held, manifest


def split_manifest_valid(manifest, train_ids, held_ids):
    try:
        end = datetime.fromisoformat(manifest["train_observation_end"])
        start = datetime.fromisoformat(manifest["holdout_start"])
        return (manifest.get("version") == "chronological_opportunity_purge_v1"
                and end.tzinfo is not None and start.tzinfo is not None and end < start
                and not set(train_ids) & set(held_ids))
    except (ValueError, TypeError, KeyError):
        return False
