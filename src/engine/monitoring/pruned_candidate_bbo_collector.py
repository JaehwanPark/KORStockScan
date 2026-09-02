"""Bounded source-only BBO collection for scanner candidates pruned pre-promotion.

The scanner has no executable quote path for candidates rejected by watch-budget
or re-entry guards.  This collector samples the existing Kiwoom ``ka10004``
quote endpoint on a sparse, fixed horizon schedule.  It never publishes a
runtime target and has no order, threshold, provider, slot, or cooldown
authority.
"""

from __future__ import annotations

import hashlib
import heapq
import math
import os
import threading
import time
from datetime import datetime, time as dt_time, timedelta, timezone
from typing import Any, Callable, Mapping

from src.utils import kiwoom_utils
from src.utils.logger import log_error
from src.utils.pipeline_event_logger import emit_pipeline_event

KST = timezone(timedelta(hours=9))

ELIGIBLE_PRUNE_REASONS = frozenset(
    {
        "reentry_cooldown_no_material_upgrade",
        "market_gainer_reserved_full",
        "general_slot_limit",
    }
)
SAMPLE_OFFSETS_SEC = (0, 3, 10, 20, 30, 60, 180, 300, 600, 1200)
EPISODE_RESET_GAP_SEC = 300.0
MIN_REQUEST_INTERVAL_SEC = 0.25
MAX_ANCHOR_TO_SCHEDULE_DELAY_SEC = 2.0
# Eight simultaneous episodes keep the 0-second anchor queue within the
# consumer's two-second schedule-lag ceiling at the enforced 250 ms minimum
# request-start interval. A larger default would make the declared 95% source
# coverage floor mathematically unreachable before network latency is counted.
MAX_ACTIVE_EPISODES = 8
MAX_PENDING_SAMPLES = MAX_ACTIVE_EPISODES * len(SAMPLE_OFFSETS_SEC)
# Process-local by design; restart provenance creates a new episode namespace.
# This is not represented as an account-wide or host-wide Kiwoom quota.
MAX_SCHEDULED_REQUESTS_PER_PROCESS_KST_DATE = 1200
MAX_RETAINED_EPISODES = 512

METRIC_CONTRACT = {
    "metric_role": "source_quality_instrumentation",
    "decision_authority": "scanner_prune_bbo_observation_only",
    "window_policy": (
        "stable_code_venue_session_episode_reset_after_300s_absence_"
        "sample_offsets_0_3_10_20_30_60_180_300_600_1200s"
    ),
    "sample_floor": (
        "each_bounded_observer_selected_prune_cohort_venue_session_"
        "verified_common_stock_exact_route_"
        "rest_bbo_episode_coverage_pct>=95_and_resolved_outcome_count>=20_"
        "and_right_censored_pct<=20"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "ka10004_exact_request_code_response_received_epoch_schedule_lag_"
        "within_consumer_floor_valid_bbo_"
        "same_venue_session_and_effective_dated_cost_contract"
    ),
    "forbidden_uses": (
        "broker_order_submit|broker_order_cancel|scanner_source_pool_change|"
        "scanner_slot_or_cooldown_change|entry_or_exit_authority|"
        "threshold_or_provider_change|quantity_or_cap_change|"
        "stale_quote_or_hard_safety_bypass|continuous_market_path_claim|"
        "full_prune_population_ev_extrapolation"
    ),
    "runtime_effect": False,
    "trading_runtime_effect": False,
    "market_data_request_effect": True,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}


def _valid_code(value: Any) -> str:
    code = str(value or "").strip().upper()
    if code.startswith("A"):
        code = code[1:]
    code = code[:6]
    return code if len(code) == 6 and code.isdigit() else ""


def _request_route(code: str, effective_venue: str) -> tuple[str, str] | None:
    if effective_venue == "KRX":
        return code, "KRX"
    if effective_venue in {"NXT", "PREMARKET_KRX_LIKE"}:
        return f"{code}_NX", "NXT"
    return None


def _session_matches_venue(effective_venue: str, market_session_bucket: str) -> bool:
    allowed = {
        "PREMARKET_KRX_LIKE": {"krx_like_premarket", "premarket_krx_like"},
        "KRX": {"krx_regular"},
        "NXT": {"nxt", "nxt_regular"},
    }
    return market_session_bucket in allowed.get(effective_venue, set())


def _session_end_epoch(now_epoch: float, effective_venue: str) -> float | None:
    now_dt = datetime.fromtimestamp(float(now_epoch), tz=KST)
    bounds_by_venue = {
        "PREMARKET_KRX_LIKE": (dt_time(hour=8), dt_time(hour=9)),
        "KRX": (dt_time(hour=9), dt_time(hour=15, minute=30)),
        "NXT": (dt_time(hour=16), dt_time(hour=20)),
    }
    bounds = bounds_by_venue.get(effective_venue)
    if bounds is None:
        return None
    start_time, end_time = bounds
    if not start_time <= now_dt.time() < end_time:
        return None
    end_dt = datetime.combine(now_dt.date(), end_time, tzinfo=KST)
    return end_dt.timestamp()


