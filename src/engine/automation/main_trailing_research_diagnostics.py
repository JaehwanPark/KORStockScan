"""Source-bound exit research diagnostics, without selection/order authority.

The automation package owns this report consumer. Existing replay/selector
metrics retain their realized-profit floor. Pure modeled exit differences and
incomplete observed price paths are separately labeled diagnostics.
"""

from collections import Counter, defaultdict
from pathlib import Path
import hashlib
from itertools import product

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.scalping.main_stop_replay import cost_known_epoch
from src.engine.scalping.pre_submit_delay_initial_policy import digest, number
from src.engine.scalping.trailing_threshold_policy import market_type_at
from src.engine.scalping.universal_trailing_replay import (
    quote_source_digest,
    expand_ws,
    _route_depths,
)
from .main_trailing_all_scope_research import _sealed, _source_path, code_contract

SCHEMA = "main_trailing_execution_diagnostics_v1"


class JointTrailingObservation:
    """One M1 pass feeds 72 fixed hypotheses; observed crossings, not fills.

    No fitted winner, provider, new raw scan or runtime policy is produced.
    A net floor arms only after an executable bid reached it; ticks/gaps can
    overshoot it. Missing history permanently censors whole-path inference.
    """

    def __init__(self, position, parent, *, usable, classifier_config=None):
        self.position, self.parent, self.usable = position, parent, usable
        self.config = classifier_config or {}
        self.m1, self.alternative, self.adverse = {}, False, 0
        self.previous, self.market = None, None
        self.gaps, self.work = Counter(), 0
        if position.get("source_gap"):
            self.gaps["position_source_gap"] += 1
        self.rows = [
            dict(
                start_delta_pct=s,
                weak_multiplier=w,
                strong_multiplier=t,
                net_floor_pct=f,
                release=r,
                armed=False,
                floor_armed=False,
                crossing=None,
            )
            for s, w, t, f, r in product(
                (-0.2, 0.0, 0.2),
                (0.5, 1.0),
                (0.5, 1.0),
                (None, 0.0, 0.2),
                ("incumbent", "flow_and_tape_two"),
            )
        ]

    def observe(self, event, *, verified):
        from src.engine.scalping.trailing_mechanical_strength import classify_ws_history
        from src.engine.scalping.trailing_exit_decision import (
            evaluate_trailing_take_profit,
        )

        if event.get("kind") == "ADD":
            self.usable = False
            self.gaps["add_requires_separate_generation"] += 1
            return
        if (
            event.get("kind") not in {"QUOTE", "GAP"}
            and event.get("status") != "source_gap"
        ):
            return
        if not verified:
            self.gaps["unverified_quote_or_interval"] += 1
            return
        known = event["known_at"]
        if self.previous is not None and known < self.previous:
            self.gaps["clock_regression"] += 1
            return
        if known - (self.previous or self.position["entry_at"]) > 2:
            self.gaps["unobserved_interval"] += 1
        self.previous = known
        market = market_type_at(known)
        if market not in self.parent:
            self.gaps["market_unobserved"] += 1
            return
        if market != self.market:
            self.alternative, self.adverse, self.market = False, 0, market
        try:
            strength, self.m1 = classify_ws_history(
                expand_ws(event["ws_data"]),
                self.m1,
                now_ms=int(known * 1000),
                max_quote_age_ms=int(event["max_quote_age_sec"] * 1000),
                market=market,
                config=self.config.get(market),
            )
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            self.gaps["classifier_source_invalid"] += 1
            return
        for obs in strength.new_observations:
            if obs["at_ms"] < self.position["entry_at"] * 1000:
                continue
            ofi, qi, tape = (
                number(obs.get(k))
                for k in ("ofi_proxy", "queue_imbalance", "signed_trade_qty")
            )
            if any(v is None for v in (ofi, qi, tape)):
                self.alternative, self.adverse = False, 0
            elif obs["reason"] == "book_and_trade_support":
                self.alternative, self.adverse = True, 0
            elif self.alternative and ofi < 0 and tape < 0:
                self.adverse += 1
                if self.adverse >= 2:
                    self.alternative, self.adverse = False, 0
            else:
                self.adverse = 0
        if strength.state == "UNKNOWN":
            self.gaps["classifier_unknown"] += 1
            self.alternative, self.adverse = False, 0
            return
        if not self.usable:
            return
        p = self.position
        cost = p["cost_model"]
        qty, basis = number(p["qty"]), number(p["buy_basis_krw"])
        buy_cost, sell_rate = number(cost["buy_cost_krw"]), number(
            cost["sell_cost_rate"]
        )

        def net(price, slippage=0):
            return 100 * (
                (
                    price * qty * (1 - slippage / 10000) * (1 - sell_rate)
                    - buy_cost
                    - basis
                )
                / basis
            )

        peak, bid = number(event.get("trade_peak_price")), number(event.get("bid"))
        if peak is None or peak <= 0 or bid is None or bid <= 0:
            self.gaps["price_unobserved"] += 1
            return
        parent = self.parent[market]
        profit, peak_profit = net(bid), round(net(peak), 2)
        for row in self.rows:
            if row["crossing"] is not None:
                continue
            start = max(
                0.1,
                round(parent["SCALP_TRAILING_START_PCT"] + row["start_delta_pct"], 6),
            )
            strong = (
                strength.strong if row["release"] == "incumbent" else self.alternative
            )
            decision = evaluate_trailing_take_profit(
                peak_price=peak,
                executable_bid=bid,
                peak_profit_pct=peak_profit,
                start_pct=start,
                strong=strong,
                weak_limit_pct=parent["SCALP_TRAILING_LIMIT_WEAK"]
                * row["weak_multiplier"],
                strong_limit_pct=parent["SCALP_TRAILING_LIMIT_STRONG"]
                * row["strong_multiplier"],
                already_armed=row["armed"],
            )
            row["armed"] = decision.armed
            floor = row["net_floor_pct"]
            breach = (
                row["floor_armed"] and profit <= floor if floor is not None else False
            )
            if floor is not None and decision.armed and profit > floor:
                row["floor_armed"] = True
            self.work += 1
            if not (decision.triggered or breach):
                continue
            sufficient = number(event["bid_qty"]) >= qty
            row["crossing"] = dict(
                known_at=known,
                event_at=event["event_at"],
                market=market,
                bid=bid,
                source_sha256=event["source_sha256"],
                start_pct=start,
                width_pct=decision.threshold_pct,
                strength="STRONG" if strong else "WEAK",
                trigger="net_floor_breach" if breach else "peak_drawdown",
                full_visible_depth=sufficient,
                observed_quote_net_pct=profit if sufficient else None,
                slippage_sensitivity_pct={
                    str(b): net(bid, b) if sufficient else None for b in (0, 30, 100)
                },
                path_censored=bool(self.gaps),
            )

    def result(self):
        return dict(
            schema="main_joint_trailing_observation_v1",
            sampling_contract="observed_quote_snapshots_not_each_buffered_depth_event",
            hypotheses=self.rows,
            hypothesis_count=len(self.rows),
            evaluations=self.work,
            gaps=dict(self.gaps),
            cost_model_usable=self.usable,
            complete_lifecycle_verified=False,
            primary_ev=None,
            selected_candidate=None,
            actual_profit_verified=False,
            runtime_effect=False,
            allowed_runtime_apply=False,
            metric_contract=dict(
                metric_role="observed_price_sensitivity",
                decision_authority="report_only",
                window_policy="frozen_observed_quotes_only",
                sample_floor="no_selection_from_diagnostic_samples",
                primary_decision_metric="source_bound_observed_crossing",
                source_quality_gate="same_position_route_epoch_clock_hash_depth_and_frozen_cost",
                forbidden_uses=[
                    "runtime_apply",
                    "actual_pnl",
                    "first_crossing_in_missing_interval",
                    "holdout_claim",
                ],
            ),
        )


