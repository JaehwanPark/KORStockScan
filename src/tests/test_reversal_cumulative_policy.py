import copy
from fractions import Fraction
from pathlib import Path

import pytest
from src.engine.scalping import reversal_cumulative_catalog as Q
from src.engine.scalping import reversal_cumulative_registration as R
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import reversal_extended_auxiliary as A
from src.engine.scalping.reversal_extended_state import State

SCOPE = "other_non_fixed|PRE|LT_20000|NXT"


def rows(prices):
    return [
        [
            1790640000.0 + i,
            101,
            i + 1,
            float(p),
            p - 1.0,
            p + 1.0,
            1.0,
            1,
            1,
            "000001_NX",
            0,
        ]
        for i, p in enumerate(prices)
    ]


def test_materialize_preserves_nested_legacy_facts_and_original_snapshot(monkeypatch):
    from src.engine.scalping import reversal_cumulative_postclose as CP

    child, definition = next(
        (b, d)
        for b, d in Q.REFINEMENTS.items()
        if d["original_definition_ref"]["branch_id"].startswith("legacy_")
    )
    original = definition["original_definition_ref"]["branch_id"]
    signal = dict(
        confirmation_price=100.0, entry_ask=101.0, signal_kind="FIRST", signal_proof={}
    )
    snapshot = [
        dict(branch_signals={original: {}}),
        dict(
            branch_inputs={
                original: dict(
                    entry_setup_evidence_v1={
                        "facts": {"buy_pressure_30s": 75.0, "return_10t_pct": 0.2}
                    },
                    recent_observed_prices=[],
                )
            }
        ),
    ]
    before = copy.deepcopy(snapshot)

    class Store:
        def get(self, ident):
            return snapshot

    monkeypatch.setattr(Q, "compose", lambda *args: signal)
    point = dict(
        snapshot_obj=1,
        cumulative_features=dict(
            spread=0.1, dd=1.0, volume=2.0, ret=0.2, session=0.3, vwap=0.4, buy10=80.0
        ),
    )
    event, source = CP.materialize(Store(), point, [child])
    facts = source["branch_inputs"][child]["facts"]
    assert event["registry_sha256"] == C.registry_for([child])
    assert event["materialization_parent_registry_sha256"] is None
    assert facts["buy_pressure_30s"] == 75.0
    assert facts["return_10t_pct"] == 0.2
    assert facts["return_60s_pct"] == 0.2
    assert facts["confirmation_price"] == 100.0
    assert snapshot == before
    snapshot[1]["branch_inputs"][original]["entry_setup_evidence_v1"]["facts"] = None
    with pytest.raises(ValueError, match="original_confirmation_facts_missing"):
        CP.materialize(Store(), point, [child])


def replay(ids, source):
    state = State(branch_ids=ids, session_anchor=source[0], offline=True)
    signals = []
    for row in source:
        ready = state.observe(
            row, symbol="000001", venue="NXT", session="NXT_PREMARKET"
        )
        if ready:
            signals.extend(ready[0]["event"]["branch_signals"].values())
        state.ready.clear()
    return state, signals


def test_catalog_is_content_addressed_and_frozen():
    assert len(Q.LEGACY_DEFINITIONS) == 1430 and len(Q.GROUPS) == 22
    from src.engine.scalping.continuous_reversal_postclose import digest

    for bid, d in Q.DEFINITIONS.items():
        assert bid == "manual_cumulative_" + digest(d)[:24]
        assert d["label_contract"] == C.LABEL
    for scope in Q.GROUPS:
        key, route = scope.rsplit("|", 1)
        for ids in Q.variants(scope).values():
            assert ids == sorted(set(ids))
            assert all(C.applicable(b, key, route) for b in ids)


def test_conditional_tristate_boundaries():
    rule = dict(
        when=dict(session_min=-0.4, session_max=0.4),
        require=dict(volume_min=1, buy_min=60, spread_max=0.1),
    )
    assert Q.condition({}, rule) is None
    assert Q.condition(dict(session=0.41), rule) is True
    assert Q.condition(dict(session=0.4, volume=1, buy10=60, spread=0.1), rule) is True
    assert Q.condition(dict(session=0.4, volume=0.9), rule) is False
    assert Q.condition(dict(session=0.4, volume=1), rule) is None
    assert Q.condition(dict(ret=-1), dict(ret_min=0, buy_min=60)) is False


def test_structure_signal_is_independent_of_first_reversal():
    bid = Q.GROUPS[SCOPE]["additions"]["A14"]
    source = rows([3000] * 125 + [3000 + i for i in range(1, 100)])
    state, signals = replay([bid], source)
    assert signals and state.legacy.turn is None
    for event in signals:
        assert event["decision_phase"] == "RISING_STRUCTURE_HOLD"
        assert event["signal_proof"]["previous_condition"] is False
        A.validate_signal(event)


