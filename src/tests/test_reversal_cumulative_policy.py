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


def scoring_contract():
    from src.engine.scalping import continuous_reversal_postclose as P

    return P.seal(
        dict(
            schema=R.SCORING_SCHEMA,
            spec=R.scoring_spec(),
            operator_receipt=R.SCORING_AUTHORITY,
            publication_date="2026-10-27",
            target_date="2026-10-28",
            parent_bundle_sha256="e" * 64,
            source_manifest_sha256="b" * 64,
            research_batch_sha256=Q.RESEARCH_RESULT,
            registry_sha256=Q.registry(),
            source_receipts=[dict(path="/fixture/source.json", sha256="c" * 64)],
            contract_file_sha256={"fixture": "d" * 64},
            scopes={
                sid: dict(
                    parent_branch_ids=g["baseline"],
                    alternatives={
                        "ADD_" + a: sorted(set(g["baseline"]) | {g["additions"][a]})
                        for a in R.SCORING_ALIASES[sid]
                    },
                )
                for sid, g in Q.GROUPS.items()
                if sid in R.SCORING_ALIASES
            },
            **P.AUTH,
        )
    )


def scored_metric(contract, w, s=0, t=0, u=0, **kw):
    from src.engine.scalping import continuous_reversal_postclose as P

    return dict(
        metric(w, s, t, u),
        chronological=metric(w, s, t, u),
        statistic_contract_sha256=P.digest(R.scoring_spec()),
        scoring_contract_sha256=contract["artifact_content_sha256"],
        statistic_source_complete=True,
        **kw,
    )


@pytest.mark.parametrize(
    "w,n,expected",
    [
        (0, 0, None),
        (1, 1, 0.20654931437723745),
        (2, 2, 0.34238022750665303),
        (102, 188, 0.4711993273835544),
    ],
)
def test_wilson_fixed_values_and_null(w, n, expected):
    actual = R.wilson_score(w, n)
    assert actual is None if expected is None else actual == pytest.approx(expected)


@pytest.mark.parametrize("w,n", [(True, 1), (-1, 1), (2, 1), (1.0, 2)])
def test_wilson_invalid_counts(w, n):
    with pytest.raises(ValueError, match="counts_invalid"):
        R.wilson_score(w, n)


def test_scoped_score_breaks_tiny_perfect_lock_without_changing_raw():
    c = scoring_contract()
    sid = next(iter(R.SCORING_ALIASES))
    cfg = c["scopes"][sid]
    m = {
        "CURRENT_NATIVE": scored_metric(c, 2),
        "ADD_A05": scored_metric(c, 36, t=26),
        "ADD_A09": scored_metric(c, 102, t=86),
    }
    old = R.select_variant(
        cfg, cfg["parent_branch_ids"], m, authority=R.SELECTION_AUTHORITY
    )
    new = R.select_variant(
        cfg,
        cfg["parent_branch_ids"],
        m,
        authority=R.SELECTION_AUTHORITY,
        scoring=c,
        scope=sid,
    )
    assert old["variant"] == "CURRENT_NATIVE"
    assert new["variant"] == "ADD_A09"
    assert new["wins"] == 102 and new["resolved"] == 188
    m["ADD_A09"]["statistic_source_complete"] = False
    assert (
        R.select_variant(
            cfg,
            cfg["parent_branch_ids"],
            m,
            authority=R.SELECTION_AUTHORITY,
            scoring=c,
            scope=sid,
        )["variant"]
        == "ADD_A05"
    )
    m["CURRENT_NATIVE"]["chronological"] = metric(0, u=4)
    assert (
        R.select_variant(
            cfg,
            cfg["parent_branch_ids"],
            m,
            authority=R.SELECTION_AUTHORITY,
            scoring=c,
            scope=sid,
        )["status"]
        == "comparison_incomplete_carry"
    )


@pytest.mark.parametrize(
    "damage",
    [
        "scope",
        "version",
        "z",
        "window",
        "label",
        "authority",
        "source",
        "membership",
        "metric",
    ],
)
def test_scoring_rejects_contract_and_metric_mutations(damage):
    from src.engine.scalping import continuous_reversal_postclose as P

    c = scoring_contract()
    sid = next(iter(R.SCORING_ALIASES))
    cfg = c["scopes"][sid]
    m = {n: scored_metric(c, 2) for n in ["CURRENT_NATIVE", *cfg["alternatives"]]}
    if damage == "scope":
        sid = SCOPE
    elif damage in {"version", "z", "label"}:
        c["spec"][{"label": "label_contract"}.get(damage, damage)] = "wrong"
    elif damage == "window":
        c["spec"]["seconds"] = 900
    elif damage == "authority":
        c["operator_receipt"] = None
    elif damage == "source":
        c["source_manifest_sha256"] = None
    elif damage == "membership":
        cfg["alternatives"]["ADD_A05"].append("unknown")
    elif damage == "metric":
        m["CURRENT_NATIVE"]["statistic_contract_sha256"] = "wrong"
    c = P.seal(c)
    with pytest.raises(ValueError, match="cumulative_scoring"):
        R.select_variant(
            cfg,
            cfg["parent_branch_ids"],
            m,
            authority=R.SELECTION_AUTHORITY,
            scoring=c,
            scope=sid,
        )


def test_chronological_first_unknown_stop_ties_boundaries_and_displacement():
    from src.engine.scalping import reversal_cumulative_postclose as CP

    def point(key, at, status="WIN", **kw):
        return dict(
            opportunity_key=key,
            confirmation_epoch=at,
            outcome={"status": status},
            **dict(day="2026-10-27", symbol="000001", route="SOR", **kw),
        )

    initial = point("a", 0, "UNRESOLVED")
    values = [
        point("d", 1801),
        point("c", 1800, "FAIL_STOP"),
        point("b", 1),
        initial,
        initial,
        dict(point("e", 1), route="NXT"),
        dict(point("f", 1), day="2026-10-28"),
        dict(point("g", 1), symbol="000002"),
    ]
    keys = {p["opportunity_key"] for p in CP.chronological_points(values)}
    assert keys == {"a", "c", "e", "f", "g"}
    assert (
        CP.chronological_metric(CP.chronological_points(values))["counts"]["UNRESOLVED"]
        == 1
    )
    assert (
        CP.chronological_points([point("z", 0), point("a", 0, "FAIL_STOP")])[0][
            "opportunity_key"
        ]
        == "a"
    )
    assert (
        CP.chronological_points([point("old-win", 10)])[0]["opportunity_key"]
        == "old-win"
    )
    assert (
        CP.chronological_points(
            [point("old-win", 10), point("new-stop", 0, "FAIL_STOP")]
        )[0]["opportunity_key"]
        == "new-stop"
    )
    with pytest.raises(ValueError, match="statistical_key_conflict"):
        CP.chronological_points([point("a", 1), point("a", 2)])


