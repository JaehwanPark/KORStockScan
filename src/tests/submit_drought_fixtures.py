"""Pure producer-built fixtures shared by BUY funnel contract tests."""

from copy import deepcopy
from datetime import datetime, timedelta

from src.engine import buy_funnel_sentinel as sentinel


def make_report(
    day="2026-09-07",
    *,
    samples=20,
    submitted=0,
    budget_passes=0,
    events=None,
    terminal_stage="blocked_ai_score",
):
    start = datetime.fromisoformat(f"{day}T09:00:00")
    if events is None:
        events = []
        for i in range(samples):
            stages = (
                (
                    "ai_confirmed",
                    "budget_pass",
                    "latency_pass",
                    "order_bundle_submitted",
                )
                if i < submitted
                else (
                    ("ai_confirmed", "budget_pass", terminal_stage)
                    if i < budget_passes
                    else ("ai_confirmed", terminal_stage)
                )
            )
            for offset, stage in enumerate(stages):
                events.append(
                    sentinel.PipelineEvent(
                        start + timedelta(minutes=60, seconds=4 * i + offset),
                        "ENTRY_PIPELINE",
                        stage,
                        "fixture",
                        "000001",
                        str(i + 1),
                        {},
                    )
                )
    end = max((e.emitted_at for e in events), default=start) + timedelta(minutes=1)
    summary = sentinel._summarize_events(events, start_at=start, end_at=end)
    classification = sentinel._classify(
        summary, None, as_of=end, scope_key="KRX|KRX_REGULAR"
    )
    contract = sentinel._entry_submit_drought_contract(classification, summary)
    scoped = deepcopy(contract)
    contract["scope_key"] = "KRX|KRX_REGULAR"
    contract["by_venue_session"] = {"KRX|KRX_REGULAR": scoped}
    return {
        "schema_version": 6,
        "target_date": day,
        "as_of": end.isoformat(),
        "classification": classification,
        "entry_submit_drought_contract": contract,
    }


def bind_history(history):
    from src.engine.automation.submit_drought_contract import make_scope_evidence

    for day in history:
        for row in day["eligible_scopes"]:
            counts = row["stage_unique"]
            source = make_report(
                day["source_date"],
                samples=counts["ai_confirmed"],
                budget_passes=counts["budget_pass"],
                submitted=counts["order_bundle_submitted"],
            )
            contract = source["entry_submit_drought_contract"]["by_venue_session"][
                "KRX|KRX_REGULAR"
            ]
            row["sentinel_evidence"] = make_scope_evidence(
                source, row["scope"], contract
            )
    return history