def test_first_hold_confirmation_is_not_shifted_by_filter():
    bid = Q.GROUPS[SCOPE]["additions"]["A10"]
    source = rows([3000] * 180 + [2999, 3000, 3000, 3000])
    _, signals = replay([bid], source)
    assert len(signals) == 1
    assert signals[0]["native_sequence"] == 183
    A.validate_signal(signals[0])


def test_source_break_cancels_pending_hold():
    bid = Q.GROUPS[SCOPE]["additions"]["A10"]
    source = rows([3000] * 180 + [2999, 3000, 3000, 3000])
    source[182][1] = 102
    _, signals = replay([bid], source)
    assert not signals


def test_dependency_is_never_an_operating_or_member():
    bid = Q.GROUPS[SCOPE]["refinements"]["F10"][Q.GROUPS[SCOPE]["baseline"][0]]
    state = State(branch_ids=[bid], session_anchor=rows([3000])[0], offline=True)
    assert state.operating_ids == (bid,)
    assert (
        Q.REFINEMENTS[bid]["original_definition_ref"]["branch_id"]
        not in state.operating_ids
    )
    assert state.registry_sha256 == C.CUMULATIVE_SHA256


def metric(w, s=0, t=0, u=0, cohort="same"):
    return dict(
        counts=dict(WIN=w, FAIL_STOP=s, FAIL_TIMEOUT=t, UNRESOLVED=u),
        source_complete=True,
        comparison_complete=True,
        source_universe_sha256=cohort,
    )


def test_fraction_wins_despite_success_retention_loss():
    group = dict(alternatives={"F": ["refined"], "J": ["joint"]})
    m = dict(CURRENT_NATIVE=metric(100, t=100), F=metric(1), J=metric(30, t=10))
    result = R.select_variant(group, ["old"], m, authority=R.SELECTION_AUTHORITY)
    assert result["branch_ids"] == ["refined"]


def test_unknown_is_not_success_and_incomplete_current_carries():
    group = dict(alternatives={"F": ["refined"]})
    result = R.select_variant(
        group,
        ["old"],
        dict(CURRENT_NATIVE=metric(0, u=100), F=metric(0, u=100)),
        authority=R.SELECTION_AUTHORITY,
    )
    assert (
        result["branch_ids"] == ["old"]
        and result["status"] == "comparison_incomplete_carry"
    )


def test_fraction_exact_and_equal_fraction_more_wins():
    group = dict(alternatives={"A": ["new"]})
    result = R.select_variant(
        group,
        ["old"],
        dict(CURRENT_NATIVE=metric(10), A=metric(11)),
        authority=R.SELECTION_AUTHORITY,
    )
    assert result["branch_ids"] == ["new"]
    result = R.select_variant(
        group,
        ["old"],
        dict(CURRENT_NATIVE=metric(0, t=48), A=metric(0, t=50)),
        authority=R.SELECTION_AUTHORITY,
    )
    assert result["branch_ids"] == ["old"]


def test_false_zero_or_mixed_cohorts_never_select():
    group = dict(alternatives={"A": ["new"]})
    result = R.select_variant(
        group,
        ["old"],
        dict(CURRENT_NATIVE=metric(10, t=1), A=metric(100, cohort="different")),
        authority=R.SELECTION_AUTHORITY,
    )
    assert result["branch_ids"] == ["old"]
    with pytest.raises(ValueError, match="counts_invalid"):
        R.select_variant(
            group,
            ["old"],
            dict(CURRENT_NATIVE=metric(True), A=metric(100)),
            authority=R.SELECTION_AUTHORITY,
        )


def test_registration_cannot_use_an_implementation_as_live_approval(tmp_path):
    with pytest.raises(ValueError, match="explicit_registration_authority"):
        R.intake(
            tmp_path,
            tmp_path / "prepared.json",
            confirm="implementation_only",
            origin_root=tmp_path,
            origin_commit="a" * 40,
        )
    assert not R.pending_path(tmp_path).exists()


def request():
    from src.engine.scalping import continuous_reversal_postclose as P

    members = {s: Q.membership(s, Q.RECOMMENDATIONS[s]) for s in Q.GROUPS}
    return P.seal(
        dict(
            schema=R.SCHEMA,
            kind="REPLACE",
            operator_receipt=R.AUTHORITY,
            publication_date="2026-10-15",
            target_date="2026-10-16",
            parent_bundle_sha256=Q.PARENT,
            research_batch_sha256=Q.RESEARCH_RESULT,
            registry_sha256=C.CUMULATIVE_SHA256,
            initial_memberships=members,
            scopes={
                s: dict(
                    remove=sorted(set(g["baseline"]) - set(members[s])),
                    add=sorted(set(members[s]) - set(g["baseline"])),
                )
                for s, g in Q.GROUPS.items()
            },
            definition_hashes={b: P.digest(d) for b, d in Q.LEGACY_DEFINITIONS.items()},
            variant_groups=R.groups(),
            selection_authority=R.SELECTION_AUTHORITY,
            comparison_result_required=False,
            contract_file_sha256={"fixture.py": "a" * 64},
            **P.AUTH,
            source_receipts=[
                dict(path="/not-live/" + name, name=name, sha256=sha)
                for name, sha in [
                    ("result-reviewed.json", Q.RESEARCH_RESULT),
                    ("frozen-manifest.json", Q.RESEARCH_MANIFEST),
                    ("native-parity.json", "b" * 64),
                    ("baseline-bundle.json", "c" * 64),
                    ("validation.json", "d" * 64),
                ]
            ],
        )
    )