def _verified_touch(event, position, entry, cutoff):
    at, known = number(event.get("event_at")), number(event.get("known_at"))
    age = number(event.get("max_quote_age_sec"))
    route, item, epoch = (event.get(k) for k in ("route", "item", "transport_epoch"))
    market = market_type_at(known) if known is not None else None
    expected_route = (position.get("routes_by_market") or {}).get(
        market, position.get("route")
    )
    expected_item = (position.get("items_by_market") or {}).get(
        market, position.get("item")
    )
    if (
        at is None
        or known is None
        or age is None
        or not 0 < age <= 0.7
        or at < entry
        or at > known
        or known > cutoff
        or known - at > age
        or route != expected_route
        or item != expected_item
        or not item
        or type(epoch) is not int
        or epoch < 0
        or type(event.get("sequence")) is not int
        or event["sequence"] <= 0
        or event.get("coverage_complete") is not True
        or event.get("source_kind") != "tick_depth"
        or event.get("source_sha256") != quote_source_digest(event)
        or not isinstance(event.get("ws_data"), dict)
        or event.get("quote_snapshot_sha256") != digest(event["ws_data"])
    ):
        return False
    try:
        ws = expand_ws(event["ws_data"])
        if (
            ws.get("market_data_transport_epoch") != epoch
            or (ws.get("last_realtime_type_item") or {}).get("0D") != item
            or str(
                (ws.get("last_realtime_type_market_route") or {}).get("0D") or ""
            ).upper()
            != str(route).upper()
        ):
            return False
        latest = max(
            _route_depths(ws, route, item, epoch),
            key=lambda r: number(r.get("received_at_ms")) or 0,
            default={},
        )
        bid = (latest.get("bid_levels") or [{}])[0]
        ask = (latest.get("ask_levels") or [{}])[0]
        received = number(latest.get("received_at_ms"))
        return (
            received is not None
            and 0 <= known - received / 1000 <= age
            and latest.get("route_sequence") == event["sequence"]
            and number(bid.get("price")) == number(event.get("bid"))
            and number(ask.get("price")) == number(event.get("ask"))
            and number(bid.get("quantity")) == number(event.get("bid_qty"))
            and number(event.get("bid")) is not None
            and 0 < number(event["bid"]) <= number(event["ask"])
            and number(event.get("bid_qty")) is not None
            and number(event["bid_qty"]) >= 0
        )
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return False