def test_scored_producer_selection_manifest_and_projection(tmp_path, monkeypatch):
    import gzip, json
    from src.engine.scalping import reversal_cumulative_postclose as CP
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.ai import offline_comparison_store as S

    parent, m = postclose_fixture(monkeypatch)
    parent["bundle_sha256"] = "e" * 64
    source = P.seal(dict(normalized_sources=dict(partitions=[])))
    c = P.seal(dict(scoring_contract(), source_manifest_sha256=source["artifact_content_sha256"]))
    sid = next(iter(R.SCORING_ALIASES))
    cfg = c["scopes"][sid]
    m["cumulative_scoring_contract"] = c
    monkeypatch.setattr(R, "pending", lambda *a: None)
    monkeypatch.setattr(R, "scoring_for_build", lambda *a: c)
    monkeypatch.setattr(P, "population_receipt", lambda *a: dict(path="fixture"))
    report = CP.build(
        tmp_path,
        "2026-10-27",
        "2026-10-27",
        parent,
        source=source,
        publish_outputs=True,
    )
    assert (
        report["primary_decision_metric"]
        == "scope_bound_chronological_wilson_and_raw_fraction"
    )
    assert R.validate_manifest(report["operating_manifest"])
    from src.engine.automation import postclose_summary_handoff as H
    terminal = json.loads((tmp_path/'report/ai_decision_action_outcome_calibration/winrate_policy_terminal_2026-10-27.json').read_text())
    assert terminal['selection_basis'] == R.SCOPED_METRIC
    assert H._operating_machine_terminal_selected(terminal,'2026-10-27',report)
    for key,value in [('selection_basis','cumulative_raw_win_fraction'),('scoring_contract_sha256','f'*64),('statistic_contract_sha256','f'*64)]:
        assert not H._operating_machine_terminal_selected(P.seal(dict(terminal,**{key:value})),'2026-10-27',report)
    with gzip.open(report["fixed_comparison_table"]["path"], "rt") as f:
        archive = json.load(f)
    assert archive["schema"] == "cumulative_fixed_comparison_table_v3"
    assert archive["scoring_contract"] == c
    assert (
        report["proposal_metrics"][sid + "::CURRENT_NATIVE"]["chronological"]["score"]
        is None
    )
    assert "chronological" not in report["proposal_metrics"][SCOPE + "::CURRENT_NATIVE"]
    with S.Store(tmp_path) as store:
        records = []
        epoch = 1793070000  # 2026-10-27 12:00 KST
        for i, (offset, status, which) in enumerate(
            [
                (0, "FAIL_STOP", "ADD_A05"),
                (10, "WIN", "CURRENT_NATIVE"),
                (1900, "WIN", "ADD_A05"),
            ]
        ):
            bid = (
                cfg["parent_branch_ids"]
                if which == "CURRENT_NATIVE"
                else [Q.GROUPS[sid]["additions"]["A05"]]
            )[0]
            snapshot = store.put(
                [
                    dict(
                        epoch=epoch + offset,
                        symbol="000001",
                        venue="SOR",
                        source_item="000001_AL",
                    ),
                    {},
                ]
            )
            records.append(
                dict(
                    opportunity_key=str(i),
                    day="2026-10-27",
                    symbol="000001",
                    scope=sid,
                    truth={bid: "TRUE"},
                    outcome={"status": status},
                    snapshot_obj=snapshot,
                )
            )
        store.commit()
        configs = {
            s: dict(v["alternatives"], CURRENT_NATIVE=v["parent_branch_ids"])
            for s, v in c["scopes"].items()
        }
        metrics, effects = CP.scoring_metrics(
            records,
            configs,
            {s: v["parent_branch_ids"] for s, v in c["scopes"].items()},
            c,
            store,
        )
    e = effects[sid + "::ADD_A05"]
    assert e["removed_keys"] == ["1"] and e["added_keys"] == ["0", "2"]
    assert metrics[sid + "::ADD_A05"]["chronological"]["resolved"] == 2
    changed = copy.deepcopy(report["operating_manifest"])
    changed.pop("cumulative_scoring_contract")
    with pytest.raises(ValueError, match="selection_schema"):
        R.validate_manifest(changed)


def test_scoring_pending_parent_source_generation_and_consumed_carry(
    tmp_path, monkeypatch
):
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    c = scoring_contract()
    parent = dict(
        bundle_sha256="e" * 64,
        continuous_reversal=dict(
            operating_manifest=dict(
                scopes={s: v["parent_branch_ids"] for s, v in c["scopes"].items()},
                registration_receipts=[request()],
            )
        ),
    )
    path = N.root(tmp_path) / "cumulative-scoring.json"
    P.write(path, c)
    monkeypatch.setattr(P, "file_hash", lambda p: "c" * 64)
    assert R.scoring_for_build(tmp_path, parent, "2026-10-27", "b" * 64) == c
    for day, sha, bundle in [
        ("2026-10-28", "b" * 64, "e" * 64),
        ("2026-10-27", "f" * 64, "e" * 64),
        ("2026-10-27", "b" * 64, "f" * 64),
    ]:
        p = dict(parent, bundle_sha256=bundle)
        with pytest.raises(ValueError, match="parent_source_or_date"):
            R.scoring_for_build(tmp_path, p, day, sha)
    parent["continuous_reversal"]["operating_manifest"][
        "cumulative_scoring_contract"
    ] = c
    assert R.scoring_for_build(tmp_path, parent, "2026-10-28", "f" * 64) == c
    with pytest.raises(ValueError, match="explicit_authority"):
        R.intake_scoring(
            tmp_path,
            path,
            confirm="implementation",
            origin_root=tmp_path,
            origin_commit="x",
        )