def manifest():
    from src.engine.scalping import continuous_reversal_postclose as P

    r = request()
    return dict(
        schema="main_operating_detector_manifest_v1",
        scopes=copy.deepcopy(r["initial_memberships"]),
        definitions={
            b: C.definition(b) for ids in r["initial_memberships"].values() for b in ids
        },
        cumulative_variant_groups=R.groups(),
        cumulative_selection_authority=R.SELECTION_AUTHORITY,
        registration_receipts=[r],
        registry_sha256=C.CUMULATIVE_SHA256,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("operator_receipt", "implementation_only"),
        ("target_date", "2026-10-19"),
        ("comparison_result_required", True),
        ("actual_order_submitted", True),
        ("initial_memberships", {}),
        ("source_receipts", []),
        ("contract_file_sha256", {}),
    ],
)
def test_request_rejects_resealed_authority_and_date_changes(field, value):
    from src.engine.scalping import continuous_reversal_postclose as P

    r = request()
    R.validate_request(r, check_sources=False)
    r[field] = value
    with pytest.raises(ValueError):
        R.validate_request(P.seal(r), check_sources=False)


def test_manifest_cannot_bypass_refinement_by_oring_original():
    m = manifest()
    assert R.validate_manifest(m)
    sid = next(s for s, v in Q.RECOMMENDATIONS.items() if v.startswith("F:"))
    m["scopes"][sid] = sorted(set(m["scopes"][sid]) | set(Q.GROUPS[sid]["baseline"]))
    with pytest.raises(ValueError, match="membership"):
        R.validate_manifest(m)


def test_consumed_registration_is_not_applied_again(tmp_path, monkeypatch):
    from src.engine.scalping import continuous_reversal_postclose as P

    r = request()
    P.write(R.pending_path(tmp_path), r)
    monkeypatch.setattr(R, "validate_request", lambda value, **kw: value)
    parent = dict(
        bundle_sha256="changed",
        continuous_reversal=dict(operating_manifest=dict(registration_receipts=[r])),
    )
    assert R.pending(tmp_path, parent, "2026-10-19") is None


def test_refinement_after_extended_root_has_exact_original_and_typed_request():
    from src.tests.test_reversal_extended_policy import FIXTURES
    from src.engine.scalping import reversal_extended_union as U

    sid = "034020|AFTER|20000_TO_100000|SOR"
    original = "manual_extended_b3f20a28786bbd4e"
    child = Q.GROUPS[sid]["refinements"]["F16"][original]
    snap = FIXTURES[original]
    base = snap["event"]["branch_signals"][original]
    # Use the exact frozen source fixture at the original confirmation.
    features = dict(
        base["branch_features"], ret=0.05, volume=1, spread=base["spread_pct"]
    )
    event = Q.compose(child, base, features)
    A.validate_signal(event)
    assert event["epoch"] == base["epoch"] and event["entry_ask"] == base["entry_ask"]
    assert event["signal_proof"]["original_confirmation"] == base
    inp = copy.deepcopy(snap["source"]["branch_inputs"][original])
    facts = inp["facts"]
    facts.update(return_60s_pct=0.05, volume_ratio_60s=1)
    inp.update(signal_proof=event["signal_proof"], signal_kind=event["signal_kind"])
    union = dict(snap["event"], branch_signals={child: event})
    typed, prompt, _ = U.production_request(
        dict(branch_inputs={child: inp}), U.V1.ARMS[1], event=union
    )
    assert typed["signals"][0]["policy_id"] == child and prompt.isascii()
    assert Q.compose(child, base, dict(features, volume=0.99)) is None
    unknown = Q.compose(child, base, dict(features, volume=None))
    A.validate_signal(unknown)
    assert unknown["signal_proof"]["refinement_truth"] == "UNKNOWN"


@pytest.mark.parametrize(
    "field,value",
    [("previous_condition", None), ("minimum_price", 1), ("root_contract", {})],
)
def test_new_root_proof_rejects_tampering(field, value):
    bid = Q.GROUPS[SCOPE]["additions"]["A14"]
    _, signals = replay([bid], rows([3000] * 125 + [3000 + i for i in range(1, 100)]))
    event = copy.deepcopy(signals[0])
    event["signal_proof"][field] = value
    with pytest.raises(ValueError):
        A.validate_signal(event)


