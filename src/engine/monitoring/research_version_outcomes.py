"""Native widget version outcomes with exact-cost, unique-owner reconciliation.

The existing ka10073 adapter owns protocol and rate limits. Publication never
queries an account. This postclose producer performs only optional read-only
cost recovery; ambiguity/partial inventory/missing costs stay null.
"""

from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from src.engine.monitoring import research_closed_loop as loop
from src.engine.monitoring.low_price_two_leg_tuning import (
    _apply_broker_realized_economics,
)
from src.engine.monitoring.policy_research_economics import aware, numeric


def native_widget_order_projection(state, *, source_date):
    """Bind the exact dated order inputs, excluding service heartbeat/config."""
    sections = [(state.get("active_date"), state.get("symbols") or {})]
    sections += [(row.get("trade_date"), row.get("symbols") or {})
                 for row in state.get("history") or []]
    orders = []
    for day, symbols in sections:
        if not day or not "2026-06-05" <= day <= source_date.isoformat():
            continue
        for symbol, native in symbols.items():
            orders.extend(dict(state_date=day, symbol=symbol, order=order)
                          for order in native.get("orders") or [])
    return dict(source_date=source_date.isoformat(), orders=sorted(orders, key=loop.digest))


def native_widget_rows(state, *, source_date):
    """Use original per-order version/signal/custody, never current policy."""
    by_order = {}
    invalid = 0
    sections = [(state.get("active_date"), state.get("symbols") or {})]
    sections += [
        (row.get("trade_date"), row.get("symbols") or {})
        for row in state.get("history") or []
    ]
    for day, symbols in sections:
        if not day or day < "2026-06-05" or day > source_date.isoformat():
            continue
        for symbol, native in symbols.items():
            for order in native.get("orders") or []:
                native_id = symbol, order.get("order_date"), order.get("order_no")
                if not native_id[1] or not native_id[2]:
                    invalid += 1
                    continue
                if native_id in by_order and by_order[native_id] != order:
                    raise ValueError("widget_native_order_projection_conflict")
                by_order[native_id] = order
    groups = defaultdict(list)
    for (symbol, day, _), order in by_order.items():
        signal = order.get("parent_entry_signal_id") or order.get("signal_id")
        version = order.get("execution_policy_content_sha256")
        groups[symbol, signal, version].append(order)
    rows = []
    for (symbol, signal, version), orders in groups.items():
        buys = [row for row in orders if row.get("side") == "BUY"]
        sells = [row for row in orders if row.get("side") == "SELL"]
        if not buys:
            continue

        def qty(row):
            return (
                row.get("filled_qty")
                if type(row.get("filled_qty")) is int and row["filled_qty"] >= 0
                else None
            )

        def prices(row):
            return numeric(row.get("fill_price"))

        buy_qty = sum(qty(row) or 0 for row in buys)
        sell_qty = sum(qty(row) or 0 for row in sells)
        clocks = [
            aware(row.get("last_reconciled_at") or row.get("filled_at"))
            for row in sells
            if qty(row)
        ]
        realization_days = {clock.date().isoformat() for clock in clocks if clock}
        terminal = (
            buy_qty > 0
            and sell_qty == buy_qty
            and len(realization_days) == 1
            and all(clocks)
            and all(
                qty(row) is not None
                and row.get("status") in {"FILLED", "CANCELED", "TERMINAL_UNFILLED"}
                and type(row.get("remaining_qty")) is int
                and row["remaining_qty"] == 0
                for row in orders
            )
            and all(
                prices(row) is not None and prices(row) > 0
                for row in orders
                if qty(row)
            )
        )
        entry_day = min(row["order_date"] for row in buys)
        target_date = next(iter(realization_days)) if terminal else entry_day
        if target_date > source_date.isoformat():
            terminal = False
        buy = sum((prices(row) or 0) * (qty(row) or 0) for row in buys)
        sell = sum((prices(row) or 0) * (qty(row) or 0) for row in sells)
        valid_version = isinstance(version, str) and len(version) == 64
        legs = []
        if terminal:
            legs = [
                dict(
                    completed=True,
                    profit_price_source="broker_target_fill_price",
                    net_profit_pct=(sell / buy - 1) * 100,
                    fill_price=buy / buy_qty,
                    target_fill_price=sell / buy_qty,
                    quantity=buy_qty,
                    buy_filled_qty=buy_qty,
                    target_filled_qty=buy_qty,
                    realization_date=target_date,
                )
            ]
        if target_date != source_date.isoformat():
            continue
        rows.append(
            dict(
                profile_id=f"widget_{symbol}_{loop.digest(signal)[:16]}",
                symbol=symbol,
                target_date=target_date,
                entry_date=entry_day,
                signal_id=signal,
                candidate_revision_sha256=(
                    buys[0].get("candidate_revision_sha256")
                    if len({row.get("candidate_revision_sha256") for row in buys}) == 1
                    else None
                ),
                native_attempt_id=loop.digest([symbol, signal, version, entry_day]),
                attempted=True,
                execution_policy_content_sha256=version,
                source_quality="pass" if terminal and valid_version else "source_gap",
                eligible_for_tuning=terminal and valid_version,
                outcome_complete_for_ev=terminal and valid_version,
                completed_full_fill=all(
                    qty(row) == row.get("requested_qty") for row in buys
                ),
                legs=legs,
                native_order_ids=[row["order_no"] for row in orders],
                realized_net_profit_krw=None,
                **loop.AUTHORITY,
            )
        )
    return rows, invalid