def _observation(position, events, parent, cutoff, *, classifier_config=None):
    """Describe verified observed quotes; never assert missing path outcomes."""
    qty = number(position.get("qty"))
    basis = number(position.get("buy_basis_krw"))
    entry = number(position.get("entry_at"))
    model = position.get("cost_model") or {}
    cost, rate = number(model.get("buy_cost_krw")), number(model.get("sell_cost_rate"))
    known = cost_known_epoch(model.get("known_at"))
    usable = (
        qty is not None
        and qty > 0
        and qty.is_integer()
        and basis is not None
        and basis > 0
        and entry is not None
        and entry > 0
        and known is not None
        and known <= entry
        and cost is not None
        and cost >= 0
        and rate is not None
        and 0 <= rate < 0.05
        and bool(model.get("source_sha256"))
    )
    counts, reasons = Counter(), Counter()
    peak_net, bid_net = None, None
    first, last, previous, reached = None, None, None, False
    lifecycle_changed = False
    joint = JointTrailingObservation(
        position, parent, usable=usable, classifier_config=classifier_config
    )
    for event in events:
        counts["events"] += 1
        if not isinstance(event, dict):
            reasons["event_not_object"] += 1
            joint.gaps["event_not_object"] += 1
            continue
        verified = (
            entry is not None and _verified_touch(event, position, entry, cutoff)
            if event.get("kind") == "QUOTE"
            else False
        )
        joint.observe(event, verified=verified)
        if event.get("kind") == "ADD":
            lifecycle_changed = True
            reasons["add_observation_requires_separate_generation"] += 1
            continue
        if event.get("kind") != "QUOTE":
            continue
        counts["quote_events"] += 1
        available = number(event.get("known_at"))
        if available is not None and available > cutoff:
            reasons["quote_after_cutoff"] += 1
            continue
        if not verified:
            reasons["quote_source_or_entry_unverified"] += 1
            continue
        if previous is not None and available < previous:
            reasons["quote_clock_regression"] += 1
            continue
        if previous is not None and available - previous > 2:
            counts["observed_gaps_over_two_seconds"] += 1
        previous = available
        first = available if first is None else first
        last = available
        counts["source_verified_observed_quotes"] += 1
        if not usable or lifecycle_changed:
            continue
        bid, peak = number(event.get("bid")), number(event.get("trade_peak_price"))
        if bid is None or bid <= 0 or peak is None or peak <= 0:
            reasons["observed_price_missing"] += 1
            continue
        current_net = round(100 * ((bid * qty * (1 - rate) - basis - cost) / basis), 2)
        current_peak = round(
            100 * ((peak * qty * (1 - rate) - basis - cost) / basis), 2
        )
        bid_net = current_net if bid_net is None else max(bid_net, current_net)
        peak_net = current_peak if peak_net is None else max(peak_net, current_peak)
        market = market_type_at(available)
        values = parent.get(market)
        if values and current_peak >= values["SCALP_TRAILING_START_PCT"]:
            reached = True
    state = (
        ("observed_start_reached" if reached else "observed_start_not_reached")
        if peak_net is not None
        else "unassessable"
    )
    return dict(
        state=state,
        counts=dict(counts),
        reasons=dict(reasons),
        first_observed_at=first,
        last_observed_at=last,
        observation_delay_sec=(
            first - entry if first is not None and entry is not None else None
        ),
        maximum_observed_peak_net_pct=peak_net,
        maximum_observed_bid_net_pct=bid_net,
        complete_lifecycle_verified=False,
        actual_profit_verified=False,
        model_cost_usable=bool(usable),
        lifecycle_changed=lifecycle_changed,
        joint_trailing_observation=joint.result(),
    )