def test_no_campaign_cannot_fall_back_to_all_variant_provider_calls(
    tmp_path, monkeypatch
):
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import reversal_auxiliary_tuning as T

    machine = P.seal(dict(operating_manifest=manifest()))
    monkeypatch.setattr(T, "config", lambda _: None)
    monkeypatch.setattr(O.L, "calls", lambda *a, **kw: pytest.fail("legacy fanout"))
    assert (
        O.prepare_inputs(tmp_path, "2026-10-15", machine)["actual_provider_calls"] == 0
    )
    P.write(O.directory(tmp_path, "2026-10-15") / "machine-comparison.json", machine)
    assert (
        O.calls(tmp_path, "2026-10-15", transport=lambda *a: pytest.fail("provider"))[
            "actual_provider_calls"
        ]
        == 0
    )


def postclose_fixture(monkeypatch):
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_cumulative_postclose as CP
    from src.engine.scalping import reversal_extended_union as U
    from src.engine.scalping import continuous_reversal_postclose as P

    m = manifest()
    parent = dict(
        bundle_sha256=Q.PARENT,
        continuous_reversal=dict(
            operating_manifest=dict(scopes={}), machine_cells={}, auxiliary_cells={}
        ),
    )
    for key, route in V.scopes():
        sid = V.scope_id(key, route)
        ids = Q.GROUPS[sid]["baseline"] if sid in Q.GROUPS else ["legacy_dd5_ge_0_4_v1"]
        parent["continuous_reversal"]["operating_manifest"]["scopes"][sid] = ids
        m["scopes"].setdefault(sid, ids)
        parent["continuous_reversal"]["machine_cells"].setdefault(
            key, dict(key=key, routes={})
        )["routes"][route] = dict(
            backend="union_v6",
            payload=dict(
                composition="ANY_MATCH_ONE_INTENT", branches=[C.branch(b) for b in ids]
            ),
        )
        arm = U.V1.ARMS[1]
        parent["continuous_reversal"]["auxiliary_cells"].setdefault(
            key, dict(key=key, routes={})
        )["routes"][route] = dict(payload=dict(arm=arm, binding=U.binding(arm)))
    m["definitions"] = {b: C.definition(b) for ids in m["scopes"].values() for b in ids}
    monkeypatch.setattr(R, "pending", lambda *a: request())
    monkeypatch.setattr(V, "detector_manifest", lambda *a, **kw: copy.deepcopy(m))
    monkeypatch.setattr(P, "completed_bars", lambda *a, **kw: ({}, []))
    return parent, m


def test_native_postclose_cache_scope_isolation_compact_projection_and_materialization(
    tmp_path, monkeypatch
):
    import gzip, json
    from src.engine.ai import offline_comparison_store as S
    from src.engine.scalping import reversal_cumulative_postclose as CP
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import reversal_extended_union as U

    parent, m = postclose_fixture(monkeypatch)
    source_rows = rows([3000] * 180 + [2980, 2981, 2982, 2983, 2984, 2985])
    raw = tmp_path / "native.json.gz"
    raw.write_bytes(
        gzip.compress(json.dumps(dict(symbols={"000001": source_rows})).encode())
    )
    rec = dict(
        day="2026-09-29",
        venue="NXT",
        session="NXT_PREMARKET",
        path=str(raw),
        sha256=P.file_hash(raw),
    )
    old = dict(rec, day="2026-09-28")
    source = P.seal(dict(normalized_sources=dict(partitions=[old, rec])))
    first = CP.build(
        tmp_path,
        "2026-10-14",
        "2026-10-15",
        parent,
        source=source,
        publish_outputs=False,
    )
    assert first["input_census"]["pre_refresh_partitions_excluded"] == 1
    assert len(first["partitions"]) == 1 and first["partitions"][0]["points"] > 0
    assert len(json.dumps(first)) < 8 * 1024**2
    assert all(
        set(v) == {"CURRENT_NATIVE", "SELECTED"}
        for v in first["fixed_proposals"].values()
    )
    table = first["fixed_comparison_table"]
    assert table["variant_count"] > 19892
    assert P.file_hash(table["path"]) == table["sha256"]
    points_seen = 0
    with S.Store(tmp_path) as store:
        for p in store.get(first["partitions"][0]["records_object"]):
            assert p["scope"] == SCOPE
            assert not any(
                b in p["truth"]
                for b in Q.GROUPS["other_non_fixed|PRE|GE_100000|NXT"][
                    "additions"
                ].values()
            )
            for original in Q.GROUPS[SCOPE]["baseline"]:
                if p["truth"].get(original) != "TRUE":
                    continue
                child = Q.GROUPS[SCOPE]["refinements"]["F21"][original]
                event, inp = CP.materialize(store, p, [child])
                if child not in event["branch_signals"]:
                    continue
                A.validate_signal(event["branch_signals"][child])
                typed, _, _ = U.production_request(inp, U.V1.ARMS[1], event=event)
                assert typed["signals"][0]["policy_id"] == child
                points_seen += 1
    assert points_seen
    monkeypatch.setattr(
        CP,
        "State",
        lambda **kw: pytest.fail("sealed partition should reuse checkpoint"),
    )
    again = CP.build(
        tmp_path,
        "2026-10-14",
        "2026-10-15",
        parent,
        source=source,
        publish_outputs=False,
    )
    assert again == first
    raw.write_bytes(b"changed")
    with pytest.raises(ValueError, match="normalized_source_changed"):
        CP.build(
            tmp_path,
            "2026-10-14",
            "2026-10-15",
            parent,
            source=source,
            publish_outputs=False,
        )