def collect_widget_outcomes(
    source_date,
    *,
    state_path,
    directory=loop.DIRECTORY,
    loader=None,
    decision_path=None,
):
    try:
        state = loop.read_object(state_path, limit=16 * 1024 * 1024)
    except FileNotFoundError:
        return dict(
            schema=loop.SCHEMA,
            source_date=source_date.isoformat(),
            status="source_gap",
            reason="native_widget_state_missing",
            rows=[],
            **loop.AUTHORITY,
        )
    rows, invalid = native_widget_rows(state, source_date=source_date)
    previous = {}
    destination = Path(directory) / f"widget_outcomes_{source_date.isoformat()}.json"
    try:
        prior = loop.read_object(destination, limit=16 * 1024 * 1024)
        if prior.get("outcomes_sha256") == loop.digest(
            {k: v for k, v in prior.items() if k != "outcomes_sha256"}
        ):
            previous = {row["native_attempt_id"]: row for row in prior.get("rows", [])}
    except FileNotFoundError:
        pass
    for row in rows:
        row["native_attempt_facts_sha256"] = loop.digest(row)
    # A symbol-day broker aggregate cannot be split by hypothetical trade order
    # or mixed policy versions. Exact costs apply only to one provable cohort.
    reconciliation = _apply_broker_realized_economics(rows, loader)
    for row in rows:
        exact = row.get("broker_realized_economics") or {}
        if exact.get("status") == "matched_exact":
            row["realized_net_profit_krw"] = exact["realized_net_profit_krw"]
        else:
            old = previous.get(row["native_attempt_id"]) or {}
            if (
                old.get("native_attempt_facts_sha256")
                == row["native_attempt_facts_sha256"]
                and (old.get("broker_realized_economics") or {}).get("status")
                == "matched_exact"
            ):
                row["broker_realized_economics"] = old["broker_realized_economics"]
                row["realized_net_profit_krw"] = old["realized_net_profit_krw"]
            else:
                row["realized_net_profit_krw"] = None
    decisions = None
    if decision_path is not None:
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            from src.trading.widget_auto_trade.engine import WidgetTradeEventRecorder

            event_path = (
                Path(decision_path).parent
                / f"widget_signal_auto_trade_events_{source_date:%Y%m%d}.jsonl"
            )
            if event_path.exists():
                recorder = WidgetTradeEventRecorder(Path(decision_path).parent)
                recorder._record_research_decision(
                    {},
                    datetime.now(ZoneInfo("Asia/Seoul")),
                    event_path,
                    source_day=str(source_date),
                )
            value = loop.read_object(decision_path, limit=16 * 1024 * 1024)
            body = {k: v for k, v in value.items() if k != "summary_sha256"}
            if value.get("source_date") != str(source_date) or value.get(
                "summary_sha256"
            ) != loop.digest(body):
                raise ValueError("native_decision_feedback_invalid")
            decisions = {k: v for k, v in value.items() if k != "native_decisions"}
        except FileNotFoundError:
            decisions = dict(
                status="source_gap", reason="native_decision_summary_missing"
            )
    receipt = dict(
        schema=loop.SCHEMA,
        source_date=source_date.isoformat(),
        status="complete",
        rows=rows,
        invalid_native_order_count=invalid,
        native_state_sha256=loop.digest(state),
        native_state_order_projection_sha256=loop.digest(native_widget_order_projection(state, source_date=source_date)),
        reconciliation=reconciliation,
        policy_decision_feedback=decisions,
        version_economics=loop.version_economics(rows),
        additional_order_calls=0,
        **loop.AUTHORITY,
    )
    loop.atomic_write(
        Path(directory) / f"widget_outcomes_{source_date.isoformat()}.json",
        {**receipt, "outcomes_sha256": loop.digest(receipt)},
    )
    return receipt


