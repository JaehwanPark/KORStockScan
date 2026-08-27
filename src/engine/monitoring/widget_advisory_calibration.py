"""Build verified next-trading-day calibration for read-only widget signals.

The first locally source-qualified 10-minute outcome enters cumulative
calibration.  The only bounded axis is the actionable 10-second confirmation
count (2 or 3).  This module never calls Kiwoom, issues tokens, reads accounts,
submits orders, controls bots, or mutates the real-trading runtime.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.monitoring import samsung_widget_advisory_evaluation as evaluation
from src.engine.monitoring.doosan_widget_contract import (
    DEFAULT_OBSERVATION_DIR as DOOSAN_OBSERVATION_DIR,
    DOOSAN_CODE,
    DOOSAN_NAME,
    STRATEGY_PROFILE as DOOSAN_STRATEGY_PROFILE,
)
from src.engine.monitoring.hanwha_ocean_widget_contract import (
    DEFAULT_OBSERVATION_DIR as HANWHA_OBSERVATION_DIR,
    HANWHA_OCEAN_CODE,
    HANWHA_OCEAN_NAME,
    STRATEGY_PROFILE as HANWHA_STRATEGY_PROFILE,
)
from src.engine.monitoring.samsung_widget_contract import (
    DEFAULT_OBSERVATION_DIR as SAMSUNG_OBSERVATION_DIR,
    KST,
    NXT_AFTERMARKET_END,
    SAMSUNG_CODE,
    SAMSUNG_NAME,
    previous_krx_trading_date,
)
from src.engine.monitoring.widget_advisory_calibration_policy import (
    DEFAULT_POLICY_DIR,
    MAX_REQUIRED_CONFIRMATIONS,
    MIN_REQUIRED_CONFIRMATIONS,
    POLICY_AUTHORITY,
    POLICY_FILE_PREFIX,
    POLICY_SCHEMA,
    WidgetCalibrationPolicyLoader,
)
from src.engine.monitoring.widget_comparison_cost import (
    comparison_cost_contract,
    round_trip_cost_pct,
)
from src.utils.market_day import is_krx_trading_day

CLEAN_BASELINE_DATE = date(2026, 6, 5)
CALIBRATION_HORIZON_MINUTES = 10
DEFAULT_OUTPUT_DIR = Path("data/report/widget_advisory_calibration")
DAILY_STATUS_ALLOWLIST = {"observed", "no_mature_actionable_sample"}

CALIBRATION_CONTRACT = {
    "metric_role": "bounded_widget_signal_calibration",
    "decision_authority": POLICY_AUTHORITY,
    "window_policy": (
        "clean_baseline_cumulative_from_first_locally_qualified_10m_outcome"
    ),
    "sample_floor": "one_decisive_target_or_adverse_first_outcome",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "daily_report_contract_and_exact_entry_touch_with_local_80pct_coverage"
    ),
    "forbidden_uses": [
        "real_order_submission",
        "account_or_quantity_decision",
        "real_trading_runtime_threshold",
        "provider_or_token_route_change",
        "bot_process_control",
        "hard_safety_or_broker_guard_bypass",
        "automatic_collector_creation_or_service_start",
    ],
}


@dataclass(frozen=True)
class WidgetSpec:
    symbol: str
    name: str
    strategy_profile: str
    observation_dir: Path
    observation_prefix: str
    evaluation_dir: Path
    evaluation_prefix: str
    expected_sessions: dict[str, int]
    target_return_pct: float


WIDGET_SPECS = (
    WidgetSpec(
        symbol=SAMSUNG_CODE,
        name=SAMSUNG_NAME,
        strategy_profile="SAMSUNG_ALL_SESSION_DYNAMIC_STRUCTURE_V1",
        observation_dir=SAMSUNG_OBSERVATION_DIR,
        observation_prefix="samsung_widget_advisory",
        evaluation_dir=Path("data/report/samsung_widget_advisory_evaluation"),
        evaluation_prefix="samsung_widget_advisory_evaluation",
        expected_sessions=evaluation.SESSION_EXPECTED_MINUTES,
        target_return_pct=0.5,
    ),
    WidgetSpec(
        symbol=DOOSAN_CODE,
        name=DOOSAN_NAME,
        strategy_profile=DOOSAN_STRATEGY_PROFILE,
        observation_dir=DOOSAN_OBSERVATION_DIR,
        observation_prefix="doosan_widget_advisory",
        evaluation_dir=Path("data/report/doosan_widget_advisory_evaluation"),
        evaluation_prefix="doosan_widget_advisory_evaluation",
        expected_sessions={"KRX_REGULAR": 390},
        target_return_pct=1.0,
    ),
    WidgetSpec(
        symbol=HANWHA_OCEAN_CODE,
        name=HANWHA_OCEAN_NAME,
        strategy_profile=HANWHA_STRATEGY_PROFILE,
        observation_dir=HANWHA_OBSERVATION_DIR,
        observation_prefix="hanwha_ocean_widget_advisory",
        evaluation_dir=Path("data/report/hanwha_ocean_widget_advisory_evaluation"),
        evaluation_prefix="hanwha_ocean_widget_advisory_evaluation",
        expected_sessions={"KRX_REGULAR": 390},
        target_return_pct=1.0,
    ),
)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _positive_int(value: object) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _next_krx_trading_date(target_date: date) -> date:
    candidate = target_date + timedelta(days=1)
    while not is_krx_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def _resolve_default_target_date(*, now: datetime | None = None) -> date:
    current = (now or datetime.now(KST)).astimezone(KST)
    if (
        is_krx_trading_day(current.date())
        and current.time().replace(tzinfo=None) >= NXT_AFTERMARKET_END
    ):
        return current.date()
    return previous_krx_trading_date(current.date())


def _daily_report_path(spec: WidgetSpec, target_date: date) -> Path:
    return spec.evaluation_dir / (
        f"{spec.evaluation_prefix}_{target_date.isoformat()}.json"
    )


def _observation_path(spec: WidgetSpec, target_date: date) -> Path:
    return spec.observation_dir / (
        f"{spec.observation_prefix}_{target_date.strftime('%Y%m%d')}.jsonl"
    )


def build_and_write_evaluation(
    spec: WidgetSpec,
    *,
    target_date: date,
    write: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = evaluation._load_rows(_observation_path(spec, target_date))
    daily = evaluation.build_daily_evaluation(
        rows,
        target_date=target_date,
        symbol_code=spec.symbol,
        expected_sessions=spec.expected_sessions,
        target_return_pct=spec.target_return_pct,
    )
    if write:
        _atomic_write(_daily_report_path(spec, target_date), daily)
    rolling = evaluation.build_rolling_report(
        spec.evaluation_dir,
        as_of_date=target_date,
        report_prefix=spec.evaluation_prefix,
        symbol_code=spec.symbol,
        target_return_pct=spec.target_return_pct,
    )
    if write:
        _atomic_write(
            spec.evaluation_dir / f"{spec.evaluation_prefix}_rolling_60d.json",
            rolling,
        )
    return daily, rolling


def _daily_report_issue(
    report: object,
    *,
    spec: WidgetSpec,
    target_date: date,
) -> str | None:
    if not isinstance(report, dict):
        return "report_not_object"
    if report.get("schema_version") != 2:
        return "schema_version_mismatch"
    if report.get("symbol") != spec.symbol:
        return "symbol_mismatch"
    if report.get("target_date") != target_date.isoformat():
        return "target_date_mismatch"
    if report.get("status") not in DAILY_STATUS_ALLOWLIST:
        return "status_not_complete"
    if _positive_int(report.get("source_row_count")) is None:
        return "source_rows_missing"
    if (
        report.get("runtime_effect") is not False
        or report.get("actual_order_submitted") is not False
        or report.get("broker_order_forbidden") is not True
    ):
        return "authority_contract_mismatch"
    metric_contract = report.get("metric_contract")
    if (
        not isinstance(metric_contract, dict)
        or metric_contract.get("decision_authority")
        != "widget_advisory_evaluation_only"
    ):
        return "metric_contract_mismatch"
    try:
        target_return_pct = float(report.get("target_return_pct"))
    except (TypeError, ValueError):
        return "target_policy_missing_or_invalid"
    if not math.isfinite(target_return_pct):
        return "target_policy_missing_or_invalid"
    if abs(target_return_pct - spec.target_return_pct) > 1e-9:
        return "target_policy_mismatch"
    try:
        fallback_adverse_pct = float(report.get("fallback_adverse_pct"))
    except (TypeError, ValueError):
        return "adverse_policy_missing_or_invalid"
    if not math.isfinite(fallback_adverse_pct):
        return "adverse_policy_missing_or_invalid"
    if abs(fallback_adverse_pct - evaluation.FALLBACK_ADVERSE_PCT) > 1e-9:
        return "adverse_policy_mismatch"
    return None


def _load_cumulative_outcomes(
    spec: WidgetSpec,
    *,
    through_date: date,
    exclude_date: date | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    outcomes: list[dict[str, Any]] = []
    excluded_reports: list[str] = []
    for path in sorted(spec.evaluation_dir.glob(f"{spec.evaluation_prefix}_*.json")):
        if path.name.endswith("_rolling_60d.json"):
            continue
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            report_date = date.fromisoformat(str(report.get("target_date") or ""))
        except (OSError, ValueError, AttributeError):
            excluded_reports.append(f"{path}:unreadable")
            continue
        if report_date < CLEAN_BASELINE_DATE or report_date > through_date:
            continue
        if exclude_date is not None and report_date == exclude_date:
            continue
        report_symbol = report.get("symbol")
        legacy_samsung_symbol = (
            spec.symbol == SAMSUNG_CODE
            and spec.evaluation_prefix == "samsung_widget_advisory_evaluation"
            and report_symbol in {None, ""}
        )
        metric_contract = report.get("metric_contract")
        try:
            report_target_return = float(report.get("target_return_pct"))
        except (TypeError, ValueError):
            report_target_return = (
                evaluation.TARGET_RETURN_PCT if legacy_samsung_symbol else None
            )
        try:
            report_fallback_adverse = float(report.get("fallback_adverse_pct"))
        except (TypeError, ValueError):
            report_fallback_adverse = (
                evaluation.FALLBACK_ADVERSE_PCT if legacy_samsung_symbol else None
            )
        if (
            report.get("schema_version") != 2
            or (report_symbol != spec.symbol and not legacy_samsung_symbol)
            or report.get("status") not in DAILY_STATUS_ALLOWLIST
            or _positive_int(report.get("source_row_count")) is None
            or not isinstance(metric_contract, dict)
            or metric_contract.get("decision_authority")
            != "widget_advisory_evaluation_only"
            or report_target_return is None
            or not math.isfinite(report_target_return)
            or abs(report_target_return - spec.target_return_pct) > 1e-9
            or report_fallback_adverse is None
            or not math.isfinite(report_fallback_adverse)
            or abs(report_fallback_adverse - evaluation.FALLBACK_ADVERSE_PCT) > 1e-9
            or report.get("runtime_effect") is not False
            or report.get("actual_order_submitted") is not False
            or report.get("broker_order_forbidden") is not True
        ):
            excluded_reports.append(f"{path}:contract_mismatch")
            continue
        outcomes.extend(_eligible_decisive_outcomes(report, source_report=str(path)))
    return outcomes, excluded_reports


def _eligible_decisive_outcomes(
    report: object,
    *,
    source_report: str,
) -> list[dict[str, Any]]:
    if not isinstance(report, dict):
        return []
    selected: list[dict[str, Any]] = []
    for outcome in report.get("outcomes", []):
        if not isinstance(outcome, dict):
            continue
        try:
            horizon = int(outcome.get("horizon_minutes") or 0)
        except (TypeError, ValueError):
            continue
        if (
            outcome.get("evaluation_eligible") is True
            and horizon == CALIBRATION_HORIZON_MINUTES
            and outcome.get("first_hit") in {"target_first", "adverse_first"}
        ):
            selected.append(
                {
                    **outcome,
                    "target_return_pct": report.get("target_return_pct"),
                    "fallback_adverse_pct": report.get("fallback_adverse_pct"),
                    "source_report": source_report,
                }
            )
    return selected


def _opportunity_net_return_proxy(outcome: dict[str, Any]) -> tuple[float, bool]:
    """Return a bounded 10-minute EV proxy and adverse-first recovery flag.

    A first adverse touch is not automatically a losing opportunity.  If the
    same mature window subsequently reaches the configured target MFE, retain
    its target EV.  Otherwise use the observed MAE (or the report's adverse
    policy when legacy evidence lacks MAE) and deduct round-trip cost.
    """

    try:
        target = float(outcome.get("target_return_pct"))
    except (TypeError, ValueError):
        target = 0.5
    if not math.isfinite(target):
        raise ValueError("widget_outcome_target_return_nonfinite")
    try:
        mfe = float(outcome.get("mfe_pct"))
    except (TypeError, ValueError):
        mfe = None
    recovered = bool(
        outcome.get("first_hit") == "adverse_first"
        and mfe is not None
        and math.isfinite(mfe)
        and mfe + 1e-9 >= target
    )
    raw_entry_at = outcome.get("entry_touched_at_kst") or outcome.get(
        "signal_observed_at_kst"
    )
    try:
        trade_date_source: date | datetime = datetime.fromisoformat(
            str(raw_entry_at or "")
        )
    except ValueError:
        source_name = Path(str(outcome.get("source_report") or "")).stem
        try:
            trade_date_source = date.fromisoformat(source_name.rsplit("_", 1)[-1])
        except ValueError as exc:
            raise ValueError("widget_outcome_trade_date_missing") from exc
    cost_pct = round_trip_cost_pct(trade_date_source)
    if outcome.get("first_hit") == "target_first" or recovered:
        return target - cost_pct, recovered
    try:
        adverse = float(outcome.get("mae_pct"))
    except (TypeError, ValueError):
        try:
            adverse = float(outcome.get("fallback_adverse_pct"))
        except (TypeError, ValueError):
            adverse = -0.3
    if not math.isfinite(adverse):
        raise ValueError("widget_outcome_adverse_return_nonfinite")
    return min(0.0, adverse) - cost_pct, recovered


def _bounded_step(previous: int, desired: int) -> int:
    desired = max(MIN_REQUIRED_CONFIRMATIONS, min(MAX_REQUIRED_CONFIRMATIONS, desired))
    if desired > previous:
        return previous + 1
    if desired < previous:
        return previous - 1
    return previous


def _select_session_policy(
    *,
    previous: dict[str, Any],
    outcomes: list[dict[str, Any]],
    session: str,
    daily_report_issue: str | None,
    cost_as_of_date: date,
) -> dict[str, Any]:
    previous_value = int(previous["required_actionable_confirmations"])
    session_outcomes = [
        row for row in outcomes if str(row.get("market_session") or "") == session
    ]
    target_first = sum(
        row.get("first_hit") == "target_first" for row in session_outcomes
    )
    adverse_first = sum(
        row.get("first_hit") == "adverse_first" for row in session_outcomes
    )
    decisive = target_first + adverse_first
    proxy_rows = [_opportunity_net_return_proxy(row) for row in session_outcomes]
    proxy_values = [value for value, _ in proxy_rows]
    adjusted_ev = sum(proxy_values) / len(proxy_values) if proxy_values else None
    recovered_adverse = sum(recovered for _, recovered in proxy_rows)
    selected = previous_value
    decision = "carry_forward_no_decisive_sample"
    reason = "no_source_qualified_decisive_10m_outcome"
    if daily_report_issue is not None:
        decision = "carry_forward_report_verification_failed"
        reason = daily_report_issue
    elif adjusted_ev is not None and adjusted_ev < 0:
        selected = _bounded_step(previous_value, MAX_REQUIRED_CONFIRMATIONS)
        decision = (
            "tighten_confirmation"
            if selected != previous_value
            else "hold_confirmation_at_upper_bound_negative_ev"
        )
        reason = "cumulative_10m_source_quality_adjusted_ev_negative"
    elif adjusted_ev is not None and adjusted_ev > 0:
        selected = _bounded_step(previous_value, MIN_REQUIRED_CONFIRMATIONS)
        decision = (
            "restore_responsive_confirmation"
            if selected != previous_value
            else "hold_confirmation_at_lower_bound_positive_ev"
        )
        reason = "cumulative_10m_source_quality_adjusted_ev_positive"
    elif adjusted_ev is not None:
        decision = "carry_forward_zero_ev"
        reason = "cumulative_10m_source_quality_adjusted_ev_zero"
    return {
        "required_actionable_confirmations": selected,
        "previous_required_actionable_confirmations": previous_value,
        "decision": decision,
        "reason": reason,
        "selected_axis": "required_actionable_confirmations",
        "bounded_range": [MIN_REQUIRED_CONFIRMATIONS, MAX_REQUIRED_CONFIRMATIONS],
        "daily_max_step": 1,
        "cumulative_decisive_sample_count": decisive,
        "cumulative_target_first_count": target_first,
        "cumulative_adverse_first_count": adverse_first,
        "cumulative_adverse_first_recovered_count": recovered_adverse,
        "source_quality_adjusted_ev_pct": (
            round(adjusted_ev, 6) if adjusted_ev is not None else None
        ),
        "round_trip_cost_pct": comparison_cost_contract(cost_as_of_date)[
            "round_trip_cost_pct"
        ],
        "comparison_cost_policy": "effective_dated_per_outcome_trade_date",
        "source_report_verification_issue": daily_report_issue,
        "rollback_value": previous_value,
        "rollback_condition": (
            "next verified cumulative opportunity EV reverses sign "
            "or policy/source verification fails"
        ),
    }


def build_calibration_policy(
    *,
    target_date: date,
    daily_reports: dict[str, dict[str, Any]],
    policy_dir: Path = DEFAULT_POLICY_DIR,
    specs: tuple[WidgetSpec, ...] = WIDGET_SPECS,
) -> tuple[dict[str, Any], dict[str, Any]]:
    effective_date = _next_krx_trading_date(target_date)
    comparison_cost = comparison_cost_contract(target_date)
    loader = WidgetCalibrationPolicyLoader(policy_dir)
    symbols: dict[str, Any] = {}
    report_symbols: dict[str, Any] = {}
    all_daily_reports_verified = True
    for spec in specs:
        daily = daily_reports.get(spec.symbol)
        report_issue = _daily_report_issue(
            daily,
            spec=spec,
            target_date=target_date,
        )
        if report_issue is not None:
            all_daily_reports_verified = False
        outcomes, excluded_reports = _load_cumulative_outcomes(
            spec,
            through_date=target_date,
            exclude_date=target_date,
        )
        target_report_path = _daily_report_path(spec, target_date)
        if report_issue is None:
            outcomes.extend(
                _eligible_decisive_outcomes(
                    daily,
                    source_report=str(target_report_path),
                )
            )
        sessions: dict[str, Any] = {}
        for session in spec.expected_sessions:
            previous = loader.resolve(
                symbol=spec.symbol,
                session=session,
                observed_date=target_date,
            )
            sessions[session] = _select_session_policy(
                previous=previous,
                outcomes=outcomes,
                session=session,
                daily_report_issue=report_issue,
                cost_as_of_date=target_date,
            )
        symbols[spec.symbol] = {
            "name": spec.name,
            "strategy_profile": spec.strategy_profile,
            "sessions": sessions,
        }
        report_symbols[spec.symbol] = {
            "name": spec.name,
            "daily_report_path": str(_daily_report_path(spec, target_date)),
            "daily_report_verified": report_issue is None,
            "daily_report_issue": report_issue,
            "cumulative_eligible_decisive_outcome_count": len(outcomes),
            "excluded_cumulative_report_count": len(excluded_reports),
            "excluded_cumulative_reports": excluded_reports,
            "sessions": sessions,
        }
    policy_version = (
        f"widget_advisory_policy_{effective_date.isoformat()}_from_"
        f"{target_date.isoformat()}"
    )
    policy = {
        "schema": POLICY_SCHEMA,
        "status": "verified",
        "policy_version": policy_version,
        "source_target_date": target_date.isoformat(),
        "effective_date": effective_date.isoformat(),
        "generated_at": datetime.now(KST).isoformat(),
        "authority": POLICY_AUTHORITY,
        "selected_axis": "required_actionable_confirmations",
        "source_quality_status": (
            "PASS" if all_daily_reports_verified else "DEGRADED_SAFE_CARRY_FORWARD"
        ),
        "symbols": symbols,
        "comparison_cost_contract": comparison_cost,
        "metric_contract": CALIBRATION_CONTRACT,
        "widget_runtime_effect": True,
        "trading_runtime_effect": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    report = {
        "schema": "widget_advisory_calibration_report_v1",
        "status": "done",
        "target_date": target_date.isoformat(),
        "effective_date": effective_date.isoformat(),
        "policy_version": policy_version,
        "all_daily_reports_verified": all_daily_reports_verified,
        "symbols": report_symbols,
        "comparison_cost_contract": comparison_cost,
        "metric_contract": CALIBRATION_CONTRACT,
        "policy_path": str(
            policy_dir / f"{POLICY_FILE_PREFIX}_{effective_date.isoformat()}.json"
        ),
        "widget_runtime_effect": True,
        "trading_runtime_effect": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return policy, report


def _policy_verification_issues(
    policy: object,
    *,
    specs: tuple[WidgetSpec, ...] = WIDGET_SPECS,
) -> list[str]:
    if not isinstance(policy, dict):
        return ["policy_not_object"]
    issues: list[str] = []
    if (
        policy.get("schema") != POLICY_SCHEMA
        or policy.get("status") != "verified"
        or not str(policy.get("policy_version") or "").strip()
        or policy.get("authority") != POLICY_AUTHORITY
    ):
        issues.append("policy_identity_contract_mismatch")
    if policy.get("metric_contract") != CALIBRATION_CONTRACT:
        issues.append("policy_metric_contract_mismatch")
    if (
        policy.get("widget_runtime_effect") is not True
        or policy.get("trading_runtime_effect") is not False
        or policy.get("runtime_effect") is not False
        or policy.get("actual_order_submitted") is not False
        or policy.get("broker_order_forbidden") is not True
    ):
        issues.append("policy_authority_contract_mismatch")
    try:
        effective_date = date.fromisoformat(str(policy.get("effective_date") or ""))
    except ValueError:
        issues.append("policy_effective_date_invalid")
        effective_date = None
    try:
        source_target_date = date.fromisoformat(
            str(policy.get("source_target_date") or "")
        )
    except ValueError:
        issues.append("policy_source_target_date_invalid")
        source_target_date = None
    if (
        source_target_date is not None
        and effective_date is not None
        and source_target_date >= effective_date
    ):
        issues.append("policy_date_order_invalid")
    symbols = policy.get("symbols")
    for spec in specs:
        symbol_policy = symbols.get(spec.symbol) if isinstance(symbols, dict) else None
        sessions = (
            symbol_policy.get("sessions") if isinstance(symbol_policy, dict) else None
        )
        for session in spec.expected_sessions:
            session_policy = (
                sessions.get(session) if isinstance(sessions, dict) else None
            )
            try:
                confirmations = int(
                    session_policy.get("required_actionable_confirmations")
                    if isinstance(session_policy, dict)
                    else 0
                )
            except (TypeError, ValueError):
                confirmations = 0
            if (
                not MIN_REQUIRED_CONFIRMATIONS
                <= confirmations
                <= MAX_REQUIRED_CONFIRMATIONS
            ):
                issues.append(f"session_policy_invalid:{spec.symbol}:{session}")
    return issues


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--policy-dir", type=Path, default=DEFAULT_POLICY_DIR)
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    target_date = (
        date.fromisoformat(args.target_date)
        if args.target_date
        else _resolve_default_target_date()
    )
    if not is_krx_trading_day(target_date):
        raise ValueError(
            f"widget_advisory_calibration_requires_krx_trading_date:{target_date}"
        )
    daily_reports: dict[str, dict[str, Any]] = {}
    rolling_reports: dict[str, dict[str, Any]] = {}
    for spec in WIDGET_SPECS:
        daily, rolling = build_and_write_evaluation(
            spec,
            target_date=target_date,
            write=args.write,
        )
        daily_reports[spec.symbol] = daily
        rolling_reports[spec.symbol] = rolling
    policy, report = build_calibration_policy(
        target_date=target_date,
        daily_reports=daily_reports,
        policy_dir=args.policy_dir,
    )
    verification_issues = _policy_verification_issues(policy)
    report["policy_verification"] = {
        "status": "pass" if not verification_issues else "fail",
        "issues": verification_issues,
    }
    if verification_issues:
        raise RuntimeError(
            "widget_advisory_policy_verification_failed:"
            + ",".join(verification_issues)
        )
    report["rolling_reports"] = {
        symbol: {
            "status": rolling.get("status"),
            "rolling_reported_mature_outcome_count": rolling.get(
                "mature_outcome_count"
            ),
            "rolling_policy_sample_floor_met": rolling.get("sample_floor_met"),
            "sample_floor_semantics": (
                "qualified_daily_report_count_floor; not mature outcome row count"
            ),
        }
        for symbol, rolling in rolling_reports.items()
    }
    if args.write:
        policy_path = args.policy_dir / (
            f"{POLICY_FILE_PREFIX}_{policy['effective_date']}.json"
        )
        report_path = args.output_dir / (
            f"widget_advisory_calibration_{target_date.isoformat()}.json"
        )
        staged_policy_path = policy_path.with_name(
            f".{policy_path.name}.{os.getpid()}.staged"
        )
        try:
            _atomic_write(staged_policy_path, policy)
            _atomic_write(report_path, report)
            policy_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged_policy_path, policy_path)
        finally:
            staged_policy_path.unlink(missing_ok=True)
    else:
        print(json.dumps({"policy": policy, "report": report}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