@pytest.mark.parametrize(
    "route,session,item",
    [
        ("KRX", "KRX_REGULAR", "000001"),
        ("SOR", "SOR_REGULAR", "000001_AL"),
        ("NXT", "NXT_REGULAR_OVERLAP", "000001_NX"),
    ],
)
def test_cumulative_replay_uses_exact_native_item_for_each_route(
    tmp_path, monkeypatch, route, session, item
):
    import gzip
    import json
    from src.engine.ai import offline_comparison_store as S
    from src.engine.scalping import reversal_cumulative_postclose as CP
    from src.engine.scalping import continuous_reversal_postclose as P

    parent, _ = postclose_fixture(monkeypatch)
    valid = rows([3000] * 180 + [2980, 2981, 2982, 2983, 2984, 2985])
    for row in valid:
        row[9] = item
    wrong_item = "000001_AL" if route != "SOR" else "000001"
    wrong = copy.deepcopy(valid)
    for row in wrong:
        row[0] += 1000
        row[1] += 1
        row[9] = wrong_item
    raw = tmp_path / "native.json.gz"
    raw.write_bytes(
        gzip.compress(json.dumps(dict(symbols={"000001": valid + wrong})).encode())
    )
    rec = dict(
        day="2026-09-29",
        venue=route,
        session=session,
        path=str(raw),
        sha256=P.file_hash(raw),
    )
    report = CP.build(
        tmp_path,
        "2026-10-14",
        "2026-10-15",
        parent,
        source=P.seal(dict(normalized_sources=dict(partitions=[rec]))),
        publish_outputs=False,
    )
    assert report["input_census"]["source_rows"] == len(valid) + len(wrong)
    assert report["input_census"]["valid_source_rows"] == len(valid)
    part = report["partitions"][0]
    assert part["points"] > 0
    with S.Store(tmp_path, readonly=True) as store:
        points = store.get(part["records_object"])
        for point in points:
            event, _ = store.get(point["snapshot_obj"])
            assert event["source_item"] == item
            assert event["venue"] == route
            assert point["scope"].endswith("|" + route)
    assert report["runtime_effect"] is False
    assert report["actual_order_submitted"] is False


def test_followup_selection_compares_fixed_originals_with_actual_current():
    from src.engine.scalping import continuous_reversal_postclose as P

    m = manifest()
    parent = dict(
        bundle_sha256="e" * 64,
        continuous_reversal=dict(
            operating_manifest=dict(
                scopes={s: copy.deepcopy(g["baseline"]) for s, g in Q.GROUPS.items()}
            )
        ),
    )
    sid = SCOPE
    report = dict(
        operating_manifest=m,
        status="completed",
        source_manifest_receipt=dict(path="fixture"),
        source_manifest_sha256="b" * 64,
        label_contract=C.LABEL,
        proposal_metrics={
            sid + "::CURRENT_NATIVE": metric(100, t=100),
            sid + "::F:F10": metric(1),
        },
    )
    chosen = R.apply_selection(report, parent)
    assert chosen["operating_manifest"]["scopes"][sid] == Q.membership(sid, "F:F10")
    assert R.validate_manifest(chosen["operating_manifest"])
    wrong = copy.deepcopy(chosen["operating_manifest"])
    r = wrong["cumulative_selection_receipt"]
    r["selected"][sid]["branch_ids"] = Q.GROUPS[sid]["baseline"]
    wrong["cumulative_selection_receipt"] = P.seal(r)
    with pytest.raises(ValueError, match="membership_changed"):
        R.validate_manifest(wrong)


def test_evidence_archive_never_overwrites_or_ignores_corruption(tmp_path):
    import hashlib

    source = tmp_path / "input.json"
    source.write_text("{}")
    dest = tmp_path / "archive"
    first = R._archive(source, dest)
    assert first == R._archive(source, dest)
    from pathlib import Path

    Path(first["path"]).write_text("corrupt")
    with pytest.raises(ValueError, match="archive_conflict"):
        R._archive(source, dest)


def test_source_and_confirmation_hold_removal_preserves_other_or_branch():
    from types import SimpleNamespace
    from src.engine.scalping import reversal_extended_runtime as LIVE

    bid = Q.GROUPS[SCOPE]["additions"]["A14"]
    _, signals = replay([bid], rows([3000] * 125 + [3000 + i for i in range(1, 100)]))
    signal = signals[0]
    event = dict(
        signal_id=signal["signal_id"],
        branch_signals={bid: signal, "other": dict(decision_phase="HIGH_BREAKOUT")},
    )
    source = dict(branch_inputs={bid: {}, "other": {}})
    state = SimpleNamespace(
        legacy=SimpleNamespace(turn=None),
        ready=[
            dict(event=dict(signal_id=event["signal_id"], branch_signals={"other": {}}))
        ],
    )
    LIVE._filter_first(event, source, state)
    assert set(event["branch_signals"]) == set(source["branch_inputs"]) == {"other"}


