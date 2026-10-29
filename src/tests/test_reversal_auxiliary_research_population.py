from collections import defaultdict
import copy
from datetime import datetime
import pytest
from src.engine.scalping import reversal_auxiliary_research_population as R


def test_reuse_only_exact_unchanged_branch_membership():
    bid = next(iter(R.C.OLD.DEFINITIONS))
    extra = next(iter(R.C.NEW_DEFINITIONS))
    old = {"scopes": {"same": [bid], "changed": [bid]}}
    new = {"scopes": {"same": [bid], "changed": [bid, extra]}}
    assert R.unchanged_scopes(old, new) == {"same"}


def test_premarket_inventory_does_not_require_aftermarket_only_date(
    tmp_path, monkeypatch
):
    from src.engine.scalping import continuous_reversal_source as source

    for day, session in [
        ("2026-10-13", "SOR_AFTERMARKET"),
        ("2026-10-28", "NXT_PREMARKET"),
    ]:
        folder = (
            tmp_path
            / "observations/scalp_micro_reversion_forward"
            / ("trade_date=" + day)
            / ("venue=NXT/session=" + session)
        )
        folder.mkdir(parents=True)
        (folder / "market_stream.jsonl").write_bytes(b"inventory must not decode raw")
    monkeypatch.setattr(
        source,
        "_source_quality_receipt",
        lambda *a: dict(eligible=True, status="closed_main_raw_epochs", receipts=[]),
    )
    machine = dict(
        partitions=[
            dict(normalized_source=dict(day="2026-10-28", session="NXT_PREMARKET"))
        ]
    )
    result = R.retained_source_inventory(
        tmp_path, machine, as_of="2026-10-28", market="PRE"
    )
    assert result["missing_eligible_dates"] == []
    assert result["empty_scope_dates"] == ["2026-10-13"]
    assert [r["day"] for r in result["rows"]] == ["2026-10-28"]
    with pytest.raises(ValueError, match="market_invalid"):
        R.retained_source_inventory(
            tmp_path, machine, as_of="2026-10-28", market="unknown"
        )


def test_reservoir_is_bounded_and_win_fail_blind():
    first = defaultdict(dict)
    second = defaultdict(dict)
    for i in range(100):
        p = dict(opportunity_key=str(i), scope="scope", outcome={"status": "WIN"})
        R.select(first, p, None, seed="fixed", limit=6)
        p["outcome"] = {"status": "FAIL_STOP"}
        R.select(second, p, None, seed="fixed", limit=6)
    assert len(first["scope"]) == 6
    assert set(first["scope"]) == set(second["scope"])


def test_retained_date_inventory_finds_omitted_valid_day_without_reading_raw(
    tmp_path, monkeypatch
):
    from src.engine.scalping import continuous_reversal_source as source

    for day in ["2026-09-28", "2026-10-12", "2026-10-13", "2026-10-16", "2026-10-17"]:
        folder = (
            tmp_path
            / "observations/scalp_micro_reversion_forward"
            / ("trade_date=" + day)
            / "venue=SOR/session=SOR_REGULAR"
        )
        folder.mkdir(parents=True)
        (folder / "market_stream.jsonl").write_bytes(
            b"raw must not be decoded by the inventory"
        )
    monkeypatch.setattr(
        source,
        "_source_quality_receipt",
        lambda root, day: dict(
            eligible=day != "2026-10-16",
            status="valid" if day != "2026-10-16" else "unverified",
            receipts=[],
        ),
    )
    machine = dict(partitions=[dict(normalized_source={"day": "2026-10-12"})])
    result = R.retained_source_inventory(tmp_path, machine, as_of="2026-10-16")
    assert result["missing_eligible_dates"] == ["2026-10-13"]
    assert result["excluded_unverified_dates"] == ["2026-10-16"]
    assert [x["day"] for x in result["rows"]] == [
        "2026-10-12",
        "2026-10-13",
        "2026-10-16",
    ]


