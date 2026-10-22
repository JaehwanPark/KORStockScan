"""Bounded official account cost observations, owned by postclose lifecycle.

No order, custody, threshold or position mutation. Broker day totals are never
allocated to individual fills. A separate reconciler must prove full coverage.
Reference: Kiwoom-Securities/Kiwoom-REST-API 953e5dbff123f437ab4d11a78a95191a685eb51f.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import uuid

from .broker_cost_reconciliation import KST, digest

SCHEMA = "holding_official_broker_cost_source_v1"
MAX_BYTES = 4 * 1024 * 1024
MAX_PAGES = 4
REFERENCE = "953e5dbff123f437ab4d11a78a95191a685eb51f"
PENDING_SCHEMA = "holding_broker_cost_pending_v1"
MAX_PENDING_DATES = 512
MAX_PENDING_RECORDS = 10000
DEFAULT_DRAIN_DATES = 2
DRAIN_BUDGET_SEC = 150
LISTS = {"ka10170": "tdy_trde_diary", "ka10076": "cntr",
         "kt00015_buy": "trst_ovrl_trde_prps_array",
         "kt00015_sell": "trst_ovrl_trde_prps_array"}


def number(value, *, signed=False) -> Decimal:
    if isinstance(value, bool) or not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", str(value).strip()):
        raise ValueError("broker_cost_numeric_missing_or_invalid")
    try:
        result = Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise ValueError("broker_cost_numeric_invalid") from exc
    if not result.is_finite() or abs(result) > Decimal("1e16") or (not signed and result < 0):
        raise ValueError("broker_cost_numeric_range_invalid")
    return result


def symbol(value):
    text = str(value or "")
    if re.fullmatch(r"[AJQ]\d{6}", text):
        text = text[1:]
    if not re.fullmatch(r"\d{6}", text):
        raise ValueError("broker_cost_symbol_invalid")
    return text


def source_path(data_root, target_date):
    if date.fromisoformat(target_date).isoformat() != target_date:
        raise ValueError("broker_cost_date_invalid")
    return Path(data_root) / "runtime/holding_broker_cost_sources" / (target_date + ".json")


def atomic(path, value):
    encoded = (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n").encode()
    if len(encoded) > MAX_BYTES:
        raise ValueError("broker_cost_source_size_limit")
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("broker_cost_output_symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".cost-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(encoded)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def validate(value, target_date):
    if (not isinstance(value, dict) or value.get("schema") != SCHEMA
            or value.get("source_date") != target_date or value.get("environment") != "real"
            or value.get("source_sha256") != digest({k: v for k, v in value.items() if k != "source_sha256"})
            or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("broker_account_sha256", "")))
            or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("local_account_key_sha256", "")))):
        raise ValueError("broker_cost_source_contract_invalid")
    observed = datetime.fromisoformat(value["observed_at"])
    if observed.tzinfo is None or observed.astimezone(KST).date().isoformat() < target_date:
        raise ValueError("broker_cost_source_clock_invalid")
    for key, observation in value["observations"].items():
        if key not in LISTS or not isinstance(observation, dict) or observation.get("complete") is not True:
            raise ValueError("broker_cost_source_page_contract_invalid")
        request = observation.get("request") or {}
        expected_api = "kt00015" if key.startswith("kt00015_") else key
        if observation.get("api_id") != expected_api:
            raise ValueError("broker_cost_api_identity_invalid")
        if key == "ka10170" and (request.get("base_dt") != target_date.replace("-", "")
                or request.get("ottks_tp") != "2" or request.get("ch_crd_tp") != "0"):
            raise ValueError("broker_cost_diary_request_scope_invalid")
        if key == "ka10076" and request != {"stk_cd": "", "qry_tp": "0", "sell_tp": "0",
                                           "ord_no": "", "stex_tp": "0"}:
            raise ValueError("broker_cost_order_request_scope_invalid")
        if key.startswith("kt00015_") and (request.get("strt_dt") != target_date.replace("-", "")
                or request.get("tp") != ("4" if key.endswith("buy") else "5")
                or request.get("gds_tp") != "1" or request.get("crnc_cd") != "KRW"
                or request.get("stk_cd") != "" or request.get("dmst_stex_tp") != "%"):
            raise ValueError("broker_cost_settlement_request_scope_invalid")
        if key.startswith("kt00015_"):
            end = datetime.strptime(request["end_dt"], "%Y%m%d").date()
            start = date.fromisoformat(target_date)
            if not start <= end <= min(start + timedelta(days=10), observed.astimezone(KST).date()):
                raise ValueError("broker_cost_settlement_date_window_invalid")
        pages = observation.get("pages")
        if not isinstance(pages, list) or not 1 <= len(pages) <= MAX_PAGES:
            raise ValueError("broker_cost_source_pages_missing")
        for page in pages:
            if (not isinstance(page, dict) or str(page.get("return_code")) != "0"
                    or not isinstance(page.get(LISTS[key]), list)):
                raise ValueError("broker_cost_source_response_invalid")
        at = datetime.fromisoformat(observation["observed_at"])
        if at.tzinfo is None or at > observed:
            raise ValueError("broker_cost_observation_clock_invalid")
        if key == "ka10076" and at.astimezone(KST).date().isoformat() != target_date:
            raise ValueError("broker_order_cost_date_unproven")
    return value


def _source_raw(path, *, account_read=None):
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("broker_cost_source_path_or_size_invalid")
    descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(descriptor,'rb') as stream:
        before=os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size>MAX_BYTES:
            raise ValueError('broker_cost_source_path_or_size_invalid')
        if account_read is not None:account_read(before.st_size)
        raw=stream.read(MAX_BYTES+1);finished=os.fstat(stream.fileno())
    signature=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    if (len(raw)!=before.st_size or len(raw)>MAX_BYTES or signature(before)!=signature(finished)
            or signature(before)!=signature(path.lstat())):
        raise ValueError("broker_cost_source_size_limit")
    return raw


def load_source(data_root, target_date):
    path = source_path(Path(data_root).resolve(), target_date)
    if not path.exists():return None
    return validate(json.loads(_source_raw(path)), target_date)


def _declared_window_unchanged(original, current):
    """A wider settlement window may add later rows, never revise old facts."""
    from collections import Counter
    omitted={'source_sha256','observed_at','observations'}
    if ({k:v for k,v in original.items() if k not in omitted}
            !={k:v for k,v in current.items() if k not in omitted}
            or set(original['observations'])!=set(current['observations'])
            or datetime.fromisoformat(current['observed_at'])<datetime.fromisoformat(original['observed_at'])):
        return False
    for key,old in original['observations'].items():
        new=current['observations'][key]
        if ({k:v for k,v in old.items() if k not in {'observed_at','request','pages'}}
                !={k:v for k,v in new.items() if k not in {'observed_at','request','pages'}}
                or datetime.fromisoformat(new['observed_at'])<datetime.fromisoformat(old['observed_at'])):
            return False
        if not key.startswith('kt00015_'):
            if old['request']!=new['request'] or old['pages']!=new['pages']:return False
            continue
        old_request=old['request'];new_request=new['request']
        if ({k:v for k,v in old_request.items() if k!='end_dt'}
                !={k:v for k,v in new_request.items() if k!='end_dt'}
                or new_request['end_dt']<old_request['end_dt']):return False
        rows_name=LISTS[key]
        headers=lambda obs:{digest({k:v for k,v in page.items() if k not in {rows_name,'return_msg'}}) for page in obs['pages']}
        if headers(old)!=headers(new):return False
        old_rows=Counter(digest(row) for page in old['pages'] for row in page[rows_name])
        new_rows=[row for page in new['pages'] for row in page[rows_name]]
        counts=Counter(digest(row) for row in new_rows)
        if old_rows-counts:return False
        remaining=old_rows.copy()
        for row in new_rows:
            sha=digest(row)
            if remaining[sha]:remaining[sha]-=1;continue
            day=row.get('trde_dt')
            if not isinstance(day,str) or not re.fullmatch(r'\d{8}',day):return False
            datetime.strptime(day,'%Y%m%d')
            execution_day=row.get('cntr_dt')
            if not isinstance(execution_day,str) or not re.fullmatch(r'\d{8}',execution_day):return False
            datetime.strptime(execution_day,'%Y%m%d')
            if (not old_request['end_dt']<day<=new_request['end_dt']
                    or not original['source_date'].replace('-','')<execution_day<=day):return False
    return True


def declared_source_bytes(data_root, reference, *, account_read=None):
    """Consume an exact native historical generation after a proven extension.

    Live generation discovery still reads the current alias. Original-window
    correction, account/provider drift, missing bytes and unknown data fail.
    """
    path=source_path(Path(data_root).resolve(),reference['source_date'])
    raw=_source_raw(path,account_read=account_read)
    if hashlib.sha256(raw).hexdigest()==reference.get('sha256'):return raw
    logical=reference.get('source_sha256')
    if (not re.fullmatch('[0-9a-f]{64}',str(logical))
            or not re.fullmatch('[0-9a-f]{64}',str(reference.get('sha256')))):
        raise ValueError('broker_cost_declared_generation_invalid')
    current=validate(json.loads(raw),reference['source_date'])
    archive=path.parent/'generations'/reference['source_date']/(logical+'.json')
    try:original_raw=_source_raw(archive,account_read=account_read)
    except FileNotFoundError:raise ValueError('broker_cost_declared_generation_missing') from None
    original=validate(json.loads(original_raw),reference['source_date'])
    if (original['source_sha256']!=logical
            or hashlib.sha256(original_raw).hexdigest()!=reference['sha256']
            or not _declared_window_unchanged(original,current)
            or _source_raw(path,account_read=account_read)!=raw):
        raise ValueError('broker_cost_declared_window_changed')
    return original_raw


def _archive_source(data_root, target_date, previous):
    """Retain the original alias bytes before a later observation replaces it."""
    if previous is None:
        return
    path = source_path(Path(data_root).resolve(), target_date)
    raw=_source_raw(path)
    if validate(json.loads(raw), target_date) != previous:
        raise ValueError("broker_cost_source_changed_before_archive")
    directory = path.parent / "generations" / target_date
    if directory.is_symlink() or directory.parent.is_symlink():
        raise ValueError("broker_cost_history_path_invalid")
    directory.mkdir(parents=True, exist_ok=True)
    archived = directory / (previous["source_sha256"] + ".json")
    if archived.is_symlink():
        raise ValueError("broker_cost_history_path_invalid")
    fd, temporary = tempfile.mkstemp(prefix=".generation-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, archived)
        except FileExistsError:
            # An incomplete or foreign generation must never replace evidence.
            if archived.is_symlink():
                raise ValueError("broker_cost_history_path_invalid")
            with archived.open("rb") as handle:
                if handle.read(MAX_BYTES + 1) != raw:
                    raise ValueError("broker_cost_history_collision")
    finally:
        Path(temporary).unlink(missing_ok=True)


def _pending_path(data_root):
    return Path(data_root) / "runtime/holding_broker_cost_pending/state.json"


@contextmanager
def _pending_lock(data_root, name="state", *, blocking=True):
    path = _pending_path(data_root).with_name(name + ".lock")
    if any(p.is_symlink() for p in (path, path.parent, path.parent.parent)):
        raise ValueError("broker_cost_pending_path_invalid")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _pending_load(data_root):
    path = _pending_path(data_root)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("broker_cost_pending_path_invalid")
    if not path.exists():
        return {"schema": PENDING_SCHEMA, "dates": {}}
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("broker_cost_pending_size_limit")
    value = json.loads(raw)
    if (not isinstance(value, dict) or value.get("schema") != PENDING_SCHEMA
            or value.get("queue_sha256") != digest({k: v for k, v in value.items() if k != "queue_sha256"})
            or not isinstance(value.get("dates"), dict) or len(value["dates"]) > MAX_PENDING_DATES):
        raise ValueError("broker_cost_pending_contract_invalid")
    count = 0
    for source_date, entry in value["dates"].items():
        source_path(data_root, source_date)
        if not isinstance(entry, dict) or not isinstance(entry.get("records"), dict):
            raise ValueError("broker_cost_pending_record_invalid")
        for key in ("last_attempt_day",):
            if key in entry:
                source_path(data_root, entry[key])
        if "last_attempt_at" in entry:
            _clock(datetime.fromisoformat(entry["last_attempt_at"]))
        for key, record in entry["records"].items():
            if not isinstance(record, dict):
                raise ValueError("broker_cost_pending_record_invalid")
            completion = record.get("completion_date", "")
            source_path(data_root, completion)
            record_id = record.get("record_id", "")
            if (not isinstance(record_id, str) or not record_id.isdigit() or int(record_id) <= 0
                    or key != completion + ":" + record_id or source_date > completion
                    or record.get("status") not in {"pending", "resolved", "expired"}
                    or not isinstance(record.get("reasons"), list)
                    or isinstance(record.get("revision"), bool)
                    or not isinstance(record.get("revision"), int) or record["revision"] < 1):
                raise ValueError("broker_cost_pending_record_invalid")
            _reasons(record["reasons"])
        count += len(entry["records"])
    if count > MAX_PENDING_RECORDS:
        raise ValueError("broker_cost_pending_population_limit")
    return value


def _pending_save(data_root, value):
    if (len(value["dates"]) > MAX_PENDING_DATES
            or sum(len(v["records"]) for v in value["dates"].values()) > MAX_PENDING_RECORDS):
        raise ValueError("broker_cost_pending_population_limit")
    value["queue_sha256"] = digest({k: v for k, v in value.items() if k != "queue_sha256"})
    atomic(_pending_path(data_root), value)
    return value


def _clock(now):
    value = now or datetime.now(KST)
    if value.tzinfo is None:
        raise ValueError("broker_cost_clock_timezone_missing")
    return value.astimezone(KST)


def _reasons(values):
    if isinstance(values, dict):
        values = [reason for value in values.values()
                  for reason in (value if isinstance(value, (list, tuple, set)) else [value])]
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, (list, tuple, set)) or not values or len(values) > 32 or any(
            not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", v) for v in values):
        raise ValueError("broker_cost_pending_reasons_invalid")
    return sorted(set(values))


def enqueue_pending(data_root, completion_date, required_dates, record_ids, reasons, *, now=None):
    """Persist unresolved consumer records; this function never uses transport.

    An explicit new unresolved observation reopens a resolved record revision.
    Expired rows remain visible and are not automatically retried.
    """
    source_path(data_root, completion_date)
    dates = sorted(set(required_dates))
    ids = sorted({str(v) for v in record_ids})
    reasons = _reasons(reasons)
    if (not dates or not ids or len(dates) > MAX_PENDING_DATES
            or len(ids) > MAX_PENDING_RECORDS
            or any(not v.isdigit() or int(v) <= 0 for v in ids)):
        raise ValueError("broker_cost_pending_request_invalid")
    for day in dates:
        source_path(data_root, day)
        if day > completion_date:
            raise ValueError("broker_cost_pending_source_after_completion")
    at = _clock(now).isoformat()
    with _pending_lock(data_root):
        queue = _pending_load(data_root)
        changed = False
        for day in dates:
            entry = queue["dates"].setdefault(day, {"records": {}})
            for record_id in ids:
                key = completion_date + ":" + record_id
                old = entry["records"].get(key)
                if old is None:
                    entry["records"][key] = {"completion_date": completion_date,
                        "record_id": record_id, "reasons": reasons, "status": "pending",
                        "revision": 1, "enqueued_at": at}
                    changed = True
                else:
                    merged = sorted(set(old["reasons"]) | set(reasons))
                    _reasons(merged)
                    if old["status"] == "resolved":
                        old.update(status="pending", revision=old["revision"] + 1, enqueued_at=at)
                        changed = True
                    if merged != old["reasons"]:
                        old["reasons"] = merged
                        changed = True
        return _pending_save(data_root, queue) if changed else queue


def resolve_pending(data_root, completion_date, record_ids,
                    reason="consumer_cost_reconciled", *, now=None):
    """Acknowledge only records whose consumer has verified a persisted receipt."""
    source_path(data_root, completion_date)
    ids = {str(v) for v in record_ids}
    if any(not v.isdigit() or int(v) <= 0 for v in ids):
        raise ValueError("broker_cost_pending_record_invalid")
    _reasons(reason)
    at = _clock(now).isoformat()
    with _pending_lock(data_root):
        queue = _pending_load(data_root)
        changed = False
        for entry in queue["dates"].values():
            for record in entry["records"].values():
                if (record["completion_date"] == completion_date and record["record_id"] in ids
                        and record["status"] != "resolved"):
                    record.update(status="resolved", resolved_at=at, resolution_reason=reason)
                    changed = True
        return _pending_save(data_root, queue) if changed else queue


def _budget(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("broker_cost_collection_budget_exhausted")


def drain_pending(data_root, target_date, *, transport=None, now=None,
                  max_dates=DEFAULT_DRAIN_DATES, budget_seconds=DRAIN_BUDGET_SEC):
    """Collect TARGET then at most one prior date, inside the existing job budget.

    Date claims are durable before transport, including interrupted attempts.
    A successful source observation never acknowledges individual record costs.
    """
    source_path(data_root, target_date)
    clock = _clock(now)
    today = clock.date()
    if target_date > today.isoformat():
        raise ValueError("broker_cost_date_outside_supported_window")
    if (isinstance(max_dates, bool) or not isinstance(max_dates, int)
            or not 1 <= max_dates <= DEFAULT_DRAIN_DATES
            or isinstance(budget_seconds, bool) or not 0 < budget_seconds <= DRAIN_BUDGET_SEC):
        raise ValueError("broker_cost_pending_budget_invalid")
    result = {"schema": "holding_broker_cost_pending_drain_v1", "source_date": target_date,
              "started_at": clock.isoformat(), "observed_at": clock.isoformat(),
              "status": "observed", "attempts": [],
              "expired_dates": [], "authority": "source_only_no_order_or_position_mutation"}
    deadline = time.monotonic() + budget_seconds
    with _pending_lock(data_root, "drain", blocking=False) as acquired:
        if not acquired:
            return {**result, "status": "drain_in_progress"}
        with _pending_lock(data_root):
            queue = _pending_load(data_root)
            for day, entry in queue["dates"].items():
                if day < "2026-09-29" or (today - date.fromisoformat(day)).days > 60:
                    changed = False
                    for record in entry["records"].values():
                        if record["status"] == "pending":
                            record.update(status="expired", expired_at=clock.isoformat(),
                                expiry_reason="broker_cost_date_outside_supported_window",
                                next_action="retain_unknown_require_external_verified_cost_source")
                            changed = True
                    if changed:
                        result["expired_dates"].append(day)
            queue["dates"].setdefault(target_date, {"records": {}})
            due = sorted((day for day, entry in queue["dates"].items()
                          if day < target_date and any(r["status"] == "pending" for r in entry["records"].values())
                          and entry.get("last_attempt_day") != today.isoformat()),
                         key=lambda day: (queue["dates"][day].get("last_attempt_day", ""), day))
            _pending_save(data_root, queue)
        for day in [target_date, *due[:max_dates - 1]]:
            if _clock(now).date() != today:
                result["status"] = "calendar_boundary_deferred"
                break
            if time.monotonic() >= deadline:
                result["status"] = "budget_deferred"
                break
            with _pending_lock(data_root):
                queue = _pending_load(data_root)
                entry = queue["dates"][day]
                # A final same-day source may supersede an early observation;
                # historical source dates still have exactly one daily claim.
                early = entry.get("last_attempt_at", "")
                final_same_day = (day == today.isoformat() and early
                    and datetime.fromisoformat(early).hour < 20 <= clock.hour)
                if entry.get("last_attempt_day") == today.isoformat() and not final_same_day:
                    result["attempts"].append({"source_date": day, "status": "already_attempted_today",
                        "last_collection_status": entry.get("last_collection_status"),
                        "source_sha256": entry.get("last_source_sha256"),
                        "last_attempt_id": entry.get("last_attempt_id"),
                        "last_attempt_receipt_sha256": entry.get("last_attempt_receipt_sha256")})
                    if entry.get("last_collection_status") != "observed":
                        result["status"] = "source_gap"
                    continue
                if day != target_date and not any(r["status"] == "pending" for r in entry["records"].values()):
                    continue
                attempt_id = clock.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex
                entry.update(last_attempt_day=today.isoformat(), last_attempt_at=clock.isoformat(),
                             last_attempt_id=attempt_id, last_collection_status="attempt_started")
                _pending_save(data_root, queue)
            attempt = {"source_date": day, "attempt_id": attempt_id, "started_at": clock.isoformat(),
                       "previous_source_sha256": None, "source_sha256": None}
            try:
                previous = load_source(data_root, day)
                attempt["previous_source_sha256"] = previous["source_sha256"] if previous else None
                source = collect(data_root, day, transport=transport, now=now, deadline=deadline)
                attempt.update(status="observed", source_sha256=source["source_sha256"],
                    source_changed=attempt["previous_source_sha256"] != source["source_sha256"],
                    source_observed_at=source["observed_at"],
                    rows={name: len(rows(source, name)) for name in source["observations"]})
            except (ValueError, OSError, TypeError, KeyError, TimeoutError) as exc:
                attempt.update(status="source_gap", reason=str(exc), actual_cost=None)
                result["status"] = "source_gap"
            attempt["observed_at"] = _clock(now).isoformat()
            attempt["receipt_sha256"] = digest(attempt)
            atomic(_pending_path(data_root).parent / "attempts" / day / (attempt_id + ".json"), attempt)
            with _pending_lock(data_root):
                queue = _pending_load(data_root)
                queue["dates"][day].update(last_collection_status=attempt["status"],
                    last_source_sha256=attempt["source_sha256"], last_attempt_receipt_sha256=attempt["receipt_sha256"])
                _pending_save(data_root, queue)
            result["attempts"].append(attempt)
        with _pending_lock(data_root):
            queue = _pending_load(data_root)
            result["queue_sha256"] = queue.get("queue_sha256")
            result["pending_dates"] = sorted(day for day, entry in queue["dates"].items()
                if any(r["status"] == "pending" for r in entry["records"].values()))
        result["observed_at"] = _clock(now).isoformat()
        result["receipt_sha256"] = digest(result)
        return result


def rows(source, name):
    return [row for page in source.get("observations", {}).get(name, {}).get("pages", [])
            for row in page[LISTS[name]]]


def reconcile_position(source, *, target_date, record_id, stock_code, buy_legs,
                       sell_legs, custody_rows, peer_records, knowledge_cutoff=None):
    """Use an entire proven position's broker total, never invented fill costs.

    Restricted to one fully closed intraday position owning all broker activity
    for that symbol/day. Mixed custody and ambiguous allocations stay unknown.
    """
    missing = {"status": "cost_source_unavailable", "actual_fees_taxes_krw": None,
               "exact_pnl_krw": None, "exact_profit_rate": None,
               "reason": "official_cost_source_unavailable"}
    if source is None:
        return missing
    try:
        validate(source, target_date)
        at = datetime.fromisoformat(source["observed_at"])
        if knowledge_cutoff is not None and at.timestamp() > knowledge_cutoff:
            return {**missing, "status": "actual_cost_pending", "reason": "cost_after_knowledge_cutoff"}
        if {str(x) for x in peer_records} != {str(record_id)}:
            raise ValueError("broker_day_symbol_position_not_unique")
        owners = [r for r in custody_rows if str(r.get("record_id")) == str(record_id)]
        if (not owners or any(r.get("source_quality_reasons") or r.get("state") not in {"full", "partial_terminal"}
                or r.get("owner_type") != "main_scalping" or r.get("owner_id") != "main_scalping:" + str(record_id)
                or digest(["broker_account", r.get("account_key")]) != source["local_account_key_sha256"]
                for r in owners)):
            raise ValueError("broker_cost_main_custody_unproven")
        totals = {}
        for side, legs in (("BUY", buy_legs), ("SELL", sell_legs)):
            if not legs or any(str(x.get("at", ""))[:10] != target_date for x in legs):
                raise ValueError("broker_cost_intraday_full_position_required")
            if any(x.get("route") not in {"KRX", "NXT", "SOR"} for x in legs):
                raise ValueError("broker_cost_route_unproven")
            for leg in legs:
                stamp = datetime.fromisoformat(leg["at"])
                stamp = stamp.replace(tzinfo=KST) if stamp.tzinfo is None else stamp
                if (stamp > at or not leg.get("order_no") or not leg.get("execution_no")
                        or number(leg["qty"]) <= 0 or number(leg["price"]) <= 0):
                    raise ValueError("broker_cost_execution_identity_or_clock_invalid")
            if len({(x.get("order_no"), x.get("execution_no")) for x in legs}) != len(legs):
                raise ValueError("broker_cost_duplicate_execution")
            qty = sum(number(x["qty"]) for x in legs)
            amount = sum(number(x["qty"]) * number(x["price"]) for x in legs)
            if qty <= 0 or amount <= 0:
                raise ValueError("broker_cost_execution_amount_invalid")
            totals[side] = (qty, amount)
        if totals["BUY"][0] != totals["SELL"][0]:
            raise ValueError("broker_cost_position_not_flat")
        # The official transaction number is not an order/execution number.
        # Only the full symbol/day set is matched to this sole Main position.
        settled = []
        transaction_ids = set()
        for key, side in (("kt00015_buy", "BUY"), ("kt00015_sell", "SELL")):
            matching = [r for r in rows(source, key) if symbol(r.get("stk_cd")) == stock_code]
            request = source.get("observations", {}).get(key, {}).get("request", {})
            if any(not re.fullmatch(r"\d{8}", str(r.get("cntr_dt", "")))
                   or not request.get("strt_dt", "") <= str(r.get("trde_dt", "")) <= request.get("end_dt", "")
                   for r in matching):
                raise ValueError("broker_cost_transaction_date_unproven")
            selected = [r for r in matching if r["cntr_dt"] == target_date.replace("-", "")]
            if not selected:
                break
            ids = [str(r.get("trde_dt")) + ":" + str(r.get("trde_no")) for r in selected]
            if (len(ids) != len(set(ids)) or transaction_ids.intersection(ids)
                    or any(not re.fullmatch(r"\d{9}", str(r.get("trde_no", "")))
                    or r.get("crnc_cd") != "KRW"
                    or r.get("io_tp_nm") != ("매수" if side == "BUY" else "매도") for r in selected)):
                raise ValueError("broker_cost_transaction_identity_invalid")
            transaction_ids.update(ids)
            observed = (sum(number(r["trde_qty_jwa_cnt"]) for r in selected),
                        sum(number(r["trde_amt"]) for r in selected))
            if observed != totals[side]:
                raise ValueError("broker_cost_settlement_activity_mismatch")
            for row in selected:
                cost = sum(number(row[k]) for k in ("cmsn", "trde_agri_tax", "incm_resi_tax"))
                if number(row["int_ls_usfe"]) != 0:
                    raise ValueError("broker_cost_credit_interest_requires_separate_reconciliation")
                amount, settlement = number(row["trde_amt"]), number(row["exct_amt"])
                if settlement != amount + (cost if side == "BUY" else -cost):
                    raise ValueError("broker_cost_settlement_cash_mismatch")
                if row.get("tax_sum_cmsn") not in (None, "") and number(row["tax_sum_cmsn"]) != cost:
                    raise ValueError("broker_cost_settlement_total_mismatch")
                settled.append(cost)
        else:
            return _position_result(sum(settled), totals, source, "broker_settled_whole_position")
        # Same-day order coverage protects against extra/manual activity that
        # a realized-only daily journal would otherwise omit.
        orders = [r for r in rows(source, "ka10076") if symbol(r.get("stk_cd")) == stock_code]
        expected = {}
        for side, legs in (("BUY", buy_legs), ("SELL", sell_legs)):
            for leg in legs:
                key = (side, str(leg["order_no"]).lstrip("0") or "0")
                q, a = expected.get(key, (Decimal(0), Decimal(0)))
                expected[key] = (q + number(leg["qty"]), a + number(leg["qty"]) * number(leg["price"]))
        actual = {}
        for row in orders:
            side = {"+매수": "BUY", "매수": "BUY", "-매도": "SELL", "매도": "SELL"}.get(row.get("io_tp_nm"))
            key = (side, str(row.get("ord_no", "")).lstrip("0") or "0")
            if key in actual or number(row["oso_qty"]) != 0 or row.get("ord_stt") != "체결":
                raise ValueError("broker_cost_order_coverage_ambiguous")
            actual[key] = (number(row["cntr_qty"]), number(row["cntr_qty"]) * number(row["cntr_pric"]))
        if not expected or actual != expected:
            raise ValueError("broker_cost_whole_position_order_coverage_missing")
        diary = [r for r in rows(source, "ka10170") if symbol(r.get("stk_cd")) == stock_code]
        if len(diary) != 1:
            raise ValueError("broker_cost_diary_scope_ambiguous")
        row = diary[0]
        if ((number(row["buy_qty"]), number(row["buy_amt"])) != totals["BUY"]
                or (number(row["sell_qty"]), number(row["sell_amt"])) != totals["SELL"]):
            raise ValueError("broker_cost_diary_activity_mismatch")
        cost = number(row["cmsn_alm_tax"])
        if number(row["pl_amt"], signed=True) != totals["SELL"][1] - totals["BUY"][1] - cost:
            raise ValueError("broker_cost_diary_pnl_mismatch")
        return _position_result(cost, totals, source, "broker_day_symbol_whole_position")
    except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
        return {**missing, "status": "actual_cost_unallocated", "reason": str(exc),
                "source_sha256": source.get("source_sha256") if isinstance(source, dict) else None}


def _position_result(cost, totals, source, basis):
    pnl = totals["SELL"][1] - totals["BUY"][1] - cost
    result = {"status": "actual_cost_reconciled", "actual_fees_taxes_krw": float(cost),
              "exact_pnl_krw": float(pnl), "exact_profit_rate": float(pnl / totals["BUY"][1] * 100),
              "cost_available_at": source["observed_at"], "reconciled_at": source["observed_at"],
              "source_sha256": source["source_sha256"], "allocation_scope": basis,
              "reason": None}
    result["receipt_sha256"] = digest(result)
    return result


def _check_pages(pages, meta, key):
    if (not isinstance(meta, dict) or not isinstance(pages, list) or not pages
            or meta.get("page_count") != len(pages) or len(pages) > MAX_PAGES
            or meta.get("continuous_terminal_received") is not True
            or any(meta.get(k) for k in ("continuous_next_key_missing", "continuous_page_limit_reached",
                                         "rate_limit_retry_exhausted", "request_failed"))):
        raise ValueError("broker_cost_incomplete_pagination:" + key)
    for page in pages:
        if (not isinstance(page, dict) or str(page.get("return_code")) != "0"
                or (key in LISTS and not isinstance(page.get(LISTS[key]), list))):
            raise ValueError("broker_cost_response_failed:" + key)
    if len(json.dumps(pages).encode()) > MAX_BYTES // 2:
        raise ValueError("broker_cost_response_size_limit")


def collect(data_root, target_date, *, transport=None, now=None, refresh=False, deadline=None):
    """One account/day request set; unchanged retries use the verified receipt."""
    fixed_clock = now
    now = now or datetime.now(KST)
    if now.tzinfo is None:
        raise ValueError("broker_cost_clock_timezone_missing")
    day = date.fromisoformat(target_date)
    today = now.astimezone(KST).date()
    if not date(2026, 9, 29) <= day <= today or (today - day).days > 60:
        raise ValueError("broker_cost_date_outside_supported_window")
    _budget(deadline)
    path = source_path(data_root, target_date)
    if path.parent.is_symlink() or path.with_suffix(".lock").is_symlink():
        raise ValueError("broker_cost_source_path_invalid")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        previous = load_source(data_root, target_date)
        config = None
        if transport is None:
            from src.utils import kiwoom_utils as K
            from src.trading.order.owner_custody_registry import broker_account_key
            config_path = K.CONFIG_PATH if K.CONFIG_PATH.exists() else K.DEV_PATH
            config = json.loads(config_path.read_text())
            if (not config.get("KIWOOM_APPKEY")
                    or K.get_api_url("/api/dostk/acnt") != "https://api.kiwoom.com/api/dostk/acnt"
                    or config.get("KIWOOM_BASE_URL", K.KIWOOM_BASE_URL) != "https://api.kiwoom.com"):
                raise ValueError("broker_cost_real_provider_identity_required")
            provider_sha = K._token_cache_key(config)
            local_key = broker_account_key()
        else:
            local_key = getattr(transport, "account_key", "test_account")
            provider_sha = digest(["test_provider", getattr(transport, "provider_key", "test")])
        alias_sha = digest(["broker_account", local_key])
        if previous and (previous["local_account_key_sha256"] != alias_sha
                or previous.get("provider_config_sha256", provider_sha) != provider_sha):
            raise ValueError("broker_cost_account_or_provider_changed")
        if (previous and not refresh and datetime.fromisoformat(previous["observed_at"]).astimezone(KST).date() == today
                and previous.get("provider_config_sha256") == provider_sha
                and (day < today or datetime.fromisoformat(previous["observed_at"]).astimezone(KST).hour >= 20)):
            return previous
        if transport is None:
            _budget(deadline)
            token = K.get_kiwoom_token(config=config)
            if not token:
                raise ValueError("broker_cost_token_unavailable")
            def transport(api, payload):
                return K.fetch_kiwoom_api_continuous(
                    url=K.get_api_url("/api/dostk/acnt"), token=token, api_id=api,
                    payload=payload, use_continuous=True, max_pages=MAX_PAGES,
                    max_retries=2, return_meta=True, request_owner="holding_broker_cost_postclose",
                    request_class=K.REQUEST_CLASS_SOURCE_ONLY, read_rate_max_wait_sec=3,
                    request_timeout=(5, 15))
        _budget(deadline)
        account, meta = transport("ka00001", {})
        _budget(deadline)
        _check_pages(account, meta, "ka00001")
        if len(account) != 1 or not re.fullmatch(r"\d{10}", str(account[0].get("acctNo", ""))):
            raise ValueError("broker_cost_account_identity_invalid")
        account_sha = digest(["kiwoom_real_account", account[0]["acctNo"]])
        if previous and (previous["broker_account_sha256"] != account_sha
                         or previous["local_account_key_sha256"] != alias_sha):
            raise ValueError("broker_cost_account_changed")
        end = min(today, day + timedelta(days=10)).strftime("%Y%m%d")
        requests = [("ka10170", "ka10170", {"base_dt": day.strftime("%Y%m%d"),
                     "ottks_tp": "2", "ch_crd_tp": "0"})]
        for side, kind in (("buy", "4"), ("sell", "5")):
            requests.append(("kt00015_" + side, "kt00015", {
                "strt_dt": day.strftime("%Y%m%d"), "end_dt": end, "tp": kind,
                "stk_cd": "", "crnc_cd": "KRW", "gds_tp": "1", "frgn_stex_code": "",
                "dmst_stex_tp": "%", "qry_sort_tp": "2"}))
        if day == today:
            requests.append(("ka10076", "ka10076", {"stk_cd": "", "qry_tp": "0",
                "sell_tp": "0", "ord_no": "", "stex_tp": "0"}))
        observations = {}
        if previous and "ka10076" in previous["observations"] and day != today:
            observations["ka10076"] = previous["observations"]["ka10076"]
        for key, api, payload in requests:
            _budget(deadline)
            pages, meta = transport(api, payload)
            _budget(deadline)
            _check_pages(pages, meta, key)
            observed_at = fixed_clock or datetime.now(KST)
            observations[key] = {"api_id": api, "request": payload, "pages": pages,
                                 "complete": True, "observed_at": observed_at.isoformat()}
        finished = fixed_clock or datetime.now(KST)
        if finished.astimezone(KST).date() != today:
            raise ValueError("broker_cost_collection_crossed_date")
        value = {"schema": SCHEMA, "source_date": target_date, "observed_at": finished.isoformat(),
                 "environment": "real", "official_reference_commit": REFERENCE,
                 "provider_config_sha256": provider_sha,
                 "broker_account_sha256": account_sha, "local_account_key_sha256": alias_sha,
                 "observations": observations, "authority": "source_only_no_order_or_position_mutation"}
        value["source_sha256"] = digest(value)
        validate(value, target_date)
        _archive_source(data_root, target_date, previous)
        atomic(path, value)
        return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--drain-pending", action="store_true")
    args = parser.parse_args(argv)
    if args.drain_pending and args.refresh:
        parser.error("--refresh cannot bypass the pending daily retry budget")
    from src.utils.constants import DATA_DIR
    try:
        if args.drain_pending:
            result = drain_pending(DATA_DIR, args.date)
            code = 0 if result["status"] == "observed" else 2
        else:
            source = collect(DATA_DIR, args.date, refresh=args.refresh)
            result = {"status": "observed", "source_date": args.date,
                          "source_sha256": source["source_sha256"],
                          "rows": {name: len(rows(source, name)) for name in source["observations"]}}
            code = 0
    except (ValueError, OSError, TypeError, KeyError) as exc:
        result = {"status": "source_gap", "source_date": args.date,
                  "reason": str(exc), "actual_cost": None}
        code = 2
    # Validate the date before constructing a report path even after failure.
    source_path(DATA_DIR, args.date)
    atomic(Path(DATA_DIR) / "report/holding_broker_cost_source" / (args.date + ".json"), result)
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