def _episode_id(
    *,
    code: str,
    effective_venue: str,
    market_session_bucket: str,
    scan_generation_id: str,
    anchor_epoch: float,
) -> str:
    raw = (
        f"{os.getpid()}|{code}|{effective_venue}|{market_session_bucket}|"
        f"{scan_generation_id}|{anchor_epoch:.6f}"
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"PRUNEBBO-{digest}"


class PrunedCandidateBBOCollector:
    """One-worker sparse sampler with bounded memory and request volume."""

    def __init__(
        self,
        token: str,
        *,
        fetch_quote: Callable[..., Mapping[str, Any] | None] | None = None,
        emit_event: Callable[..., Any] | None = None,
        clock: Callable[[], float] | None = None,
        autostart: bool = True,
        max_active_episodes: int = MAX_ACTIVE_EPISODES,
        max_pending_samples: int = MAX_PENDING_SAMPLES,
        max_daily_requests: int = MAX_SCHEDULED_REQUESTS_PER_PROCESS_KST_DATE,
        min_request_interval_sec: float = MIN_REQUEST_INTERVAL_SEC,
    ) -> None:
        self._token = str(token or "").strip()
        self._fetch_quote = fetch_quote or kiwoom_utils.get_stock_orderbook_ka10004
        self._emit_event = emit_event or emit_pipeline_event
        self._clock = clock or time.time
        self._autostart = bool(autostart)
        self._max_active_episodes = max(1, int(max_active_episodes))
        self._max_pending_samples = max(1, int(max_pending_samples))
        self._max_daily_requests = max(1, int(max_daily_requests))
        self._min_request_interval_sec = max(
            MIN_REQUEST_INTERVAL_SEC, float(min_request_interval_sec)
        )
        self._condition = threading.Condition(threading.RLock())
        self._episodes: dict[str, dict[str, Any]] = {}
        self._latest_episode_by_key: dict[tuple[str, str, str], str] = {}
        self._tasks: list[tuple[float, int, str, int, int]] = []
        self._sequence = 0
        self._scheduled_date = ""
        self._scheduled_request_count = 0
        self._last_request_started_epoch = 0.0
        self._worker_error_count = 0
        self._receipt_emit_failure_count = 0
        self._request_gap_count = 0
        self._captured_sample_count = 0
        self._configured_epoch: float | None = None
        self._configuration_receipt_status = "not_emitted"
        self._configuration_receipt_emit_failure_count = 0
        self._stop_requested = False
        self._worker: threading.Thread | None = None

    def update_token(self, token: str) -> None:
        normalized = str(token or "").strip()
        if not normalized:
            return
        with self._condition:
            self._token = normalized

    def _ensure_worker_locked(self) -> None:
        if not self._autostart or (self._worker and self._worker.is_alive()):
            return
        self._worker = threading.Thread(
            target=self._worker_loop,
            name="scanner-prune-bbo-observer",
            daemon=True,
        )
        self._worker.start()

    def _active_episode_count_locked(self) -> int:
        return sum(
            str(row.get("state") or "") == "scheduled"
            for row in self._episodes.values()
        )

    def _roll_daily_budget_locked(self, now_epoch: float) -> None:
        current_date = datetime.fromtimestamp(now_epoch, tz=KST).date().isoformat()
        if self._scheduled_date != current_date:
            self._scheduled_date = current_date
            self._scheduled_request_count = 0

    def _budget_fields_locked(self) -> dict[str, Any]:
        return {
            "scanner_prune_observer_budget_kst_date": self._scheduled_date,
            "scanner_prune_observer_active_episode_count": (
                self._active_episode_count_locked()
            ),
            "scanner_prune_observer_pending_sample_count": len(self._tasks),
            "scanner_prune_observer_process_daily_scheduled_request_count": (
                self._scheduled_request_count
            ),
            "scanner_prune_observer_process_daily_remaining_request_count": max(
                0, self._max_daily_requests - self._scheduled_request_count
            ),
            "scanner_prune_observer_worker_alive": bool(
                self._worker and self._worker.is_alive()
            ),
            "scanner_prune_observer_worker_error_count": self._worker_error_count,
            "scanner_prune_observer_receipt_emit_failure_count": (
                self._receipt_emit_failure_count
            ),
            "scanner_prune_observer_request_gap_count": self._request_gap_count,
            "scanner_prune_observer_captured_sample_count": (
                self._captured_sample_count
            ),
            "scanner_prune_observer_configured": self._configured_epoch is not None,
            "scanner_prune_observer_configured_epoch": self._configured_epoch,
            "scanner_prune_observer_configuration_receipt_status": (
                self._configuration_receipt_status
            ),
            "scanner_prune_observer_configuration_receipt_emit_failure_count": (
                self._configuration_receipt_emit_failure_count
            ),
        }

    def configuration_receipt_fields(
        self, *, configuration_status: str, configured_epoch: float
    ) -> dict[str, Any]:
        """Return a secret-free receipt proving this PID configured the observer."""

        with self._condition:
            self._configured_epoch = float(configured_epoch)
            self._roll_daily_budget_locked(self._configured_epoch)
            self._configuration_receipt_status = "emit_pending"
            fields = {
                **METRIC_CONTRACT,
                "scanner_prune_observer_configuration_status": str(
                    configuration_status or "configured"
                ),
                "scanner_prune_observer_configured": True,
                "scanner_prune_observer_configured_epoch": round(
                    self._configured_epoch, 6
                ),
                "scanner_prune_observer_configured_at": datetime.fromtimestamp(
                    self._configured_epoch, tz=KST
                ).isoformat(),
                "scanner_prune_observer_process_pid": os.getpid(),
                "scanner_prune_observer_token_present": bool(self._token),
                "scanner_prune_observer_sample_offsets_sec": list(SAMPLE_OFFSETS_SEC),
                "scanner_prune_observer_episode_reset_gap_sec": (EPISODE_RESET_GAP_SEC),
                "scanner_prune_observer_max_anchor_to_schedule_delay_sec": (
                    MAX_ANCHOR_TO_SCHEDULE_DELAY_SEC
                ),
                "scanner_prune_observer_max_active_episode_count": (
                    self._max_active_episodes
                ),
                "scanner_prune_observer_max_pending_sample_count": (
                    self._max_pending_samples
                ),
                "scanner_prune_observer_max_process_daily_scheduled_request_count": (
                    self._max_daily_requests
                ),
                "scanner_prune_observer_min_request_interval_sec": (
                    self._min_request_interval_sec
                ),
                "scanner_prune_observer_market_data_request_effect": True,
                **self._budget_fields_locked(),
            }
            # The event itself is the proof of a successful append.  Internal
            # state remains ``emit_pending`` until the logger call returns and
            # is then exposed on later schedule receipts.
            fields["scanner_prune_observer_configuration_receipt_status"] = "emitted"
            return fields

    def record_configuration_receipt_result(self, *, emitted: bool) -> None:
        with self._condition:
            self._configuration_receipt_status = "emitted" if emitted else "emit_failed"
            if not emitted:
                self._configuration_receipt_emit_failure_count += 1

    def _trim_retained_locked(self) -> None:
        if len(self._episodes) <= MAX_RETAINED_EPISODES:
            return
        removable = sorted(
            (
                (float(row.get("last_seen_epoch") or 0.0), episode_id)
                for episode_id, row in self._episodes.items()
                if str(row.get("state") or "") != "scheduled"
            )
        )
        for _last_seen, episode_id in removable:
            if len(self._episodes) <= MAX_RETAINED_EPISODES:
                break
            row = self._episodes.pop(episode_id, None)
            if not row:
                continue
            key = tuple(row.get("episode_key") or ())
            if self._latest_episode_by_key.get(key) == episode_id:
                self._latest_episode_by_key.pop(key, None)

    def offer(
        self,
        target: Mapping[str, Any],
        *,
        reason: str,
        scan_generation_id: str,
        scan_rank: int,
        ranked_candidate_count: int,
        venue_fields: Mapping[str, Any],
        observed_epoch: float | None = None,
    ) -> dict[str, Any]:
        """Bind a stable prune episode and schedule sparse exact-route samples."""

        reason = str(reason or "").strip()
        if reason not in ELIGIBLE_PRUNE_REASONS:
            return {"eligible": False, "schedule_status": "ineligible_prune_reason"}
        code = _valid_code(target.get("Code"))
        generation_id = str(scan_generation_id or "").strip()
        effective_venue = (
            str(venue_fields.get("effective_venue") or venue_fields.get("venue") or "")
            .strip()
            .upper()
        )
        market_session_bucket = (
            str(venue_fields.get("market_session_bucket") or "").strip().lower()
        )
        route = _request_route(code, effective_venue) if code else None
        now_epoch = float(self._clock() if observed_epoch is None else observed_epoch)
        base = {
            "eligible": True,
            "scanner_prune_observer_schedule_status": "source_quality_blocked",
            "scanner_prune_observer_reason": reason,
            "scanner_prune_observer_episode_id": "",
            "scanner_prune_observer_market_data_request_effect": True,
            **METRIC_CONTRACT,
        }
        if not self._token:
            return {**base, "scanner_prune_observer_schedule_status": "token_missing"}
        if not code or not generation_id:
            return {
                **base,
                "scanner_prune_observer_schedule_status": "lineage_missing",
            }
        if (
            not market_session_bucket
            or route is None
            or not _session_matches_venue(effective_venue, market_session_bucket)
        ):
            return {
                **base,
                "scanner_prune_observer_schedule_status": (
                    "explicit_venue_or_session_missing_or_conflicting"
                ),
            }
        session_end_epoch = _session_end_epoch(now_epoch, effective_venue)
        if session_end_epoch is None:
            return {
                **base,
                "scanner_prune_observer_schedule_status": "outside_supported_session",
            }
        offsets = tuple(
            offset
            for offset in SAMPLE_OFFSETS_SEC
            if now_epoch + float(offset) < session_end_epoch
        )
        if not offsets:
            return {
                **base,
                "scanner_prune_observer_schedule_status": "no_in_session_horizon",
            }

        episode_key = (code, effective_venue, market_session_bucket)
        with self._condition:
            self._roll_daily_budget_locked(now_epoch)
            previous_id = self._latest_episode_by_key.get(episode_key)
            previous = self._episodes.get(previous_id or "")
            previous_gap_sec = (
                now_epoch - float(previous.get("last_seen_epoch") or 0.0)
                if previous is not None
                else None
            )
            reusable_previous = bool(
                previous is not None
                and previous_gap_sec is not None
                and 0.0 <= previous_gap_sec <= EPISODE_RESET_GAP_SEC
            )
            if reusable_previous:
                previous["last_seen_epoch"] = now_epoch
                previous["observed_reasons"] = sorted(
                    set(previous.get("observed_reasons") or ()) | {reason}
                )
                previous_generation_ids = list(
                    previous.get("scan_generation_ids") or []
                )
                if generation_id not in previous_generation_ids:
                    previous_generation_ids.append(generation_id)
                previous["scan_generation_ids"] = previous_generation_ids[-64:]
                if previous.get("state") in {"scheduled", "completed"}:
                    return {
                        **base,
                        "scanner_prune_observer_schedule_status": (
                            "existing_episode_reused"
                            if previous.get("state") == "scheduled"
                            else "completed_episode_reused"
                        ),
                        "scanner_prune_observer_episode_id": previous_id,
                        "scanner_prune_observer_anchor_generation_id": previous.get(
                            "anchor_generation_id"
                        ),
                        "scanner_prune_observer_anchor_reason": previous.get(
                            "anchor_reason"
                        ),
                        "scanner_prune_observer_anchor_epoch": previous.get(
                            "anchor_epoch"
                        ),
                        "scanner_prune_observer_schedule_started_epoch": previous.get(
                            "schedule_started_epoch"
                        ),
                        "scanner_prune_observer_anchor_to_schedule_delay_sec": (
                            previous.get("anchor_to_schedule_delay_sec")
                        ),
                        "scanner_prune_observer_request_code": previous.get(
                            "request_code"
                        ),
                        "scanner_prune_observer_expected_observed_venue": previous.get(
                            "expected_observed_venue"
                        ),
                        "scanner_prune_observer_scheduled_sample_count": len(
                            previous.get("scheduled_offsets_sec") or []
                        ),
                        **self._budget_fields_locked(),
                    }

            request_code, expected_observed_venue = route
            episode_id = (
                str(previous_id)
                if reusable_previous and previous is not None
                else _episode_id(
                    code=code,
                    effective_venue=effective_venue,
                    market_session_bucket=market_session_bucket,
                    scan_generation_id=generation_id,
                    anchor_epoch=now_epoch,
                )
            )
            anchor_epoch = (
                float(previous.get("anchor_epoch") or now_epoch)
                if reusable_previous and previous is not None
                else now_epoch
            )
            anchor_generation_id = (
                str(previous.get("anchor_generation_id") or generation_id)
                if reusable_previous and previous is not None
                else generation_id
            )
            anchor_reason = (
                str(previous.get("anchor_reason") or reason)
                if reusable_previous and previous is not None
                else reason
            )
            anchor_scan_rank = (
                int(previous.get("anchor_scan_rank") or scan_rank)
                if reusable_previous and previous is not None
                else int(scan_rank)
            )
            anchor_ranked_candidate_count = (
                int(
                    previous.get("anchor_ranked_candidate_count")
                    or ranked_candidate_count
                )
                if reusable_previous and previous is not None
                else int(ranked_candidate_count)
            )
            anchor_to_schedule_delay_sec = max(0.0, now_epoch - anchor_epoch)

            def deferred(status: str) -> dict[str, Any]:
                deferred_episode = previous if reusable_previous else None
                if deferred_episode is None:
                    deferred_episode = {
                        "episode_key": episode_key,
                        "episode_id": episode_id,
                        "code": code,
                        "name": str(target.get("Name") or "-"),
                        "effective_venue": effective_venue,
                        "market_session_bucket": market_session_bucket,
                        "request_code": request_code,
                        "expected_observed_venue": expected_observed_venue,
                        "anchor_reason": anchor_reason,
                        "observed_reasons": [reason],
                        "anchor_generation_id": anchor_generation_id,
                        "scan_generation_ids": [generation_id],
                        "anchor_scan_rank": anchor_scan_rank,
                        "anchor_ranked_candidate_count": (
                            anchor_ranked_candidate_count
                        ),
                        "anchor_epoch": anchor_epoch,
                        "last_seen_epoch": now_epoch,
                    }
                deferred_episode["state"] = "deferred"
                deferred_episode["last_deferred_status"] = status
                deferred_episode["last_seen_epoch"] = now_epoch
                self._episodes[episode_id] = deferred_episode
                self._latest_episode_by_key[episode_key] = episode_id
                self._trim_retained_locked()
                return {
                    **base,
                    "scanner_prune_observer_schedule_status": status,
                    "scanner_prune_observer_episode_id": episode_id,
                    "scanner_prune_observer_anchor_generation_id": (
                        deferred_episode.get("anchor_generation_id")
                    ),
                    "scanner_prune_observer_anchor_reason": deferred_episode.get(
                        "anchor_reason"
                    ),
                    "scanner_prune_observer_request_code": request_code,
                    "scanner_prune_observer_expected_observed_venue": (
                        expected_observed_venue
                    ),
                    "scanner_prune_observer_scheduled_sample_count": 0,
                    "scanner_prune_observer_anchor_epoch": round(anchor_epoch, 6),
                    "scanner_prune_observer_anchor_to_schedule_delay_sec": round(
                        anchor_to_schedule_delay_sec, 6
                    ),
                    **self._budget_fields_locked(),
                }

            if self._active_episode_count_locked() >= self._max_active_episodes:
                return deferred("active_episode_capacity_rejected")
            # A deferred opportunity remains the same 300-second episode.  Once
            # its first-prune anchor is older than the consumer's executable
            # schedule-lag ceiling, sampling a later repeat would spend REST
            # budget on observations that must all be rejected (or, worse,
            # silently re-anchor a biased survivor).  Keep it explicitly
            # deferred until the episode reset gap creates a new opportunity.
            if anchor_to_schedule_delay_sec > MAX_ANCHOR_TO_SCHEDULE_DELAY_SEC:
                return deferred("anchor_schedule_latency_exceeded")
            if len(self._tasks) + len(offsets) > self._max_pending_samples:
                return deferred("pending_sample_capacity_rejected")
            if self._scheduled_request_count + len(offsets) > self._max_daily_requests:
                return deferred("daily_request_budget_rejected")

            episode = {
                "episode_key": episode_key,
                "episode_id": episode_id,
                "state": "scheduled",
                "code": code,
                "name": str(target.get("Name") or "-"),
                "effective_venue": effective_venue,
                "market_session_bucket": market_session_bucket,
                "request_code": request_code,
                "expected_observed_venue": expected_observed_venue,
                "anchor_reason": anchor_reason,
                "observed_reasons": sorted(
                    set(previous.get("observed_reasons") or ()) | {reason}
                    if reusable_previous and previous is not None
                    else {reason}
                ),
                "anchor_generation_id": anchor_generation_id,
                "scan_generation_ids": (
                    list(previous.get("scan_generation_ids") or [])
                    if reusable_previous and previous is not None
                    else [generation_id]
                )[-64:],
                "anchor_scan_rank": anchor_scan_rank,
                "anchor_ranked_candidate_count": anchor_ranked_candidate_count,
                "anchor_epoch": anchor_epoch,
                "schedule_started_epoch": now_epoch,
                "anchor_to_schedule_delay_sec": anchor_to_schedule_delay_sec,
                "session_end_epoch": session_end_epoch,
                "last_seen_epoch": now_epoch,
                "scheduled_offsets_sec": list(offsets),
                "completed_sample_count": 0,
            }
            self._episodes[episode_id] = episode
            self._latest_episode_by_key[episode_key] = episode_id
            for sample_index, offset_sec in enumerate(offsets):
                self._sequence += 1
                heapq.heappush(
                    self._tasks,
                    (
                        now_epoch + float(offset_sec),
                        self._sequence,
                        episode_id,
                        sample_index,
                        int(offset_sec),
                    ),
                )
            self._scheduled_request_count += len(offsets)
            self._trim_retained_locked()
            self._ensure_worker_locked()
            self._condition.notify_all()
            return {
                **base,
                "scanner_prune_observer_schedule_status": "new_episode_scheduled",
                "scanner_prune_observer_episode_id": episode_id,
                "scanner_prune_observer_anchor_generation_id": anchor_generation_id,
                "scanner_prune_observer_anchor_reason": anchor_reason,
                "scanner_prune_observer_anchor_epoch": round(anchor_epoch, 6),
                "scanner_prune_observer_schedule_started_epoch": round(now_epoch, 6),
                "scanner_prune_observer_anchor_to_schedule_delay_sec": round(
                    anchor_to_schedule_delay_sec, 6
                ),
                "scanner_prune_observer_request_code": request_code,
                "scanner_prune_observer_expected_observed_venue": (
                    expected_observed_venue
                ),
                "scanner_prune_observer_scheduled_sample_count": len(offsets),
                "scanner_prune_observer_scheduled_offsets_sec": list(offsets),
                "scanner_prune_observer_episode_reset_gap_sec": (EPISODE_RESET_GAP_SEC),
                "scanner_prune_observer_max_active_episodes": (
                    self._max_active_episodes
                ),
                "scanner_prune_observer_max_process_daily_requests": (
                    self._max_daily_requests
                ),
                "scanner_prune_observer_min_request_interval_sec": (
                    self._min_request_interval_sec
                ),
                "scanner_prune_observer_max_request_attempts_per_sample": 1,
                **self._budget_fields_locked(),
            }

    def _pop_due_task(self, now_epoch: float) -> tuple | None:
        with self._condition:
            if not self._tasks or self._tasks[0][0] > now_epoch:
                return None
            if (
                self._last_request_started_epoch > 0
                and now_epoch - self._last_request_started_epoch
                < self._min_request_interval_sec
            ):
                return None
            task = heapq.heappop(self._tasks)
            self._last_request_started_epoch = now_epoch
            episode = self._episodes.get(task[2])
            return (task, dict(episode)) if episode else None

    def run_due_once(self, *, now_epoch: float | None = None) -> bool:
        """Process one due sample; exposed for deterministic tests."""

        actual_now = float(self._clock() if now_epoch is None else now_epoch)
        item = self._pop_due_task(actual_now)
        if item is None:
            return False
        task, episode = item
        try:
            self._collect_and_emit(task, episode, request_started_epoch=actual_now)
        except Exception as exc:
            self._record_unexpected_task_failure(task, episode, exc)
        return True

    def _record_unexpected_task_failure(
        self,
        task: tuple[float, int, str, int, int],
        episode: Mapping[str, Any],
        exc: Exception,
    ) -> None:
        due_epoch, _sequence, episode_id, sample_index, offset_sec = task
        failure_epoch = float(self._clock())
        terminal_sample = sample_index + 1 >= len(
            episode.get("scheduled_offsets_sec") or []
        )
        fallback_receipt = {
            "scanner_prune_observer_episode_id": episode_id,
            "scanner_prune_observer_anchor_generation_id": episode.get(
                "anchor_generation_id"
            ),
            "scanner_scan_generation_id": episode.get("anchor_generation_id"),
            "scanner_scan_rank": episode.get("anchor_scan_rank"),
            "scanner_ranked_candidate_count": episode.get(
                "anchor_ranked_candidate_count"
            ),
            "scanner_prune_reason": episode.get("anchor_reason"),
            "scanner_prune_observer_anchor_reason": episode.get("anchor_reason"),
            "scanner_prune_observer_anchor_epoch": round(
                float(episode.get("anchor_epoch") or 0.0), 6
            ),
            "scanner_prune_observer_schedule_started_epoch": round(
                float(episode.get("schedule_started_epoch") or 0.0), 6
            ),
            "scanner_prune_observer_anchor_to_schedule_delay_sec": round(
                float(episode.get("anchor_to_schedule_delay_sec") or 0.0), 6
            ),
            "scanner_prune_observer_sample_index": int(sample_index),
            "scanner_prune_observer_scheduled_offset_sec": int(offset_sec),
            "scanner_prune_observer_due_epoch": round(float(due_epoch), 6),
            "scanner_prune_observer_request_started_epoch": round(
                failure_epoch, 6
            ),
            "scanner_prune_observer_observed_epoch": round(failure_epoch, 6),
            "scanner_prune_observer_observed_at": datetime.fromtimestamp(
                failure_epoch, tz=KST
            ).isoformat(),
            "scanner_prune_observer_request_completed_epoch": round(
                failure_epoch, 6
            ),
            "scanner_prune_observer_schedule_lag_sec": round(
                max(0.0, failure_epoch - float(due_epoch)), 6
            ),
            "scanner_prune_observer_request_code": episode.get("request_code"),
            "scanner_prune_observer_response_request_code": (
                "absent_unexpected_collector_failure"
            ),
            "scanner_prune_observer_expected_observed_venue": episode.get(
                "expected_observed_venue"
            ),
            "scanner_prune_observer_route_match": False,
            "scanner_prune_observer_status": "source_quality_gap",
            "scanner_prune_observer_gap_reason": (
                f"unexpected_collector_failure:{type(exc).__name__}"
            ),
            "scanner_prune_observer_terminal_sample": terminal_sample,
            "scanner_prune_observer_source_quality_pass": False,
            "scanner_prune_observer_price_source": "absent_source_quality_gap",
            "scanner_prune_observer_best_bid": None,
            "scanner_prune_observer_best_ask": None,
            "effective_venue": episode.get("effective_venue"),
            "venue": episode.get("effective_venue"),
            "market_session_bucket": episode.get("market_session_bucket"),
            **METRIC_CONTRACT,
        }
        fallback_emit_failed = False
        try:
            emit_result = self._emit_event(
                "ENTRY_PIPELINE",
                str(episode.get("name") or "-"),
                str(episode.get("code") or ""),
                "scalping_scanner_prune_bbo_observation",
                fields=fallback_receipt,
            )
            fallback_emit_failed = bool(
                isinstance(emit_result, Mapping)
                and emit_result.get("structured_append_succeeded") is False
            )
        except Exception:
            fallback_emit_failed = True
        with self._condition:
            self._worker_error_count += 1
            self._request_gap_count += 1
            if fallback_emit_failed:
                self._receipt_emit_failure_count += 1
            current = self._episodes.get(episode_id)
            if current is not None:
                current["completed_sample_count"] = (
                    int(current.get("completed_sample_count") or 0) + 1
                )
                current["last_worker_error_type"] = type(exc).__name__
                if terminal_sample:
                    current["state"] = "completed"
                    current["completed_epoch"] = max(
                        float(due_epoch), self._last_request_started_epoch
                    )
            self._trim_retained_locked()
        log_error(
            "[SCANNER_PRUNE_BBO_OBSERVER] worker sample failed "
            f"episode={episode_id} sample={sample_index} "
            f"error={type(exc).__name__} "
            f"fallback_receipt_emitted={str(not fallback_emit_failed).lower()}"
        )

    def _worker_loop(self) -> None:
        while True:
            with self._condition:
                if self._stop_requested:
                    return
                now_epoch = float(self._clock())
                next_due = self._tasks[0][0] if self._tasks else None
                next_allowed = max(
                    float(next_due or now_epoch),
                    self._last_request_started_epoch + self._min_request_interval_sec,
                )
                if next_due is None or next_allowed > now_epoch:
                    timeout = (
                        60.0
                        if next_due is None
                        else max(0.01, min(60.0, next_allowed - now_epoch))
                    )
                    self._condition.wait(timeout=timeout)
                    continue
            try:
                self.run_due_once()
            except Exception as exc:
                with self._condition:
                    self._worker_error_count += 1
                log_error(
                    "[SCANNER_PRUNE_BBO_OBSERVER] worker sample failed "
                    f"error={type(exc).__name__}"
                )

    def _collect_and_emit(
        self,
        task: tuple[float, int, str, int, int],
        episode: Mapping[str, Any],
        *,
        request_started_epoch: float,
    ) -> None:
        due_epoch, _sequence, episode_id, sample_index, offset_sec = task
        request_code = str(episode.get("request_code") or "")
        status = "source_quality_gap"
        gap_reason = "request_not_attempted"
        snapshot: Mapping[str, Any] = {}
        session_end_epoch = float(episode.get("session_end_epoch") or 0.0)
        request_attempted = bool(
            session_end_epoch > 0 and request_started_epoch < session_end_epoch
        )
        if not request_attempted:
            gap_reason = "request_skipped_outside_episode_session"
        else:
            try:
                raw = self._fetch_quote(
                    self._token,
                    request_code,
                    explicit_request_code=True,
                    max_retries=1,
                )
                snapshot = raw if isinstance(raw, Mapping) else {}
                gap_reason = "empty_or_invalid_ka10004_response"
            except Exception as exc:
                gap_reason = f"ka10004_request_exception:{type(exc).__name__}"
        request_completed_epoch = float(self._clock())

        best_bid = snapshot.get("best_bid")
        best_ask = snapshot.get("best_ask")
        received_epoch = snapshot.get("rest_received_ts")
        try:
            bid = int(best_bid)
            ask = int(best_ask)
            received = float(received_epoch)
        except (TypeError, ValueError, OverflowError):
            bid = ask = 0
            received = 0.0
        response_request_code = str(snapshot.get("request_code") or "").upper()
        response_stock_code = _valid_code(snapshot.get("stock_code"))
        source = str(snapshot.get("source") or "")
        route_match = bool(
            response_request_code == request_code
            and response_stock_code == episode.get("code")
        )
        receipt_time_valid = bool(
            math.isfinite(received)
            and request_started_epoch <= received <= request_completed_epoch + 0.1
        )
        bbo_valid = bool(bid > 0 and ask >= bid)
        if not request_attempted:
            pass
        elif source != "ka10004_rest_orderbook":
            gap_reason = "ka10004_source_provenance_invalid"
        elif not route_match:
            gap_reason = "ka10004_exact_request_route_mismatch"
        elif not receipt_time_valid:
            gap_reason = "ka10004_response_received_epoch_invalid"
        elif not bbo_valid:
            gap_reason = "ka10004_bbo_invalid_or_crossed"
        else:
            status = "captured"
            gap_reason = "not_applicable_capture_pass"

        observed_epoch = received if status == "captured" else request_completed_epoch
        quote_age_ms = (
            max(0.0, (request_completed_epoch - received) * 1000.0)
            if status == "captured"
            else None
        )
        terminal_sample = sample_index + 1 >= len(
            episode.get("scheduled_offsets_sec") or []
        )
        fields = {
            "scanner_prune_observer_episode_id": episode_id,
            "scanner_prune_observer_anchor_generation_id": episode.get(
                "anchor_generation_id"
            ),
            "scanner_scan_generation_id": episode.get("anchor_generation_id"),
            "scanner_scan_rank": episode.get("anchor_scan_rank"),
            "scanner_ranked_candidate_count": episode.get(
                "anchor_ranked_candidate_count"
            ),
            "scanner_prune_reason": episode.get("anchor_reason"),
            "scanner_prune_observer_anchor_reason": episode.get("anchor_reason"),
            "scanner_prune_observer_anchor_epoch": round(
                float(episode.get("anchor_epoch") or 0.0), 6
            ),
            "scanner_prune_observer_schedule_started_epoch": round(
                float(episode.get("schedule_started_epoch") or 0.0), 6
            ),
            "scanner_prune_observer_anchor_to_schedule_delay_sec": round(
                float(episode.get("anchor_to_schedule_delay_sec") or 0.0), 6
            ),
            "scanner_prune_observer_sample_index": int(sample_index),
            "scanner_prune_observer_scheduled_offset_sec": int(offset_sec),
            "scanner_prune_observer_due_epoch": round(float(due_epoch), 6),
            "scanner_prune_observer_request_started_epoch": round(
                request_started_epoch, 6
            ),
            "scanner_prune_observer_observed_epoch": round(observed_epoch, 6),
            "scanner_prune_observer_observed_at": datetime.fromtimestamp(
                observed_epoch, tz=KST
            ).isoformat(),
            "scanner_prune_observer_request_completed_epoch": round(
                request_completed_epoch, 6
            ),
            "scanner_prune_observer_schedule_lag_sec": round(
                max(0.0, request_started_epoch - float(due_epoch)), 6
            ),
            "scanner_prune_observer_request_elapsed_ms": round(
                max(0.0, request_completed_epoch - request_started_epoch) * 1000.0,
                3,
            ),
            "scanner_prune_observer_request_code": request_code,
            "scanner_prune_observer_response_request_code": (
                response_request_code or "absent_no_valid_response"
            ),
            "scanner_prune_observer_expected_observed_venue": episode.get(
                "expected_observed_venue"
            ),
            "scanner_prune_observer_route_match": route_match,
            "scanner_prune_observer_status": status,
            "scanner_prune_observer_gap_reason": gap_reason,
            "scanner_prune_observer_terminal_sample": terminal_sample,
            "scanner_prune_observer_source_quality_pass": status == "captured",
            "scanner_prune_observer_price_source": (
                "ka10004_rest_orderbook_exact_request_code"
                if status == "captured"
                else "absent_source_quality_gap"
            ),
            "scanner_prune_observer_best_bid": bid if status == "captured" else None,
            "scanner_prune_observer_best_ask": ask if status == "captured" else None,
            "scanner_prune_observer_quote_age_ms": quote_age_ms,
            "scanner_prune_observer_bid_req_base_tm": str(
                snapshot.get("bid_req_base_tm") or "absent_or_undocumented"
            ),
            "scanner_prune_observer_bid_req_base_tm_authority": (
                "raw_not_freshness_input"
            ),
            "effective_venue": episode.get("effective_venue"),
            "venue": episode.get("effective_venue"),
            "market_session_bucket": episode.get("market_session_bucket"),
            **METRIC_CONTRACT,
        }
        emit_failed = False
        try:
            emit_result = self._emit_event(
                "ENTRY_PIPELINE",
                str(episode.get("name") or "-"),
                str(episode.get("code") or ""),
                "scalping_scanner_prune_bbo_observation",
                fields=fields,
            )
            emit_failed = bool(
                isinstance(emit_result, Mapping)
                and emit_result.get("structured_append_succeeded") is False
            )
        except Exception as exc:
            emit_failed = True
            emit_failure_type = type(exc).__name__
        else:
            emit_failure_type = "structured_append_not_succeeded"
        if emit_failed:
            log_error(
                "[SCANNER_PRUNE_BBO_OBSERVER] receipt emit failed "
                f"episode={episode_id} sample={sample_index} "
                f"error={emit_failure_type}"
            )
        with self._condition:
            if emit_failed:
                self._receipt_emit_failure_count += 1
            if status == "captured":
                self._captured_sample_count += 1
            else:
                self._request_gap_count += 1
            current = self._episodes.get(episode_id)
            if current is not None:
                current["completed_sample_count"] = (
                    int(current.get("completed_sample_count") or 0) + 1
                )
                if terminal_sample:
                    current["state"] = "completed"
                    current["completed_epoch"] = request_completed_epoch
            self._trim_retained_locked()

    def stop(self, *, timeout_sec: float = 1.0) -> None:
        with self._condition:
            self._stop_requested = True
            self._condition.notify_all()
            worker = self._worker
        if worker and worker.is_alive():
            worker.join(timeout=max(0.0, float(timeout_sec)))


_GLOBAL_LOCK = threading.Lock()
_GLOBAL_COLLECTOR: PrunedCandidateBBOCollector | None = None


def configure_global_collector(token: str) -> PrunedCandidateBBOCollector | None:
    """Configure the process-local observer without affecting scanner policy."""

    normalized = str(token or "").strip()
    if not normalized:
        return None
    global _GLOBAL_COLLECTOR
    with _GLOBAL_LOCK:
        if _GLOBAL_COLLECTOR is None:
            _GLOBAL_COLLECTOR = PrunedCandidateBBOCollector(normalized)
            configuration_status = "collector_created"
        else:
            _GLOBAL_COLLECTOR.update_token(normalized)
            configuration_status = "collector_token_refreshed"
        collector = _GLOBAL_COLLECTOR
    configured_epoch = time.time()
    receipt_fields = collector.configuration_receipt_fields(
        configuration_status=configuration_status,
        configured_epoch=configured_epoch,
    )
    emitted = False
    failure_type = "structured_append_not_succeeded"
    try:
        emit_result = emit_pipeline_event(
            "ENTRY_PIPELINE",
            "scanner_prune_bbo_observer",
            "-",
            "scalping_scanner_prune_bbo_source_loaded",
            fields=receipt_fields,
        )
        emitted = not (
            isinstance(emit_result, Mapping)
            and emit_result.get("structured_append_succeeded") is False
        )
    except Exception as exc:
        failure_type = type(exc).__name__
    collector.record_configuration_receipt_result(emitted=emitted)
    if not emitted:
        log_error(
            "[SCANNER_PRUNE_BBO_OBSERVER] configuration receipt emit failed "
            f"pid={os.getpid()} error={failure_type}"
        )
    return collector


def offer_global_prune_observation(
    target: Mapping[str, Any],
    *,
    reason: str,
    scan_generation_id: str,
    scan_rank: int,
    ranked_candidate_count: int,
    venue_fields: Mapping[str, Any],
    observed_epoch: float | None = None,
) -> dict[str, Any]:
    with _GLOBAL_LOCK:
        collector = _GLOBAL_COLLECTOR
    if collector is None:
        normalized_reason = str(reason or "").strip()
        eligible = normalized_reason in ELIGIBLE_PRUNE_REASONS
        if not eligible:
            return {"eligible": False, "schedule_status": "ineligible_prune_reason"}
        return {
            "eligible": True,
            "scanner_prune_observer_schedule_status": "collector_not_configured",
            "scanner_prune_observer_reason": normalized_reason,
            "scanner_prune_observer_episode_id": "",
            "scanner_prune_observer_configured": False,
            "scanner_prune_observer_configuration_receipt_status": "not_emitted",
            "scanner_prune_observer_market_data_request_effect": True,
            **METRIC_CONTRACT,
        }
    try:
        return collector.offer(
            target,
            reason=reason,
            scan_generation_id=scan_generation_id,
            scan_rank=scan_rank,
            ranked_candidate_count=ranked_candidate_count,
            venue_fields=venue_fields,
            observed_epoch=observed_epoch,
        )
    except Exception as exc:
        return {
            "eligible": str(reason or "") in ELIGIBLE_PRUNE_REASONS,
            "scanner_prune_observer_schedule_status": (
                f"source_only_offer_error:{type(exc).__name__}"
            ),
            "scanner_prune_observer_market_data_request_effect": True,
            **METRIC_CONTRACT,
        }


__all__ = [
    "ELIGIBLE_PRUNE_REASONS",
    "MAX_ANCHOR_TO_SCHEDULE_DELAY_SEC",
    "METRIC_CONTRACT",
    "PrunedCandidateBBOCollector",
    "SAMPLE_OFFSETS_SEC",
    "configure_global_collector",
    "offer_global_prune_observation",
]