@pytest.mark.parametrize("cas_conflict", [False, True, "other_pending"])
def test_isolated_intake_requires_current_code_and_exact_parent_and_freezes_evidence(
    tmp_path, monkeypatch, cas_conflict
):
    from pathlib import Path
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import continuous_reversal_policy_v6 as V

    r = request()
    r["contract_file_sha256"] = {
        Path(m.__file__).name: P.file_hash(m.__file__) for m in V.contract_modules()
    }
    receipts = []
    for rec in r["source_receipts"]:
        source = tmp_path / "prepared-evidence" / rec["name"]
        source.parent.mkdir(exist_ok=True)
        source.write_text("{}")
        receipts.append(dict(rec, path=str(source), sha256=P.file_hash(source)))
    r["source_receipts"] = receipts
    prepared = P.seal(
        dict(
            r,
            schema=R.PREPARED,
            status="prepared_waiting_deployment",
            operator_receipt=None,
        )
    )
    prepared_path = tmp_path / "prepared.json"
    P.write(prepared_path, prepared)
    data = tmp_path / "isolated-data"
    point = R.N.root(data) / "current.json"
    P.write(point, dict(bundle_sha256="f" * 64 if cas_conflict is True else Q.PARENT))
    if cas_conflict == "other_pending":
        P.write(
            point.parent / "joint-registration.json",
            dict(parent_bundle_sha256=Q.PARENT, artifact_content_sha256="e" * 64),
        )
    monkeypatch.setattr(
        V, "_attested_activation_parent", lambda *a, **kw: dict(bundle_sha256=Q.PARENT)
    )
    # Evidence integrity itself is exercised by _archive; this fixture uses
    # synthetic bytes rather than copying private historical research sources.
    monkeypatch.setattr(R, "_receipts", lambda *a, **kw: None)
    args = dict(confirm=R.AUTHORITY, origin_root=tmp_path, origin_commit="a" * 40)
    if cas_conflict:
        with pytest.raises(
            ValueError,
            match=(
                "other_registration_pending"
                if cas_conflict == "other_pending"
                else "parent_cas_failed"
            ),
        ):
            R.intake(data, prepared_path, **args)
        assert not R.pending_path(data).exists()
    else:
        adopted = R.intake(data, prepared_path, **args)
        assert (
            adopted["operator_receipt"] == R.AUTHORITY
            and adopted["actual_order_submitted"] is False
        )
        assert R.N._read(point) == dict(bundle_sha256=Q.PARENT)
        assert all(
            Path(rec["path"]).is_relative_to(data) for rec in adopted["source_receipts"]
        )
        assert R.intake(data, prepared_path, **args) == adopted
        assert not (R.N.root(data) / "candidates").exists()
    wrong = P.seal(dict(prepared, contract_file_sha256={"stale.py": "a" * 64}))
    P.write(prepared_path, wrong)
    with pytest.raises(ValueError, match="prepared_code_or_authority_changed"):
        R.intake(data, prepared_path, **args)


def test_relative_source_is_resolved_under_data_mount_not_cwd_and_future_is_rejected(
    tmp_path, monkeypatch
):
    import json, gzip
    from src.engine.scalping import reversal_cumulative_postclose as CP
    from src.engine.scalping import continuous_reversal_postclose as P

    parent, m = postclose_fixture(monkeypatch)
    raw = tmp_path / "native.gz"
    raw.write_bytes(
        gzip.compress(
            json.dumps(
                dict(symbols={"000001": rows([3000] * 125 + [2999, 3000, 3000])})
            ).encode()
        )
    )
    rec = dict(
        day="2026-09-29",
        venue="NXT",
        session="NXT_PREMARKET",
        path="data/native.gz",
        sha256=P.file_hash(raw),
    )
    cwd = tmp_path / "src"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    result = CP.build(
        tmp_path,
        "2026-10-14",
        "2026-10-15",
        parent,
        source=P.seal(dict(normalized_sources=dict(partitions=[rec]))),
        publish_outputs=False,
    )
    assert result["input_census"]["source_rows"] == 128
    with pytest.raises(ValueError, match="source_after_observation_date"):
        CP.build(
            tmp_path,
            "2026-10-14",
            "2026-10-15",
            parent,
            source=P.seal(
                dict(normalized_sources=dict(partitions=[dict(rec, day="2026-10-15")]))
            ),
            publish_outputs=False,
        )