def cumulative_source(tmp_path):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    sid = "036930|REGULAR|GE_100000|SOR"
    bid = next(iter(R.C.OLD.DEFINITIONS))
    manifest = dict(scopes={sid: [bid]}, detector_manifest_hash="a" * 64)
    parent = dict(
        continuous_reversal=dict(
            schema="continuous_reversal_policy_v6", operating_manifest=manifest
        )
    )
    parent["bundle_sha256"] = N.digest(parent)
    day = "2026-10-15"
    at = datetime(2026, 10, 15, 10, tzinfo=R.K.KST).timestamp()
    source = tmp_path / "normalized.json.gz"
    source.write_bytes(b"original frozen source")
    points = []
    with R.S.Store(tmp_path) as store:
        for index, (truth, status) in enumerate(
            [
                ("TRUE", "WIN"),
                ("FALSE", "WIN"),
                ("TRUE", "UNRESOLVED"),
                ("TRUE", "FAIL_STOP"),
            ]
        ):
            event = dict(
                symbol="036930",
                market="REGULAR",
                venue="SOR",
                epoch=at + index,
                branch_signals={bid: {"signal_id": str(index)}},
            )
            obj = store.put([event, {"branch_inputs": {bid: {}}}])
            points.append(
                dict(
                    opportunity_key=str(index),
                    scope=sid,
                    symbol="036930",
                    day=day,
                    truth={bid: truth},
                    outcome={"status": status, "hit_at": at + 60},
                    snapshot_obj=obj,
                )
            )
        records_obj = store.put(points)
    part = dict(
        normalized_source=dict(
            day=day,
            venue="SOR",
            session="SOR_REGULAR",
            path=str(source),
            sha256=R.P.file_hash(source),
            rows=200,
        ),
        records_object=records_obj,
        records_sha256=R.P.digest(points),
        points=len(points),
    )
    machine = R.P.seal(
        dict(
            source_date=day,
            operating_manifest=manifest,
            label_contract=R.C.LABEL,
            partitions=[part],
            execution_code_sha256="b" * 64,
        )
    )
    return parent, machine, points, source


def test_cumulative_census_uses_all_points_but_only_current_confirmations(tmp_path):
    parent, machine, _, _ = cumulative_source(tmp_path)
    result = R.build_cumulative(tmp_path, parent, machine, seed="blind", per_scope=6)
    counts = next(iter(result["eligible_census"].values()))
    assert counts["all_points"] == 4
    assert counts["current_machine_confirmations"] == 3
    assert counts["not_selected_machine_confirmation"] == 1
    assert counts["outcome_not_evaluable"] == 1
    assert counts["eligible_WIN"] == counts["eligible_FAIL_STOP"] == 1
    with R.S.Store(tmp_path, readonly=True) as store:
        points = store.get(result["partitions"][0]["records_object"])
    assert {p["opportunity_key"] for p in points} == {"0", "3"}
    assert all(
        p["operating_outcome"]["operating_status"] == "not_observed" for p in points
    )
    assert result["allowed_runtime_apply"] is False


def test_cumulative_census_discloses_missing_retained_source_date(
    tmp_path, monkeypatch
):
    parent, machine, _, _ = cumulative_source(tmp_path)
    monkeypatch.setattr(
        R,
        "retained_source_inventory",
        lambda *a, **kw: R.P.seal(
            dict(
                missing_eligible_dates=["2026-10-13"],
                excluded_unverified_dates=[],
                **R.P.AUTH,
            )
        ),
    )
    result = R.build_cumulative(tmp_path, parent, machine, seed="blind")
    assert result["retained_source_coverage_complete"] is False
    assert result["retained_source_inventory"]["missing_eligible_dates"] == [
        "2026-10-13"
    ]


@pytest.mark.parametrize("defect", ["source", "label", "membership", "date", "parent"])
def test_cumulative_population_rejects_changed_source_or_policy(tmp_path, defect):
    parent, machine, _, source = cumulative_source(tmp_path)
    if defect == "source":
        source.write_bytes(b"changed original")
    elif defect == "label":
        machine["label_contract"] = dict(R.C.LABEL, horizon_seconds=600)
    elif defect == "membership":
        machine["operating_manifest"] = dict(scopes={})
    elif defect == "date":
        machine["partitions"][0]["normalized_source"]["day"] = "2026-09-28"
    else:
        parent["bundle_sha256"] = "c" * 64
    machine = R.P.seal(machine)
    with pytest.raises(ValueError):
        R.build_cumulative(tmp_path, parent, machine, seed="blind")


def test_late_conflict_is_removed_from_reservoir_and_eligible_denominator(tmp_path):
    parent, machine, points, _ = cumulative_source(tmp_path)
    bad = copy.deepcopy(points[0])
    bad["outcome"]["status"] = "FAIL_STOP"
    records = points + [bad]
    with R.S.Store(tmp_path) as store:
        ident = store.put(records)
    machine["partitions"][0].update(
        records_object=ident, records_sha256=R.P.digest(records), points=len(records)
    )
    result = R.build_cumulative(tmp_path, parent, R.P.seal(machine), seed="blind")
    counts = next(iter(result["eligible_census"].values()))
    assert counts["eligible_WIN"] == 0
    assert counts["conflicting_source_excluded"] == 1
    with R.S.Store(tmp_path, readonly=True) as store:
        selected = store.get(result["partitions"][0]["records_object"])
    assert [p["opportunity_key"] for p in selected] == ["3"]


