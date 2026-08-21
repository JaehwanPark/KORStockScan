"""Promote verified symbol-specific widget research to next-day runtime policy.

The bridge is intentionally separate from the low-price two-leg owner.  It
only accepts a complete clean-baseline research report, emits an exact-date
policy, and never starts a process or calls an account/order API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.monitoring.widget_symbol_signal_policy_research import (
    AUTHORITY as RESEARCH_AUTHORITY,
    CLEAN_BASELINE_DATE,
    METRIC_CONTRACT as RESEARCH_METRIC_CONTRACT,
    OWNER,
    REPORT_SCHEMA,
    SYMBOLS,
    resolve_completed_research_end_date,
)
from src.engine.monitoring.samsung_widget_contract import KST
from src.trading.order.episode_quantity import EPISODE_LEG_QUANTITY
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

POLICY_SCHEMA = "widget_symbol_runtime_policy_v1"
POLICY_AUTHORITY = "postclose_widget_symbol_runtime_policy_v1"
DEFAULT_RESEARCH_DIR = DATA_DIR / "report" / "widget_symbol_signal_policy_research"
DEFAULT_POLICY_DIR = DATA_DIR / "runtime" / "widget_symbol_runtime_policy"
DEFAULT_APPLY_REPORT_DIR = DATA_DIR / "report" / "widget_symbol_runtime_policy_apply"
POLICY_PREFIX = "widget_symbol_runtime_policy"
SUPPORTED_RESEARCH_SCHEMAS = {
    "widget_symbol_signal_policy_research_v2",
    REPORT_SCHEMA,
}

OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "69642586f7d84ba9fd8a6faf1f1537c7fda6568b",
    "retrieved_at_kst": "2026-08-13T10:18:06+09:00",
    "inspected_paths": [
        "kiwoom_docs/종목정보.md",
        "kiwoom_docs/시세.md",
        "kiwoom_docs/차트.md",
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "kiwoom/core",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_contracts": [
        "POST /api/dostk/stkinfo; api-id=ka10001",
        "POST /api/dostk/mrkcond; api-id=ka10004",
        "POST /api/dostk/chart; api-id=ka10064",
        "POST /api/dostk/chart; api-id=ka10080",
        "POST /api/dostk/chart; api-id=ka20005",
        "POST /api/dostk/mrkcond; api-id=ka90008",
    ],
}

METRIC_CONTRACT = {
    "metric_role": "bounded_widget_symbol_runtime_policy_apply",
    "decision_authority": POLICY_AUTHORITY,
    "window_policy": "exact_next_krx_trading_date_only",
    "sample_floor": RESEARCH_METRIC_CONTRACT["sample_floor"],
    "primary_decision_metric": "notional_weighted_ev_pct",
    "source_quality_gate": [
        "complete_clean_baseline_research_report",
        "holdout_pass_widget_signal_policy_candidate",
        "positive_calibration_halves_and_holdout_ev",
        "exact_date_policy_loader_round_trip",
    ],
    "forbidden_uses": [
        "cross_symbol_policy_transfer",
        "same_day_runtime_apply",
        "stale_policy_auto_extension",
        "low_price_two_leg_owner_mutation",
        "account_or_order_api",
        "token_issue_or_refresh",
        "process_control",
        "broker_guard_bypass",
    ],
}


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def next_krx_trading_date(value: date) -> date:
    candidate = value + timedelta(days=1)
    while not is_krx_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def _positive_metric(payload: dict[str, Any], key: str) -> bool:
    try:
        return float(payload.get(key)) > 0.0
    except (TypeError, ValueError):
        return False


def _high_entry_cap_evidence_valid(result: dict[str, Any], max_entries: int) -> bool:
    if max_entries < 4:
        return True
    comparisons = result.get("entry_cap_comparison")
    if not isinstance(comparisons, dict):
        return False
    for window in (
        "calibration",
        "calibration_first_half",
        "calibration_second_half",
        "holdout",
    ):
        comparison = comparisons.get(window)
        if not isinstance(comparison, dict):
            return False
        for cap in range(4, max_entries + 1):
            evidence = comparison.get(str(cap))
            incremental = (
                evidence.get("incremental") if isinstance(evidence, dict) else None
            )
            if (
                not isinstance(evidence, dict)
                or evidence.get("incremental_ev_positive") is not True
                or not isinstance(incremental, dict)
                or int(incremental.get("episode_count") or 0) < 1
                or not _positive_metric(incremental, "notional_weighted_ev_pct")
            ):
                return False
    return True


def _payload_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _normalized_selected_parameters(selected: object) -> dict[str, Any] | None:
    if not isinstance(selected, dict):
        return None
    required = {
        "segment",
        "lookback_bars",
        "drawdown_pct",
        "near_low_pct",
        "reclaim_ticks",
        "target_bps",
        "max_completed_entries_per_day",
        "setup_valid_bars",
        "reentry_cooldown_bars",
        "force_flat_time",
    }
    optional = {
        "anchor_mode",
        "minimum_history_bars",
        "max_reclaim_chase_ticks",
    }
    if not required.issubset(selected) or set(selected) - required - optional:
        return None
    try:
        lookback = int(selected["lookback_bars"])
        drawdown = float(selected["drawdown_pct"])
        near_low = float(selected["near_low_pct"])
        reclaim_ticks = int(selected["reclaim_ticks"])
        target_bps = int(selected["target_bps"])
        max_entries = int(selected["max_completed_entries_per_day"])
        setup_valid = int(selected["setup_valid_bars"])
        cooldown = int(selected["reentry_cooldown_bars"])
        minimum_history = int(selected.get("minimum_history_bars", lookback))
        max_reclaim_chase_ticks = int(selected.get("max_reclaim_chase_ticks", 2))
    except (TypeError, ValueError):
        return None
    segment = str(selected["segment"])
    anchor_mode = str(selected.get("anchor_mode", "rolling"))
    segment_windows = {
        "morning": ("09:03:00", "10:30:00"),
        "midday": ("10:30:00", "13:30:00"),
        "afternoon": ("13:30:00", "15:00:00"),
    }
    if (
        segment not in segment_windows
        or lookback not in {15, 30, 45}
        or anchor_mode not in {"rolling", "session"}
        or not 2 <= minimum_history <= lookback
        or max_reclaim_chase_ticks not in {2, 6}
        or (max_reclaim_chase_ticks != 2 and segment != "morning")
        or not 0.5 <= drawdown <= 2.0
        or not 0.2 <= near_low <= 0.75
        or reclaim_ticks not in {1, 2}
        or not 30 <= target_bps <= 100
        or not 1 <= max_entries <= 5
        or setup_valid != 5
        or cooldown != 10
        or str(selected["force_flat_time"]) != "15:19:00"
    ):
        return None
    start_time, end_time = segment_windows[segment]
    signal_policy = {
        "segment": segment,
        "segment_start_time": start_time,
        "segment_end_time": end_time,
        "lookback_bars": lookback,
        "drawdown_pct": drawdown,
        "near_low_pct": near_low,
        "reclaim_ticks": reclaim_ticks,
        "target_bps": target_bps,
        "setup_valid_bars": setup_valid,
        "reentry_cooldown_bars": cooldown,
        "force_flat_time": "15:19:00",
    }
    if "anchor_mode" in selected:
        signal_policy["anchor_mode"] = anchor_mode
    if "minimum_history_bars" in selected:
        signal_policy["minimum_history_bars"] = minimum_history
    if "max_reclaim_chase_ticks" in selected:
        signal_policy["max_reclaim_chase_ticks"] = max_reclaim_chase_ticks
    return {
        "signal_policy": signal_policy,
        "execution_policy": {
            "session": "KRX_REGULAR",
            "market_venue": "KRX",
            "allowed_entry_sessions": ["KRX_REGULAR"],
            "allowed_entry_venues": ["KRX"],
            "allowed_entry_states": ["ENTRY_CAUTION", "ENTRY_READY"],
            "leg_quantity_each": EPISODE_LEG_QUANTITY,
            "add_trigger_bps_from_initial_fill": [],
            "take_profit_bps_from_equal_share_average": target_bps,
            "max_completed_entries_per_day": max_entries,
            "reentry_cooldown_minutes": cooldown,
            "new_entry_cutoff_time": end_time,
            "force_flat_at_session_end": True,
            "force_exit_time": "15:19:00",
            "overnight_forbidden": True,
            "source_final_exit_action": "sell_own_filled_quantity",
        },
    }


def _validated_selected_policy(result: object) -> dict[str, Any] | None:
    if not isinstance(result, dict):
        return None
    calibration = result.get("calibration")
    first = result.get("calibration_first_half")
    second = result.get("calibration_second_half")
    holdout = result.get("holdout")
    if not all(
        isinstance(value, dict) for value in (calibration, first, second, holdout)
    ):
        return None
    selected = result.get("selected_policy")
    try:
        max_entries = int(
            selected.get("max_completed_entries_per_day")
            if isinstance(selected, dict)
            else 0
        )
    except (TypeError, ValueError):
        max_entries = 0
    if (
        result.get("decision") != "holdout_pass_widget_signal_policy_candidate"
        or result.get("runtime_effect") is not False
        or result.get("allowed_runtime_apply") is not False
        or not _positive_metric(calibration, "notional_weighted_ev_pct")
        or not _positive_metric(first, "notional_weighted_ev_pct")
        or not _positive_metric(second, "notional_weighted_ev_pct")
        or not _positive_metric(holdout, "notional_weighted_ev_pct")
        or int(holdout.get("episode_count") or 0) < 4
        or not _high_entry_cap_evidence_valid(result, max_entries)
    ):
        return None
    return _normalized_selected_parameters(selected)


def _validated_observation_policy(result: object) -> dict[str, Any] | None:
    """Return a source-only policy for prospective exact-data collection."""

    if not isinstance(result, dict) or result.get("runtime_effect") is not False:
        return None
    selected = result.get("selected_policy")
    if not isinstance(selected, dict):
        diagnostic = result.get("best_diagnostic_candidate")
        selected = (
            diagnostic.get("parameters") if isinstance(diagnostic, dict) else None
        )
    normalized = _normalized_selected_parameters(selected)
    if normalized is None:
        return None
    return {
        "signal_policy": normalized["signal_policy"],
        "observation_authority": "prospective_exact_observation_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def build_policy(
    research: dict[str, Any], *, evidence_report_path: Path | None = None
) -> dict[str, Any]:
    if (
        research.get("schema") not in SUPPORTED_RESEARCH_SCHEMAS
        or research.get("status") != "complete"
        or research.get("start_date") != CLEAN_BASELINE_DATE.isoformat()
        or research.get("runtime_effect") is not False
        or research.get("allowed_runtime_apply") is not False
        or research.get("actual_order_submitted") is not False
        or research.get("broker_order_forbidden") is not True
        or (research.get("owner_contract") or {}).get("owner") != OWNER
        or (research.get("owner_contract") or {}).get("authority") != RESEARCH_AUTHORITY
        or research.get("metric_contract") != RESEARCH_METRIC_CONTRACT
    ):
        raise ValueError("widget_symbol_research_contract_invalid")
    source_meta = research.get("source_meta")
    if not isinstance(source_meta, dict) or any(
        not isinstance(source_meta.get(symbol), dict)
        or source_meta[symbol].get("symbol") != symbol
        or source_meta[symbol].get("request_code") != symbol
        or source_meta[symbol].get("market") != "KRX_regular"
        or source_meta[symbol].get("source_quality_status") != "PASS"
        for symbol in SYMBOLS
    ):
        raise ValueError("widget_symbol_research_krx_source_provenance_invalid")
    source_date = date.fromisoformat(str(research.get("end_date") or ""))
    effective_date = next_krx_trading_date(source_date)
    evidence_path = evidence_report_path or (
        DEFAULT_RESEARCH_DIR
        / f"widget_symbol_signal_policy_research_{source_date.isoformat()}.json"
    )
    symbols: dict[str, Any] = {}
    observation_symbols: dict[str, Any] = {}
    for symbol, name in SYMBOLS.items():
        result = (research.get("symbols") or {}).get(symbol)
        if research.get("schema") == REPORT_SCHEMA and isinstance(result, dict):
            selected_contract = result.get("selected_policy")
            if not isinstance(selected_contract, dict):
                diagnostic = result.get("best_diagnostic_candidate")
                selected_contract = (
                    diagnostic.get("parameters")
                    if isinstance(diagnostic, dict)
                    else None
                )
            if isinstance(selected_contract, dict) and not {
                "anchor_mode",
                "minimum_history_bars",
                "max_reclaim_chase_ticks",
            }.issubset(selected_contract):
                raise ValueError("widget_symbol_research_v3_parameters_missing")
        observation = _validated_observation_policy(result)
        if observation is not None:
            observation_symbols[symbol] = {"name": name, **observation}
        selected = _validated_selected_policy(result)
        if selected is None:
            continue
        symbols[symbol] = {
            "name": name,
            **selected,
            "evidence": {
                "calibration": result["calibration"],
                "calibration_first_half": result["calibration_first_half"],
                "calibration_second_half": result["calibration_second_half"],
                "holdout": {
                    key: value
                    for key, value in result["holdout"].items()
                    if key != "episodes"
                },
                "entry_cap_comparison": result.get("entry_cap_comparison"),
            },
        }
    return {
        "schema": POLICY_SCHEMA,
        "status": (
            "verified"
            if symbols
            else "observation_only" if observation_symbols else "no_ready_policy"
        ),
        "policy_version": (
            f"widget_symbol_runtime_policy_{effective_date.isoformat()}_"
            f"from_{source_date.isoformat()}"
        ),
        "source_target_date": source_date.isoformat(),
        "effective_date": effective_date.isoformat(),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "evidence_report_path": str(evidence_path),
        "evidence_report_sha256": _payload_sha256(research),
        "source_quality_status": "PASS",
        "official_reference": OFFICIAL_REFERENCE,
        "authority": POLICY_AUTHORITY,
        "owner": OWNER,
        "symbols": symbols,
        "observation_symbols": observation_symbols,
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": bool(symbols),
        "observation_runtime_effect": bool(observation_symbols),
        "actual_order_submitted": False,
        "broker_order_forbidden": not bool(symbols),
    }


class WidgetSymbolRuntimePolicyLoader:
    """Load only a verified policy whose effective date is exactly today."""

    def __init__(
        self,
        policy_dir: Path = DEFAULT_POLICY_DIR,
        *,
        research_dir: Path = DEFAULT_RESEARCH_DIR,
    ) -> None:
        self.policy_dir = policy_dir
        self.research_dir = research_dir

    def resolve_all(self, *, observed_date: date) -> dict[str, dict[str, Any]]:
        path = self.policy_dir / f"{POLICY_PREFIX}_{observed_date.isoformat()}.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != POLICY_SCHEMA
            or payload.get("status") != "verified"
            or payload.get("effective_date") != observed_date.isoformat()
            or payload.get("authority") != POLICY_AUTHORITY
            or payload.get("owner") != OWNER
            or payload.get("metric_contract") != METRIC_CONTRACT
            or payload.get("runtime_effect") is not True
            or payload.get("actual_order_submitted") is not False
            or payload.get("broker_order_forbidden") is not False
            or payload.get("source_quality_status") != "PASS"
        ):
            return {}
        try:
            source_date = date.fromisoformat(
                str(payload.get("source_target_date") or "")
            )
        except ValueError:
            return {}
        if (
            source_date >= observed_date
            or next_krx_trading_date(source_date) != observed_date
        ):
            return {}
        evidence_path = Path(str(payload.get("evidence_report_path") or ""))
        if not evidence_path.is_absolute():
            evidence_path = self.research_dir / evidence_path.name
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if not isinstance(evidence, dict) or _payload_sha256(evidence) != str(
            payload.get("evidence_report_sha256") or ""
        ):
            return {}
        try:
            reconstructed = build_policy(evidence, evidence_report_path=evidence_path)
        except (TypeError, ValueError):
            return {}
        if reconstructed != payload:
            return {}
        symbols = payload.get("symbols")
        if not isinstance(symbols, dict):
            return {}
        resolved: dict[str, dict[str, Any]] = {}
        for symbol, value in symbols.items():
            if symbol not in SYMBOLS or not isinstance(value, dict):
                continue
            raw_signal_policy = value.get("signal_policy")
            raw_signal_policy = (
                raw_signal_policy if isinstance(raw_signal_policy, dict) else {}
            )
            signal_keys = {
                "segment",
                "lookback_bars",
                "drawdown_pct",
                "near_low_pct",
                "reclaim_ticks",
                "target_bps",
                "setup_valid_bars",
                "reentry_cooldown_bars",
                "force_flat_time",
                "anchor_mode",
                "minimum_history_bars",
                "max_reclaim_chase_ticks",
            }
            selected = {
                "selected_policy": {
                    **{
                        key: raw_signal_policy[key]
                        for key in signal_keys
                        if key in raw_signal_policy
                    },
                    "max_completed_entries_per_day": (
                        value.get("execution_policy") or {}
                    ).get("max_completed_entries_per_day"),
                },
                "calibration": (value.get("evidence") or {}).get("calibration"),
                "calibration_first_half": (value.get("evidence") or {}).get(
                    "calibration_first_half"
                ),
                "calibration_second_half": (value.get("evidence") or {}).get(
                    "calibration_second_half"
                ),
                "holdout": (value.get("evidence") or {}).get("holdout"),
                "entry_cap_comparison": (value.get("evidence") or {}).get(
                    "entry_cap_comparison"
                ),
                "decision": "holdout_pass_widget_signal_policy_candidate",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
            normalized = _validated_selected_policy(selected)
            if normalized is None or normalized["signal_policy"] != value.get(
                "signal_policy"
            ):
                continue
            execution = normalized["execution_policy"]
            if execution != value.get("execution_policy"):
                continue
            resolved[symbol] = {
                "symbol": symbol,
                "name": SYMBOLS[symbol],
                "policy_id": str(payload["policy_version"]),
                "source_target_date": source_date.isoformat(),
                "effective_date": observed_date.isoformat(),
                "policy_path": str(path),
                "signal_policy": normalized["signal_policy"],
                "execution_policy": normalized["execution_policy"],
                "authority": POLICY_AUTHORITY,
                "official_reference": OFFICIAL_REFERENCE,
                "evidence_window": (
                    f"{CLEAN_BASELINE_DATE.isoformat()}_{source_date.isoformat()}"
                ),
                "evidence_artifact": str(
                    DEFAULT_RESEARCH_DIR
                    / f"widget_symbol_signal_policy_research_{source_date.isoformat()}.json"
                ),
            }
        return resolved

    def resolve_observation_all(
        self, *, observed_date: date
    ) -> dict[str, dict[str, Any]]:
        """Load exact-date source-only policies without granting order authority."""

        path = self.policy_dir / f"{POLICY_PREFIX}_{observed_date.isoformat()}.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != POLICY_SCHEMA
            or payload.get("status") not in {"verified", "observation_only"}
            or payload.get("effective_date") != observed_date.isoformat()
            or payload.get("authority") != POLICY_AUTHORITY
            or payload.get("owner") != OWNER
            or payload.get("metric_contract") != METRIC_CONTRACT
            or payload.get("observation_runtime_effect") is not True
            or payload.get("actual_order_submitted") is not False
            or payload.get("broker_order_forbidden")
            is not (not bool(payload.get("symbols")))
            or payload.get("source_quality_status") != "PASS"
        ):
            return {}
        evidence_path = Path(str(payload.get("evidence_report_path") or ""))
        if not evidence_path.is_absolute():
            evidence_path = self.research_dir / evidence_path.name
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            source_date = date.fromisoformat(
                str(payload.get("source_target_date") or "")
            )
        except (OSError, ValueError):
            return {}
        if (
            source_date >= observed_date
            or next_krx_trading_date(source_date) != observed_date
            or _payload_sha256(evidence)
            != str(payload.get("evidence_report_sha256") or "")
        ):
            return {}
        try:
            reconstructed = build_policy(evidence, evidence_report_path=evidence_path)
        except (TypeError, ValueError):
            return {}
        if reconstructed != payload:
            return {}
        resolved: dict[str, dict[str, Any]] = {}
        observation_symbols = payload.get("observation_symbols")
        if not isinstance(observation_symbols, dict):
            return {}
        for symbol, value in observation_symbols.items():
            if symbol not in SYMBOLS or not isinstance(value, dict):
                continue
            result = (evidence.get("symbols") or {}).get(symbol)
            normalized = _validated_observation_policy(result)
            if normalized is None or normalized["signal_policy"] != value.get(
                "signal_policy"
            ):
                continue
            resolved[symbol] = {
                "symbol": symbol,
                "name": SYMBOLS[symbol],
                "policy_id": str(payload["policy_version"]),
                "source_target_date": source_date.isoformat(),
                "effective_date": observed_date.isoformat(),
                "policy_path": str(path),
                "signal_policy": normalized["signal_policy"],
                "authority": "prospective_exact_observation_only",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        return resolved


def write_outputs(
    research: dict[str, Any],
    *,
    policy_dir: Path = DEFAULT_POLICY_DIR,
    apply_report_dir: Path = DEFAULT_APPLY_REPORT_DIR,
    evidence_report_path: Path | None = None,
) -> tuple[Path, Path, dict[str, Any]]:
    policy = build_policy(research, evidence_report_path=evidence_report_path)
    effective_date = date.fromisoformat(policy["effective_date"])
    policy_path = policy_dir / f"{POLICY_PREFIX}_{effective_date.isoformat()}.json"
    _atomic_write(policy_path, policy)
    loaded = WidgetSymbolRuntimePolicyLoader(policy_dir).resolve_all(
        observed_date=effective_date
    )
    observed = WidgetSymbolRuntimePolicyLoader(policy_dir).resolve_observation_all(
        observed_date=effective_date
    )
    expected = set(policy["symbols"]) if policy["status"] == "verified" else set()
    verification = {
        "status": (
            "pass"
            if set(loaded) == expected
            and set(observed) == set(policy["observation_symbols"])
            else "fail"
        ),
        "expected_symbols": sorted(expected),
        "loaded_symbols": sorted(loaded),
        "expected_observation_symbols": sorted(policy["observation_symbols"]),
        "loaded_observation_symbols": sorted(observed),
        "policy_path": str(policy_path),
    }
    apply_report = {
        "schema": "widget_symbol_runtime_policy_apply_report_v1",
        "status": "complete" if verification["status"] == "pass" else "failed",
        "source_target_date": policy["source_target_date"],
        "effective_date": policy["effective_date"],
        "selected_symbols": sorted(expected),
        "withheld_symbols": sorted(set(SYMBOLS) - expected),
        "policy_status": policy["status"],
        "policy_verification": verification,
        "metric_contract": METRIC_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
    }
    report_path = apply_report_dir / (
        f"widget_symbol_runtime_policy_apply_{policy['source_target_date']}.json"
    )
    _atomic_write(report_path, apply_report)
    if verification["status"] != "pass":
        raise RuntimeError("widget_symbol_runtime_policy_round_trip_failed")
    return policy_path, report_path, apply_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date")
    parser.add_argument("--research-dir", type=Path, default=DEFAULT_RESEARCH_DIR)
    parser.add_argument("--policy-dir", type=Path, default=DEFAULT_POLICY_DIR)
    parser.add_argument(
        "--apply-report-dir", type=Path, default=DEFAULT_APPLY_REPORT_DIR
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-active", action="store_true")
    args = parser.parse_args(argv)
    if args.check_active:
        target = (
            date.fromisoformat(args.target_date)
            if args.target_date
            else datetime.now(KST).date()
        )
        active = WidgetSymbolRuntimePolicyLoader(
            args.policy_dir
        ).resolve_observation_all(observed_date=target)
        print(
            json.dumps(
                {
                    "effective_date": target.isoformat(),
                    "active_symbols": sorted(active),
                },
                ensure_ascii=False,
            )
        )
        return 0 if active else 3
    source_date = (
        date.fromisoformat(args.target_date)
        if args.target_date
        else resolve_completed_research_end_date()
    )
    research_path = (
        args.research_dir
        / f"widget_symbol_signal_policy_research_{source_date.isoformat()}.json"
    )
    research = json.loads(research_path.read_text(encoding="utf-8"))
    policy = build_policy(research, evidence_report_path=research_path)
    result: dict[str, Any] = {
        "source_target_date": policy["source_target_date"],
        "effective_date": policy["effective_date"],
        "selected_symbols": sorted(policy["symbols"]),
        "policy_status": policy["status"],
        "runtime_effect": False,
    }
    if args.write:
        policy_path, report_path, apply_report = write_outputs(
            research,
            policy_dir=args.policy_dir,
            apply_report_dir=args.apply_report_dir,
            evidence_report_path=research_path,
        )
        result.update(
            {
                "policy_path": str(policy_path),
                "report_path": str(report_path),
                "verification": apply_report["policy_verification"],
            }
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