def test_registered_type_first_keeps_native_low_proof_not_path_phase_schema():
    original = "manual_type_ae4445459dc942c8"
    sid = "403870|REGULAR|20000_TO_100000|SOR"
    child = Q.GROUPS[sid]["refinements"]["F05"][original]
    features = dict(
        ret=-0.1,
        session=-1,
        vwap=0.1,
        buy10=70,
        volume=1,
        dd=1,
        structure="FALLING",
        session_trend="DOWN",
    )
    base = dict(
        symbol="403870",
        market="REGULAR",
        venue="SOR",
        source_item="403870_AL",
        epoch=1790640100.0,
        native_epoch=101,
        native_sequence=10,
        confirmation_price=30000.0,
        entry_ask=30010.0,
        event_id="native-type-first",
        signal_id="native-type-first",
        decision_phase="FIRST_UPTICK",
        low_price=29990.0,
        spread_pct=0.1,
        drawdown_5m_pct=1,
        volume_ratio_60s=1,
        branch_features=features,
        branch_definition_sha256=C.branch(original)["definition_sha256"],
    )
    assert C.matches(original, base, features) is True
    event = Q.compose(child, base, dict(features, spread=0.1))
    A.validate_signal(event)


def test_cli_override_rejected_before_mutable_seed_and_consumed_uses_current(
    tmp_path, monkeypatch
):
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import continuous_reversal_operating_postclose as O

    P.write(R.pending_path(tmp_path), request())
    monkeypatch.setattr(R, "validate_request", lambda r, **kw: r)
    monkeypatch.setattr(R, "consumed", lambda *a: False)
    monkeypatch.setattr(
        R,
        "load_offline_parent",
        lambda *a: pytest.fail("must not reopen original transition"),
    )
    monkeypatch.setattr(P, "prepare_research", lambda *a: pytest.fail("mutable seed"))
    argv = [
        "--data-root",
        str(tmp_path),
        "--date",
        "2026-10-14",
        "--publication-date",
        "2026-10-15",
    ]
    with pytest.raises(ValueError, match="input_override_forbidden"):
        P.main(argv + ["--seed-research", str(tmp_path / "seed")])
    monkeypatch.setattr(R, "consumed", lambda *a: True)
    current = {"bundle_sha256": "current"}
    seen = []
    monkeypatch.setattr(O, "active", lambda *a: current)
    monkeypatch.setattr(
        O,
        "machine_report",
        lambda data, day, pub, parent, **kw: seen.append(parent)
        or dict(status="fixture_current"),
    )
    assert P.main(argv) == 0 and seen == [current]


def _midnight_report_parent(monkeypatch, tmp_path):
    from datetime import datetime
    from types import SimpleNamespace
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure import runtime_release_router as router

    selector = tmp_path / "runtime/runtime_release_selection.json"
    selector.parent.mkdir()
    selector.write_bytes(b"original-selected-release")
    origin = tmp_path / "immutable-release"
    monkeypatch.setattr(
        O,
        "datetime",
        SimpleNamespace(now=lambda tz: datetime(2026, 10, 23, 1, tzinfo=tz)),
        raising=False,
    )
    monkeypatch.setattr(
        router, "selected_release", lambda workspace: (origin, "reviewed-commit")
    )

    def runtime(**kwargs):
        raise ValueError("v6_contract_code_changed:reversal_code_handoff.py")

    monkeypatch.setattr(N, "load_effective", runtime)
    monkeypatch.setattr(
        R,
        "load_offline_parent",
        lambda *a: pytest.fail("unrelated registration parent"),
    )
    return O, V, N, selector, origin


def test_midnight_reports_share_original_attested_parent_without_runtime_relaxation(
    monkeypatch, tmp_path
):
    from src.engine.scalping import ai_action_outcome_calibration as calibration
    from src.engine.scalping import strategy_owner_replay

    O, V, N, selector, origin = _midnight_report_parent(monkeypatch, tmp_path)
    parent = dict(
        bundle_sha256="original-policy",
        target_date="2026-10-22",
        continuous_reversal=dict(schema=V.SCHEMA),
        machine_policy=dict(original=True),
    )
    calls = []

    def attest(data, day, **kwargs):
        calls.append((day, kwargs))
        return parent

    monkeypatch.setattr(V, "_attested_activation_parent", attest)
    monkeypatch.setattr(
        strategy_owner_replay,
        "entry_operating_model_identity",
        lambda: "reviewed-model",
    )
    assert O.active(tmp_path, "2026-10-22") is parent
    fingerprint = calibration._main_mechanistic_input_fingerprint(
        tmp_path, "2026-10-22"
    )
    assert len(fingerprint) == 64
    original_read = Path.read_bytes
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda path: original_read(path)
        + (b"\n" if path.name == "continuous_reversal_operating_postclose.py" else b""),
    )
    assert (
        calibration._main_mechanistic_input_fingerprint(tmp_path, "2026-10-22")
        != fingerprint
    )
    assert (
        calls
        == [("2026-10-22", dict(origin_root=origin, origin_commit="reviewed-commit"))]
        * 3
    )
    assert selector.read_bytes() == b"original-selected-release"
    with pytest.raises(ValueError, match="v6_contract_code_changed"):
        N.load_effective(data_root=tmp_path, target_date="2026-10-23")


def test_same_day_report_cannot_borrow_yesterdays_attestation(monkeypatch, tmp_path):
    O, V, N, selector, origin = _midnight_report_parent(monkeypatch, tmp_path)
    monkeypatch.setattr(
        V,
        "_attested_activation_parent",
        lambda *a, **kw: pytest.fail("dated runtime check bypassed"),
    )
    with pytest.raises(ValueError, match="v6_contract_code_changed"):
        O.load_report_parent(tmp_path, "2026-10-23")