def test_manual_handoff_never_becomes_a_realized_loss_or_research_failure():
    from src.engine.scalping.main_stop_policy import digest

    handoff = dict(
        schema="main_stop_handoff_source_v1",
        owner="main",
        position_key="position",
        pin_sha256="a" * 64,
        at=1100.0,
        registered=True,
        source_stage="preset",
        exit_rule="scalp_preset_hard_stop_pct",
        decision_profit_pct=-1.47,
        actual_order_submitted=False,
        handoff_enabled=True,
        actual_realized_net_krw=None,
        allowed_runtime_apply=False,
    )
    handoff["source_sha256"] = digest(handoff)
    label = dict(status="WIN", hit_at=1200.0)
    result = R.operating_path_status(
        label,
        entry_at=1000.0,
        position_key="position",
        pin_sha256="a" * 64,
        handoffs=[handoff],
    )
    assert result["research_status"] == "WIN"
    assert result["operating_status"] == "manual_handoff_before_target"
    assert result["actual_realized_net_krw"] is None
    assert (
        R.operating_path_status(
            label, entry_at=1000.0, position_key="position", pin_sha256="a" * 64
        )["operating_status"]
        == "not_observed"
    )
    changed = dict(handoff, position_key="foreign")
    changed["source_sha256"] = digest(
        {k: v for k, v in changed.items() if k != "source_sha256"}
    )
    with pytest.raises(ValueError, match="handoff_binding_invalid"):
        R.operating_path_status(
            label,
            entry_at=1000.0,
            position_key="position",
            pin_sha256="a" * 64,
            handoffs=[changed],
        )


def history_prefix(root, event, *, received=None, price=100, scope="test", count=5):
    from datetime import timedelta
    from src.trading.market import completed_history as H
    from src.trading.market.session_contract import resolve_market_session

    at = event["epoch"]
    now = received if received is not None else at - 0.01
    clock = datetime.fromtimestamp(at, H.KST)
    end = clock.replace(second=0, microsecond=0) - timedelta(minutes=1)
    rows = [
        dict(
            source_timestamp=(end - timedelta(minutes=count - i - 1)).strftime(
                "%Y%m%d%H%M%S"
            ),
            시가=price,
            고가=price + 2,
            저가=price - 1,
            현재가=price + 1,
            거래량=10 + i,
        )
        for i in range(count)
    ]
    identity = H.key(
        [scope],
        event["source_item"],
        clock.strftime("%Y%m%d"),
        resolve_market_session(clock).session_regime,
    )
    assert H.publish(
        root,
        identity,
        rows,
        dict(
            api_id="ka10080",
            request_code=event["source_item"],
            rest_received_ts_ms=int(now * 1000),
        ),
        now=now,
    )
    return identity, rows


@pytest.mark.parametrize(
    "fault", ["valid", "missing", "future", "stale", "conflict", "early"]
)
def test_causal_history_population_never_borrows_future_or_wrong_scope(tmp_path, fault):
    from src.engine.scalping import reversal_auxiliary_production_input as M

    event = dict(
        epoch=datetime(2026, 10, 29, 10, 5, 30, tzinfo=R.K.KST).timestamp(),
        source_item="097520_NX",
    )
    if fault != "missing":
        observed = dict(event)
        if fault == "stale":
            observed["epoch"] -= 60
        history_prefix(
            tmp_path,
            observed,
            received=event["epoch"] + 1 if fault == "future" else None,
            count=1 if fault == "early" else 5,
        )
    if fault == "conflict":
        history_prefix(tmp_path, event, scope="other", price=200)
    snapshot = [event, {}]
    R.attach_completed_contexts(tmp_path, [snapshot])
    result = M.completed_candle_source(snapshot[1]["entry_candle_context"], event)
    assert result["status"] == (
        "observed" if fault in {"valid", "early"} else "unavailable"
    )
    frozen = copy.deepcopy(snapshot)
    # A correction received after confirmation must not rewrite the snapshot.
    history_prefix(tmp_path, event, received=event["epoch"] + 2, price=300)
    R.attach_completed_contexts(tmp_path, [snapshot])
    assert snapshot == frozen
    if fault == "valid":
        fresh = [event, {}]
        R.attach_completed_contexts(tmp_path, [fresh])
        assert fresh == frozen
        assert result["original_context"]["bars"][-1]["c"] == 101