def build(manifest_path, *, input_root, report_path):
    """Consume sealed input/results; bounded cost evidence, no operational files."""
    from src.engine.lifecycle.research_disk_budget import use

    output = Path(report_path).resolve().parent
    with (
        use(output),
        storage.index(output / "scratch") as allocated_index,
        storage.index(output / "scratch") as joint_index,
    ):
        return _build(
            manifest_path,
            input_root=input_root,
            report_path=report_path,
            allocated_index=allocated_index,
            joint_index=joint_index,
        )


def _build(manifest_path, *, input_root, report_path, allocated_index, joint_index):
    root, report_path = Path(input_root).resolve(), Path(report_path).resolve()
    output = report_path.parent
    before = byte_generation(report_path)
    manifest_before = byte_generation(Path(manifest_path))
    manifest, report = _sealed(Path(manifest_path)), _sealed(report_path)
    if (
        report.get("status") != "complete"
        or report.get("schema") != "main_all_scope_exit_research_v2"
        or report.get("code_contract_sha256") != code_contract()
        or report.get("input_manifest_path") != str(Path(manifest_path).resolve())
        or report.get("input_manifest_generation") != manifest_before
        or report.get("source_date") != manifest.get("source_date")
        or report.get("target_date") != manifest.get("target_date")
        or report.get("allowed_runtime_apply") is not False
    ):
        raise ValueError("trailing_diagnostic_report_binding_invalid")
    cohort_counts, statuses = Counter(), Counter()
    comparisons = defaultdict(lambda: dict(n=0, delta=0.0, notional=0.0, percent=0.0))
    result_ids = set()
    allocated_counts = Counter()
    allocated_comparisons = defaultdict(lambda: dict(n=0, delta=0.0, notional=0.0))
    from src.engine.lifecycle.holding_research_cost import valid_annotation

    for reference in storage.iter_tree(output, report["partition_results_ref"]):
        checkpoint = _sealed(_source_path(output, reference["path"]))
        if checkpoint["artifact_sha256"] != reference["artifact_sha256"]:
            raise ValueError("trailing_diagnostic_checkpoint_binding_invalid")
        aliases = checkpoint["candidate_aliases"]
        parent_sha = aliases["incumbent"]
        for row in storage.iter_tree(output, checkpoint["result_records_ref"]):
            row = storage.expand_outcomes(output, row)
            identity, context = row["identity"], row["context"]
            if identity in result_ids:
                raise ValueError("trailing_diagnostic_duplicate_identity")
            result_ids.add(identity)
            kind = context["evidence_kind"]
            cohort_counts[kind] += 1
            baseline = row["outcomes"][parent_sha]
            statuses[(kind, baseline["status"], baseline.get("reason"))] += 1
            basis = number(context.get("buy_basis_krw"))
            base_net = number(baseline.get("modeled_net_pnl_krw"))
            allocated = context.get("holding_research_cost")
            if allocated is not None and not valid_annotation(
                allocated, dict(context, position_key=identity)
            ):
                raise ValueError("holding_research_cost_annotation_invalid")
            if allocated is not None and kind == "actual_completed":
                storage.put(
                    allocated_index, identity, dict(identity=identity, **allocated)
                )
                allocated_counts[allocated["status"]] += 1
            for name, sha in aliases.items():
                outcome = row["outcomes"][sha]
                net = number(outcome.get("modeled_net_pnl_krw"))
                if (
                    basis is None
                    or basis <= 0
                    or base_net is None
                    or net is None
                    or baseline.get("status") != "modeled_full_exit"
                    or outcome.get("status") != "modeled_full_exit"
                ):
                    continue
                if (
                    kind == "actual_entry_alternative_exit"
                    and allocated is not None
                    and allocated.get("status") == "research_cost_allocated"
                ):
                    reference = number(allocated.get("allocated_net_pnl_krw"))
                    total_basis = number(allocated.get("buy_basis_krw"))
                    known = cost_known_epoch(allocated.get("cost_available_at"))
                    if (
                        reference is None
                        or total_basis is None
                        or total_basis <= 0
                        or known is None
                        or known > manifest["as_of"]
                    ):
                        raise ValueError(
                            "holding_research_cost_annotation_economics_invalid"
                        )
                    diagnostic = allocated_comparisons[name]
                    diagnostic["n"] += 1
                    diagnostic["delta"] += net - max(base_net, reference)
                    diagnostic["notional"] += total_basis
                metric = comparisons[(kind, name)]
                metric["n"] += 1
                metric["delta"] += net - base_net
                metric["percent"] += 100 * (net - base_net) / basis
                metric["notional"] += basis
    observations, input_ids = [], set()
    parent = manifest["approved_parent_receipt"]["market_values"]
    for reference in storage.iter_tree(root, manifest["partitions_ref"]):
        partition = _sealed(
            _source_path(root, reference["path"]), reference["artifact_sha256"]
        )
        for position in partition["positions"]:
            identity = position["position_key"]
            if identity in input_ids:
                raise ValueError("trailing_diagnostic_duplicate_input")
            input_ids.add(identity)
            if position["evidence_kind"] == "actual_entry_alternative_exit":
                continue
            from src.engine.lifecycle.research_input_budget import Claim

            with Claim(128 * 1024):
                observation = _observation(
                    position,
                    storage.iter_tree(root, partition["paths"][identity]),
                    parent,
                    manifest["as_of"],
                    classifier_config=manifest["approved_parent_receipt"].get(
                        "classifier_parameters"
                    ),
                )
                storage.put(
                    joint_index,
                    identity,
                    dict(
                        identity=identity,
                        symbol=position.get("symbol"),
                        evidence_kind=position["evidence_kind"],
                        **observation.pop("joint_trailing_observation"),
                    ),
                )
            observations.append(
                dict(
                    identity=identity,
                    symbol=position.get("symbol"),
                    evidence_kind=position["evidence_kind"],
                    automatic_management_allowed=position.get(
                        "automatic_management_allowed"
                    ),
                    route=position.get("route"),
                    **observation,
                )
            )
    if input_ids != result_ids:
        raise ValueError("trailing_diagnostic_population_mismatch")
    observed = Counter((row["evidence_kind"], row["state"]) for row in observations)
    metrics = []
    for (kind, name), value in sorted(comparisons.items()):
        metrics.append(
            dict(
                evidence_kind=kind,
                candidate=name,
                paired_count=value["n"],
                exit_only_paired_delta_net_krw=value["delta"],
                exit_only_equal_weight_delta_pct=value["percent"] / value["n"],
                exit_only_notional_weighted_delta_pct=100
                * value["delta"]
                / value["notional"],
            )
        )
    if (
        byte_generation(report_path) != before
        or byte_generation(Path(manifest_path)) != manifest_before
        or code_contract() != report["code_contract_sha256"]
    ):
        raise ValueError("trailing_diagnostic_input_changed")
    body = dict(
        schema=SCHEMA,
        source_date=manifest["source_date"],
        target_date=manifest["target_date"],
        diagnostic_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        report_path=str(report_path),
        report_generation=before,
        input_manifest_path=str(Path(manifest_path).resolve()),
        input_manifest_generation=manifest_before,
        population_count=len(result_ids),
        cohort_counts=dict(cohort_counts),
        incumbent_outcomes=[
            dict(evidence_kind=k[0], status=k[1], reason=k[2], count=n)
            for k, n in sorted(statuses.items(), key=lambda x: str(x[0]))
        ],
        observation_counts=[
            dict(evidence_kind=k[0], state=k[1], count=n)
            for k, n in sorted(observed.items())
        ],
        position_observations=observations,
        joint_trailing_observations_ref=storage.write_tree(
            output, (value for _, value, _ in storage.records(joint_index))
        ),
        exit_only_comparisons=metrics,
        holding_allocated_cost_rows_ref=storage.write_tree(
            output, (value for _, value, _ in storage.records(allocated_index))
        ),
        holding_allocated_cost_status_counts=dict(allocated_counts),
        holding_allocated_cost_comparisons=[
            dict(
                candidate=name,
                paired_count=value["n"],
                candidate_minus_max_parent_allocated_net_krw=value["delta"],
                notional_weighted_delta_pct=100 * value["delta"] / value["notional"],
                economics_scope="main_holding_exit_research_only",
                actual_execution_cost=False,
                actual_pnl_krw=None,
                selector_eligible=False,
                allowed_runtime_apply=False,
            )
            for name, value in sorted(allocated_comparisons.items())
        ],
        economic_comparison_state=(
            "paired_modeled" if metrics else "source_or_execution_insufficient"
        ),
        selector_metrics_redefined=False,
        actual_profit_verified=False,
        runtime_effect=False,
        allowed_runtime_apply=False,
        metric_contract=dict(
            metric_role="funnel_count",
            decision_authority="report_only",
            window_policy="frozen_source_window",
            sample_floor="existing_family_contract",
            primary_decision_metric="existing_selector_unchanged",
            source_quality_gate="sealed_input_and_result_identity",
            forbidden_uses=[
                "runtime_apply",
                "actual_pnl",
                "source_gap_as_zero",
                "parent_carry_as_uplift",
            ],
        ),
    )
    body["artifact_sha256"] = digest(body)
    return body
