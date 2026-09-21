"""Bounded AL completed-minute projection of successfully persisted stream rows.

No network, subscriptions, trading decisions, or missing-tick imputation. The
canonical journal remains authoritative; a projection failure cannot undo it.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
SCHEMA = "shared_ws_completed_bars_v1"
SESSION_OPEN = {"SOR_PREMARKET": "08:00", "SOR_REGULAR": "09:00", "SOR_AFTERMARKET": "16:00"}
SESSION_END = {"SOR_PREMARKET": "08:50", "SOR_REGULAR": "15:30", "SOR_AFTERMARKET": "20:00"}
METRIC_CONTRACT = {
    "metric_role": "source_quality_gate", "decision_authority": "market_data_only",
    "window_policy": "exact_item_session_epoch_completed_minutes",
    "sample_floor": "consumer_required_lookback", "primary_decision_metric": "complete_bars",
    "source_quality_gate": "durable_cursor_original_clocks_volume_continuity",
    "forbidden_uses": ["order_authority", "missing_tick_imputation", "quiet_reconnect", "profit_claim"],
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def item_integrity(integrity, item):
    result = dict(integrity)
    rejections = result.pop("item_rejections", {})
    result["item_rejection_count"] = rejections.get(item, 0)
    return result


def process_identity():
    pid = os.getpid()
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    return {"pid": pid, "start_ticks": int(fields[19]),
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip()}


def atomic_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".bars-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class CompletedBarProjection:
    """One existing canonical writer owns one session partition projection."""
    def __init__(self, root, *, max_bars=400, lateness_sec=1.0, symbols=None):
        self.symbols = None if symbols is None else frozenset(symbols)
        if self.symbols is not None and (not self.symbols or len(self.symbols) > 128 or any(not re.fullmatch(r"[0-9]{6}", c) for c in self.symbols)):
            raise ValueError("completed_bar_publish_scope_invalid")
        self.root = Path(root)
        self.max_bars = max_bars
        self.lateness_sec = lateness_sec
        self.series = {}
        self.errors = 0
        self.producer = process_identity()
        self._paths = set()

    def invalidate(self):
        self.series.clear()
        for path in self._paths:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass  # The live integrity receipt also carries projection_errors.

    def _restore(self, path, *, epoch, integrity, stamp):
        # A bounded checkpoint preserves sealed historical bars, never a
        # partially observed minute across restart. No full journal rescan.
        bars, revision = {}, 0
        try:
            with path.open("rb") as handle:
                raw = handle.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError("checkpoint_size")
            old = json.loads(raw)
            if not isinstance(old, dict):
                raise ValueError("checkpoint_shape")
            expected = old.pop("content_sha256")
            if (digest(old) != expected or old["schema"] != SCHEMA
                    or old["trade_date"] != path.parent.parent.name
                    or old["source_item"] != path.parent.name
                    or old["session"] != path.stem):
                raise ValueError("checkpoint_hash")
            for bar in old["bars"][-self.max_bars:]:
                if bar["status"] == "complete":
                    bars[bar["minute_epoch"]] = bar
            revision = old["revision"]
        except (OSError, ValueError, KeyError, TypeError):
            pass
        return {"epoch": epoch, "bars": bars, "last": None,
                "watermark": stamp, "integrity": integrity, "revision": revision}

    def _session_coverage(self, *, key, point, cumulative, qty, integrity, previous=None):
        """Prove the first print, without synthesizing quiet opening minutes.

        A zero-origin premarket print or the same producer's durable earlier
        session cursor can establish the cumulative-volume boundary. A new
        PID/epoch, loss, missing cursor or intervening volume cannot do so.
        """
        day, item, session = key
        if session not in SESSION_OPEN or qty <= 0:
            return None
        start = datetime.fromisoformat(day + "T" + SESSION_OPEN[session]).replace(tzinfo=KST).timestamp()
        prior_cumulative, prior_hash, prior_cursor, tail_receipt = 0, None, None, None
        if (previous is not None and previous.get("eligible") is True and previous["minute"] + 60 <= start
                and point.series_sequence == previous["sequence"] + 1
                and cumulative - previous["cumulative"] == qty):
            prior_cumulative, prior_hash = previous["cumulative"], previous["hash"]
            prior_cursor = dict(previous)
            basis = "same_generation_session_boundary_cumulative_continuity"
        elif session == "SOR_PREMARKET":
            if cumulative != qty:
                return None
            basis = "first_premarket_print_cumulative_equals_quantity"
        else:
            predecessor = {"SOR_REGULAR": "SOR_PREMARKET", "SOR_AFTERMARKET": "SOR_REGULAR"}[session]
            path = self.root / day / item / (predecessor + ".json")
            try:
                with path.open("rb") as handle:
                    raw = handle.read(2 * 1024 * 1024 + 1)
                if len(raw) > 2 * 1024 * 1024:
                    return None
                prior = json.loads(raw)
                if not isinstance(prior, dict):
                    return None
                prior_hash = prior.pop("content_sha256")
                cursor = prior["cursor"]
                if (digest(prior) != prior_hash or prior["schema"] != SCHEMA
                        or prior["trade_date"] != day or prior["source_item"] != item
                        or prior["session"] != predecessor or prior["producer"] != self.producer
                        or prior["source_epoch"] != point.sequence_epoch
                        or prior["integrity"] != integrity
                        or prior["source_commit"] != os.getenv("KORSTOCKSCAN_RUNTIME_GIT_COMMIT", "")
                        or cursor["minute"] + 60 > start
                        or cursor.get("eligible") is not True
                        or type(cursor["cumulative"]) is not int):
                    return None
                # The last partial minute need not have caused a publication.
                # Inspect only a bounded canonical tail, never a full-day scan.
                journal = Path(prior["journal_path"])
                if journal.exists():
                    end = journal.stat().st_size
                    offset = max(0, end - 2 * 1024 * 1024)
                    with journal.open("rb") as handle:
                        handle.seek(offset)
                        tail = handle.read(end - offset)
                    tail_receipt = {"path": str(journal), "start_byte": offset,
                                    "end_byte": end, "sha256": hashlib.sha256(tail).hexdigest()}
                    if offset:
                        tail = tail.split(b"\n", 1)[-1]
                    for line in tail.splitlines():
                        row = json.loads(line)
                        if not isinstance(row, dict):
                            return None
                        if row.get("source_item") != item or row.get("sequence_epoch") != point.sequence_epoch:
                            continue
                        if row["series_sequence"] <= cursor["sequence"]:
                            continue
                        event = datetime.fromisoformat(row["exchange_timestamp"])
                        receive = datetime.fromisoformat(row["local_receive_timestamp"])
                        raw_cumulative = row.get("cumulative_volume_raw")
                        if (row.get("session_bucket") != predecessor or row.get("venue") != "SOR"
                                or row.get("realtime_type") != "0B"
                                or event.tzinfo is None or receive.tzinfo is None
                                or event.astimezone(KST).date().isoformat() != day
                                or not event.timestamp() <= receive.timestamp() <= datetime.fromisoformat(point.local_receive_timestamp).timestamp()
                                or event.timestamp() >= start or row.get("path_consumer_eligible") is not True
                                or not isinstance(raw_cumulative, str) or not re.fullmatch(r"[+]?[0-9]+", raw_cumulative)):
                            return None
                        cursor = {"sequence": row["series_sequence"], "cumulative": int(raw_cumulative),
                                  "minute": int(event.timestamp()) // 60 * 60, "hash": digest(row), "eligible": True}
                if cumulative - cursor["cumulative"] != qty:
                    return None
                prior_cumulative = cursor["cumulative"]
                prior_cursor = dict(cursor)
                basis = "same_generation_prior_session_cumulative_continuity"
            except (OSError, ValueError, KeyError, TypeError):
                return None
        return {"start_epoch": int(start), "basis": basis,
                "source_epoch": point.sequence_epoch, "prior_content_sha256": prior_hash,
                "prior_cursor": prior_cursor, "prior_journal_tail": tail_receipt,
                "prior_cumulative": prior_cumulative, "first_cumulative": cumulative,
                "first_quantity": qty, "first_event": point.exchange_timestamp}

    def consume(self, points, *, integrity, journal_path, now_ts=None, durable_cursor=None):
        now_ts = time.time() if now_ts is None else now_ts
        source_integrity = json.loads(json.dumps(integrity))
        touched = set()
        for p in points:
            item = getattr(p, "source_item", "")
            if (not re.fullmatch(r"[0-9]{6}_AL", item) or p.venue != "SOR"
                    or getattr(p, "realtime_type", None) != "0B"):
                continue
            if self.symbols is not None and item[:6] not in self.symbols:
                continue
            integrity = item_integrity(source_integrity, item)
            stamp = datetime.fromisoformat(p.exchange_timestamp)
            if stamp.tzinfo is None or p.sequence_epoch != integrity["observer_epoch"]:
                continue
            stamp = stamp.astimezone(KST)
            received = datetime.fromisoformat(p.local_receive_timestamp).timestamp()
            if not math.isfinite(received) or not stamp.timestamp() <= received <= now_ts:
                continue
            key = (stamp.date().isoformat(), item, p.session_bucket)
            if p.session_bucket not in SESSION_OPEN:
                continue
            clock = stamp.strftime("%H:%M")
            in_session = SESSION_OPEN[p.session_bucket] <= clock < SESSION_END[p.session_bucket]
            minute = int(stamp.timestamp()) // 60 * 60
            state = self.series.get(key)
            if state is None:
                if len(self.series) >= 128:
                    raise ValueError("completed_bar_series_capacity")
                checkpoint = self.root / key[0] / item / (key[2] + ".json")
                state = self.series[key] = self._restore(checkpoint, epoch=p.sequence_epoch, integrity=integrity, stamp=stamp.timestamp())
            changed_epoch = state["epoch"] != p.sequence_epoch
            changed_integrity = state["integrity"] != integrity
            if changed_epoch or changed_integrity:
                state.pop("session_coverage", None)
                for bar in state["bars"].values():
                    if bar["status"] == "pending":
                        bar["status"] = "gap"
                        bar["issues"].append("source_generation_or_loss_changed")
                state.update(epoch=p.sequence_epoch, last=None, integrity=integrity)
            last = state["last"]
            issues = []
            if getattr(p, "path_consumer_eligible", True) is not True:
                issues.append("canonical_path_ineligible")
            try:
                if not isinstance(p.cumulative_volume_raw, str) or not re.fullmatch(r"[+]?[0-9]+", p.cumulative_volume_raw):
                    raise ValueError("cumulative_volume_missing")
                if not isinstance(p.trade_volume_raw, str) or not re.fullmatch(r"[+-]?[0-9]+", p.trade_volume_raw):
                    raise ValueError("print_volume_missing")
                cumulative, qty = int(p.cumulative_volume_raw), abs(int(p.trade_volume_raw))
                price = float(p.trade_price)
                if not math.isfinite(price) or price <= 0 or price != int(price) or qty != p.trade_qty:
                    raise ValueError("trade_fields_conflict")
                price = int(price)
            except (ValueError, TypeError, OverflowError):
                state["last"] = None
                state["invalid_from_minute"] = minute
                for bar in state["bars"].values():
                    if bar["status"] == "pending":
                        bar["status"] = "gap"
                        bar["issues"].append("trade_fields_invalid")
                touched.add(key)
                continue
            if in_session and (last is None or not state["bars"]):
                coverage = None
                if not state["bars"] and not issues and not state.get("invalid_from_minute"):
                    coverage = self._session_coverage(key=key, point=p, cumulative=cumulative,
                                                      qty=qty, integrity=integrity, previous=last)
                if coverage is None:
                    issues.append("startup_or_reconnect_partial_minute")
                else:
                    state["session_coverage"] = coverage
            if last is not None:
                if p.series_sequence <= last["sequence"]:
                    # Retries cannot add volume twice. Conflicting/reordered rows
                    # are conservative source gaps, never silently revised history.
                    if p.series_sequence == last["sequence"] and digest(p.as_dict()) == last["hash"]:
                        continue
                    issues.append("duplicate_or_reordered_sequence")
                if p.series_sequence != last["sequence"] + 1:
                    issues.append("sequence_gap")
                if cumulative - last["cumulative"] != qty:
                    issues.append("cumulative_print_gap")
                if stamp.timestamp() < state["watermark"] - self.lateness_sec:
                    issues.append("late_trade")
                if issues:
                    for prev in state["bars"].values():
                        if prev["minute_epoch"] >= last["minute"]:
                            prev["status"] = "gap"
                            prev["issues"] = sorted(set(prev["issues"] + issues))
            if in_session:
                bar = state["bars"].get(minute)
                if bar is None:
                    bar = state["bars"][minute] = {
                        "minute_epoch": minute, "source_time": datetime.fromtimestamp(minute, KST).strftime("%Y%m%d%H%M%S"),
                        "open": price, "high": price, "low": price, "close": price, "volume": 0,
                        "first_event": stamp.timestamp(), "last_event": stamp.timestamp(),
                        "first_sequence": p.series_sequence, "last_sequence": p.series_sequence,
                        "first_cumulative": cumulative, "last_cumulative": cumulative,
                        "status": "pending", "issues": [], "available_at_epoch": None,
                        "source_epoch": p.sequence_epoch, "source_item": item,
                        "producer": self.producer,
                        "source_commit": os.getenv("KORSTOCKSCAN_RUNTIME_GIT_COMMIT", ""),
                    }
                elif bar["status"] == "complete":
                    issues.append("late_revision_after_publication")
                bar["issues"] = sorted(set(bar["issues"] + issues))
                if bar["issues"]:
                    bar["status"] = "gap"
                if stamp.timestamp() < bar["first_event"]:
                    bar["open"], bar["first_event"] = price, stamp.timestamp()
                if stamp.timestamp() >= bar["last_event"]:
                    bar["close"], bar["last_event"] = price, stamp.timestamp()
                bar.update(high=max(bar["high"], price), low=min(bar["low"], price),
                           volume=bar["volume"] + qty, last_cumulative=cumulative, last_sequence=p.series_sequence)
            state["watermark"] = max(state["watermark"], stamp.timestamp())
            state["last"] = {"sequence": p.series_sequence, "cumulative": cumulative,
                             "minute": minute, "hash": digest(p.as_dict()),
                             "eligible": not any(issue != "startup_or_reconnect_partial_minute" for issue in issues)}
            if not in_session:
                state["boundary_cursor"] = state["last"]
            for old in state["bars"].values():
                if old["status"] == "pending" and old["minute_epoch"] + 60 + self.lateness_sec <= state["watermark"]:
                    old["status"] = "complete"
                    old["available_at_epoch"] = now_ts
            for old_key in sorted(state["bars"])[:-self.max_bars]:
                del state["bars"][old_key]
                state["history_truncated"] = True
            state["revision"] += 1
            touched.add(key)
        for key in touched:
            day, item, session = key
            state = self.series[key]
            # Pending price changes need no file rewrite. Sealing, invalidation,
            # loss and epoch changes always publish immediately, in the writer.
            publication_key = digest([state["integrity"], state.get("invalid_from_minute"),
                state.get("session_coverage"), state.get("boundary_cursor"), [
                bar if bar["status"] == "complete" else
                [minute, bar["status"], bar["issues"]]
                for minute, bar in sorted(state["bars"].items())]])
            if state.get("publication_key") == publication_key:
                continue
            payload = {"schema": SCHEMA, "trade_date": day, "source_item": item, "session": session,
                "adjustment": "raw_same_day", "market_data_route": "krx_nxt_integrated",
                "producer": self.producer, "source_commit": os.getenv("KORSTOCKSCAN_RUNTIME_GIT_COMMIT", ""),
                "generated_at_epoch": now_ts, "source_epoch": state["epoch"],
                "integrity": state["integrity"], "watermark_epoch": state["watermark"],
                "revision": state["revision"], "cursor": state["last"],
                "invalid_from_minute": state.get("invalid_from_minute"),
                "session_coverage": state.get("session_coverage"),
                "history_truncated": state.get("history_truncated", False),
                "journal_path": str(journal_path), "durable_cursor": durable_cursor,
                "metric_contract": METRIC_CONTRACT,
                "empty_minute_policy": "no_print_observed_not_imputed",
                "bars": [state["bars"][m] for m in sorted(state["bars"])],
                "actual_order_submitted": False, "runtime_effect": False}
            payload["content_sha256"] = digest(payload)
            path = self.root/day/item/(session + ".json")
            self._paths.add(path)
            atomic_json(path, payload)
            state["publication_key"] = publication_key