def outcome_feedback(source_date, *, directory=loop.DIRECTORY):
    """Mature exact realized facts only; pending/CF are separate diagnostics."""
    directory = loop._directory(directory)
    rows, sources, decisions = {}, {}, {}
    for path in sorted(Path(directory).glob("widget_outcomes_*.json")):
        if path.stem[-10:] > source_date.isoformat():
            continue
        value = loop.read_object(path, limit=16 * 1024 * 1024)
        body = {k: v for k, v in value.items() if k != "outcomes_sha256"}
        if value.get("outcomes_sha256") != loop.digest(body):
            raise ValueError("version_feedback_hash_invalid")
        sources[str(path.resolve())] = value["outcomes_sha256"]
        native_decisions = value.get("policy_decision_feedback")
        if native_decisions:
            decisions[value["source_date"]] = native_decisions
        for row in value.get("rows") or []:
            native = row["native_attempt_id"]
            old = rows.get(native)
            if (
                old
                and (old.get("broker_realized_economics") or {}).get("status")
                == "matched_exact"
                and old.get("broker_realized_economics")
                != row.get("broker_realized_economics")
            ):
                raise ValueError("conflicting_native_exact_cost_outcome")
            rows[native] = row
    ordered_rows = sorted(
        rows.values(), key=lambda row: (row["target_date"], row["native_attempt_id"])
    )
    from datetime import date, timedelta
    from src.utils.market_day import is_krx_trading_day

    dates, day = [], source_date
    while len(dates) < 30 and day >= date(2026, 6, 5):
        if is_krx_trading_day(day):
            dates.append(day.isoformat())
        day -= timedelta(days=1)
    return dict(
        schema=loop.SCHEMA,
        source_date=source_date.isoformat(),
        cumulative=loop.version_economics(ordered_rows),
        rolling_last_30=loop.version_economics(
            [row for row in ordered_rows if row["target_date"] in dates]
        ),
        holdout_last_16=loop.version_economics(
            [row for row in ordered_rows if row["target_date"] in dates[:16]]
        ),
        window_dates=dict(
            rolling_last_30=sorted(dates), holdout_last_16=sorted(dates[:16])
        ),
        source_hashes=sources,
        native_policy_decisions=decisions,
        mature_only_for_economics=True,
        counterfactual_economics_separate=True,
        **loop.AUTHORITY,
    )


def episode_feedback(source_date, *, report_root=None):
    from src.utils.constants import DATA_DIR

    root = Path(report_root or DATA_DIR / "report")
    path = (
        root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{source_date}.json"
    )
    try:
        value = loop.read_object(path, limit=128 * 1024 * 1024)
    except FileNotFoundError:
        return dict(
            status="waiting",
            reason="native_episode_version_report_missing",
            **loop.AUTHORITY,
        )
    economics = value.get("policy_version_economics")
    if (
        value.get("target_date") != str(source_date)
        or not isinstance(economics, dict)
        or economics.get("economic_basis")
        != "actual_exact_cost_completed_only_CF_separate"
    ):
        return dict(
            status="source_gap",
            reason="native_episode_version_report_invalid",
            **loop.AUTHORITY,
        )
    return dict(
        status="complete",
        source_date=str(source_date),
        source_report_sha256=loop.digest(value),
        cumulative=economics,
        rolling_last_30=value.get("policy_version_rolling_last_30"),
        holdout_last_16=value.get("policy_version_holdout_last_16"),
        **loop.AUTHORITY,
    )


def mature_widget_retired_revisions(feedback):
    """Retire only matured exact-cost revisions; missing economics never votes."""
    import math

    retired = set()
    cumulative = (feedback.get("cumulative") or {}).get("strategy_revisions") or {}
    holdout = (feedback.get("holdout_last_16") or {}).get("strategy_revisions") or {}
    for revision, full in cumulative.items():
        tail = holdout.get(revision) or {}
        if revision == "unattributed_version":
            continue
        try:
            valid = all(
                type(bucket.get("exact_completed_count")) is int
                and bucket["exact_completed_count"] >= floor
                and type(bucket.get("realized_net_return_pct")) in (int, float)
                and math.isfinite(bucket["realized_net_return_pct"])
                and bucket["realized_net_return_pct"] <= 0
                and type(bucket.get("realized_buy_notional_krw")) in (int, float)
                and bucket["realized_buy_notional_krw"] > 0
                for bucket, floor in ((full, 6), (tail, 4))
            )
            if valid:
                retired.add(revision)
        except (KeyError, TypeError, ValueError):
            continue
    return retired