@pytest.mark.parametrize("available", [True, False])
def test_completed_context_native_campaign_and_selection_consumer(
    tmp_path, monkeypatch, available
):
    from src.tests.test_reversal_auxiliary_production_input import definitions, FIXTURES
    from src.engine.scalping import reversal_auxiliary_registry as G
    from src.engine.scalping import reversal_auxiliary_production_input as M
    from src.engine.scalping import reversal_auxiliary_tuning as T
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.ai import offline_comparison_store as S

    f = copy.deepcopy(next(iter(FIXTURES.values())))
    snapshot = [f["event"], f["source"]]
    original, compact, current = definitions(f)
    scopes = current["production_input_contract"]["scope_ids"]
    sid = scopes[0]
    candidate = G.production_definition(
        compact,
        scope_ids=scopes,
        production_contract=M.contract(scopes, completed_candles=True),
    )
    for definition in (original, compact, current, candidate):
        G.register(tmp_path, definition)
    if available:
        history_prefix(tmp_path, snapshot[0])
    day = datetime.fromtimestamp(snapshot[0]["epoch"], R.K.KST).date().isoformat()
    manifest = dict(
        scopes={sid: list(snapshot[0]["branch_signals"])},
        detector_manifest_hash="a" * 64,
    )
    parent = dict(
        bundle_sha256="b" * 64, continuous_reversal=dict(operating_manifest=manifest)
    )
    with S.Store(tmp_path) as store:
        from src.tests.test_offline_comparison_store import activate

        activate(store)
        point = dict(
            opportunity_key=R.U.opportunity(snapshot[0]),
            scope=sid,
            symbol=snapshot[0]["symbol"],
            day=day,
            outcome=dict(status="WIN"),
            snapshot_obj=store.put(snapshot),
        )
        points = [point]
        obj = store.put(points)
    machine = R.P.seal(
        dict(
            source_date=day,
            operating_manifest=manifest,
            policy_schema="continuous_reversal_policy_v6",
            partitions=[dict(records_object=obj, records_sha256=R.P.digest(points))],
        )
    )
    monkeypatch.setattr(
        I, "effective_bindings", lambda *a, **kw: {sid: current["registry_sha256"]}
    )
    T.configure(
        tmp_path,
        candidate=candidate["registry_sha256"],
        scopes=scopes,
        seed="causal-test",
    )
    campaign = T.prepare(tmp_path, day, machine, parent)
    if not available:
        assert campaign["pairs"] == []
        assert len(campaign["completed_context_exclusions"]) == 1
        calls = T.calls(
            tmp_path,
            day,
            transport=lambda *a, **k: pytest.fail("source gap spent budget"),
        )
        assert calls["new_calls"] == 0
        report = T.evaluate(tmp_path, day)
        assert report["comparison_complete"] is False
        assert (
            report["completed_context_exclusions"]
            == campaign["completed_context_exclusions"]
        )
        return
    with S.Store(tmp_path) as store:
        pair = campaign["pairs"][0]
        snap = store.get(pair["snapshot_obj"])
        req = store.request(pair["requests"]["candidate"])
        assert req == G.request(snap, candidate)
        assert (
            G.production_request(snap, candidate)[0][M.CANDLE_FIELD]["status"]
            == "observed"
        )
    report = T.evaluate(tmp_path, day)
    assert report["scopes"][sid]["paired_points"] == 0
    assert report["scopes"][sid]["improved"] is False
    assert report["comparison_complete"] is False
    assert campaign["completed_context_code_sha256"]

    def offline_transport(req, **kwargs):
        definition = (
            candidate
            if req["candidate"]["production_input_contract"]["version"]
            == M.CANDLE_VERSION
            else current
        )
        logical = G.production_request(snap, definition)[0]
        env = G.envelope(logical, definition)
        aliases = env["citation_map"]
        return dict(
            provider_provenance=dict(response_id="offline-fixture"),
            candidate_response=dict(
                assessed={aliases[x["ref"]]: True for x in logical["signals"]},
                screen=dict(
                    verdict="PASS",
                    risk="NO_BLOCKING_RISK",
                    fact=aliases["observed_machine_signal"],
                ),
                confidence=60,
            ),
        )

    calls = T.calls(tmp_path, day, transport=offline_transport)
    assert calls["new_calls"] == 2
    resolved = T.evaluate(tmp_path, day)
    assert resolved["comparison_complete"] is True
    assert resolved["scopes"][sid]["paired_points"] == 1
    assert resolved["scopes"][sid]["improved"] is False  # Same decision is no edge.


def test_cumulative_population_has_no_lifetime_batch_cap(tmp_path, monkeypatch):
    from src.trading.market import completed_history as H

    counts = []

    def reader(root, requests):
        counts.append(len(requests))
        return [
            dict(status="unavailable", reason="history_database_absent")
            for _ in requests
        ]

    monkeypatch.setattr(H, "causal_prefixes", reader)
    event = dict(
        epoch=datetime(2026, 10, 29, 10, 5, 30, tzinfo=R.K.KST).timestamp(),
        source_item="097520_NX",
    )
    snapshots = [[event, {}] for _ in range(4097)]
    R.attach_completed_contexts(tmp_path, snapshots)
    assert counts == [4096, 1]
    assert all(
        s[1]["entry_candle_source_gap"] == "history_database_absent" for s in snapshots
    )