@pytest.mark.parametrize(
    "reason",
    [
        "continuous_reversal_current_hash_invalid",
        "active_policy_code_handoff_source_changed:source.json",
    ],
)
def test_report_parent_never_reclassifies_source_corruption(
    monkeypatch, tmp_path, reason
):
    O, V, N, selector, origin = _midnight_report_parent(monkeypatch, tmp_path)

    def broken(**kwargs):
        raise ValueError(reason)

    monkeypatch.setattr(N, "load_effective", broken)
    monkeypatch.setattr(
        V,
        "_attested_activation_parent",
        lambda *a, **kw: pytest.fail("source corruption bypassed"),
    )
    with pytest.raises(ValueError, match=reason):
        O.load_report_parent(tmp_path, "2026-10-22")


@pytest.mark.parametrize(
    "error",
    [
        FileNotFoundError("missing original handoff"),
        ValueError("v6_historical_parent_source_changed:source.json"),
        ValueError("v6_historical_parent_code_changed"),
    ],
)
def test_midnight_parent_proof_failure_never_falls_back_to_registration(
    monkeypatch, tmp_path, error
):
    O, V, N, selector, origin = _midnight_report_parent(monkeypatch, tmp_path)

    def broken(*args, **kwargs):
        raise error

    monkeypatch.setattr(V, "_attested_activation_parent", broken)
    with pytest.raises(type(error), match=str(error)):
        O.active(tmp_path, "2026-10-22")


def test_midnight_parent_rejects_selector_transition_during_validation(
    monkeypatch, tmp_path
):
    O, V, N, selector, origin = _midnight_report_parent(monkeypatch, tmp_path)

    def race(*args, **kwargs):
        selector.write_bytes(b"successor")
        return dict(target_date="2026-10-22")

    monkeypatch.setattr(V, "_attested_activation_parent", race)
    with pytest.raises(ValueError, match="postclose_report_parent_selection_changed"):
        O.active(tmp_path, "2026-10-22")


def test_auxiliary_carry_uses_one_snapshot_under_existing_publisher_lock(
    tmp_path, monkeypatch
):
    import fcntl
    from src.engine.scalping import reversal_cumulative_postclose as CP
    from src.engine.scalping import (
        reversal_auxiliary_intraday as I,
        reversal_auxiliary_registry as A,
    )
    from src.engine.scalping import (
        reversal_extended_union as U,
        continuous_reversal_policy_v6 as V,
    )

    parent, m = postclose_fixture(monkeypatch)
    monkeypatch.setattr(R, "_receipts", lambda *a, **kw: None)
    ident = A.register(tmp_path, A.definition(U.V1.ARMS[1], input_version=U.VERSION))
    bindings = {V.scope_id(k, r): ident for k, r in V.scopes()}
    overlay = {"fixture_snapshot": True}
    reads = []

    def effective(*args, **kwargs):
        with (I.root(tmp_path) / "publisher.lock").open("a") as probe:
            with pytest.raises(BlockingIOError):
                fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return bindings

    monkeypatch.setattr(I, "effective_bindings", effective)
    monkeypatch.setattr(I, "current", lambda *a, **kw: reads.append(1) or overlay)

    def lineage(data, bundle, view):
        assert view is overlay
        return []

    monkeypatch.setattr(I, "lineage_sources", lineage)
    monkeypatch.setattr(
        I,
        "independent_scopes",
        lambda data, bundle, view: (
            {SCOPE} if view is overlay else pytest.fail("mixed snapshot")
        ),
    )
    machine = dict(
        registration_change=request(),
        operating_manifest=m,
        source_receipts=[],
        execution_code_sha256="a" * 64,
    )
    result = CP.initial_reports(
        tmp_path, "2026-10-14", "2026-10-15", parent, machine, publish_policy=False
    )
    assert len(reads) == 1 and result["auxiliary_registry_bindings"] == bindings
    assert (
        result["auxiliary_independent_scopes"] == [SCOPE]
        and result["actual_provider_calls"] == 0
    )
    with (I.root(tmp_path) / "publisher.lock").open("a") as probe:
        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.parametrize(
    "scope,original,price",
    [
        ("other_non_fixed|PRE|20000_TO_100000|NXT", "legacy_dd5_0_8_vol_up_v1", 30000),
        (SCOPE, "manual_joint_9a28e37e454ce928", 3000),
    ],
)
def test_original_source_unknown_remains_unknown_through_refinement(
    scope, original, price
):
    child = Q.GROUPS[scope]["refinements"]["F10"][original]
    source = rows([price] * 20 + [price * 0.99, price * 0.991])
    state, signals = replay([child], source)
    assert not signals
    assert state.coverage_snapshot[child] == "UNKNOWN"
    assert state.coverage_counts[child]["UNKNOWN"] > 0
