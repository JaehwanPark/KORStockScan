"""Optional source-only receipt child of machine attribution; no live gate."""

from collections import Counter
import hashlib
import json

from src.trading.market.entry_adverse_flow import CONTRACT

METRIC_CONTRACT = dict(
    metric_role="funnel_count",
    decision_authority="source_quality_only",
    window_policy="exact_source_date_then_post_apply_version_window",
    sample_floor="not_applicable_for_receipt_accounting",
    primary_decision_metric="notional_weighted_ev_pct_in_existing_lifecycle_owner",
    source_quality_gate="exact_date_scope_identity_body_hash_and_terminal_receipts",
    forbidden_uses=[
        "live_approval",
        "profitability_from_counts",
        "counterfactual_full_fill",
        "missing_cost_as_zero",
    ],
)


def build_summary(*, target_date, report_root):
    path = (
        report_root
        / "entry_adverse_flow_events"
        / f"entry_adverse_flow_{target_date}.jsonl"
    )
    result = dict(
        schema="entry_adverse_flow_summary_v1",
        target_date=target_date,
        status="not_observed",
        optional_when_absent=True,
        runtime_effect=False,
        allowed_runtime_apply=False,
        metric_contract=METRIC_CONTRACT,
        source_path=str(path),
        source_sha256=None,
        items=[],
        contract_errors=[],
        economics_status="not_reconciled_use_existing_lifecycle_owner",
        net_profit_krw=None,
        notional_weighted_ev_pct=None,
    )
    if target_date < "2026-06-05":
        result["status"] = "pre_clean_baseline_excluded"
        return result
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return result
    except OSError as exc:
        result.update(status="source_unreadable", contract_errors=[type(exc).__name__])
        return result
    result["source_sha256"] = hashlib.sha256(raw).hexdigest()
    latest = {}
    for index, line in enumerate(raw.splitlines(), 1):
        try:
            event = json.loads(line)
            state = event["state"]
            scope = state["scope"]
            digest = hashlib.sha256(
                json.dumps(
                    state, sort_keys=True, separators=(",", ":"), allow_nan=False
                ).encode()
            ).hexdigest()
            if (
                event["schema"] != "entry_adverse_flow_receipt_v1"
                or event["target_date"] != target_date
                or state["signal_at"][:10] != target_date
                or state["contract"] != CONTRACT
                or event["receipt_sha256"] != digest
                or not isinstance(state["identity"], str)
                or not state["identity"]
                or not isinstance(state.get("action"), str)
                or set(scope) != {"owner", "scope_id", "symbol", "route", "session"}
                or any(not isinstance(v, str) or not v for v in scope.values())
            ):
                raise ValueError("receipt_contract_invalid")
            key = (tuple(sorted(scope.items())), state["identity"])
            latest[key] = dict(state, receipt_sha256=digest)
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            result["contract_errors"].append(dict(line=index, reason=str(exc)))
    counts = Counter()
    for row in latest.values():
        action = row.get("action", "")
        if action == "TRANSPORT_STARTED":
            category = "transport_started"
        elif isinstance(action, str) and action.startswith("SKIP_"):
            category = "not_sent_terminal"
        elif action in {"WAIT", "CONTINUE"}:
            category = "pending"
        else:
            result["contract_errors"].append(
                dict(identity=row["identity"], reason="unknown_action")
            )
            continue
        counts[category] += 1
        result["items"].append(dict(row, category=category))
    result.update(
        status="source_contract_gap" if result["contract_errors"] else "loaded",
        observed_guard_identity_count=len(latest),
        denominator_note="guard_intake_before_final_original_liquidity_and_submit_guards_not_all_executable_opportunities",
        counts=dict(counts),
        conservation_ok=len(latest) == sum(counts.values())
        and not result["contract_errors"],
    )
    return result