def native_preparation_files(data, day):
    import json
    from src.engine.scalping import continuous_reversal_postclose as P

    raw = data / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text('{"fixture":"native private input"}\n')
    stat = raw.stat()
    audit = data / "report/observation_source_quality_audit" / f"observation_source_quality_audit_{day}.json"
    body = dict(
        target_date=day, audit_phase="preflight", status="warning",
        consumer_implementation_sha256="fixture-consumer",
        summary=dict(tuning_input_allowed=True),
        source=dict(generation_stable=True, pipeline_events=str(raw.resolve()),
                    generation={name: getattr(stat, field) for name, field in (
                        ("device", "st_dev"), ("inode", "st_ino"), ("size_bytes", "st_size"),
                        ("mtime_ns", "st_mtime_ns"), ("ctime_ns", "st_ctime_ns"))}),
    )
    P.write(audit, body)
    P.write(Path(str(audit)+".final-contract.json"), dict(
        schema="observation_source_quality_final_binding_v1", target_date=day,
        audit_phase="preflight", artifact_sha256=P.file_hash(audit),
        implementation_sha256=body["consumer_implementation_sha256"],
    ))
    eod = data / "runtime/update_kospi_status" / f"update_kospi_{day}.json"
    P.write(eod, dict(status="completed_with_warnings", target_date=day,
                      db_state=dict(latest_quote_date=day, rows_on_latest_date=10)))
    return eod, audit, raw


@pytest.mark.parametrize("fault", ["eod_missing", "eod_date", "rows", "audit", "raw", "blocked"])
def test_scoring_prepare_rejects_invalid_source_before_creation(tmp_path, monkeypatch, fault):
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    day="2026-10-27"
    eod, audit, raw = native_preparation_files(tmp_path, day)
    if fault=="eod_missing": eod.unlink()
    elif fault=="eod_date": P.write(eod, dict(status="completed", target_date="2026-10-26"))
    elif fault=="rows": P.write(eod, dict(status="completed", target_date=day, db_state=dict(latest_quote_date=day,rows_on_latest_date=True)))
    elif fault=="audit": audit.unlink()
    elif fault=="raw": raw.write_text('changed')
    else:
        import json
        value=json.loads(audit.read_text());value["summary"]["tuning_input_allowed"]=False
        P.write(audit,value)
    monkeypatch.setattr(N,"validate",lambda *a,**k:None)
    monkeypatch.setattr(P,"ensure_population",lambda *a,**k:pytest.fail("invalid source must not create population"))
    c=scoring_contract()
    parent=dict(target_date=day,bundle_sha256="e"*64,continuous_reversal=dict(operating_manifest=dict(
        scopes={s:v['parent_branch_ids'] for s,v in c['scopes'].items()},registration_receipts=[request()])))
    with pytest.raises(ValueError, match="eod_source_invalid|preflight_invalid"):
        R.prepare_scoring(tmp_path,tmp_path/"out",parent=parent,day=day)
    assert not (tmp_path/"out").exists()


