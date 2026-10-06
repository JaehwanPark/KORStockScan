"""Existing Main calibration's bounded, non-publishing price comparison adapter.

This is a report helper, not a collector, broker simulator or runtime policy
publisher. Minute-price counterfactuals never stand in for actual executions.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
import gzip
import hashlib
import json
import math
from pathlib import Path

from src.engine.scalping.entry_strategy_policy import digest

SCHEMA = "main_submit_drought_research_v1"
EXIT = dict(
    schema="next_minute_open_twenty_minute_net_v1",
    round_trip_cost_pct=0.23,
    slippage_pct=0.10,
    target_net_pct=0.5,
    stop_net_pct=-0.5,
    minutes=20,
    same_bar_both="excluded",
    maximum_bar_gap_sec=60,
)


def kernel_seals():
    return {
        name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in (
            "main_submit_drought_research.py",
            "entry_setup_evidence.py",
            "entry_strategy_policy.py",
            "entry_admission_recipe.py",
            "entry_setup_source_repair.py",
            "ai_decision_quality.py",
            "entry_candle_context.py",
            "ai_action_outcome_calibration.py",
        )
    }


def finite(value):
    return (
        float(value) if type(value) in (int, float) and math.isfinite(value) else None
    )


def seal(value):
    return {**value, "artifact_content_sha256": digest(value)}


def price_path(at, bars):
    """Outcomes use only the frozen entry/cost/exit definition, never MFE."""
    dt = datetime.fromisoformat(at)
    if dt.tzinfo is None:
        return dict(status="decision_clock_unproven", net_return_pct=None)
    start = (dt.replace(second=0, microsecond=0) + timedelta(minutes=1)).timestamp()
    entry = bars.get(start)
    if not entry or finite(entry.get("open")) is None or entry["open"] <= 0:
        return dict(status="next_minute_open_missing", net_return_pct=None)
    price = entry["open"]
    cost = EXIT["round_trip_cost_pct"] + EXIT["slippage_pct"]
    target = price * (1 + (EXIT["target_net_pct"] + cost) / 100)
    stop = price * (1 + (EXIT["stop_net_pct"] + cost) / 100)
    for minute in range(EXIT["minutes"]):
        bar = bars.get(start + minute * 60)
        if not bar:
            return dict(status="price_path_gap_or_unmature", net_return_pct=None)
        values = [finite(bar.get(k)) for k in ("open", "high", "low", "close")]
        if (
            None in values
            or min(values) <= 0
            or values[2] > min(values[0], values[3])
            or values[1] < max(values[0], values[3])
        ):
            return dict(status="price_bar_invalid", net_return_pct=None)
        high, low = bar["high"] >= target, bar["low"] <= stop
        if high and low:
            return dict(status="same_bar_target_stop_ambiguous", net_return_pct=None)
        if high or low:
            return dict(
                status="target_first" if high else "adverse_first",
                net_return_pct=EXIT["target_net_pct"] if high else EXIT["stop_net_pct"],
            )
    return dict(
        status="timeout", net_return_pct=(bar["close"] / price - 1) * 100 - cost
    )


def metrics(rows):
    values = [
        r["outcome"]["net_return_pct"]
        for r in rows
        if finite(r["outcome"].get("net_return_pct")) is not None
    ]
    wins = [v for v in values if v > 0]
    losses = [v for v in values if v < 0]
    return dict(
        selected_count=len(rows),
        mature_count=len(values),
        pending_count=len(rows) - len(values),
        wins=len(wins),
        losses=len(losses),
        zero_count=sum(v == 0 for v in values),
        win_rate=len(wins) / len(values) if values else None,
        average_win_pct=sum(wins) / len(wins) if wins else None,
        average_loss_pct=sum(losses) / len(losses) if losses else None,
        cumulative_net_pct=sum(values) if values else None,
        maximum_loss_pct=min(values) if values else None,
        symbols=len({r["stock_code"] for r in rows}),
        selected_symbols=sorted({r["stock_code"] for r in rows}),
        outcome_states=dict(Counter(r["outcome"]["status"] for r in rows)),
    )


def choose(baseline, candidates):
    """Win-rate comparison only; no success-retention or sample-size floors."""
    eligible = []
    for name, value in candidates.items():
        if value.get("duplicate_of"):
            continue
        if baseline["win_rate"] is not None:
            rate = value["win_rate"]
            threshold = baseline["win_rate"]
        else:
            # Use the same exit model's decisive wins/losses. Timeout payouts
            # vary, so their observed average sizes own the alternate benchmark.
            states = value.get("outcome_states") or {}
            wins, losses = value.get("wins", 0), value.get("losses", 0)
            gain, loss = EXIT["target_net_pct"], abs(EXIT["stop_net_pct"])
            if states.get("timeout"):
                gain = finite(value.get("average_win_pct"))
                loss = finite(value.get("average_loss_pct"))
                if gain is None or gain <= 0 or loss is None or loss >= 0:
                    continue
                loss = abs(loss)
            rate = wins / (wins + losses) if wins + losses else None
            threshold = loss / (gain + loss)
        if rate is None:
            continue
        if rate > threshold:
            eligible.append((rate, name))
    if not eligible:
        return dict(
            status="incumbent_carried",
            winner=None,
            reason="no_candidate_higher_comparable_win_rate",
        )
    best = max(rate for rate, _ in eligible)
    winners = [name for rate, name in eligible if rate == best]
    return dict(
        status="research_winner" if len(winners) == 1 else "incumbent_carried",
        winner=winners[0] if len(winners) == 1 else None,
        reason="higher_win_rate" if len(winners) == 1 else "candidate_tie",
    )


def _prices(data_root, day, external_dir):
    prices, receipts = defaultdict(dict), []
    if external_dir is not None:
        external_dir = Path(external_dir)
        manifest_path = external_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        receipts.append(
            dict(
                path=str(manifest_path.resolve()),
                sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            )
        )
        for receipt in manifest:
            code = str(receipt["code"])
            if len(code) != 6 or not code.isdigit():
                raise ValueError("external_symbol_invalid")
            path = external_dir / f"{code}.json"
            blob = path.read_bytes()
            if (
                len(blob) != receipt["bytes"]
                or hashlib.sha256(blob).hexdigest() != receipt["sha256"]
            ):
                raise ValueError("external_price_manifest_mismatch:" + code)
            if not receipt.get("url") or not receipt.get("retrieved_at"):
                raise ValueError("external_source_provenance_missing")
            for b in json.loads(blob):
                ts = datetime.strptime(b["localDateTime"], "%Y%m%d%H%M%S")
                from zoneinfo import ZoneInfo

                ts = ts.replace(tzinfo=ZoneInfo("Asia/Seoul"))
                if ts.date().isoformat() != day:
                    raise ValueError("external_price_date_mismatch")
                prices[(code, "KRX", "KRX_REGULAR")][ts.timestamp()] = {
                    "open": b["openPrice"],
                    "high": b["highPrice"],
                    "low": b["lowPrice"],
                    "close": b["currentPrice"],
                }
            receipts.append({**receipt, "path": str(path.resolve())})
        return prices, receipts, "external_krx_minute_price_cf"
    path = (
        Path(data_root)
        / "report/machine_completed_price_source"
        / f"machine_completed_price_source_{day}.json"
    )
    if not path.is_file():
        return prices, [], "native_completed_minute_price_cf"
    v = json.loads(path.read_text())
    if v.get("source_date") != day or v.get("artifact_content_sha256") != digest(
        {k: x for k, x in v.items() if k != "artifact_content_sha256"}
    ):
        raise ValueError("native_price_source_invalid")
    receipts.append(
        dict(
            path=str(path.resolve()),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            provenance=v.get("provenance"),
        )
    )
    for b in v.get("prices") or []:
        if (
            b.get("completed_bar_only") is not True
            or b.get("source_quality") != "pass_completed_ka10080_bar"
        ):
            continue
        ts = datetime.fromisoformat(b["timestamp"])
        if ts.tzinfo is None or ts.date().isoformat() != day:
            raise ValueError("native_price_clock_invalid")
        key = (
            str(b["stock_code"]),
            str(b["effective_venue"]).upper(),
            str(b["session_bucket"]).upper(),
        )
        value = {k: b.get(k) for k in ("open", "high", "low", "close")}
        old = prices[key].get(ts.timestamp())
        if old is not None and old != value:
            raise ValueError("native_price_duplicate_conflict")
        prices[key][ts.timestamp()] = value
    return prices, receipts, "native_completed_minute_price_cf"


def _candidate(row, samsung):
    if (row["venue"], row["session"]) != ("KRX", "KRX_REGULAR"):
        return False
    f = row["features"]
    pressure, delta, change, absorption = (
        finite(f.get(k))
        for k in (
            "buy_pressure_10t",
            "net_aggressive_delta_10t",
            "price_change_10t_pct",
            "same_price_buy_absorption",
        )
    )
    return bool(
        row["candidate_source_valid"]
        and pressure is not None
        and pressure >= (60 if samsung else 55)
        and delta is not None
        and delta > 0
        and change is not None
        and change >= 0
        and (not samsung or absorption is not None and absorption >= 2)
    )


def _traces(data_root, day):
    """Preserve exact natural risk fields and their original response custody."""
    path = Path(data_root) / "ai_decision_trace" / f"ai_decision_trace_{day}.jsonl"
    if not path.is_file():
        path = path.with_suffix(path.suffix + ".gz")
    if not path.is_file():
        return {}, None
    h, size, index = hashlib.sha256(), 0, {}
    limit = path.stat().st_size if path.suffix != ".gz" else None
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as stream:
        for blob in stream:
            if limit is not None and size + len(blob) > limit:
                break
            h.update(blob)
            size += len(blob)
            t = json.loads(blob)
            sha = t.get("machine_observation_sha256")
            if not sha:
                continue
            final = t.get("decision_quality_final_response")
            if not isinstance(final, dict) or digest(final) != t.get(
                "decision_quality_final_response_sha256"
            ):
                continue
            risk = dict(
                schema="entry_setup_risk_adjudication_v1",
                risk_verdict=final.get("entry_ai_advisory_verdict"),
                risk_codes=final.get("entry_ai_raw_risk_codes"),
                supporting_fact_ids=final.get("entry_ai_raw_supporting_fact_ids"),
                contradicting_fact_ids=final.get("entry_ai_raw_contradicting_fact_ids"),
                confidence=t.get("entry_ai_raw_confidence"),
            )
            value = dict(
                decision_ts=t.get("decision_ts"),
                risk_field_projection=risk,
                decision_trace_id=t.get("decision_trace_id"),
                stock_code=t.get("stock_code"),
                original_response_sha256=t.get("response_sha256"),
                final_response_sha256=t["decision_quality_final_response_sha256"],
                original_contract_status=t.get("decision_quality_contract_status"),
                original_screen_contract_errors=final.get(
                    "entry_ai_advisory_contract_errors"
                ),
                remote_guard_applied=bool(
                    final.get("remote_buy_guard_applied")
                    or final.get("decision_quality_runtime_action_mapping")
                    == "remote_buy_guard_wait"
                    or t.get("decision_quality_runtime_action_mapping")
                    == "remote_buy_guard_wait"
                ),
            )
            if sha in index and index[sha] != value:
                index[sha] = dict(source_gap="exact_machine_trace_response_conflict")
                continue
            index[sha] = value
    return index, dict(
        path=str(path.resolve()),
        bytes=size,
        sha256=h.hexdigest(),
        byte_basis="decompressed_prefix" if path.suffix == ".gz" else "file_prefix",
    )


def build_daily(
    *,
    data_root,
    target_date,
    bundle,
    external_dir=None,
    source_bytes=None,
    source_sha256=None,
    cutoff=None,
):
    """One day, exact source receipts, row exclusions and frozen opportunity anchors."""
    from src.engine.scalping.entry_setup_evidence import (
        validate_entry_setup_evidence,
        mechanistic_entry_policy_decision,
        validate_mechanistic_risk_screen,
    )
    from src.engine.scalping.entry_admission_recipe import SOFT_CONFIRMATION
    from src.engine.scalping.mechanistic_entry_runtime_policy import for_cohort

    path = (
        Path(data_root)
        / "ai_decision_payloads"
        / f"ai_decision_payloads_{target_date}.jsonl"
    )
    if target_date < "2026-09-29" or source_bytes is not None and source_bytes <= 0:
        raise ValueError("research_policy_era_or_prefix_invalid")
    if cutoff is not None:
        parsed_cutoff = datetime.fromisoformat(cutoff)
        if (
            parsed_cutoff.tzinfo is None
            or parsed_cutoff.date().isoformat() != target_date
        ):
            raise ValueError("research_cutoff_invalid")
    if not path.is_file():
        path = path.with_suffix(path.suffix + ".gz")
    if source_bytes is None and path.suffix != ".gz":
        source_bytes = path.stat().st_size
    prices, price_receipts, price_basis = _prices(data_root, target_date, external_dir)
    traces, trace_receipt = _traces(data_root, target_date)
    rows, excluded, byte_count, source_hash = [], Counter(), 0, hashlib.sha256()
    seen = set()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as stream:
        for blob in stream:
            if source_bytes is not None and byte_count + len(blob) > source_bytes:
                break
            byte_count += len(blob)
            source_hash.update(blob)
            o = json.loads(blob)
            if o.get("schema") != "mechanistic_entry_observation_v1":
                continue
            sha = o.get("machine_observation_sha256")
            if sha in seen:
                excluded["duplicate_capture"] += 1
                continue
            seen.add(sha)
            try:
                if sha != digest(
                    {k: v for k, v in o.items() if k != "machine_observation_sha256"}
                ):
                    raise ValueError("capture_hash_invalid")
                if any(
                    o.get(k) is not x
                    for k, x in (
                        ("redacted", False),
                        ("provider_called", False),
                        ("runtime_effect", False),
                        ("allowed_runtime_apply", False),
                        ("actual_order_submitted", False),
                        ("broker_order_forbidden", True),
                    )
                ):
                    raise ValueError("capture_authority_or_redaction_invalid")
                s = o["source"]["setup_evidence"]
                raw = s["strategy_raw_input"]
                at = datetime.fromisoformat(o["captured_at"])
                if at.tzinfo is None or at.date().isoformat() != target_date:
                    raise ValueError("source_clock_invalid")
                if cutoff is not None and at > datetime.fromisoformat(cutoff):
                    raise ValueError("source_after_frozen_cutoff")
                if (
                    finite(raw.get("entry_machine_input_as_of")) is None
                    or raw["entry_machine_input_as_of"] > at.timestamp()
                ):
                    raise ValueError("future_or_missing_source_cutoff")
                code = str(
                    raw.get("stock_code") or o["label_context"].get("stock_code") or ""
                )
                if (
                    len(code) != 6
                    or not code.isdigit()
                    or code != str(o["label_context"].get("stock_code"))
                ):
                    raise ValueError("capture_symbol_identity_invalid")
                venue, session = (
                    str(raw["effective_venue"]).upper(),
                    str(raw["session_bucket"]).upper(),
                )
                scoped = for_cohort(bundle, (venue, session))
                restoration = None
                setup_errors = validate_entry_setup_evidence(s)
                if setup_errors == ["entry_setup_evidence_sha256_invalid"]:
                    from src.engine.scalping.entry_setup_source_repair import (
                        restore_original_recipe_metadata,
                    )

                    s, restoration = restore_original_recipe_metadata(o)
                    setup_errors = validate_entry_setup_evidence(s)
                if scoped is None:
                    raise ValueError("policy_scope_missing")
                if setup_errors:
                    raise ValueError("setup_contract_invalid:" + "|".join(setup_errors))
                if s["strategy_raw_sha256"] != digest(raw):
                    raise ValueError("original_raw_hash_invalid")
                d = mechanistic_entry_policy_decision(
                    s, policy=scoped["machine_policy"]
                )
                effective = d.get("effective_setup_evidence") or s
                f = raw.get("features") or {}
                source_valid = (
                    effective.get("source_quality", {}).get("status")
                    == "fresh_consistent"
                    and f.get("tick_aggressor_pressure_usable") is True
                    and f.get("tick_context_stale") is False
                    and f.get("quote_stale") is False
                    and f.get("quote_fresh_for_entry") is True
                    and finite(f.get("quote_age_ms")) is not None
                    and 0 <= f["quote_age_ms"] <= 3000
                    and finite(f.get("tick_latest_age_ms")) is not None
                    and 0 <= f["tick_latest_age_ms"] <= 3000
                    and finite(f.get("tick_aggressor_trusted_count")) is not None
                    and f["tick_aggressor_trusted_count"] >= 10
                    and d.get("liquidity_inputs_complete") is True
                    and d.get("liquidity_threshold_pass") is True
                    and not effective.get("invalidation_facts")
                )
                screen = traces.get(sha)
                if screen and not screen.get("source_gap"):
                    screen = dict(screen)
                    risk = screen["risk_field_projection"]
                    errors = validate_mechanistic_risk_screen(
                        risk, setup_evidence=s, policy=scoped["machine_policy"]
                    )
                    try:
                        response_at = datetime.fromisoformat(screen["decision_ts"])
                        entry_at = at.replace(second=0, microsecond=0) + timedelta(
                            minutes=1
                        )
                        if (
                            response_at.tzinfo is None
                            or not at <= response_at < entry_at
                        ):
                            raise ValueError("auxiliary_response_after_scenario_entry")
                    except (ValueError, TypeError, KeyError):
                        errors = [*errors, "auxiliary_response_clock_unproven"]
                    receipt = d.get("admission_recipe") or {}
                    legacy_only = set(
                        effective.get("corroborated_risk_codes") or []
                    ) <= {"CONFIRMATION_MISSING"} and all(
                        row["resolved"]
                        and row["original"]["fact_id"] in SOFT_CONFIRMATION
                        for row in receipt.get("fact_ledger") or []
                    )
                    screen["validation_errors"] = errors
                    screen["A_eligible"] = bool(
                        source_valid
                        and not errors
                        and d["action"] == "ENTER_NOW"
                        and d.get("admission_recipe_trigger_pass") is True
                        and risk["risk_verdict"] == "CAUTION"
                        and risk["risk_codes"] == ["CONFIRMATION_MISSING"]
                        and legacy_only
                    )
                    screen["B_eligible"] = bool(
                        source_valid
                        and not errors
                        and d["action"] == "ENTER_NOW"
                        and risk["risk_verdict"] == "PASS"
                        and screen["remote_guard_applied"]
                    )
                    screen["candidate_effective_verdict"] = (
                        "PASS" if screen["A_eligible"] else risk["risk_verdict"]
                    )
                    screen["effective_is_research_only"] = True
                elif screen:
                    screen = dict(
                        screen,
                        validation_errors=[screen["source_gap"]],
                        A_eligible=False,
                        B_eligible=False,
                        risk_field_projection={"risk_verdict": None},
                        remote_guard_applied=False,
                    )
                rows.append(
                    dict(
                        stock_code=code,
                        captured_at=at.isoformat(),
                        epoch=at.timestamp(),
                        venue=venue,
                        session=session,
                        broker_route=o["label_context"].get("broker_route"),
                        source_event_stage=o.get("source_event_stage"),
                        watch_admission_id=o.get("watch_admission_id"),
                        auxiliary_screen=screen,
                        original_metadata_restoration=restoration,
                        scanner_promotion_id=o.get("scanner_promotion_id"),
                        source_sha256=sha,
                        raw_sha256=s["strategy_raw_sha256"],
                        policy_sha256=digest(scoped["machine_policy"]),
                        native_action=o["source"]["assessment"].get("action"),
                        action=d["action"],
                        features={
                            k: f.get(k)
                            for k in (
                                "buy_pressure_10t",
                                "net_aggressive_delta_10t",
                                "price_change_10t_pct",
                                "same_price_buy_absorption",
                                "large_sell_print_detected",
                            )
                        },
                        candidate_source_valid=source_valid,
                        reversible_large_sell_block=(
                            d["action"] == "BLOCK"
                            and effective.get("invalidation_facts")
                            == ["hard_blocker:large_sell_print_present"]
                        ),
                        outcome=price_path(
                            at.isoformat(), prices.get((code, venue, session), {})
                        ),
                    )
                )
            except (ValueError, TypeError, KeyError) as exc:
                excluded[str(exc)] += 1
    if source_bytes is not None and byte_count != source_bytes:
        raise ValueError("source_prefix_not_a_complete_capture_boundary")
    if source_sha256 is not None and source_hash.hexdigest() != source_sha256:
        raise ValueError("frozen_source_prefix_sha256_mismatch")
    # Keep venue/session and both watch kinds visible while deduplicating all
    # repeated observations of the same symbol opportunity across stages.
    anchors, groups, history = [], {}, defaultdict(list)
    for r in sorted(rows, key=lambda r: (r["epoch"], r["source_sha256"])):
        history[(r["stock_code"], r["venue"], r["session"])].append(r)
    for key, stream in sorted(history.items()):
        end = -1
        for index, r in enumerate(stream):
            if r["epoch"] < end:
                continue
            end = r["epoch"] + 1800
            samsung = r["stock_code"] == "005930"
            selected = _candidate(r, samsung) and r["action"] != "BLOCK"
            retry = None
            if r["reversible_large_sell_block"]:
                last, attempts = r["epoch"], 0
                for follow in stream[index + 1 :]:
                    if follow["epoch"] > r["epoch"] + 30 or attempts >= 3:
                        break
                    if (
                        follow["epoch"] - last < 1
                        or follow["raw_sha256"] == r["raw_sha256"]
                    ):
                        continue
                    last, attempts = follow["epoch"], attempts + 1
                    if (
                        follow["features"].get("large_sell_print_detected") is False
                        and _candidate(follow, samsung)
                        and follow["action"] != "BLOCK"
                    ):
                        retry = follow
                        break
            anchors.append({**r, "candidate": selected, "retry": retry})
    for samsung in (True, False):
        all_population = [
            r for r in anchors if (r["stock_code"] == "005930") == samsung
        ]
        population = [
            r
            for r in all_population
            if (r["venue"], r["session"]) == ("KRX", "KRX_REGULAR")
        ]
        baseline = metrics(
            [
                r
                for r in population
                if r["action"] == "ENTER_NOW" and r["candidate_source_valid"]
            ]
        )
        direct = metrics([r for r in population if r["candidate"]])
        retried = metrics(
            [
                r["retry"] if r["retry"] else r
                for r in population
                if r["candidate"] or r["retry"]
            ]
        )
        candidates = {("C" if samsung else "D"): direct, "E": retried}
        if not any(r["retry"] for r in population):
            retried["duplicate_of"] = "C" if samsung else "D"
        groups["samsung" if samsung else "non_samsung"] = dict(
            population_count=len(population),
            baseline=baseline,
            candidates=candidates,
            selection=choose(baseline, candidates),
            source_valid_count=sum(r["candidate_source_valid"] for r in population),
            source_gap_count=sum(not r["candidate_source_valid"] for r in population),
        )
        groups["samsung" if samsung else "non_samsung"]["by_scope"] = {
            "|".join(key): dict(
                observation_count=len(values),
                native_actions=dict(Counter(r["native_action"] for r in values)),
                stages=dict(Counter(str(r["source_event_stage"]) for r in values)),
            )
            for key, values in _partition(rows, samsung).items()
        }
        # Provider-screened cases use their own exact response denominator.
        # They are not mixed into the independent machine opportunity rate.
        screens = [
            r
            for r in rows
            if r["auxiliary_screen"] and (r["stock_code"] == "005930") == samsung
        ]
        screen_baseline = metrics(
            [
                r
                for r in screens
                if not r["auxiliary_screen"]["validation_errors"]
                and r["auxiliary_screen"]["risk_field_projection"]["risk_verdict"]
                == "PASS"
                and not r["auxiliary_screen"]["remote_guard_applied"]
            ]
        )
        screen_candidates = {
            name: metrics(
                [r for r in screens if r["auxiliary_screen"][name + "_eligible"]]
            )
            for name in ("A", "B")
        }
        groups["samsung" if samsung else "non_samsung"]["auxiliary_comparison"] = dict(
            exact_linked_count=len(screens),
            baseline=screen_baseline,
            candidates=screen_candidates,
            selection=choose(screen_baseline, screen_candidates),
        )
    return seal(
        dict(
            schema=SCHEMA,
            target_date=target_date,
            exit_contract=EXIT,
            price_basis=price_basis,
            runtime_effect=False,
            allowed_runtime_apply=False,
            actual_order_submitted=False,
            broker_order_forbidden=True,
            result_is_realized_profit=False,
            external_price_is_execution_receipt=False,
            source_receipt=dict(
                path=str(path.resolve()),
                bytes=byte_count,
                sha256=source_hash.hexdigest(),
                byte_basis="decompressed_prefix"
                if path.suffix == ".gz"
                else "file_prefix",
            ),
            trace_source_receipt=trace_receipt,
            price_source_receipts=price_receipts,
            bundle_sha256=bundle.get("bundle_sha256"),
            kernel_sha256=digest(kernel_seals()),
            kernel_seals=kernel_seals(),
            frozen_cutoff=cutoff,
            included_count=len(rows),
            excluded_count=sum(excluded.values()),
            total_count=len(rows) + sum(excluded.values()),
            exclusions=dict(excluded),
            independent_opportunity_count=len(anchors),
            deduplicated_count=len(rows) - len(anchors),
            comparison_contract_sha256=digest(
                dict(
                    exit_contract=EXIT,
                    price_basis=price_basis,
                    kernels=kernel_seals(),
                    machine_policies={
                        key: digest(value["machine_policy"])
                        for key, value in (bundle.get("scope_policies") or {}).items()
                    },
                )
            ),
            groups=groups,
            observations=rows,
            uncertainty="Observational price scenarios; no actual fill or paired execution evidence.",
        )
    )


def _partition(rows, samsung):
    partitions = defaultdict(list)
    for row in rows:
        if (row["stock_code"] == "005930") == samsung:
            partitions[(row["venue"], row["session"])].append(row)
    return partitions


def refresh_daily_projection(data_root, day, bundle):
    """Existing postclose owner reuses cached prices; no fetch or publication."""
    import fcntl

    if not isinstance(bundle, dict):
        return dict(
            status="source_gap", reason="exact_incumbent_missing", runtime_effect=False
        )
    price = (
        Path(data_root)
        / "report/machine_completed_price_source"
        / f"machine_completed_price_source_{day}.json"
    )
    if not price.is_file():
        return dict(
            status="source_gap",
            reason="cached_completed_price_source_missing",
            runtime_effect=False,
        )
    output = (
        Path(data_root)
        / "report/ai_decision_action_outcome_calibration"
        / f"main_submit_drought_research_{day}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            previous = load_projection(data_root, day)
            if previous.get("status") == "observed_price_counterfactual":
                stored = json.loads(output.read_text())
                source = Path(stored["source_receipt"]["path"])
                if (
                    source.suffix != ".gz"
                    and source.stat().st_size == stored["source_receipt"]["bytes"]
                    and stored.get("price_basis") == "native_completed_minute_price_cf"
                    and stored.get("bundle_sha256") == bundle.get("bundle_sha256")
                    and stored.get("frozen_cutoff") is None
                ):
                    return previous
            result = build_daily(data_root=data_root, target_date=day, bundle=bundle)
            result = seal(
                {
                    k: v
                    for k, v in {
                        **result,
                        "compatible_cumulative_comparison": cumulative_projection(
                            data_root, result
                        ),
                    }.items()
                    if k != "artifact_content_sha256"
                }
            )
            from src.engine.scalping.ai_action_outcome_calibration import (
                _atomic_write_json,
            )

            _atomic_write_json(output, result)
            return load_projection(data_root, day)
        except (ValueError, KeyError, OSError, TypeError) as exc:
            return dict(status="source_gap", reason=str(exc), runtime_effect=False)


def _merge_metrics(values):
    merged = {
        k: sum(v[k] for v in values)
        for k in (
            "selected_count",
            "mature_count",
            "pending_count",
            "wins",
            "losses",
            "zero_count",
        )
    }
    merged["win_rate"] = (
        merged["wins"] / merged["mature_count"] if merged["mature_count"] else None
    )
    for field, count in (("average_win_pct", "wins"), ("average_loss_pct", "losses")):
        merged[field] = (
            sum(v[field] * v[count] for v in values if v[count]) / merged[count]
            if merged[count]
            else None
        )
    merged["cumulative_net_pct"] = (
        sum(v["cumulative_net_pct"] for v in values if v["mature_count"])
        if merged["mature_count"]
        else None
    )
    losses = [
        v["maximum_loss_pct"] for v in values if v["maximum_loss_pct"] is not None
    ]
    merged["maximum_loss_pct"] = min(losses) if losses else None
    merged["selected_symbols"] = sorted(
        {symbol for v in values for symbol in v["selected_symbols"]}
    )
    merged["symbols"] = len(merged["selected_symbols"])
    states = Counter()
    for v in values:
        states.update(v["outcome_states"])
    merged["outcome_states"] = dict(states)
    return merged


def cumulative_projection(data_root, current):
    """Merge daily metrics once per date; changed definitions stay partitioned."""
    compatible, excluded = [current], []
    root = Path(data_root) / "report/ai_decision_action_outcome_calibration"
    for path in sorted(root.glob("main_submit_drought_research_*.json")):
        old = json.loads(path.read_text())
        day = old.get("target_date")
        if not isinstance(day, str) or day >= current["target_date"]:
            continue
        if (
            old.get("comparison_contract_sha256")
            != current["comparison_contract_sha256"]
        ):
            excluded.append(
                dict(
                    target_date=day,
                    reason="comparison_definition_or_price_basis_changed",
                )
            )
            continue
        if (
            load_projection(data_root, day).get("status")
            != "observed_price_counterfactual"
        ):
            excluded.append(
                dict(target_date=day, reason="source_or_kernel_receipt_invalid")
            )
            continue
        compatible.append(old)
    groups = {}
    for scope in ("samsung", "non_samsung"):
        values = [r["groups"][scope] for r in compatible]
        baseline = _merge_metrics([v["baseline"] for v in values])
        candidates = {
            key: _merge_metrics([v["candidates"][key] for v in values])
            for key in values[0]["candidates"]
        }
        if all(v["candidates"]["E"].get("duplicate_of") for v in values):
            candidates["E"]["duplicate_of"] = "C" if scope == "samsung" else "D"
        groups[scope] = dict(
            baseline=baseline,
            candidates=candidates,
            selection=choose(baseline, candidates),
        )
        auxiliary = [v["auxiliary_comparison"] for v in values]
        aux_baseline = _merge_metrics([v["baseline"] for v in auxiliary])
        aux_candidates = {
            key: _merge_metrics([v["candidates"][key] for v in auxiliary])
            for key in ("A", "B")
        }
        groups[scope]["auxiliary_comparison"] = dict(
            baseline=aux_baseline,
            candidates=aux_candidates,
            selection=choose(aux_baseline, aux_candidates),
            exact_linked_count=sum(v["exact_linked_count"] for v in auxiliary),
        )
    return dict(
        schema="main_submit_drought_compatible_cumulative_v1",
        comparison_contract_sha256=current["comparison_contract_sha256"],
        sources=[
            dict(
                target_date=v["target_date"],
                source_sha256=v["source_receipt"]["sha256"],
            )
            for v in compatible
        ],
        incompatible_sources=excluded,
        groups=groups,
        runtime_effect=False,
        result_is_realized_profit=False,
    )


def load_projection(data_root, day):
    path = (
        Path(data_root)
        / "report/ai_decision_action_outcome_calibration"
        / f"main_submit_drought_research_{day}.json"
    )
    if not path.is_file():
        return dict(status="not_observed", runtime_effect=False)
    try:
        v = json.loads(path.read_text())
        if (
            v.get("schema") != SCHEMA
            or v.get("target_date") != day
            or v.get("artifact_content_sha256")
            != digest({k: x for k, x in v.items() if k != "artifact_content_sha256"})
            or v.get("kernel_sha256") != digest(kernel_seals())
            or v.get("exit_contract") != EXIT
            or v.get("total_count")
            != v.get("included_count", 0) + v.get("excluded_count", 0)
            or any(
                v.get(k) is not x
                for k, x in (
                    ("runtime_effect", False),
                    ("allowed_runtime_apply", False),
                    ("actual_order_submitted", False),
                    ("broker_order_forbidden", True),
                    ("result_is_realized_profit", False),
                )
            )
        ):
            raise ValueError("research_contract_invalid")
        for receipt in (v["source_receipt"], v.get("trace_source_receipt")):
            if not receipt:
                continue
            source = Path(receipt["path"])
            opener = gzip.open if source.suffix == ".gz" else open
            h = hashlib.sha256()
            remaining = receipt["bytes"]
            with opener(source, "rb") as stream:
                while remaining:
                    blob = stream.read(min(remaining, 1024 * 1024))
                    if not blob:
                        raise ValueError("research_source_prefix_missing")
                    h.update(blob)
                    remaining -= len(blob)
            if h.hexdigest() != receipt["sha256"]:
                raise ValueError("research_source_prefix_changed")
        for price_receipt in v["price_source_receipts"]:
            if (
                hashlib.sha256(Path(price_receipt["path"]).read_bytes()).hexdigest()
                != price_receipt["sha256"]
            ):
                raise ValueError("research_price_source_changed")
        return dict(
            status="observed_price_counterfactual",
            path=str(path.resolve()),
            artifact_content_sha256=v["artifact_content_sha256"],
            groups=v["groups"],
            price_basis=v["price_basis"],
            runtime_effect=False,
            result_is_realized_profit=False,
            cumulative=v.get("compatible_cumulative_comparison"),
        )
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return dict(status="source_gap", reason=str(exc), runtime_effect=False)