@pytest.mark.parametrize("only_a09", [False, True])
@pytest.mark.parametrize("fault", [None, "stage", "output", "locked", "reader", "raw", "source", "parent", "stage_race", "prepare_race"])
def test_scoring_preparation_and_intake_are_separate_and_hash_bound(
    tmp_path, monkeypatch, only_a09, fault
):
    from src.engine.automation import postclose_summary_handoff as H
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    c = scoring_contract()
    day = "2026-10-27"
    parent = dict(
        bundle_sha256="e" * 64,
        target_date=day,
        continuous_reversal=dict(
            operating_manifest=dict(
                scopes={s: v["parent_branch_ids"] for s, v in c["scopes"].items()},
                registration_receipts=[request()],
            )
        ),
    )
    if only_a09:
        scopes = parent["continuous_reversal"]["operating_manifest"]["scopes"]
        for key, route in V.scopes():
            scopes.setdefault(V.scope_id(key, route), ["legacy_dd5_ge_0_4_v1"])
    source = P.seal(
        dict(
            normalized_sources=dict(
                partitions=[dict(day=day, venue="SOR", session="SOR_REGULAR")]
            )
        )
    )
    source_path = tmp_path / "source.json"
    P.write(source_path, source)
    receipt = dict(path=str(source_path), sha256=P.file_hash(source_path))
    native_preparation_files(tmp_path, day)
    monkeypatch.setattr(N, "validate", lambda *a, **kw: True)
    monkeypatch.setattr(P, "ensure_population", lambda *a, **kw: source)
    monkeypatch.setattr(P, "population_receipt", lambda *a: receipt)
    if fault=='prepare_race':
        import fcntl
        stage=H.stage_path(tmp_path/'report',day,'main_machine_policy')
        def source_with_scheduled_writer(*a,**k):
            with stage.with_suffix('.lock').open('a') as writer:
                fcntl.flock(writer,fcntl.LOCK_EX|fcntl.LOCK_NB)
                P.write(stage,dict(status='running'))
            return source
        monkeypatch.setattr(P,'ensure_population',source_with_scheduled_writer)
        with pytest.raises(ValueError,match='machine_stage_already_started'):
            R.prepare_scoring(tmp_path,tmp_path/'prepared',parent=parent,day=day)
        assert not (tmp_path/'prepared').exists()
        return
    prepared = R.prepare_scoring(
        tmp_path, tmp_path / "prepared", parent=parent, day=day,
        scope_candidates={"other_non_fixed|REGULAR|LT_20000|SOR": ["A09"]} if only_a09 else None,
    )
    assert prepared["preparation_basis"] == R.SOURCE_FIRST
    assert not H.stage_path(tmp_path/"report",day,"main_machine_policy").exists()
    assert not (tmp_path/"report/continuous_reversal_operating"/day/"machine.json").exists()
    if only_a09:
        assert list(prepared["scopes"]) == ["other_non_fixed|REGULAR|LT_20000|SOR"]
        assert prepared["unscored_scope_policy"] == "carry_parent"
        assert len(prepared["frozen_parent_scopes"]) == 128
    pointer = N.root(tmp_path) / "cumulative-scoring.json"
    assert not pointer.exists() and prepared["operator_receipt"] is None
    with pytest.raises(ValueError, match="scoring_contract_invalid"):
        R.validate_scoring(prepared)
    P.write(
        N.root(tmp_path) / "current.json", dict(bundle_sha256=parent["bundle_sha256"])
    )
    monkeypatch.setattr(V, "_attested_activation_parent", lambda *a, **kw: parent)
    args = dict(
        confirm=R.SCORING_AUTHORITY, origin_root=tmp_path, origin_commit="a" * 40
    )
    if fault:
        import fcntl
        import json
        stage = H.stage_path(tmp_path/'report',day,'main_machine_policy')
        lock = None
        if fault=='stage': P.write(stage,dict(status='running'))
        elif fault=='output': P.write(tmp_path/'report/continuous_reversal_operating'/day/'machine-comparison.json',{})
        elif fault=='locked':
            lock=stage.with_suffix('.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        elif fault=='raw': (tmp_path/'pipeline_events'/f'pipeline_events_{day}.jsonl').write_text('changed')
        elif fault=='source': source_path.write_text('{}')
        elif fault=='parent':
            monkeypatch.setattr(V,'_attested_activation_parent',lambda *a,**k:dict(parent,bundle_sha256='f'*64))
        elif fault=='stage_race':
            def admitted(*a,**k):
                P.write(stage,dict(status='running'));return parent
            monkeypatch.setattr(V,'_attested_activation_parent',admitted)
        else:
            changed=P.seal(dict(prepared,preparation_reader_code_sha256='f'*64))
            P.write(tmp_path/'prepared/prepared-scoring.json',changed)
        try:
            with pytest.raises(ValueError,match='stage_|preparation_reader_changed|preflight_invalid|prepared_source_changed|preparation_inputs_changed|parent_changed'):
                R.intake_scoring(tmp_path,tmp_path/'prepared/prepared-scoring.json',**args)
            assert not pointer.exists()
        finally:
            if lock:lock.close()
        return
    adopted = R.intake_scoring(
        tmp_path, tmp_path / "prepared/prepared-scoring.json", **args
    )
    assert adopted["operator_receipt"] == R.SCORING_AUTHORITY
    assert (
        R.scoring_for_build(tmp_path, parent, day, source["artifact_content_sha256"])
        == adopted
    )
    assert (
        R.intake_scoring(tmp_path, tmp_path / "prepared/prepared-scoring.json", **args)
        == adopted
    )
    Path(prepared["source_receipts"][0]["path"]).write_text("corrupted")
    with pytest.raises(ValueError, match="source_changed"):
        R.intake_scoring(tmp_path, tmp_path / "prepared/prepared-scoring.json", **args)


def test_scoring_bad_point_is_excluded_without_blocking_valid_rows(tmp_path):
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import reversal_cumulative_postclose as CP
    from src.engine.ai import offline_comparison_store as S

    c = scoring_contract()
    sid = next(iter(R.SCORING_ALIASES))
    cfg = c["scopes"][sid]
    configs = {
        s: dict(v["alternatives"], CURRENT_NATIVE=v["parent_branch_ids"])
        for s, v in c["scopes"].items()
    }
    current = {s: v["parent_branch_ids"] for s, v in c["scopes"].items()}
    with S.Store(tmp_path) as store:
        records = []
        for i, at in enumerate([1793070000, float(10**30)]):
            snap = store.put(
                [
                    dict(
                        epoch=at, symbol="000001", venue="SOR", source_item="000001_AL"
                    ),
                    {},
                ]
            )
            records.append(
                dict(
                    opportunity_key=str(i),
                    scope=sid,
                    day="2026-10-27",
                    symbol="000001",
                    outcome={"status": "WIN"},
                    truth={cfg["parent_branch_ids"][0]: "TRUE"},
                    snapshot_obj=snap,
                )
            )
        m, e = CP.scoring_metrics(records, configs, current, c, store)
        assert m[sid + "::CURRENT_NATIVE"]["chronological"]["wins"] == 1
        assert m[sid + "::CURRENT_NATIVE"]["wins"] == 1
        assert m[sid + "::CURRENT_NATIVE"]["statistic_source_complete"] is True
        assert e[sid + "::CURRENT_NATIVE"]["excluded_keys"] == ["1"]
        research = P.seal(dict(c, operator_receipt=None))
        mr, _ = CP.scoring_metrics(
            records, configs, current, research, store, research_only=True
        )
    same = {
        n: dict(
            mr[sid + "::" + n],
            source_complete=True,
            comparison_complete=True,
            source_universe_sha256="s",
        )
        for n in configs[sid]
    }
    result = R.select_variant(
        cfg,
        current[sid],
        same,
        authority=None,
        scoring=research,
        scope=sid,
        research_only=True,
    )
    assert result["research_only"] and result["variant"] == "CURRENT_NATIVE"
    with pytest.raises(ValueError, match="scoring_contract_invalid"):
        R.select_variant(
            cfg,
            current[sid],
            same,
            authority=R.SELECTION_AUTHORITY,
            scoring=research,
            scope=sid,
        )


def scoped_a09_contract(parent):
    from src.engine.scalping import continuous_reversal_postclose as P

    c = scoring_contract()
    sid = "other_non_fixed|REGULAR|LT_20000|SOR"
    c["scopes"] = {sid: copy.deepcopy(c["scopes"][sid])}
    c["scopes"][sid]["alternatives"] = {
        "ADD_A09": c["scopes"][sid]["alternatives"]["ADD_A09"]
    }
    c["unscored_scope_policy"] = "carry_parent"
    c["frozen_parent_scopes"] = copy.deepcopy(
        parent["continuous_reversal"]["operating_manifest"]["scopes"]
    )
    return P.seal(c)


@pytest.mark.parametrize("defect", ["missing_carry", "empty_scopes", "unknown_alias", "missing_parent", "changed_target_parent"])
def test_scoped_adoption_rejects_incomplete_or_expanded_contract(monkeypatch, defect):
    from src.engine.scalping import continuous_reversal_postclose as P

    parent, _ = postclose_fixture(monkeypatch)
    c = scoped_a09_contract(parent)
    assert R.validate_scoring(c)
    sid = next(iter(c["scopes"]))
    if defect == "missing_carry":
        c.pop("unscored_scope_policy")
    elif defect == "empty_scopes":
        c["scopes"] = {}
    elif defect == "unknown_alias":
        c["scopes"][sid]["alternatives"]["ADD_UNKNOWN"] = c["scopes"][sid]["parent_branch_ids"]
    elif defect == "missing_parent":
        c["frozen_parent_scopes"].pop(next(iter(c["frozen_parent_scopes"])))
    else:
        c["frozen_parent_scopes"][sid] = []
    with pytest.raises(ValueError, match="cumulative_scoring_"):
        R.validate_scoring(P.seal(c))


def test_a09_only_selection_carries_every_other_scope_despite_better_metrics(monkeypatch):
    from src.engine.scalping import continuous_reversal_postclose as P

    parent, m = postclose_fixture(monkeypatch)
    c = scoped_a09_contract(parent)
    sid = next(iter(c["scopes"]))
    m["cumulative_scoring_contract"] = c
    metrics = {
        sid + "::CURRENT_NATIVE": scored_metric(c, 2),
        sid + "::ADD_A09": scored_metric(c, 113, s=9, t=82, u=118),
    }
    # Tempt an unrelated registered scope with an apparently perfect variant.
    other = next(s for s in R.groups() if s != sid)
    metrics[other + "::ADD_A12"] = metric(100)
    machine = P.seal(dict(status="completed", source_manifest_receipt={"fixture": True},
                         source_manifest_sha256="b" * 64, label_contract=C.LABEL,
                         operating_manifest=m, proposal_metrics=metrics))
    result = R.apply_selection(machine, parent)
    assert R.validate_manifest(result["operating_manifest"])
    scopes = result["operating_manifest"]["scopes"]
    expected = copy.deepcopy(c["frozen_parent_scopes"])
    expected[sid] = c["scopes"][sid]["alternatives"]["ADD_A09"]
    assert scopes == expected
    assert result["cumulative_selection"][sid]["variant"] == "ADD_A09"
    assert result["cumulative_selection"][other]["status"] == "carried_unscored_scope"
    altered = copy.deepcopy(result["operating_manifest"])
    altered["scopes"][other] = []
    with pytest.raises(ValueError, match="unscored_membership_changed"):
        R.validate_manifest(altered)


def test_scoped_postclose_does_not_enumerate_unapproved_alternatives(tmp_path, monkeypatch):
    import gzip, json
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import reversal_cumulative_postclose as CP

    parent, m = postclose_fixture(monkeypatch)
    c = scoped_a09_contract(parent)
    m["cumulative_scoring_contract"] = c
    monkeypatch.setattr(R, "pending", lambda *a: None)
    monkeypatch.setattr(R, "scoring_for_build", lambda *a: c)
    source = P.seal(dict(normalized_sources=dict(partitions=[])))
    report = CP.build(tmp_path, "2026-10-27", "2026-10-27", parent, source=source, publish_outputs=False)
    with gzip.open(report["fixed_comparison_table"]["path"], "rt") as handle:
        complete = json.load(handle)
    for sid, options in complete["fixed_proposals"].items():
        assert set(options) - {"SELECTED"} == ({"ADD_A09", "CURRENT_NATIVE"} if sid in c["scopes"] else {"CURRENT_NATIVE"})
    for options in report["fixed_proposals"].values():
        assert set(options) == {"SELECTED", "CURRENT_NATIVE"}
        assert options["SELECTED"] == options["CURRENT_NATIVE"]
    assert report["operating_manifest"]["scopes"] == c["frozen_parent_scopes"]


def test_scoped_pending_rejects_different_full_parent_map(tmp_path, monkeypatch):
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    parent, m = postclose_fixture(monkeypatch)
    c = scoped_a09_contract(parent)
    parent["bundle_sha256"] = c["parent_bundle_sha256"]
    parent["continuous_reversal"]["operating_manifest"]["registration_receipts"] = [request()]
    P.write(N.root(tmp_path)/"cumulative-scoring.json", c)
    monkeypatch.setattr(R, "validate_scoring", lambda *a, **kw: c)
    other = next(s for s in m["scopes"] if s not in c["scopes"])
    parent["continuous_reversal"]["operating_manifest"]["scopes"][other] = []
    with pytest.raises(ValueError, match="parent_scope_map_changed"):
        R.scoring_for_build(tmp_path,parent,"2026-10-27","b"*64)


@pytest.mark.parametrize('fault', [None, 'code', 'parent', 'raw', 'stage', 'busy'])
def test_source_first_intent_fulfills_only_exact_approved_recipe(tmp_path, monkeypatch, fault):
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.automation import postclose_summary_handoff as H
    from src.engine.lifecycle.research_admission import acquire

    day = '2026-10-27'
    sid = 'other_non_fixed|REGULAR|LT_20000|SOR'
    parent, _ = postclose_fixture(monkeypatch)
    parent.update(bundle_sha256='e'*64, target_date=day)
    parent['continuous_reversal']['operating_manifest']['registration_receipts'] = [request()]
    monkeypatch.setattr(R, 'pending', lambda *a: None)
    native_preparation_files(tmp_path, day)
    source = P.seal(dict(normalized_sources=dict(partitions=[dict(day=day,venue='SOR',session='SOR_REGULAR')])))
    src = tmp_path/'source.json'
    P.write(src, source)
    monkeypatch.setattr(N, 'validate', lambda *a, **k: True)
    monkeypatch.setattr(V, '_attested_activation_parent', lambda *a, **k: parent)
    monkeypatch.setattr(P, 'ensure_population', lambda *a, **k: source)
    monkeypatch.setattr(P, 'population_receipt', lambda *a: dict(path=str(src),sha256=P.file_hash(src)))
    P.write(N.root(tmp_path)/'current.json', dict(bundle_sha256=parent['bundle_sha256']))
    assert R.fulfill_scoring(tmp_path,day,day)['status']=='not_requested'
    assert not R.scoring_path(tmp_path).exists()
    kwargs=dict(publication=day,scope_candidates={sid:['A09']},origin_root=tmp_path,origin_commit='a'*40)
    from src.engine.infrastructure import runtime_release_router as router
    monkeypatch.setattr(router, 'selected_release', lambda *_: (tmp_path, 'a'*40))
    with pytest.raises(ValueError, match='explicit_authority'):
        R.request_scoring(tmp_path,confirm='implementation',**kwargs)
    intent=R.request_scoring(tmp_path,confirm=R.SCORING_AUTHORITY,**kwargs)
    assert 'source_manifest_sha256' not in intent
    assert len(intent['frozen_parent_scopes'])==128
    assert not R.scoring_path(tmp_path).exists()
    assert R.fulfill_scoring(tmp_path,day,'2026-10-28')['status']=='not_requested_for_publication'
    assert R.request_scoring(tmp_path,confirm=R.SCORING_AUTHORITY,**kwargs)==intent
    reservation=[]
    if fault=='code':
        P.write(R.scoring_intent_path(tmp_path),P.seal(dict(intent,preparation_reader_code_sha256='f'*64)))
    elif fault=='parent': parent['bundle_sha256']='f'*64
    elif fault=='raw': (tmp_path/'pipeline_events'/f'pipeline_events_{day}.jsonl').write_text('changed')
    elif fault=='stage': P.write(H.stage_path(tmp_path/'report',day,'main_machine_policy'),dict(status='running'))
    elif fault=='busy':
        reservation=[acquire(tmp_path,'main_machine_policy',day),acquire(tmp_path,'main_machine_policy',day)]
        assert all(reservation)
    try:
        if fault:
            with pytest.raises(ValueError,match='code_changed|parent_scope_map_changed|preflight_invalid|stage_already_started|admission_busy'):
                R.fulfill_scoring(tmp_path,day,day)
            assert not R.scoring_path(tmp_path).exists()
            return
        registered=R.fulfill_scoring(tmp_path,day,day)
        assert registered['source_first_intent_sha256']==intent['artifact_content_sha256']
        assert registered['operator_receipt']==R.SCORING_AUTHORITY
        assert registered['scopes']==intent['scopes']
        assert len(registered['frozen_parent_scopes'])==128
        assert R.fulfill_scoring(tmp_path,day,day)==registered
        # A late exact resume reads immutable evidence, never reinserts a new request.
        P.write(H.stage_path(tmp_path/'report',day,'main_machine_policy'),dict(status='succeeded'))
        assert R.fulfill_scoring(tmp_path,day,day)==registered
        P.write(src, {})
        with pytest.raises(ValueError,match='prepared_source_changed'):
            R.scoring_for_build(tmp_path,parent,day,source['artifact_content_sha256'])
        archived=Path(registered['source_receipts'][0]['path'])
        archived.write_text('corrupted')
        with pytest.raises(ValueError,match='source_changed'):
            R.fulfill_scoring(tmp_path,day,day)
    finally:
        for item in reservation: item.close()


def test_scoring_replay_cache_binds_actual_requested_detection_memberships(tmp_path, monkeypatch):
    import gzip, json
    from src.engine.scalping import reversal_cumulative_postclose as CP
    from src.engine.scalping import continuous_reversal_postclose as P

    parent, _ = postclose_fixture(monkeypatch)
    parent['bundle_sha256']='e'*64
    stream=rows([3000]*125+[2980,2981,2982])
    for i,row in enumerate(stream): row[0]=1793070000+i;row[9]='000001_AL'
    raw=tmp_path/'regular.json.gz'
    raw.write_bytes(gzip.compress(json.dumps(dict(symbols={'000001':stream})).encode()))
    source=P.seal(dict(normalized_sources=dict(partitions=[dict(day='2026-10-27',venue='SOR',session='SOR_REGULAR',path=str(raw),sha256=P.file_hash(raw))])))
    c=scoring_contract();c['source_manifest_sha256']=source['artifact_content_sha256']
    c['unscored_scope_policy']='carry_parent'
    c['frozen_parent_scopes']=parent['continuous_reversal']['operating_manifest']['scopes']
    sid='other_non_fixed|REGULAR|LT_20000|SOR'
    c['scopes']={sid:c['scopes'][sid]}
    alternatives=c['scopes'][sid]['alternatives']
    c['scopes'][sid]['alternatives']={'ADD_A05':alternatives['ADD_A05']}
    monkeypatch.setattr(R,'pending',lambda *a:None)
    monkeypatch.setattr(R,'scoring_for_build',lambda *a:P.seal(c))
    monkeypatch.setattr(P,'population_receipt',lambda *a:dict(path='private-fixture'))
    actual=CP.State;observed=[]
    def state(**kwargs):
        observed.append(kwargs['branch_ids']);return actual(**kwargs)
    monkeypatch.setattr(CP,'State',state)
    def build(): return CP.build(tmp_path,'2026-10-27','2026-10-27',parent,source=source,publish_outputs=False)
    build();assert len(observed)==1
    build();assert len(observed)==1
    c['scopes'][sid]['alternatives']={'ADD_A09':alternatives['ADD_A09']}
    build();assert len(observed)==2 and observed[0]!=observed[1]
    build();assert len(observed)==2


def test_scoped_machine_selection_survives_enabled_auxiliary_campaign_and_issue(tmp_path, monkeypatch):
    from src.engine.scalping import reversal_cumulative_postclose as CP
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import reversal_auxiliary_tuning as T
    from src.engine.scalping import reversal_auxiliary_registry as G
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import reversal_extended_union as U

    parent, m = postclose_fixture(monkeypatch)
    parent['bundle_sha256']='e'*64
    parent['continuous_reversal']['schema']=V.SCHEMA
    source=P.seal(dict(normalized_sources=dict(partitions=[])))
    contract=P.seal(dict(scoring_contract(),source_manifest_sha256=source['artifact_content_sha256']))
    monkeypatch.setattr(R,'pending',lambda *a:None)
    monkeypatch.setattr(R,'scoring_for_build',lambda *a:contract)
    monkeypatch.setattr(P,'population_receipt',lambda *a:dict(path='private-fixture'))
    machine=CP.build(tmp_path,'2026-10-27','2026-10-27',parent,source=source)
    before=copy.deepcopy(machine['operating_manifest'])
    ident=G.register(tmp_path,G.definition(U.V1.ARMS[1],input_version=U.VERSION))
    bindings={V.scope_id(k,r):ident for k,r in V.scopes()}
    monkeypatch.setattr(I,'effective_bindings',lambda *a,**k:bindings.copy())
    monkeypatch.setattr(I,'current',lambda *a,**k:None)
    monkeypatch.setattr(I,'lineage_sources',lambda *a:[])
    monkeypatch.setattr(I,'independent_scopes',lambda *a:set())
    monkeypatch.setattr(I,'rollback_bindings',lambda *a:bindings.copy())
    sid='other_non_fixed|REGULAR|LT_20000|SOR'
    T.configure(tmp_path,candidate=ident,scopes=[sid],seed='scoped-native-test',max_pairs=50)
    from src.tests.test_offline_comparison_store import activate
    from src.engine.ai import offline_comparison_store as S
    with S.Store(tmp_path) as store: activate(store)
    campaign=T.prepare(tmp_path,'2026-10-27',machine,parent)
    assert campaign['machine_report_sha256']==machine['artifact_content_sha256']
    auxiliary=T.auxiliary_report(tmp_path,'2026-10-27','2026-10-27',parent,publish_policy=False)
    issued=T.read(O.directory(tmp_path,'2026-10-27')/'machine.json')
    assert issued['operating_manifest']==before and R.validate_manifest(before)
    assert issued['cumulative_selection']==machine['cumulative_selection']
    assert auxiliary['auxiliary_registry_bindings']==bindings
    assert issued['artifact_content_sha256']!=machine['artifact_content_sha256']
    assert T.read(O.directory(tmp_path,'2026-10-27')/'machine-comparison.json')==machine


@pytest.mark.parametrize('fault', [None, 'review', 'recipe', 'source', 'stage', 'materialized', 'selector', 'archive', 'review_race'])
def test_pending_scoring_handoff_keeps_approval_and_selected_reader(tmp_path, monkeypatch, fault):
    import json
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure import runtime_release_router as router
    from src.engine.automation import postclose_summary_handoff as H

    day=datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat()
    data=tmp_path/'data'; root=tmp_path/'target'; source_root=tmp_path/'source'
    root.mkdir(); source_root.mkdir()
    parent,_=postclose_fixture(monkeypatch)
    parent.update(bundle_sha256='e'*64,target_date=day)
    parent['continuous_reversal']['operating_manifest']['registration_receipts']=[request()]
    monkeypatch.setattr(V,'_attested_activation_parent',lambda *a,**k:parent)
    monkeypatch.setattr(router,'selected_release',lambda *_:(source_root,'a'*40))
    P.write(N.root(data)/'current.json',dict(bundle_sha256=parent['bundle_sha256']))
    intent=R.request_scoring(data,publication=day,scope_candidates={'other_non_fixed|REGULAR|LT_20000|SOR':['A09']},
        confirm=R.SCORING_AUTHORITY,origin_root=source_root,origin_commit='a'*40)
    path=R.scoring_intent_path(data); original=path.read_bytes(); expected=P.file_hash(path)
    selector=data/'runtime/runtime_release_selection.json'; P.write(selector,dict(root=str(root)))
    monkeypatch.setattr(router,'selected_release',lambda *_:(root,'b'*40))
    fields=('contract_file_sha256','preparation_reader_code_sha256')
    source={k:intent[k] for k in fields}
    target=dict(contract_file_sha256={**source['contract_file_sha256'],'new_module.py':'f'*64},
        preparation_reader_code_sha256='d'*64)
    proposed=P.seal(dict(intent,**target,activation_parent_origin=dict(root=str(root),commit='b'*40)))
    review=dict(status='reviewed',intent_sha256=expected,source_code=source,target_code=target,
        target_root=str(root),target_commit='b'*40,recipe_changed=False)
    if fault=='review': review['target_commit']='c'*40
    review_path=tmp_path/'review.json'; P.write(review_path,review)
    def context(code_root,commit,old,**kwargs):
        if code_root==source_root:
            return {**source, 'contract_file_sha256':{} if fault=='source' else source['contract_file_sha256']}
        if fault=='recipe': proposed['scopes']={}
        if fault=='selector': P.write(selector,dict(changed=True))
        return dict(target,proposed=proposed)
    monkeypatch.setattr(R,'_scoring_handoff_context',context)
    if fault=='stage': P.write(H.stage_path(data/'report',day,'main_machine_policy'),dict(status='running'))
    if fault=='materialized': P.write(R.scoring_path(data),{})
    if fault=='archive':
        def fail(*a): raise OSError('archive_failed')
        monkeypatch.setattr(R,'_archive',fail)
    if fault=='review_race':
        original_archive=R._archive
        def race(source, destination):
            if Path(source)==review_path:P.write(review_path,dict(changed=True))
            return original_archive(source,destination)
        monkeypatch.setattr(R,'_archive',race)
    if fault:
        with pytest.raises((ValueError,OSError)):
            R.handoff_scoring_intent(data,expected_sha256=expected,review_path=review_path,confirm=R.SCORING_AUTHORITY)
        assert path.read_bytes()==original
        return
    new=R.handoff_scoring_intent(data,expected_sha256=expected,review_path=review_path,confirm=R.SCORING_AUTHORITY)
    assert new['scopes']==intent['scopes']
    assert new['frozen_parent_scopes']==intent['frozen_parent_scopes']
    assert new['spec']==intent['spec']
    assert new['contract_file_sha256']==target['contract_file_sha256']
    assert new['code_handoff']['predecessor_content_sha256']==intent['artifact_content_sha256']
    archived=Path(new['code_handoff']['predecessor_intent']['path'])
    assert archived.read_bytes()==original
    assert R._validate_scoring_intent(new)==new
    assert not R.scoring_path(data).exists()
    with pytest.raises(ValueError,match='explicit_authority'):
        R.handoff_scoring_intent(data,expected_sha256=P.file_hash(path),review_path=review_path,confirm='tests')


def test_request_scoring_rejects_selector_advance_before_publication(tmp_path, monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure import runtime_release_router as router
    parent,_=postclose_fixture(monkeypatch)
    parent['continuous_reversal']['operating_manifest']['registration_receipts']=[request()]
    parent['bundle_sha256']='e'*64
    monkeypatch.setattr(V,'_attested_activation_parent',lambda *a,**k:parent)
    monkeypatch.setattr(router,'selected_release',lambda *_:(tmp_path,'b'*40))
    P.write(N.root(tmp_path)/'current.json',dict(bundle_sha256='e'*64))
    with pytest.raises(ValueError,match='selected_generation_changed'):
        R.request_scoring(tmp_path,publication=datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat(),
            scope_candidates={'other_non_fixed|REGULAR|LT_20000|SOR':['A09']},confirm=R.SCORING_AUTHORITY,
            origin_root=tmp_path,origin_commit='a'*40)
    assert not R.scoring_intent_path(tmp_path).exists()


def _materialized_scoring_fixture(data, monkeypatch):
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure import runtime_release_router as router
    day = "2026-10-27"
    parent, _ = postclose_fixture(monkeypatch)
    parent.update(bundle_sha256="e" * 64, target_date=day)
    parent["continuous_reversal"]["operating_manifest"]["registration_receipts"] = [request()]
    monkeypatch.setattr(R, "pending", lambda *a: None)
    native_preparation_files(data, day)
    source = P.seal(dict(normalized_sources=dict(partitions=[dict(day=day, venue="SOR", session="SOR_REGULAR")])))
    source_path = data / "source.json"
    P.write(source_path, source)
    monkeypatch.setattr(N, "validate", lambda *a, **k: True)
    monkeypatch.setattr(V, "_attested_activation_parent", lambda *a, **k: parent)
    monkeypatch.setattr(P, "ensure_population", lambda *a, **k: source)
    monkeypatch.setattr(P, "population_receipt", lambda *a: dict(path=str(source_path), sha256=P.file_hash(source_path)))
    monkeypatch.setattr(router, "selected_release", lambda *_: (data, "a" * 40))
    P.write(N.root(data) / "current.json", dict(bundle_sha256=parent["bundle_sha256"]))
    intent = R.request_scoring(data, publication=day,
        scope_candidates={"other_non_fixed|REGULAR|LT_20000|SOR": ["A09"]},
        origin_root=data, origin_commit="a" * 40, confirm=R.SCORING_AUTHORITY)
    bound = R.fulfill_scoring(data, day, day)
    return day, intent, bound


@pytest.mark.parametrize("damage", [None, "binding", "recipe", "code", "archive_missing", "archive_changed", "unmaterialized", "future_pending", "corrupt", "symlink", "live_reference"])
def test_deployment_distinguishes_exact_materialization_from_pending_approval(tmp_path, monkeypatch, damage):
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    day, intent, bound = _materialized_scoring_fixture(tmp_path, monkeypatch)
    path = R.scoring_intent_path(tmp_path)
    original = path.read_bytes()
    materialized = R.scoring_path(tmp_path)
    archived = next(Path(r["path"]) for r in bound["source_receipts"] if r["sha256"] == P.file_hash(path))
    monkeypatch.setattr(V, "contract_modules", lambda: [])
    if damage in ("binding", "recipe", "code"):
        key = {"binding": "source_first_intent_sha256", "recipe": "parent_bundle_sha256", "code": "preparation_reader_code_sha256"}[damage]
        P.write(materialized, P.seal(dict(bound, **{key: "f" * 64})))
    elif damage == "archive_missing": archived.unlink()
    elif damage == "archive_changed": archived.write_bytes(archived.read_bytes() + b" ")
    elif damage == "unmaterialized": materialized.unlink()
    elif damage == "future_pending":
        P.write(path, P.seal(dict(intent, publication_date="2026-10-28", target_date="2026-10-29")))
    elif damage == "live_reference":
        replaced = [dict(r, path=str(path)) if r["path"] == str(archived) else r for r in bound["source_receipts"]]
        P.write(materialized, P.seal(dict(bound, source_receipts=replaced)))
    elif damage == "corrupt": materialized.write_text("invalid")
    elif damage == "symlink":
        target = tmp_path / "outside.json"
        target.write_bytes(materialized.read_bytes())
        materialized.unlink()
        materialized.symlink_to(target)
    if damage is not None:
        with pytest.raises((ValueError, OSError)) as failure:
            R.pending_scoring_code_check(tmp_path, day)
        if damage in ("binding", "recipe", "code"):
            assert "fulfillment_binding_invalid" in str(failure.value)
        elif damage == "archive_changed":
            assert "fulfillment_evidence_changed" in str(failure.value)
        elif damage in ("unmaterialized", "future_pending"):
            assert "pending_scoring_code_changed" in str(failure.value)
    else:
        result = R.pending_scoring_code_check(tmp_path, day)
        assert result["request_state"] == "materialized"
        assert result["materialized_sha256"] == P.file_hash(materialized)
        assert result["sha256"] == P.file_hash(path)
    if damage != "future_pending": assert path.read_bytes() == original


def test_materialized_scoring_bytes_remain_in_real_deployment_cas(tmp_path, monkeypatch):
    from src.engine.automation import ordered_intraday_deploy as D
    day, _, _ = _materialized_scoring_fixture(tmp_path / "data", monkeypatch)
    driver = object.__new__(D.Deployment)
    driver.workspace, driver.day = tmp_path, day
    driver._assert_failed_transition_unchanged = lambda: None
    driver.pending_scoring = R.pending_scoring_code_check(tmp_path / "data", day)
    path = R.scoring_path(tmp_path / "data")
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="deployment_pending_scoring_changed"):
        driver.assert_unchanged()
