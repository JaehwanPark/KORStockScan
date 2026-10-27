"""Real causal detector/reader contracts for the joint operating successor."""

import copy
from datetime import datetime
from types import SimpleNamespace
import threading
import pytest
from src.engine.scalping import reversal_joint_catalog as J
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import reversal_extended_state as S
from src.engine.scalping import reversal_extended_auxiliary as A
from src.engine.scalping import continuous_reversal as K


@pytest.fixture
def joint_frozen_source(tmp_path):
    """Restore exact historical bytes for tests; never tune or promote them.

    Keep only the five immutable inputs consumed by these tests, independent
    of workspace data symlinks, operational policies, and mutable tmp reports.
    """
    import gzip
    import hashlib
    import io
    import json
    from pathlib import Path
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    assets = Path(__file__).parent / "fixtures/reversal_joint_registration"
    manifest_raw = (assets / "manifest.json").read_bytes()
    assert (
        hashlib.sha256(manifest_raw).hexdigest()
        == "5f5d0647b07a9b1f601593524330cee76365ecc063015c53a8a32cde1b4fb724"
    )
    manifest = json.loads(manifest_raw)
    assert manifest["use"] == "test_only_immutable_input_not_tuning_or_promotion"
    assert manifest["original_parent_bundle_sha256"] == J.PARENT
    assert len(manifest["files"]) == 5
    assert sum(r["bytes"] for r in manifest["files"]) == 7864175
    target = tmp_path / "frozen-joint-inputs"
    for receipt in manifest["files"]:
        path = assets / receipt["fixture_file"]
        assert path.parent == assets and not path.is_symlink()
        with path.open("rb") as handle:
            compressed = handle.read(receipt["gzip_bytes"] + 1)
        assert len(compressed) == receipt["gzip_bytes"]
        assert hashlib.sha256(compressed).hexdigest() == receipt["gzip_sha256"]
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as handle:
            raw = handle.read(receipt["bytes"] + 1)
        assert len(raw) == receipt["bytes"]
        assert hashlib.sha256(raw).hexdigest() == receipt["sha256"]
        relative = Path(receipt["original_relative_path"])
        assert not relative.is_absolute() and ".." not in relative.parts
        restored = target / relative
        restored.parent.mkdir(parents=True, exist_ok=True)
        restored.write_bytes(raw)
        assert restored.read_bytes() == raw
    data = target / "data"
    parent_path = N.root(data) / "generations" / (J.PARENT + ".json")
    parent = json.loads(parent_path.read_bytes())
    assert (
        parent["bundle_sha256"]
        == J.PARENT
        == N.digest({k: v for k, v in parent.items() if k != "bundle_sha256"})
    )
    family = parent["continuous_reversal"]["native_parent_bundle"][
        "continuous_reversal"
    ]
    for name in ("machine", "auxiliary"):
        source = (
            N.root(data)
            / "sources"
            / ("reversal-" + family[name + "_report_sha256"] + ".json")
        )
        value = json.loads(source.read_bytes())
        assert value == P.seal(value)
        assert value["artifact_content_sha256"] == family[name + "_report_sha256"]
    evidence = (
        target
        / "tmp/main-machine-joint-research-20261013/operating-application-plan-evidence.json"
    )
    assert P.file_hash(evidence) == J.EVIDENCE_FILE_SHA256
    assert (
        P.file_hash(evidence.parent / "opportunity-frontier-result.json")
        == J.RESEARCH_RESULT
    )
    return dict(data=data, parent=parent, evidence=evidence)


T = datetime(2026, 10, 13, 16, 20, tzinfo=K.KST).timestamp()


@pytest.fixture
def prefix_readiness(monkeypatch):
    from src.engine.scalping import reversal_source_diagnostics as D
    from src.engine.scalping import reversal_current_backend as dispatch

    def build(bid="G4", session="SOR_REGULAR"):
        stamp = datetime(
            2026, 10, 21, 11 if session == "SOR_REGULAR" else 17, tzinfo=K.KST
        ).timestamp()
        values = [
            [stamp + i, 7, i + 1, 11000, 10990, 11010, 1, 1, 1, "127120_AL", 0]
            for i in range(71)
        ]
        state = S.State(
            branch_ids=[bid], offline=True, session_anchor=values[0], generation="scope"
        )
        for r in values:
            state.observe(r, symbol="127120", venue="SOR", session=session)
        market = K.market_bucket(session)
        key = C.cell_key("127120", market, 11000)
        cell = dict(
            backend="union_v6",
            scope_execution_hash="scope",
            payload=dict(branches=[dict(branch_id=bid)]),
        )
        family = dict(
            family_sha256="family",
            registry_sha256=C.registry_for([bid]),
            machine_cells={key: dict(routes={"SOR": cell})},
        )
        owner = SimpleNamespace(
            _LOCK=threading.RLock(),
            _FAMILY=family,
            _GENERATION="family",
            _STATES={("127120", "SOR", "127120_AL", market, "2026-10-21", key): state},
            R=None,
        )
        monkeypatch.setattr(dispatch, "backend", lambda: owner)
        candidate = SimpleNamespace(
            code="127120", route="krx_nxt_integrated", discovery_price=11000
        )
        return D, state, candidate, values[-1], bid

    return build


@pytest.mark.parametrize(
    "bid,session,expected",
    [
        ("G4", "SOR_REGULAR", 100 * (11010 / 10990 - 1)),
        (
            "manual_cumulative_01fc4db1dba5571d25f9a3f5",
            "SOR_AFTERMARKET",
            100 * (11010 - 10990) / 11000,
        ),
    ],
)
def test_prefix_readiness_projects_native_quote_without_inventing_confirmation(
    prefix_readiness, bid, session, expected
):
    D, state, candidate, last, bid = prefix_readiness(bid, session)
    before = copy.deepcopy(
        (
            state._feature_values,
            state.diagnostic_rolling,
            dict(state.coverage_snapshot),
            list(state.ready),
        )
    )
    result = D.branch_readiness(candidate, now=last[0] + 0.1, deadline=last[0] + 60)
    desc = result["branch_descriptors"][bid]
    assert desc["feature_values"]["spread"] == pytest.approx(expected)
    assert desc["feature_availability"] == "complete" and not desc["missing_inputs"]
    assert (
        desc["feature_basis"] == "prefix_context_no_confirmation"
        and desc["detector_truth"] == "FALSE"
    )
    assert (
        not state.ready
        and (
            state._feature_values,
            state.diagnostic_rolling,
            dict(state.coverage_snapshot),
            list(state.ready),
        )
        == before
    )


@pytest.mark.parametrize(
    "case",
    [
        "stale_source",
        "missing_quote",
        "crossed_quote",
        "invalid_source",
        "unbound_prefix",
        "explicit_unknown",
        "confirmation_unknown",
        "nonfinite_quote",
    ],
)
def test_prefix_quote_projection_preserves_missing_stale_and_confirmed_unknown(
    prefix_readiness, case
):
    D, state, candidate, last, bid = prefix_readiness()
    now = last[0] + 0.1
    if case == "stale_source":
        now = last[0] + 3.001
    elif case == "missing_quote":
        last[4] = None
    elif case == "crossed_quote":
        last[4] = last[5] + 1
    elif case == "nonfinite_quote":
        last[5] = float("inf")
    elif case == "invalid_source":
        last[8] = 0
    elif case == "unbound_prefix":
        state.diagnostic_rolling["identity"] = (0, 0, 0)
    elif case == "explicit_unknown":
        state.diagnostic_rolling["values"]["spread"] = None
    elif case == "confirmation_unknown":
        state.diagnostic_features[bid] = dict(
            identity=tuple(last[:3]), values=dict(state._feature_values, spread=None)
        )
    # Real State stores a separate native row value; replace its current view
    # only for the invalid-source/quote negative cases.
    if case in {"missing_quote", "crossed_quote", "invalid_source", "nonfinite_quote"}:
        state.legacy.last = last
    result = D.branch_readiness(candidate, now=now, deadline=now + 60)
    desc = result["branch_descriptors"][bid]
    assert (
        "spread" in desc["missing_inputs"] and desc["feature_values"]["spread"] is None
    )


def test_prefix_projection_cannot_reuse_a_different_state_generation(prefix_readiness):
    D, state, candidate, last, bid = prefix_readiness()
    state.generation = "different-scope"
    result = D.branch_readiness(candidate, now=last[0] + 0.1, deadline=last[0] + 60)
    assert (
        result["status"] == "unobservable"
        and result["reason"] == "native_interval_unobserved"
    )


def row(i, p=110000, qty=1):
    return [T + i, 1, i + 1, p, p, p + 1, qty, 1, 1, "036930_AL", 0]


def feed(state, values):
    result = []
    for value in values:
        result += state.observe(
            value, symbol="036930", venue="SOR", session="KRX_NXT_AFTERMARKET"
        )
    return result


@pytest.mark.parametrize("warm,vwap_truth", [(20, "UNKNOWN"), (121, "TRUE")])
def test_composed_confirmation_keeps_original_and_never_emits_dependency(
    warm, vwap_truth
):
    bid = J.ALIASES["jusung_after_refined"]
    base = "legacy_dd5_ge_0_4_v1"
    values = [row(i) for i in range(warm)] + [
        row(warm, 109300, 100000),
        row(warm + 1, 109400),
        row(warm + 2, 109500),
    ]
    original = S.State(branch_ids=[base], offline=True, session_anchor=values[0])
    candidate = S.State(branch_ids=[bid], offline=True, session_anchor=values[0])
    old = feed(original, values)
    new = feed(candidate, values)
    assert old and new
    originals = {
        r["event"]["event_id"]: r["event"]["branch_signals"][base] for r in old
    }
    for ready in new:
        assert set(ready["event"]["branch_signals"]) == {bid}
        e = ready["event"]["branch_signals"][bid]
        A.validate_signal(e)
        assert e["epoch"] == originals[e["event_id"]]["epoch"]
        assert e["entry_ask"] == originals[e["event_id"]]["entry_ask"]
        assert e["signal_proof"]["refinement_truth"] == vwap_truth
    assert all(base not in r["event"]["branch_signals"] for r in candidate.ready)


@pytest.mark.parametrize("warm,truth", [(20, "UNKNOWN"), (121, "TRUE")])
def test_composed_original_and_refinement_features_build_strict_production_request(
    warm, truth
):
    from src.engine.scalping import (
        reversal_extended_runtime as E,
        reversal_path_runtime as ORIGINAL,
    )
    from src.engine.scalping import reversal_auxiliary_contract as V1
    from src.engine.scalping.continuous_reversal_postclose import digest

    bid = J.ALIASES["jusung_after_refined"]
    values = [row(i) for i in range(warm)] + [
        row(warm, 109300, 100000),
        row(warm + 1, 109400),
        row(warm + 2, 109500),
    ]
    state = S.State(branch_ids=[bid], offline=True, session_anchor=values[0])
    ready = feed(state, values)[0]
    event, source = E.snapshot(state, ready)
    signal = event["branch_signals"][bid]
    original = J.validate_composed(signal)
    frozen = copy.deepcopy((event, source))
    claim_digest = digest(frozen)
    assert signal["signal_proof"]["refinement_truth"] == truth
    assert signal["drawdown_5m_pct"] != signal["branch_features"]["dd"]
    facts = source["branch_inputs"][bid]["facts"]
    assert facts["drawdown_5m_pct"] == original["drawdown_5m_pct"]
    assert facts["volume_ratio_60s"] == original["volume_ratio_60s"]
    unadapted = ORIGINAL.State._source(state, signal, ready["row"])
    assert {
        k: v
        for k, v in facts.items()
        if k not in {"drawdown_5m_pct", "volume_ratio_60s"}
    } == {
        k: v
        for k, v in unadapted["facts"].items()
        if k not in {"drawdown_5m_pct", "volume_ratio_60s"}
    }
    inp, _, _ = A.production_request(
        source["branch_inputs"][bid],
        V1.ARMS[0],
        phase=signal["decision_phase"],
        event=signal,
    )
    A.validate_input_signal(inp, signal)
    assert (event, source) == frozen and digest((event, source)) == claim_digest
    assert E.snapshot(state, ready) == frozen
    bad = copy.deepcopy(inp)
    bad["entry_setup_evidence_v1"]["facts"]["drawdown_5m_pct"] += 0.1
    with pytest.raises(ValueError, match="path_auxiliary_feature_input_conflict"):
        A.validate_input_signal(bad, signal)


@pytest.mark.parametrize("field", ["drawdown_5m_pct", "volume_ratio_60s"])
def test_composed_source_rejects_altered_original_top_features(field):
    bid = J.ALIASES["jusung_after_refined"]
    values = [row(i) for i in range(121)] + [row(121, 109300, 100000), row(122, 109400)]
    state = S.State(branch_ids=[bid], offline=True, session_anchor=values[0])
    ready = feed(state, values)[0]
    signal = copy.deepcopy(ready["event"]["branch_signals"][bid])
    signal[field] = (signal[field] or 0) + 0.1
    with pytest.raises(ValueError, match="joint_original_feature_projection_conflict"):
        state._source(signal, ready["row"])


def test_noncomposed_source_bytes_remain_the_original_projection():
    from src.engine.scalping import reversal_path_runtime as ORIGINAL
    from src.engine.scalping.continuous_reversal_postclose import digest

    base = J.ALIASES["jusung_after_breakout"]
    values = [row(i) for i in range(61)] + [row(61, 110100)]
    state = S.State(branch_ids=[base], offline=True, session_anchor=values[0])
    ready = feed(state, values)[0]
    event = ready["event"]["branch_signals"][base]
    assert digest(state._source(event, ready["row"])) == digest(
        ORIGINAL.State._source(state, event, ready["row"])
    )


def test_refinement_false_consumes_confirmation_without_later_refinement_root():
    bid = J.ALIASES["jusung_after_refined"]
    state = S.State(branch_ids=[bid], offline=True, session_anchor=row(0))
    values = [row(i) for i in range(121)] + [
        row(121, 109300),
        row(122, 109400),
        row(123, 109500),
    ]
    assert not feed(state, values)
    assert not state.ready
    # Price at/above VWAP alone cannot invent a new original confirmation.
    assert not feed(state, [row(124, 109500, 100000)])


def test_independent_breakout_has_no_first_turn_dependency():
    bid = J.ALIASES["jusung_after_breakout"]
    state = S.State(branch_ids=[bid], offline=True, session_anchor=row(0))
    result = feed(state, [row(i) for i in range(61)] + [row(61, 110100)])
    assert result and bid in result[-1]["event"]["branch_signals"]
    e = result[-1]["event"]["branch_signals"][bid]
    A.validate_signal(e)
    assert e["decision_phase"] == "HIGH_BREAKOUT"
    assert "anchor_event_id" not in e["signal_proof"]


def test_diagnostic_rolling_dd_is_bound_without_overwriting_base_cache():
    state = S.State(
        branch_ids=["legacy_dd5_ge_0_4_v1"], offline=True, session_anchor=row(0)
    )
    feed(state, [row(i) for i in range(61)] + [row(61, 109300)])
    assert "dd" not in state._feature_values
    assert state.diagnostic_rolling["identity"] == tuple(row(61, 109300)[:3])
    assert state.diagnostic_rolling["values"]["dd"] > 0


def test_content_addressed_policy_ref_preserves_version_and_detects_tampering(tmp_path):
    from src.engine.lifecycle.policy_snapshot_reference import persist, resolve
    from src.engine.lifecycle.avg_down_policy_replay import snapshot_version

    snapshot = {
        "schema": "avg_down_full_policy_snapshot_v1",
        "rules": {"LIMIT": 5},
        "files": {"original": "x" * 20000},
    }
    ref = persist(snapshot, tmp_path)
    assert resolve(ref) == snapshot and snapshot_version(ref) == snapshot_version(
        snapshot
    )
    assert len(str(ref)) < len(str(snapshot)) / 10
    again = persist(snapshot, tmp_path)
    assert again == ref
    from pathlib import Path

    Path(ref["path"]).write_text("{}")
    with pytest.raises(ValueError, match="source_changed"):
        resolve(ref)


def test_policy_components_reuse_static_source_bytes_when_only_one_file_changes(
    tmp_path,
):
    from src.engine.lifecycle.policy_snapshot_reference import persist, resolve
    from pathlib import Path

    snapshot = {
        "schema": "avg_down_full_policy_snapshot_v1",
        "rules": {"LIMIT": 5},
        "files": {"constant": "x" * 200000, "moving": {"peak": 100}},
        "loaded_code": {"static": "f" * 200000},
    }
    ref = persist(snapshot, tmp_path)
    assert resolve(ref) == snapshot
    folder = Path(ref["path"]).parent
    before = {p.name: p.stat().st_size for p in folder.rglob("*.json")}
    newer = copy.deepcopy(snapshot)
    newer["files"]["moving"]["peak"] = 101
    second = persist(newer, tmp_path)
    assert resolve(second) == newer
    after = {p.name: p.stat().st_size for p in folder.rglob("*.json")}
    assert sum(size for name, size in after.items() if name not in before) < 3000


def test_anchor_writer_coalesces_new_streams_and_catches_up_during_write(
    tmp_path, monkeypatch
):
    import threading
    from src.engine.scalping import reversal_anchor_index as I

    callbacks = []
    writes = []
    monkeypatch.setattr(I, "_VERSIONS", {})
    monkeypatch.setattr(I, "_PENDING", set())
    monkeypatch.setattr(
        I,
        "_SINK",
        lambda callback, **kw: (callbacks.append(callback) or {"status": "queued"}),
    )
    owner = SimpleNamespace(_LOCK=threading.RLock(), _ANCHORS={}, _ANCHOR_CURSORS={})

    def save(root, day, anchors, cursors, **kwargs):
        writes.append(anchors)
        if len(writes) == 1:
            owner._ANCHORS[("123456", "SOR", "123456_AL", "REGULAR", day)] = [
                T,
                1,
                1,
                10000,
            ]
            assert I.enqueue(root, day, owner)
        return dict(structured_append_succeeded=True)

    monkeypatch.setattr(I, "save", save)
    for _ in range(100):
        assert I.enqueue(tmp_path, "2026-10-13", owner)
    assert len(callbacks) == 1
    assert callbacks.pop()()["structured_append_succeeded"]
    assert len(writes) == 2 and len(writes[-1]) == 1 and not I._PENDING


def test_new_stream_anchor_is_initialized_after_nonempty_day_restore(
    monkeypatch, joint_frozen_source
):
    from src.engine.scalping import reversal_path_runtime as R
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from pathlib import Path
    import json

    bundle = joint_frozen_source["parent"]
    # This is a frozen read, never configure or mutate a runtime policy file.
    f = bundle["continuous_reversal"]["native_parent_bundle"]["continuous_reversal"]
    monkeypatch.setattr(R, "_FAMILY", f)
    monkeypatch.setattr(R, "_GENERATION", f["family_sha256"])
    monkeypatch.setattr(R, "_STATES", {})
    monkeypatch.setattr(R, "_ANCHORS", {})
    day = "2026-10-13"
    monkeypatch.setattr(R, "_RESTORED_DAYS", {day})
    monkeypatch.setattr(R, "_EMPTY_PREFIX_DAYS", set())
    stamp = datetime(2026, 10, 13, 10, tzinfo=K.KST).timestamp()
    envelope = dict(
        observed_epoch=stamp,
        provider_trade_epoch=stamp,
        trade_price=10000,
        transport_epoch=1,
        route_sequence=1,
        inline_best_bid=10000,
        inline_best_ask=10001,
        trade_qty=1,
        aggressor_side="BUY",
        item="123456_AL",
        market_route="krx_nxt_integrated",
    )
    R.observe_normalized("123456", "KRX_REGULAR", envelope)
    key = ("123456", "SOR", "123456_AL", "REGULAR", day)
    assert R._ANCHORS[key] == [stamp, 1, 1, 10000.0]
    R.observe_normalized(
        "123456",
        "KRX_REGULAR",
        dict(
            envelope,
            observed_epoch=stamp + 1,
            provider_trade_epoch=stamp + 1,
            trade_price=10100,
            route_sequence=2,
        ),
    )
    assert R._ANCHORS[key][3] == 10000


def test_anchor_index_incremental_restore_preserves_first_fact_and_partial_line(
    tmp_path, monkeypatch
):
    import json
    from src.engine.scalping import reversal_path_runtime as R
    from src.engine.scalping import reversal_anchor_index as I
    from src.engine.scalping import continuous_reversal_source as source

    day = "2026-10-13"
    path = tmp_path / "raw.jsonl"

    def raw(i, p=10000):
        return dict(
            schema="scalp_micro_reversion_market_stream_point_v3",
            symbol="123456",
            venue="SOR",
            session_bucket="KRX_REGULAR",
            source_item="123456_AL",
            trade_price=p,
            local_receive_timestamp=K.iso(T + i),
            exchange_timestamp=K.iso(T + i),
            sequence_epoch=99,
            series_sequence=i + 1,
            native_transport_epoch=7,
            native_route_sequence=i + 1,
            path_consumer_eligible=True,
            path_order_status="accept",
        )

    line = json.dumps(raw(0)) + "\n"
    path.write_text(line + json.dumps(raw(1))[:30])
    monkeypatch.setattr(
        source, "discover", lambda *a: [dict(files=[dict(path=str(path))])]
    )
    for field, value in [
        ("_RESTORED_DAYS", set()),
        ("_EMPTY_PREFIX_DAYS", set()),
        ("_ANCHORS", {}),
        ("_ANCHOR_CURSORS", {}),
        ("_ANCHOR_ROOTS", {}),
        ("_STATES", {}),
    ]:
        monkeypatch.setattr(R, field, value)
    assert R.restore_session_anchors(tmp_path, day)["status"] == "prefix_incomplete"
    key = ("123456", "SOR", "123456_AL", "REGULAR", day)
    assert R._ANCHORS[key] == [T, 7, 1, 10000]
    path.write_text(line + json.dumps(raw(1, 10500)) + "\n")
    assert R.restore_session_anchors(tmp_path, day)["status"] == "restored"
    monkeypatch.setattr(R, "_RESTORED_DAYS", set())
    monkeypatch.setattr(R, "_ANCHORS", {})
    assert R.restore_session_anchors(tmp_path, day)["bytes_read"] == 0
    assert R._ANCHORS[key][3] == 10000
    body = I.load(tmp_path, day)
    assert body[0][key][1] == 7
    saved = I.location(tmp_path, day)
    corrupt = json.loads(saved.read_text())
    corrupt["anchors"][0]["row"][3] = 99999
    saved.write_text(json.dumps(corrupt))
    with pytest.raises(ValueError, match="contract_invalid"):
        I.load(tmp_path, day)


def test_incomplete_restore_resumes_on_existing_preparation_cadence(
    tmp_path, monkeypatch
):
    import json
    from src.engine.scalping import reversal_path_runtime as R
    from src.engine.scalping import reversal_anchor_index as I
    from src.engine.scalping import continuous_reversal_source as source

    p = tmp_path / "raw.jsonl"
    day = "2026-10-13"
    rows = [
        dict(
            schema="scalp_micro_reversion_market_stream_point_v3",
            symbol=f"{i:06d}",
            venue="SOR",
            session_bucket="KRX_REGULAR",
            source_item=f"{i:06d}_AL",
            trade_price=10000,
            local_receive_timestamp=K.iso(T + i),
            exchange_timestamp=K.iso(T + i),
            sequence_epoch=1,
            series_sequence=i + 1,
            path_consumer_eligible=True,
            path_order_status="accept",
        )
        for i in range(10)
    ]
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    monkeypatch.setattr(
        source, "discover", lambda *a: [dict(files=[dict(path=str(p))])]
    )
    monkeypatch.setattr(I, "LIMIT", 2048)
    for field, value in [
        ("_RESTORED_DAYS", set()),
        ("_EMPTY_PREFIX_DAYS", set()),
        ("_ANCHORS", {}),
        ("_ANCHOR_CURSORS", {}),
        ("_ANCHOR_ROOTS", {}),
        ("_STATES", {}),
        ("_FAMILY", {}),
    ]:
        monkeypatch.setattr(R, field, value)
    assert (
        R.restore_session_anchors(tmp_path, day, max_bytes=500)["status"]
        == "prefix_incomplete"
    )
    monkeypatch.setattr(I, "LIMIT", 16 * 1024 * 1024)
    assert R.prepare_anchor_source_step(tmp_path, day)["status"] == "restored"
    assert len(R._ANCHORS) == 10


def test_union_state_receives_late_restored_anchor_without_replaying_old_confirmations(
    monkeypatch, joint_frozen_source
):
    from src.engine.scalping import reversal_extended_runtime as E
    from src.engine.scalping import reversal_path_runtime as R
    from pathlib import Path
    import json

    f = joint_frozen_source["parent"]["continuous_reversal"]
    monkeypatch.setattr(E, "_FAMILY", f)
    monkeypatch.setattr(E, "_STATES", {})
    monkeypatch.setattr(E, "observe_native", lambda *a: None)
    monkeypatch.setattr(R, "_ANCHORS", {})

    def envelope(seq, price):
        return dict(
            observed_epoch=T + seq,
            provider_trade_epoch=T + seq,
            trade_price=price,
            transport_epoch=1,
            route_sequence=seq,
            inline_best_bid=price,
            inline_best_ask=price + 1,
            trade_qty=10,
            aggressor_side="BUY",
            item="123456_AL",
            market_route="krx_nxt_integrated",
        )

    E.observe_normalized("123456", "KRX_REGULAR", envelope(1, 10000))
    stream = ("123456", "SOR", "123456_AL", "REGULAR", "2026-10-13")
    state = E._STATES[stream + ("other_non_fixed|REGULAR|LT_20000",)]
    assert state.session_anchor is None
    R._ANCHORS[stream] = [T - 1, 1, 1, 9990]
    E.observe_normalized("123456", "KRX_REGULAR", envelope(2, 10010))
    assert (
        state.session_anchor[3] == 9990
        and state.features(state.legacy.last)["session"] is not None
    )


def test_identifiable_lost_first_fact_is_not_replaced_by_a_later_price(
    tmp_path, monkeypatch
):
    import json
    from src.engine.scalping import reversal_path_runtime as R
    from src.engine.scalping import continuous_reversal_source as source
    from src.engine.scalping import reversal_anchor_index as I

    p = tmp_path / "raw.jsonl"
    day = "2026-10-13"
    first = dict(
        schema="scalp_micro_reversion_market_stream_point_v3",
        symbol="123456",
        venue="SOR",
        session_bucket="KRX_REGULAR",
        source_item="123456_AL",
        trade_price=None,
        local_receive_timestamp=K.iso(T),
        exchange_timestamp=K.iso(T),
        sequence_epoch=1,
        series_sequence=1,
        path_consumer_eligible=True,
        path_order_status="accept",
    )
    later = dict(
        first,
        trade_price=10100,
        local_receive_timestamp=K.iso(T + 1),
        exchange_timestamp=K.iso(T + 1),
        series_sequence=2,
    )
    p.write_text(json.dumps(first) + "\n" + json.dumps(later) + "\n")
    monkeypatch.setattr(
        source, "discover", lambda *a: [dict(files=[dict(path=str(p))])]
    )
    for field, value in [
        ("_RESTORED_DAYS", set()),
        ("_EMPTY_PREFIX_DAYS", set()),
        ("_ANCHORS", {}),
        ("_ANCHOR_CURSORS", {}),
        ("_ANCHOR_ROOTS", {}),
        ("_STATES", {}),
        ("_ANCHOR_GAPS", set()),
    ]:
        monkeypatch.setattr(R, field, value)
    assert R.restore_session_anchors(tmp_path, day)["status"] == "restored"
    key = ("123456", "SOR", "123456_AL", "REGULAR", day)
    assert key in R._ANCHOR_GAPS and key not in R._ANCHORS
    assert key in I.load(tmp_path, day)[2]


@pytest.mark.parametrize(
    "receipt,expected",
    [
        ({"native_source_current": False}, "source_unavailable"),
        ({"selected_pending_count": 1}, "observation_incomplete"),
        ({"selected_branch_truth": {"a": "FALSE"}}, "observation_incomplete"),
        (
            {
                "selected_branch_truth": {"a": "FALSE"},
                "selected_lifecycle_counts": {"a": {"FALSE": 10}},
            },
            "pattern_not_matched",
        ),
        (
            {
                "selected_branch_truth": {"a": "FALSE"},
                "selected_lifecycle_counts": {"a": {"TRUE": 1, "FALSE": 10}},
            },
            "observation_incomplete",
        ),
        (
            {"selected_branch_truth": {"a": "FALSE"}, "source_censored_count": 1},
            "source_unavailable",
        ),
    ],
)
def test_native_terminal_distinguishes_lifecycle_from_last_false(receipt, expected):
    from src.engine.scalping.zero_base_probe import native_wait_result

    assert native_wait_result(receipt, {})[0] == expected


@pytest.mark.parametrize("gap", ["epoch", "sequence", "clock"])
def test_fresh_disconnected_print_cannot_become_complete_no_match(gap):
    from src.engine.scalping.zero_base_probe import native_wait_result

    bid = "legacy_dd5_ge_0_4_v1"
    state = S.State(branch_ids=[bid], offline=True, session_anchor=row(0))
    feed(state, [row(0), row(1)])
    assert state.coverage_source_censored == 0
    following = [row(2), row(3)]
    if gap == "epoch":
        for value in following:
            value[1] = 2
    elif gap == "sequence":
        for value in following:
            value[2] += 1
    else:
        for value in following:
            value[0] -= 2
    feed(state, following)
    assert state.coverage_source_censored == 1
    receipt = dict(
        native_source_current=True,
        selected_branch_truth=dict(state.coverage_snapshot),
        selected_lifecycle_counts=state.coverage_counts,
        source_censored_count=state.coverage_source_censored,
    )
    assert native_wait_result(receipt, {})[0] == "observation_incomplete"


def test_partial_source_wait_uses_original_residence_and_event_wakeup(monkeypatch):
    from src.engine.scalping import zero_base_probe as Z
    from src.engine.scalping import reversal_source_diagnostics as D

    clock = [100.0]
    waits = []
    monkeypatch.setattr(Z.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        Z.time, "sleep", lambda sec: clock.__setitem__(0, clock[0] + sec)
    )
    monkeypatch.setattr(D, "observation_sequence", lambda item: 0)

    def wait(item, seq, sec):
        waits.append(sec)
        clock[0] += sec

    monkeypatch.setattr(D, "wait_observation", wait)
    monkeypatch.setattr(
        Z, "probe_ws_snapshot", lambda *a, **kw: {"market_data_transport_epoch": 3}
    )
    monkeypatch.setattr(
        Z, "exact_probe_ws_data", lambda *a, **kw: ({"curr": 10000}, "ready")
    )
    monkeypatch.setattr(
        Z,
        "probe_ws_observation",
        lambda *a, **kw: dict(
            exact_0b_count=5 if clock[0] >= 121 else 3,
            exact_0d_count=6,
            latest_0b_ms=1,
            latest_0d_ms=1,
            first_0b_ms=0,
        ),
    )
    data, obs, _ = Z.wait_for_exact_probe_ws_data(
        SimpleNamespace(_market_data_transport_epoch=3),
        code="123456",
        route="krx_nxt_integrated",
        after_epoch=100,
        now=lambda: clock[0],
        timeout_sec=15,
        empty_timeout_sec=10,
        min_exact_0b_count=5,
        residence_deadline_epoch=250,
        required_window_sec=120,
    )
    assert data and obs["residence_wait_applied"] and 21 <= clock[0] - 100 < 23
    assert waits and max(waits) <= 1 and obs["effective_wait_budget_ms"] == 150000


def test_approved_selector_uses_own_whole_opportunity_denominator_and_carries_incomplete():
    from src.engine.scalping import reversal_joint_registration as R

    sid = "036930|AFTER|GE_100000|SOR"
    old = ["legacy_dd5_ge_0_4_v1", "manual_extended_27bebc59a6315682"]
    groups = R.variant_groups(
        {
            "continuous_reversal": {
                "operating_manifest": {
                    "scopes": {
                        sid: old,
                        "other_non_fixed|PRE|LT_20000|NXT": [
                            "legacy_dd5_0_8_vol_up_v1",
                            "manual_extended_f74502b35a4fae1f",
                            "manual_residual_29b499784843baed",
                            "manual_residual_bac0e83e966ed3ea",
                        ],
                    }
                }
            }
        }
    )
    current = groups[sid]["alternatives"]["JOINT_BALANCED"]

    def metric(w, f):
        return dict(
            counts={"WIN": w, "FAIL_STOP": f},
            source_complete=True,
            comparison_complete=True,
            source_universe_sha256="a" * 64,
        )

    metrics = {
        "CURRENT_NATIVE": metric(7, 3),
        "PREVIOUS_BASELINE": metric(6, 4),
        "ADD_A_ONLY": metric(80, 20),
        "REPLACE_F_ONLY": metric(8, 2),
    }
    result = R.select_variant(
        groups, sid, current, metrics, authority=R.SELECTION_AUTHORITY
    )
    assert (
        result["variant"] == "ADD_A_ONLY"
        and result["branch_ids"] == groups[sid]["alternatives"]["ADD_A_ONLY"]
    )
    metrics["CURRENT_NATIVE"]["source_complete"] = False
    assert (
        R.select_variant(
            groups, sid, current, metrics, authority=R.SELECTION_AUTHORITY
        )["branch_ids"]
        == current
    )


def test_registration_exact_delta_native_publisher_and_dated_handoff(
    tmp_path, monkeypatch, joint_frozen_source
):
    import json
    from pathlib import Path
    from src.engine.scalping import reversal_joint_registration as R
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import continuous_reversal_policy as dispatch
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_auxiliary_registry as G
    from src.engine.scalping import reversal_auxiliary_intraday as I

    original_root = N.root(joint_frozen_source["data"])
    parent = joint_frozen_source["parent"]
    evidence = joint_frozen_source["evidence"]
    frozen = tmp_path / "evidence.json"
    frozen.write_bytes(evidence.read_bytes())
    result_source = tmp_path / "frontier.json"
    result_source.write_bytes(
        (evidence.parent / "opportunity-frontier-result.json").read_bytes()
    )
    request = P.seal(
        dict(
            schema=R.SCHEMA,
            kind="REPLACE",
            operator_receipt=R.AUTHORITY,
            parent_bundle_sha256=J.PARENT,
            research_batch_sha256=J.RESEARCH_RESULT,
            registry_sha256=C.JOINT_SHA256,
            scopes=J.changes(),
            definition_hashes={b: P.digest(d) for b, d in J.DEFINITIONS.items()},
            variant_groups=R.variant_groups(parent),
            selection_authority=R.SELECTION_AUTHORITY,
            comparison_result_required=False,
            source_receipts=[
                dict(path=str(p), sha256=P.file_hash(p))
                for p in (frozen, result_source)
            ],
            publication_date="2026-10-13",
            target_date="2026-10-14",
        )
    )
    R.validate_request(request)
    manifest = V.detector_manifest(parent, effective_date="2026-10-14", changes=request)
    before = parent["continuous_reversal"]["operating_manifest"]["scopes"]
    assert {s for s in before if before[s] != manifest["scopes"][s]} == set(J.changes())
    assert [len(manifest["scopes"][s]) for s in J.changes()] == [3, 5]
    # Real registry/projection writes use the fixture root only. Provider/store
    # comparison is forbidden by this initial registration contract.
    bindings = {}
    for key, route in V.scopes():
        arm = parent["continuous_reversal"]["auxiliary_cells"][key]["routes"][route][
            "payload"
        ]["arm"]
        bindings[V.scope_id(key, route)] = G.register(
            tmp_path, G.definition(arm, input_version=V.A.VERSION)
        )
    monkeypatch.setattr(I, "effective_bindings", lambda *a, **kw: bindings)
    monkeypatch.setattr(I, "current", lambda *a, **kw: None)
    monkeypatch.setattr(I, "lineage_sources", lambda *a: [])
    code = {
        Path(m.__file__).name: P.file_hash(m.__file__) for m in V.contract_modules()
    }
    machine = P.seal(
        dict(
            schema="fixture",
            source_date="2026-10-13",
            target_date="2026-10-13",
            publication_date="2026-10-13",
            parent_bundle_sha256=J.PARENT,
            registration_change=request,
            operating_manifest=manifest,
            execution_code_sha256=P.digest(code),
            source_receipts=[],
            source_manifest_sha256=parent["continuous_reversal"][
                "source_manifest_sha256"
            ],
        )
    )
    out = tmp_path / "typed"
    aux = R.initial_reports(
        tmp_path,
        "2026-10-13",
        "2026-10-13",
        parent,
        machine,
        output_directory=out,
        publish_policy=False,
    )
    issued = json.loads((out / "machine.json").read_text())
    assert aux["actual_provider_calls"] == 0 and aux["comparison_complete"] is False
    assert aux["scope_census"]["new_ready"] == 128 and not aux["scope_pending"]
    root = N.root(tmp_path)
    root.mkdir(parents=True, exist_ok=True)
    native = parent["continuous_reversal"]["native_parent_bundle"]
    for name in ("machine", "auxiliary"):
        filename = (
            "reversal-"
            + native["continuous_reversal"][name + "_report_sha256"]
            + ".json"
        )
        dest = root / "sources" / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((original_root / "sources" / filename).read_bytes())
    monkeypatch.setattr(N, "load_effective", lambda **kw: parent)
    # Old immutable source validation belongs to intake's attested origin.
    # This test exercises new native serialization, family validation and reader.
    monkeypatch.setattr(
        N,
        "_validate_bundle_sources",
        lambda b, r: (
            V.validate_family(b["continuous_reversal"])
            if b["continuous_reversal"]["schema"] == V.SCHEMA
            else V.V4.validate_family(b["continuous_reversal"])
        ),
    )
    bundle = V.stage(
        tmp_path,
        "2026-10-13",
        "2026-10-13",
        issued,
        aux,
        target_date="2026-10-14",
        release_commit="a" * 40,
    )
    V.validate_family(bundle["continuous_reversal"])
    N.validate(bundle, target_date="2026-10-14")
    assert bundle["continuous_reversal"]["contract_file_sha256"] == code
    assert (
        bundle["continuous_reversal"]["native_parent_bundle"]["bundle_sha256"]
        != native["bundle_sha256"]
    )
    assert parent["bundle_sha256"] == J.PARENT  # Frozen predecessor not relabelled.
    monkeypatch.setattr(N, "load", lambda **kw: bundle)
    handoff = dispatch.direct_handoff(tmp_path, "2026-10-13")
    assert (
        handoff["scope_census"]["new_ready"] == 128
        and not handoff["current_pid_consumption_claimed"]
    )

    # A later approved whole-variant selection must reach auxiliary preparation.
    # Keep the actual native family validator and selector; no provider calls.
    from src.engine.scalping import reversal_auxiliary_tuning as tuning
    from src.engine.ai import offline_comparison_store as store_module
    from src.tests.test_offline_comparison_store import activate

    future_manifest = V.detector_manifest(bundle, effective_date="2026-10-15")
    groups = future_manifest["approved_variant_groups"]
    metrics = {}
    for scope, group in groups.items():
        for variant in (*group["alternatives"], "CURRENT_NATIVE"):
            metrics[scope + "::" + variant] = {
                "counts": {
                    "WIN": 80 if variant == "ADD_A_ONLY" else 7,
                    "FAIL_STOP": 20 if variant == "ADD_A_ONLY" else 3,
                }
            }
    next_machine = P.seal(
        dict(
            schema="fixture",
            source_date="2026-10-14",
            publication_date="2026-10-14",
            status="completed",
            policy_schema=V.SCHEMA,
            parent_bundle_sha256=bundle["bundle_sha256"],
            operating_manifest=future_manifest,
            cells=copy.deepcopy(
                list(bundle["continuous_reversal"]["machine_cells"].values())
            ),
            execution_code_sha256=P.digest(code),
            label_contract=C.LABEL,
            source_manifest_sha256=issued["source_manifest_sha256"],
            source_manifest_receipt={
                "path": str(frozen),
                "sha256": P.file_hash(frozen),
            },
            proposal_metrics=metrics,
            partitions=[],
            quarantined_conflicts=[],
            registration_change=None,
        )
    )
    selected = R.apply_selection(next_machine, bundle)
    assert (
        selected["operating_manifest"]["scopes"]
        != bundle["continuous_reversal"]["operating_manifest"]["scopes"]
    )
    candidate = G.register(
        tmp_path, G.definition(V.A.V1.ARMS[0], input_version=V.A.VERSION)
    )
    tuning.configure(
        tmp_path,
        candidate=candidate,
        scopes=list(groups),
        seed="approved-variant-test",
        max_pairs=2,
    )
    with store_module.Store(tmp_path) as store:
        activate(store)
    before = copy.deepcopy((bundle, selected))
    campaign = tuning.prepare(tmp_path, "2026-10-14", selected, bundle)
    assert campaign["machine_report_sha256"] == selected["artifact_content_sha256"]
    assert (bundle, selected) == before
    for defect in (
        "parent",
        "receipt",
        "definitions",
        "nongroup",
        "cells",
        "metrics",
        "authority",
        "source",
    ):
        damaged = copy.deepcopy(selected)
        sid = next(iter(groups))
        if defect == "parent":
            damaged["parent_bundle_sha256"] = "b" * 64
        elif defect == "receipt":
            damaged["operating_manifest"].pop("variant_selection_receipt")
        elif defect == "definitions":
            damaged["operating_manifest"]["definitions"] = {}
        elif defect == "nongroup":
            other = next(
                s for s in damaged["operating_manifest"]["scopes"] if s not in groups
            )
            damaged["operating_manifest"]["scopes"][other] = ["unapproved_detector"]
        elif defect == "cells":
            damaged["cells"] = []
        elif defect == "metrics":
            damaged["proposal_metrics"][sid + "::ADD_A_ONLY"] = {
                "counts": {"WIN": 0, "FAIL_STOP": 100}
            }
        elif defect == "authority":
            damaged["operating_manifest"]["selection_authority"] = "unapproved"
        else:
            damaged["source_manifest_receipt"] = None
        with pytest.raises(
            ValueError, match="auxiliary_tuning_machine_membership_changed"
        ):
            tuning.prepare(tmp_path, "2026-10-14", P.seal(damaged), bundle)
    assert tuning.prepare(tmp_path, "2026-10-14", selected, bundle) == campaign
    with store_module.Store(tmp_path) as store:
        assert store.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0

    bad = copy.deepcopy(bundle["continuous_reversal"])
    sid = next(iter(J.changes()))
    bad["operating_manifest"]["scopes"][sid] = [J.ALIASES["jusung_after_breakout"]]
    bad["family_sha256"] = P.digest(
        {k: v for k, v in bad.items() if k != "family_sha256"}
    )
    with pytest.raises(ValueError):
        V.validate_family(bad)

    # Tomorrow's actual activation must dispatch the joint receipt validator,
    # even when today's unchanged parent still has the previous code hashes.
    from src.engine.infrastructure import runtime_release_router as router

    request["activation_parent_origin"] = dict(
        root=str(tmp_path / "old"), commit="b" * 40
    )
    request = P.seal(request)
    bf = copy.deepcopy(bundle["continuous_reversal"])
    bf["registration_code_transition"] = request
    bf["operating_manifest"]["change_receipt"] = request
    bf["family_sha256"] = P.digest(
        {k: v for k, v in bf.items() if k != "family_sha256"}
    )
    activated = copy.deepcopy(bundle)
    activated["continuous_reversal"] = bf
    activated["bundle_sha256"] = N.digest(
        {k: v for k, v in activated.items() if k != "bundle_sha256"}
    )
    N._atomic_write_json(root / "candidates/policy_2026-10-14.json", activated)
    monkeypatch.setattr(N, "validate", lambda *a, **kw: None)
    monkeypatch.setattr(V, "validate_sources", lambda *a, **kw: None)
    calls = []

    def current(**kwargs):
        calls.append(True)
        if len(calls) == 1:
            raise ValueError("v4_contract_code_changed:reversal_path_runtime.py")
        return activated

    monkeypatch.setattr(N, "load_effective", current)
    monkeypatch.setattr(V, "_attested_activation_parent", lambda *a, **kw: parent)
    monkeypatch.setattr(
        router, "selected_release", lambda *a: (tmp_path / "new", "a" * 40)
    )
    receipt = V.activate(
        tmp_path, "2026-10-14", now=datetime(2026, 10, 14, 7, 35, tzinfo=K.KST)
    )
    assert (
        receipt["status"] == "activated"
        and receipt["previous_bundle_sha256"] == J.PARENT
    )


@pytest.mark.parametrize(
    "predecessor_review,damage",
    [
        (review, damage)
        for review in (False, True, "closed", "prepared", "cold")
        for damage in (
            None,
            "code",
            "source",
            "pointer",
            "date",
            "authority",
            "members",
            "seal",
            "selector",
            "absent",
        )
    ]
    + [
        (review, damage)
        for review in (True, "closed", "prepared")
        for damage in (
            "review_missing",
            "review_day",
            "review_origin",
            "review_pid",
            "review_race",
            "review_consumed",
        )
    ],
)
def test_active_code_handoff_is_exact_and_never_reselects_policy(
    tmp_path, monkeypatch, damage, predecessor_review, missing_origin=False,
    activation_rollover=False,
):
    from pathlib import Path
    from src.engine.scalping import (
        reversal_code_handoff as H,
        continuous_reversal_policy_v6 as V,
    )
    from src.engine.scalping import (
        mechanistic_entry_runtime_policy as N,
        continuous_reversal_postclose as P,
    )
    from src.engine.infrastructure import runtime_release_router as router

    root = tmp_path / "release"
    data = tmp_path / "data"
    day = datetime.now(P.KST).date().isoformat()
    commit = "b" * 40
    code = root / "src/engine/scalping/reversal_code_handoff.py"
    code.parent.mkdir(parents=True)
    code.write_text("reviewed code")
    old = data / "source.json"
    old.parent.mkdir()
    old.write_text("frozen source")
    pointer = N.root(data) / "current.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text('{"bundle_sha256":"bundle"}')
    selector = data / "runtime/runtime_release_selection.json"
    selector.write_text(
        __import__("json").dumps(dict(git_commit=commit, release_root=str(root)))
    )
    monkeypatch.setattr(H, "__file__", str(code))
    monkeypatch.setattr(
        V, "contract_modules", lambda: [SimpleNamespace(__file__=str(code))]
    )
    monkeypatch.setattr(router, "selected_release", lambda *a: (root, commit))
    receipt = P.seal(
        dict(
            schema=H.SCHEMA,
            authority=H.AUTHORITY,
            target_date=day,
            release_root=str(root),
            release_commit=commit,
            bundle_sha256="bundle",
            current_pointer_sha256=P.file_hash(pointer),
            code_hashes={str(code): P.file_hash(code)},
            source_hashes={str(old): P.file_hash(old)},
            policy_reselected=False,
            provider_called=False,
        )
    )
    if damage == "date":
        receipt["target_date"] = "2026-10-01"
    if damage == "authority":
        receipt["authority"] = "unapproved"
    if damage == "members":
        receipt["code_hashes"] = {str(old): P.file_hash(old)}
    receipt = P.seal(receipt)
    receipt_day = day
    if activation_rollover:
        from datetime import date, timedelta

        receipt_day = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
        source = (date.fromisoformat(day) - timedelta(days=3)).isoformat()
        pointer.write_text(__import__("json").dumps(dict(bundle_sha256="bundle", effective_date=source)))
        selected = dict(
            git_commit=commit, release_root=str(root), approved_by="user",
            approval_scope="after_postclose_deploy_for_next_regular_start",
            actual_pid_consumed=False, main_start_authorized=False,
            source_date=source, next_operating_date=day,
            selected_at_kst=receipt_day + "T14:55:33+09:00",
        )
        selector.write_text(__import__("json").dumps(selected))
        receipt.update(target_date=receipt_day, activation_date=day,
                       source_trading_date=source,
                       parent_effective_date=source,
                       current_pointer_sha256=P.file_hash(pointer),
                       issued_at_kst=receipt_day + "T14:54:00+09:00")
        if activation_rollover == "active":
            selected.update(approval_scope="ordered_intraday_deploy_and_restart", actual_pid_consumed=True)
            selector.write_text(__import__("json").dumps(selected))
            receipt.update(activation_date=receipt_day, next_activation_date=day)
            source = (date.fromisoformat(source) - timedelta(days=1)).isoformat()
            receipt["source_trading_date"] = source
        if damage == "activation_date":
            receipt["activation_date"] = receipt_day
            receipt["next_activation_date"] = receipt_day
        elif damage == "activation_source":
            receipt["source_trading_date"] = receipt_day
        elif damage == "parent_effective":
            receipt["parent_effective_date"] = receipt_day
        elif damage == "legacy_activation":
            receipt.pop("activation_date")
            receipt.pop("next_activation_date", None)
        elif damage == "activation_consumed":
            selected["actual_pid_consumed"] = True
            selector.write_text(__import__("json").dumps(selected))
        receipt = P.seal(receipt)
    if predecessor_review:
        from src.engine.automation import intraday_release_handoff as IH

        selected = tmp_path / "incumbent"
        selected.mkdir()
        old_commit = "a" * 40
        selector.write_text(
            __import__("json").dumps(
                dict(
                    git_commit=old_commit,
                    release_root=str(selected),
                    **(
                        dict(
                            main_start_authorized=False,
                            approval_scope="after_postclose_deploy_for_next_regular_start",
                            next_operating_date="2026-10-26",
                        )
                        if predecessor_review == "cold"
                        else {}
                    ),
                )
            )
        )
        identity = dict(pid=123, start_ticks="456", cwd=str(selected / "src"))
        monkeypatch.setattr(
            router, "selected_release", lambda *a: (selected, old_commit)
        )
        monkeypatch.setattr(IH, "_identity", lambda pid: identity)
        context = IH._PREDECESSOR_REVIEW.set(
            dict(
                day=day,
                root=selected,
                commit=old_commit,
                code_root=root,
                code_commit=commit,
                identity=identity,
            )
        )
        if predecessor_review == "closed":
            closed = dict(
                schema="intraday_closed_consumption_observation_v1",
                pid_identity=identity,
            )
            IH._PREDECESSOR_REVIEW.get()["closed_observation"] = closed
            calls = []

            def closed_observation(day):
                calls.append(day)
                return (
                    {}
                    if damage == "review_pid"
                    or damage == "review_race"
                    and len(calls) > 1
                    else closed
                )

            monkeypatch.setattr(
                IH, "closed_consumption_observation", closed_observation
            )
            monkeypatch.setattr(
                IH,
                "_identity",
                lambda pid: (_ for _ in ()).throw(
                    AssertionError("closed origin is not live")
                ),
            )
        if predecessor_review in {"prepared", "cold"}:
            IH._PREDECESSOR_REVIEW.get()["identity"] = dict(
                identity, cwd=str(tmp_path / "previously-consumed/src")
            )
            observation = dict(
                target_date=day,
                release_commit=old_commit,
                runtime_effect=False,
                actual_pid_consumed=False,
                allowed_runtime_apply=False,
                source_hashes={str(old): P.file_hash(old)},
            )
            IH._PREDECESSOR_REVIEW.get()[
                (
                    "postclose_observation"
                    if predecessor_review == "cold"
                    else "prepared_observation"
                )
            ] = observation
            if predecessor_review == "cold":
                monkeypatch.setattr(IH, "DATA_DIR", data)
            monkeypatch.setattr(
                IH,
                "_identity",
                lambda pid: (_ for _ in ()).throw(
                    AssertionError("prepared origin has no live PID")
                ),
            )
            if damage == "review_pid":
                observation["actual_pid_consumed"] = True
            if damage == "review_race":
                visits = []
                original_sha = IH._sha

                def changed(path):
                    visits.append(path)
                    return original_sha(path) if len(visits) == 1 else "changed"

                monkeypatch.setattr(IH, "_sha", changed)
        if damage == "review_missing":
            IH._PREDECESSOR_REVIEW.set(None)
        if damage == "review_day":
            IH._PREDECESSOR_REVIEW.get()["day"] = "2026-10-01"
        if predecessor_review not in {"closed", "prepared"} and damage in (
            "review_pid",
            "review_race",
        ):
            visits = []

            def observed(pid):
                visits.append(pid)
                return (
                    dict(identity, start_ticks="changed")
                    if damage == "review_pid" or len(visits) > 1
                    else identity
                )

            monkeypatch.setattr(IH, "_identity", observed)
        # Scope ends even when the native source validation raises.
        import contextlib

        stack = contextlib.ExitStack()
        stack.callback(IH._PREDECESSOR_REVIEW.reset, context)
        if predecessor_review == "cold":
            cold_review = IH._PREDECESSOR_REVIEW.get()
            IH._PREDECESSOR_REVIEW.set(None)

            @contextlib.contextmanager
            def native_cold_review(target):
                assert target == "2026-10-26"
                token = IH._PREDECESSOR_REVIEW.set(cold_review)
                try:
                    yield cold_review["postclose_observation"]
                finally:
                    IH._PREDECESSOR_REVIEW.reset(token)

            monkeypatch.setattr(IH, "stopped_postclose_review", native_cold_review)
        receipt = P.seal(
            dict(
                receipt,
                origin_root=str(selected),
                origin_commit=old_commit,
                origin_selection_sha256=P.file_hash(selector),
                actual_pid_consumed=False,
            )
        )
        if not missing_origin:
            N._atomic_write_json(
                H.path(data, day, old_commit, "bundle"),
                P.seal(
                    dict(receipt, release_root=str(selected), release_commit=old_commit)
                ),
            )
        if damage == "review_origin":
            receipt = P.seal(dict(receipt, origin_commit="c" * 40))
        if damage == "review_consumed":
            receipt = P.seal(dict(receipt, actual_pid_consumed=True))
    if damage == "seal":
        receipt["policy_reselected"] = True
    dest = H.path(data, receipt_day, commit, "bundle")
    N._atomic_write_json(dest, receipt)
    if damage == "code":
        code.write_text("unreviewed code")
    if damage == "source":
        old.write_text("changed source")
    if damage == "pointer":
        pointer.write_text('{"bundle_sha256":"other"}')
    if damage == "selector":
        selector.write_text("{}")
    if damage == "absent":
        dest.unlink()
    frozen = {p: p.read_bytes() for p in (code, old, pointer, selector)}
    bundle = {"bundle_sha256": "bundle", **({"source_date": source} if activation_rollover else {})}
    try:
        if damage:
            with pytest.raises(ValueError):
                H.validate(
                    bundle,
                    data,
                    original_error=ValueError("v4_contract_code_changed:test"),
                )
        else:
            assert (
                H.validate(
                    bundle,
                    data,
                    original_error=ValueError("v4_contract_code_changed:test"),
                )
                is bundle
            )
    finally:
        if predecessor_review:
            stack.close()
    assert frozen == {p: p.read_bytes() for p in frozen}


@pytest.mark.parametrize("damage", [None, "activation_date", "activation_source", "parent_effective",
    "legacy_activation", "activation_consumed", "source", "code", "pointer",
    "selector", "seal", "members", "absent"])
def test_activation_uses_declared_date_instead_of_receipt_issue_date(
    tmp_path, monkeypatch, damage
):
    test_active_code_handoff_is_exact_and_never_reselects_policy(
        tmp_path, monkeypatch, damage, False, activation_rollover=True
    )


@pytest.mark.parametrize("damage", [None, "activation_date", "activation_source", "parent_effective",
    "legacy_activation", "source", "code", "pointer", "selector", "seal", "absent"])
def test_consumed_code_handoff_declares_the_next_parent_activation(tmp_path, monkeypatch, damage):
    test_active_code_handoff_is_exact_and_never_reselects_policy(
        tmp_path, monkeypatch, damage, False, activation_rollover="active"
    )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "review_missing",
        "review_day",
        "review_origin",
        "review_pid",
        "review_race",
        "review_consumed",
        "absent",
        "source",
    ],
)
def test_midnight_prepared_review_uses_own_receipt_without_origin_day_receipt(
    tmp_path, monkeypatch, damage
):
    test_active_code_handoff_is_exact_and_never_reselects_policy(
        tmp_path, monkeypatch, damage, "prepared", missing_origin=True
    )


@pytest.mark.parametrize("postclose", [False, True])
@pytest.mark.parametrize(
    "damage", [None, "selection_changed", "observed_selection_changed"]
)
def test_second_code_handoff_preserves_selector_provenance_without_freezing_transition(
    tmp_path,
    monkeypatch,
    damage,
    postclose,
    cold_activation=False,
    coordination=False,
    closed_parent=False,
):
    import json
    from pathlib import Path
    from src.engine.scalping import (
        reversal_code_handoff as H,
        continuous_reversal_policy_v6 as V,
    )
    from src.engine.scalping import (
        mechanistic_entry_runtime_policy as N,
        continuous_reversal_postclose as P,
    )
    from src.engine.infrastructure import runtime_release_router as router

    data = tmp_path / "data"
    origin = tmp_path / "old"
    root = tmp_path / "new"
    root.mkdir()
    origin.mkdir()
    day = datetime.now(P.KST).date().isoformat()
    if cold_activation:

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 10, 25, 14, 54, tzinfo=P.KST)

        monkeypatch.setattr(H, "datetime", Clock)
        day = "2026-10-25"
    commit = "b" * 40
    code = root / "src/engine/scalping/reversal_code_handoff.py"
    code.parent.mkdir(parents=True)
    code.write_text("reviewed")
    pointer = N.root(data) / "current.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text('{"bundle_sha256":"bundle"}')
    bundle = {
        "bundle_sha256": "bundle",
        "target_date": day,
        "continuous_reversal": {"operating_manifest": {"definitions": {}}},
    }
    N._atomic_write_json(N.root(data) / "generations/bundle.json", bundle)
    selector = data / "runtime/runtime_release_selection.json"
    selector.write_text(json.dumps(dict(git_commit="a" * 40, release_root=str(origin))))
    if cold_activation:
        selector.write_text(
            json.dumps(
                dict(
                    git_commit="a" * 40,
                    release_root=str(origin),
                    approved_by="user",
                    approval_scope="after_postclose_deploy_for_next_regular_start",
                    actual_pid_consumed=False,
                    source_date="2026-10-23",
                    next_operating_date="2026-10-26",
                )
            )
        )
    source = data / "policy.json"
    source.write_text("frozen policy")
    initial_sha = P.file_hash(selector)
    parity = tmp_path / "parity.json"
    parity.write_text(
        json.dumps(
            dict(
                status="pass",
                mismatches=0,
                parent_bundle_sha256="bundle",
                contract_file_sha256={code.name: P.file_hash(code)},
                confirmation_parity={"hits": 1},
            )
        )
    )
    monkeypatch.setattr(H, "__file__", str(code))
    monkeypatch.setattr(H, "code_hashes", lambda: {str(code): P.file_hash(code)})
    monkeypatch.setattr(
        V, "contract_modules", lambda: [SimpleNamespace(__file__=str(code))]
    )
    monkeypatch.setattr(N, "validate", lambda *a, **kw: None)
    selected = [origin, "a" * 40]
    monkeypatch.setattr(router, "selected_release", lambda *a: tuple(selected))
    monkeypatch.setattr(router, "validate_release", lambda *a: None)
    monkeypatch.setattr(router, "git", lambda *a: commit)
    if closed_parent:
        from datetime import timedelta
        from src.engine.automation import intraday_release_handoff as I
        from src.engine.automation import ordered_intraday_deploy as D
        from src.engine.automation import next_preopen_readiness as R

        source_day = (
            datetime.fromisoformat(day).date() - timedelta(days=1)
        ).isoformat()
        bundle["target_date"] = source_day
        bundle["source_date"] = (
            datetime.fromisoformat(source_day).date() - timedelta(days=1)
        ).isoformat()
        N._atomic_write_json(N.root(data) / "generations/bundle.json", bundle)
        pointer.write_text(
            json.dumps(dict(bundle_sha256="bundle", effective_date=source_day))
        )
        selection = json.loads(selector.read_bytes())
        selection.update(
            approved_by="user",
            approval_scope="ordered_intraday_deploy_and_restart",
            actual_pid_consumed=True,
            main_start_authorized=False,
        )
        selector.write_text(json.dumps(selection))
        initial_sha = P.file_hash(selector)
        closed = dict(
            schema="intraday_closed_consumption_observation_v1",
            target_date="wrong" if damage == "closed_source" else source_day,
            release_commit="a" * 40,
            selection_sha256=initial_sha,
            runtime_effect=damage == "closed_flags",
            current_observation_verified=False,
            new_pid_consumption_claimed=False,
        )
        if damage == "closed_basis":
            closed["basis"] = "interrupted"
        visits = []

        def closure():
            visits.append(True)
            return {
                **closed,
                **(
                    {"terminal_at": "changed"}
                    if damage == "closed_changed" and len(visits) > 1
                    else {}
                ),
            }

        monkeypatch.setattr(I, "closed_consumption_observation", closure)
        monkeypatch.setattr(R, "target_after_postclose", lambda _: day)
        monkeypatch.setattr(
            D, "_main_pids", lambda: [123] if damage == "closed_live" else []
        )
        monkeypatch.setattr(D, "_session_absent", lambda: True)

        def original_receipt(_, receipt_day, *args):
            if receipt_day == day or damage == "closed_missing":
                return None
            assert receipt_day == source_day
            return dict(
                bundle_sha256="bundle", source_hashes={str(source): P.file_hash(source)}
            )

        monkeypatch.setattr(H, "_validated_origin_receipt", original_receipt)
        if damage == "closed_hold":
            (data / "runtime/operator_startup_hold.json").write_text("{}")
    control = data / "runtime/research_release_transition/current.json"
    if coordination:
        from src.engine.infrastructure.research_release_transition import Transition

        original_transition = Transition(tmp_path, "original")
        with original_transition.owner():
            pass
        original_control_sha = P.file_hash(control)
        if damage == "coordination_race":
            native_hash = P.file_hash

            def raced_hash(path):
                if Path(path) == parity:
                    with Transition(tmp_path, "racing").owner():
                        pass
                return native_hash(path)

            monkeypatch.setattr(P, "file_hash", raced_hash)

    def inspect(*args, **kwargs):
        assert (
            not closed_parent
        ), "closed native parent must not inspect future preparation"
        if damage == "selection_changed":
            selector.write_text("{}")
        observed = dict(
            bundle_sha256="bundle",
            source_hashes={
                str(source): P.file_hash(source),
                str(selector): (
                    "0" * 64 if damage == "observed_selection_changed" else initial_sha
                ),
            },
        )
        if coordination:
            observed["source_hashes"][str(control)] = (
                "0" * 64
                if damage == "observed_coordination_changed"
                else original_control_sha
            )
            if damage == "coordination_changed":
                with Transition(tmp_path, "changed").owner():
                    pass
            elif damage == "coordination_corrupt":
                control.write_text("{}")
            elif damage == "foreign_publishing":
                with Transition(tmp_path, "foreign").owner() as foreign:
                    foreign.value["state"] = "publishing"
                    foreign._save()
            elif damage == "coordination_symlink":
                control.unlink()
                control.symlink_to(original_transition.path)
        return json.dumps(observed)

    monkeypatch.setattr(H.subprocess, "check_output", inspect)
    options = {}
    if postclose:
        from datetime import timedelta

        source_day = (
            datetime.fromisoformat(day).date() - timedelta(days=1)
        ).isoformat()

        def postclose_origin(*args):
            assert args[2] == source_day
            result = json.loads(inspect())
            result["verification_basis"] = (
                "verified_previous_day_postclose_native_code_ancestry"
            )
            return result

        monkeypatch.setattr(H, "_postclose_origin_receipt", postclose_origin)
        options["postclose_source_date"] = source_day
    if damage:
        with pytest.raises(
            ValueError,
            match="parent_changed|selection_changed|coordination|transition|closed_parent",
        ):
            H.issue(
                data,
                day,
                origin_root=origin,
                release_root=root,
                parity_path=parity,
                confirm=H.AUTHORITY,
                **options,
            )
        assert not H.path(data, day, commit, "bundle").exists()
        return
    receipt = H.issue(
        data,
        day,
        origin_root=origin,
        release_root=root,
        parity_path=parity,
        confirm=H.AUTHORITY,
        **options,
    )
    assert (
        receipt["origin_selection_sha256"] == initial_sha
        and str(selector) not in receipt["source_hashes"]
    )
    assert receipt["source_hashes"][str(source)] == P.file_hash(source)
    if closed_parent:
        assert (
            receipt["origin_verification_basis"]
            == "verified_ordered_closed_native_parent"
        )
        assert receipt["source_trading_date"] == bundle["source_date"]
        assert receipt["origin_closed_observation"]["target_date"] == source_day
    assert receipt["activation_date"] == ("2026-10-26" if cold_activation else day)
    assert receipt["issued_at_kst"].startswith(day)
    if cold_activation:
        assert receipt["source_trading_date"] == "2026-10-23"
        assert receipt["next_activation_date"] == "2026-10-26"
    else:
        assert receipt["next_activation_date"] > receipt["activation_date"]
    # The actual authorized selection changes, including the PID attestation;
    # the receipt must bind its current root/commit, not the predecessor bytes.
    selected[:] = [root, commit]
    selector.write_text(
        json.dumps(
            dict(git_commit=commit, release_root=str(root), actual_pid_consumed=True)
        )
    )
    if coordination:
        assert str(control) not in receipt["source_hashes"]
        assert (
            receipt["origin_transition_observation"]["sha256"] == original_control_sha
        )
        # Exercise the real native transition, including its publishing state,
        # rather than a mock that leaves the coordination pointer unchanged.
        transition = Transition(tmp_path, "successor")
        with transition.owner():
            probe = data / "runtime/fixture.json"
            transition.add(probe, b"{}")
            transition.publish(
                verify=lambda: H.validate(
                    bundle, data, original_error=ValueError("code_changed")
                )
            )
    assert H.validate(bundle, data, original_error=ValueError("code_changed")) is bundle
    selector.write_text(json.dumps(dict(git_commit="c" * 40, release_root=str(root))))
    with pytest.raises(ValueError, match="selection_changed"):
        H.validate(bundle, data, original_error=ValueError("code_changed"))


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "observed_coordination_changed",
        "coordination_changed",
        "coordination_corrupt",
        "foreign_publishing",
        "coordination_race",
        "coordination_symlink",
    ],
)
def test_native_transition_coordination_is_observed_without_freezing_policy(
    tmp_path, monkeypatch, damage
):
    test_second_code_handoff_preserves_selector_provenance_without_freezing_transition(
        tmp_path, monkeypatch, damage, False, coordination=True
    )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "closed_missing",
        "closed_changed",
        "closed_live",
        "closed_basis",
        "closed_flags",
        "closed_source",
        "closed_hold",
    ],
)
def test_closed_issuer_uses_native_parent_without_future_preparation_dependency(
    tmp_path, monkeypatch, damage
):
    test_second_code_handoff_preserves_selector_provenance_without_freezing_transition(
        tmp_path, monkeypatch, damage, False, closed_parent=True
    )


@pytest.mark.parametrize(
    "damage", [None, "source", "code", "scope", "target", "membership", "selection"]
)
def test_stopped_future_main_reader_keeps_issuer_and_workflow_separate(
    tmp_path, monkeypatch, damage
):
    import json
    from pathlib import Path
    from src.engine.scalping import (
        reversal_code_handoff as A,
        mechanistic_entry_runtime_policy as N,
        continuous_reversal_policy_v6 as V,
    )
    from src.engine.automation import intraday_release_handoff as I
    from src.engine.infrastructure import runtime_release_router as R

    root, previous = tmp_path / "workflow", tmp_path / "selected"
    own = root / "src/engine/scalping/reversal_code_handoff.py"
    own.parent.mkdir(parents=True)
    own.write_text("fixture issuer")
    previous.mkdir()
    code = root / "consumer.py"
    code.write_text("reviewed future reader")
    data = tmp_path / "data"
    selector = data / "runtime/runtime_release_selection.json"
    selector.parent.mkdir(parents=True)
    selection = dict(git_commit="a" * 40, release_root=str(previous))
    selector.write_text(json.dumps(selection))
    monkeypatch.setattr(A, "__file__", str(own))
    monkeypatch.setattr(
        R,
        "selected_release",
        lambda _: (previous, "c" * 40 if damage == "selection" else "a" * 40),
    )
    monkeypatch.setattr(
        V, "contract_modules", lambda: [SimpleNamespace(__file__=str(code))]
    )
    observation = dict(
        source_date="2026-10-27",
        prepared_target_date="2026-10-28",
        runtime_effect=False,
        actual_pid_consumed=False,
        allowed_runtime_apply=False,
    )
    review = dict(
        code_root=root, code_commit="b" * 40, postclose_observation=observation
    )
    monkeypatch.setattr(I, "predecessor_review_matches", lambda *a: damage != "scope")
    bundle = dict(
        bundle_sha256="f" * 64,
        source_date="2026-10-27",
        publication_date="2026-10-27",
        target_date="wrong" if damage == "target" else "2026-10-28",
        continuous_reversal=dict(
            schema="continuous_reversal_policy_v6",
            release_commit="a" * 40,
            contract_file_sha256={
                "wrong" if damage == "membership" else "consumer.py": "d" * 64
            },
        ),
    )
    calls = []

    def native(value, directory, *, historical_code_root):
        assert (
            value is bundle and directory == data and historical_code_root == previous
        )
        calls.append("issuer")
        if damage == "source":
            raise ValueError("original_source_changed")

    def delta(candidate, commit, origin, paths, expected):
        assert (candidate, commit, origin) == (root, "b" * 40, "a" * 40)
        assert paths == {"consumer.py": "consumer.py"} and expected == N.digest(
            {"consumer.py": "d" * 64}
        )
        calls.append("code")
        if damage == "code":
            raise ValueError("unreviewed_code")

    monkeypatch.setattr(N, "_validate_bundle_sources", native)
    monkeypatch.setattr(I, "_verify_entry_code_delta", delta)
    token = I._PREDECESSOR_REVIEW.set(review)
    try:
        if damage:
            with pytest.raises((ValueError, FileNotFoundError)):
                A.validate(bundle, data, original_error=ValueError("code_changed"))
        else:
            assert (
                A.validate(bundle, data, original_error=ValueError("code_changed"))
                is bundle
            )
            assert calls == ["issuer", "code"]
            assert not (
                data / "runtime/mechanistic_entry_policy/code_handoffs"
            ).exists()
    finally:
        I._PREDECESSOR_REVIEW.reset(token)


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "seal",
        "commit",
        "day",
        "pid",
        "bundle",
        "epoch",
        "hash",
        "outside",
        "owner",
        "ttl",
        "role",
        "exit",
    ],
)
def test_prepared_issuer_transfers_native_byte_custody(tmp_path, monkeypatch, damage):
    import hashlib, json, os, subprocess, time
    from pathlib import Path
    from src.engine.scalping import reversal_code_handoff as A, mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure import validation_digest_session as D
    from src.engine.infrastructure import runtime_release_router as R

    data, origin = tmp_path / "data", tmp_path / "issuer"
    data.mkdir()
    origin.mkdir()
    source = data / "bars.json"
    source.write_bytes(b"x" * D.MIN_BYTES)
    bundle = dict(
        source_date="2026-10-27", continuous_reversal=dict(release_commit="a" * 40)
    )
    monkeypatch.setattr(
        R,
        "_release_identity",
        lambda *a: dict(source_integrity="git_commit_and_clean_runtime_source"),
    )

    class Pipe:
        pid = 12345
        returncode = 1 if damage == "exit" else 0
        args = []

        def __init__(self, args, **kwargs):
            assert "N._validate_bundle_sources(bundle" in args[3]
            assert kwargs["cwd"] == origin

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def communicate(self, raw, **kwargs):
            assert json.loads(raw) == bundle
            session = D.ACTIVE.get()
            binding = dict(session.binding, pid=self.pid)
            entry = dict(
                identity=D.identity(source),
                digest=hashlib.sha256(source.read_bytes()).hexdigest(),
                created=time.time(),
            )
            body = dict(
                schema="native_prepared_issuer_bytes_v1",
                issuer_root=str(origin),
                issuer_commit="a" * 40,
                bundle_digest=N.digest(bundle),
                binding=binding,
                uid=os.getuid(),
                entries={str(source): entry},
                semantic_verdict=False,
                runtime_effect=False,
            )
            if damage == "commit":
                body["issuer_commit"] = "b" * 40
            if damage == "day":
                binding["day"] = "2026-10-26"
            if damage == "pid":
                binding["pid"] += 1
            if damage == "bundle":
                body["bundle_digest"] = "b" * 64
            if damage == "epoch":
                entry["identity"][6] -= 1
            if damage == "hash":
                entry["digest"] = "unknown"
            if damage == "outside":
                other = tmp_path / "outside.json"
                other.write_bytes(source.read_bytes())
                entry["identity"] = D.identity(other)
                body["entries"] = {str(other): entry}
            if damage == "owner":
                body["uid"] += 1
            if damage == "ttl":
                entry["created"] -= 601
            if damage == "role":
                binding["role"] = "observer"
            capsule = dict(body=body, sha256=D._sha(body))
            if damage == "seal":
                capsule["sha256"] = "b" * 64
            return json.dumps(capsule), "original native failure"

    monkeypatch.setattr(A.subprocess, "Popen", Pipe)
    with D.postclose_session(data, bundle["source_date"]) as session:
        if damage:
            with pytest.raises((ValueError, subprocess.CalledProcessError)):
                A._validate_prepared_issuer(bundle, data, origin)
            assert not session.entries
        else:
            assert A._validate_prepared_issuer(bundle, data, origin) is bundle
            assert (
                session.entries[str(source)]["digest"]
                == hashlib.sha256(source.read_bytes()).hexdigest()
            )
            assert session.stats["admitted_native_bytes"] == source.stat().st_size
            source.write_bytes(b"y" * D.MIN_BYTES)
            with pytest.raises(D.ValidationDeferred, match="epoch_changed"):
                session.digest(source)


def test_prepared_issuer_real_native_subprocess_digest_handoff(tmp_path, monkeypatch):
    import hashlib, os, shutil, sys
    from pathlib import Path
    from src.engine.scalping import reversal_code_handoff as A, mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure import validation_digest_session as D
    from src.engine.infrastructure import runtime_release_router as R

    data, origin = tmp_path / "data", tmp_path / "issuer"
    data.mkdir()
    infra = origin / "src/engine/infrastructure"
    infra.mkdir(parents=True)
    automation = origin / "src/engine/automation"
    automation.mkdir()
    scalping = origin / "src/engine/scalping"
    scalping.mkdir()
    shutil.copyfile(D.__file__, infra / "validation_digest_session.py")
    (automation / "main_trailing_source_store.py").write_text(
        "from contextlib import nullcontext\ndef read_session(data): return nullcontext()\n"
    )
    (scalping / "mechanistic_entry_runtime_policy.py").write_text(
        "import hashlib,json\nfrom src.engine.infrastructure import validation_digest_session as D\ndef digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()\ndef _validate_bundle_sources(b,data):\n assert D.reused_digest(data/'bars.json') == b['source_sha256'], 'native_source_changed'\n"
    )
    python = origin / ".venv/bin/python"
    python.parent.mkdir(parents=True)
    python.symlink_to(sys.executable)
    source = data / "bars.json"
    source.write_bytes(b"x" * D.MIN_BYTES)
    bundle = dict(
        source_date="2026-10-27",
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        continuous_reversal=dict(release_commit="a" * 40),
    )
    monkeypatch.setattr(
        R,
        "_release_identity",
        lambda *a: dict(source_integrity="git_commit_and_clean_runtime_source"),
    )
    with D.postclose_session(data, bundle["source_date"]) as session:
        assert A._validate_prepared_issuer(bundle, data, origin) is bundle
        assert session.entries[str(source)]["digest"] == bundle["source_sha256"]
        assert session.entries[str(source)]["native_generation_proof"]



def test_cold_code_handoff_publishes_next_activation_date(tmp_path, monkeypatch):
    test_second_code_handoff_preserves_selector_provenance_without_freezing_transition(
        tmp_path, monkeypatch, None, False, cold_activation=True
    )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "source_date",
        "main_live",
        "session_live",
        "restart",
        "hold",
        "consumed",
        "source_selection",
        "next_date",
        "eod_date",
        "eod_status",
        "eod_rows",
        "failed_commit",
        "failed_status",
        "failed_run",
        "failed_exit",
        "ancestry",
        "changed",
    ],
)
def test_postclose_midnight_handoff_requires_stopped_exact_native_ancestry(
    tmp_path,
    monkeypatch,
    damage,
    legacy_damage=False,
    completed=False,
    observation_day="2026-10-24",
    source_day="2026-10-23",
    next_day="2026-10-26",
    selected_day=None,
    retained_workflow=False,
    parent_source=None,
    legacy_undeclared=False,
):
    import json
    from pathlib import Path
    from datetime import timedelta
    from src.engine.scalping import (
        reversal_code_handoff as H,
        continuous_reversal_postclose as P,
    )
    from src.engine.automation import ordered_intraday_deploy as D

    data = tmp_path / "data"
    origin = tmp_path / "origin"
    origin.mkdir()
    day = observation_day
    source = source_day
    selection = data / "runtime/runtime_release_selection.json"
    selection.parent.mkdir(parents=True)
    selected = dict(
        git_commit="a" * 40,
        release_root=str(origin),
        source_date=source,
        approved_by="user",
        approval_scope="after_postclose_deploy_for_next_regular_start",
        actual_pid_consumed=False,
        next_operating_date=next_day,
    )
    if selected_day:
        selected["selected_at_kst"] = selected_day + "T00:21:20+09:00"
    if damage == "consumed":
        selected["actual_pid_consumed"] = True
    if damage == "source_selection":
        selected["source_date"] = day
    if damage == "next_date":
        selected["next_operating_date"] = "invalid"
    if legacy_damage is not False:
        from src.engine.infrastructure import research_release_transition as T

        prior = dict(
            actual_pid_consumed=True,
            git_commit="b" * 40,
            release_root=str(tmp_path / "consumed"),
        )
        prior_raw = json.dumps(prior).encode()
        selection.write_bytes(prior_raw)
        transaction = T.Transition(tmp_path, "cold-source")
        proof_path = (
            data / "report/main_startup_validation" / source / "original-p5/final.json"
        )
        proof_path.parent.mkdir(parents=True)
        p5 = dict(
            schema="main_policy_load_exit_validation_v1",
            status="passed",
            findings=[],
            target_date=source,
            execution_release_root=str(origin),
            execution_release_commit="a" * 40,
            child_terminated=True,
            load_check_passed=True,
            protected_sources_unchanged=True,
        )
        proof_path.write_text(json.dumps(p5))
        selected.update(
            approval_scope="postclose_recovery_before_next_regular_start",
            previous_git_commit=prior["git_commit"],
            previous_release_root=prior["release_root"],
            predecessor_selection_sha256=T.sha(prior_raw),
            previous_selection_backup=str(
                transaction.directory / ("before-" + T.sha(prior_raw) + ".bytes")
            ),
            candidate_p5_path=str(proof_path),
            candidate_p5_sha256=P.file_hash(proof_path),
        )
        if legacy_damage == "unknown_scope":
            selected["approval_scope"] = "unapproved_other_operation"
        with transaction.owner():
            raw = json.dumps(selected).encode()
            transaction.add(selection, raw)
            transaction.execute(
                [lambda: transaction.write(selection, raw)], verify=lambda: None
            )
        if legacy_damage in {"p5_fail", "p5_day", "p5_root"}:
            p5.update(
                {
                    "p5_fail": dict(status="failed"),
                    "p5_day": dict(target_date=day),
                    "p5_root": dict(execution_release_root="wrong"),
                }[legacy_damage]
            )
            proof_path.write_text(json.dumps(p5))
        if legacy_damage == "snapshot":
            (transaction.directory / ("after-" + T.sha(raw) + ".bytes")).write_bytes(
                b"{}"
            )
        if legacy_damage == "predecessor":
            Path(selected["previous_selection_backup"]).write_bytes(b"{}")
        if legacy_damage == "missing_transition":
            transaction.path.unlink()
        if legacy_damage == "unsealed":
            transaction.path.write_text("{}")
    else:
        selection.write_text(json.dumps(selected))
    eod = data / "runtime/update_kospi_status" / ("update_kospi_" + source + ".json")
    eod.parent.mkdir()
    eod_body = dict(
        schema_version=1,
        target_date=day if damage == "eod_date" else source,
        status="running" if damage == "eod_status" else "completed_with_warnings",
        failed_steps=[],
        db_state=dict(
            latest_quote_date=source,
            rows_on_latest_date=0 if damage == "eod_rows" else 4,
        ),
    )
    eod.write_text(json.dumps(eod_body, indent=3) + "\n")
    status = (
        data
        / "report/threshold_cycle_postclose_status"
        / ("threshold_cycle_postclose_" + source + ".status.json")
    )
    status.parent.mkdir(parents=True)
    status.write_text(
        json.dumps(
            dict(
                schema_version=2,
                run_id="invalid" if damage == "failed_run" else "d" * 32,
                exit_code=0 if damage == "failed_exit" else 1,
                report_type="threshold_cycle_postclose_status",
                target_date=source,
                status="running" if damage == "failed_status" else "failed",
                code_commit="b" * 40 if damage == "failed_commit" else "a" * 40,
                runtime_effect=False,
            )
        )
    )
    if completed:
        from src.engine.automation import postclose_done_controller as controller

        workflow_root = tmp_path / "workflow" if retained_workflow else origin
        script = workflow_root / "deploy/run_threshold_cycle_postclose.sh"
        script.parent.mkdir(parents=True)
        script.write_text("reviewed workflow")
        body = json.loads(status.read_bytes())
        body.update(
            status="succeeded",
            exit_code=0,
            code_commit="b" * 40,
            reason="verified_main_completed",
            workflow_source=dict(
                root=str(workflow_root),
                commit="a" * 40,
                script=str(script),
                sha256=P.file_hash(script),
            ),
        )
        if damage == "failed_commit":
            body["workflow_source"]["commit"] = "b" * 40
        if damage == "failed_status":
            body["status"] = "running"
        if damage == "failed_exit":
            body["exit_code"] = 1
        status.write_text(json.dumps(body))
        report = (
            data
            / "report/postclose_done_controller"
            / ("postclose_done_controller_" + source + ".json")
        )
        report.parent.mkdir()
        attempt = report.parent / "attempt.json"
        verification = report.parent / "verification.json"
        attempt.write_text("{}")
        verification.write_text("{}")
        report.write_text(
            json.dumps(
                dict(
                    main_run_id=(
                        "wrong" if damage == "controller_run" else body["run_id"]
                    ),
                    attempt_path=str(attempt),
                    verification_attempt_path=str(verification),
                )
            )
        )

        def verify_origin(command, **kwargs):
            assert command[0] == str(origin / ".venv/bin/python")
            assert kwargs["cwd"] == origin and kwargs["env"]["PYTHONPATH"] == str(
                origin
            )
            assert (
                "started_after_ns=0" in command[3]
                and "generation_only=True" not in command[3]
            )
            return json.dumps(
                ["current_contract_failed"] if damage == "controller_invalid" else []
            )

        monkeypatch.setattr(H.subprocess, "check_output", verify_origin)
        if retained_workflow:
            from src.engine.infrastructure import runtime_release_router as router

            def verify_workflow(workspace, selection):
                assert workspace == tmp_path
                assert selection["release_root"] == str(workflow_root)
                assert selection["git_commit"] == "a" * 40
                return workflow_root, "a" * 40

            monkeypatch.setattr(router, "validate_release", verify_workflow)
    if damage == "restart":
        (tmp_path / "restart.flag").touch()
    if damage == "hold":
        (data / "runtime/operator_startup_hold.json").write_text("{}")
    monkeypatch.setattr(D, "_main_pids", lambda: [42] if damage == "main_live" else [])
    monkeypatch.setattr(D, "_session_absent", lambda: damage != "session_live")
    ancestry_days = []

    def ancestry(*args):
        ancestry_days.append(args[1])
        if damage == "ancestry" or (selected_day and args[1] == source):
            return None
        result = dict(
            bundle_sha256="bundle", source_hashes={str(data / "old.json"): "0" * 64}
        )
        if retained_workflow and damage != "workflow_ancestry":
            result["source_hashes"][str(script)] = P.file_hash(script)
        return result

    monkeypatch.setattr(H, "_validated_origin_receipt", ancestry)
    if selected_day:
        predecessor = H.path(data, selected_day, "a" * 40, "bundle")
        predecessor.parent.mkdir(parents=True)
        predecessor.write_text(
            json.dumps(dict(postclose_source_date=parent_source or source))
        )
        if legacy_undeclared:
            from src.engine.scalping import mechanistic_entry_runtime_policy as native
            predecessor.write_text("{}")
            monkeypatch.setattr(native, "validate", lambda *a, **kw: None)
            native._atomic_write_json(native.root(data) / "generations/bundle.json",
                dict(bundle_sha256="bundle", target_date=source))
            native._atomic_write_json(native.root(data) / "current.json",
                dict(bundle_sha256="bundle", effective_date=source))
    original = D._owned_metadata
    reads = []

    def inspect(path):
        if damage == "changed" and path == eod and reads:
            eod.write_text(json.dumps({**eod_body, "changed": True}))
        result = original(path)
        if path == eod:
            reads.append(True)
        return result

    monkeypatch.setattr(D, "_owned_metadata", inspect)
    before = eod.read_bytes(), status.read_bytes()
    args = (
        data,
        day,
        day if damage == "source_date" else source,
        origin,
        "a" * 40,
        "bundle",
        "pointer",
        "c" * 40,
    )
    if damage or legacy_damage not in {None, False}:
        with pytest.raises(
            (ValueError, OSError),
            match="active_policy_postclose_|transition_record_invalid|No such file",
        ):
            H._postclose_origin_receipt(*args)
        assert not H.path(data, day, "c" * 40, "bundle").exists()
        return
    proof = H._postclose_origin_receipt(*args)
    assert ancestry_days == ([source, selected_day] if selected_day else [source])
    frozen = H.path(data, day, "c" * 40, "bundle").with_suffix("") / "postclose_origin"
    assert (frozen / eod.name).read_bytes() == before[0] and (
        frozen / status.name
    ).read_bytes() == before[1]
    assert (
        str(eod) not in proof["source_hashes"]
        and str(status) not in proof["source_hashes"]
    )
    assert (
        proof["verification_basis"] == "verified_closed_postclose_native_code_ancestry"
    )
    assert all(
        P.file_hash(name) == sha
        for name, sha in proof["source_hashes"].items()
        if name != str(data / "old.json")
    )
    assert eod.read_bytes() == before[0] and status.read_bytes() == before[1]


@pytest.mark.parametrize("day", ["2026-10-24", "2026-10-25", "2026-10-26"])
def test_closed_postclose_handoff_spans_weekend_without_changing_source(
    tmp_path, monkeypatch, day
):
    test_postclose_midnight_handoff_requires_stopped_exact_native_ancestry(
        tmp_path, monkeypatch, None, observation_day=day, completed=True
    )


def test_closed_postclose_handoff_uses_exact_selected_issue_day(tmp_path, monkeypatch):
    test_postclose_midnight_handoff_requires_stopped_exact_native_ancestry(
        tmp_path,
        monkeypatch,
        None,
        observation_day="2026-10-25",
        selected_day="2026-10-24",
        completed=True,
        retained_workflow=True,
    )


def test_closed_postclose_handoff_rejects_unbound_old_workflow(tmp_path, monkeypatch):
    test_postclose_midnight_handoff_requires_stopped_exact_native_ancestry(
        tmp_path,
        monkeypatch,
        "workflow_ancestry",
        observation_day="2026-10-25",
        selected_day="2026-10-24",
        completed=True,
        retained_workflow=True,
    )


@pytest.mark.parametrize(
    "selected_day,parent_source",
    [
        ("2026-10-26", None),
        ("2026-10-23", None),
        ("2026-10-24", "2026-10-22"),
    ],
)
def test_closed_postclose_handoff_rejects_foreign_selection_ancestry(
    tmp_path, monkeypatch, selected_day, parent_source
):
    with pytest.raises(ValueError, match="active_policy_postclose_"):
        test_postclose_midnight_handoff_requires_stopped_exact_native_ancestry(
            tmp_path,
            monkeypatch,
            None,
            observation_day="2026-10-25",
            selected_day=selected_day,
            completed=True,
            parent_source=parent_source,
        )


@pytest.mark.parametrize(
    "source,day,target",
    [
        ("2026-10-23", "2026-10-27", "2026-10-26"),
        ("2026-10-23", "2026-10-25", "2026-10-27"),
        ("2026-10-24", "2026-10-25", "2026-10-26"),
        ("2026-10-23", "2026-10-23", "2026-10-26"),
    ],
)
def test_closed_postclose_handoff_rejects_wrong_calendar_window(
    tmp_path, monkeypatch, source, day, target
):
    with pytest.raises(ValueError, match="active_policy_postclose_"):
        test_postclose_midnight_handoff_requires_stopped_exact_native_ancestry(
            tmp_path,
            monkeypatch,
            None,
            observation_day=day,
            source_day=source,
            next_day=target,
            completed=True,
        )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "main_live",
        "session_live",
        "restart",
        "hold",
        "consumed",
        "source_selection",
        "next_date",
        "eod_date",
        "eod_status",
        "eod_rows",
        "failed_commit",
        "failed_status",
        "failed_run",
        "failed_exit",
        "ancestry",
        "changed",
        "controller_run",
        "controller_invalid",
    ],
)
def test_completed_postclose_midnight_reuses_verified_whole_chain(
    tmp_path, monkeypatch, damage
):
    test_postclose_midnight_handoff_requires_stopped_exact_native_ancestry(
        tmp_path, monkeypatch, damage, completed=True
    )


@pytest.mark.parametrize(
    "legacy_damage",
    [
        None,
        "unknown_scope",
        "p5_fail",
        "p5_day",
        "p5_root",
        "snapshot",
        "predecessor",
        "missing_transition",
        "unsealed",
    ],
)
def test_midnight_legacy_cold_scope_requires_original_native_transaction_and_p5(
    tmp_path, monkeypatch, legacy_damage
):
    test_postclose_midnight_handoff_requires_stopped_exact_native_ancestry(
        tmp_path, monkeypatch, None, legacy_damage=legacy_damage
    )


@pytest.mark.parametrize(
    "anchor,expected", [(10200, "TRUE"), (9900, "FALSE"), (None, "UNKNOWN")]
)
def test_general_pre_refinement_applies_only_at_original_volume_confirmation(
    anchor, expected
):
    base = "legacy_dd5_0_8_vol_up_v1"
    bid = J.ALIASES["general_pre_refined"]
    values = [row(i, 10200, 1) for i in range(121)] + [
        row(121, 10100, 20000),
        row(122, 10110),
    ]
    if anchor is not None:
        values[0][3:6] = [anchor, anchor, anchor + 1]
    for r in values:
        r[9] = "123456_NX"
    initial = values[0] if anchor is not None else None
    original = S.State(branch_ids=[base], session_anchor=initial, offline=True)
    candidate = S.State(branch_ids=[bid], session_anchor=initial, offline=True)

    def run(state):
        hits = []
        for r in values:
            hits += state.observe(
                r, symbol="123456", venue="NXT", session="NXT_PREMARKET"
            )
        return hits

    old = run(original)
    new = run(candidate)
    assert old
    if expected == "FALSE":
        assert not new
    else:
        assert new
        e = new[-1]["event"]["branch_signals"][bid]
        A.validate_signal(e)
        assert e["signal_proof"]["refinement_truth"] == expected
        assert (
            e["epoch"] == old[-1]["event"]["epoch"]
            and e["entry_ask"] == old[-1]["event"]["entry_ask"]
        )


@pytest.mark.parametrize("case", ["empty", "cannot_fit", "generation"])
def test_source_wait_never_resets_original_deadline_or_waits_through_generation(
    case, monkeypatch
):
    from src.engine.scalping import zero_base_probe as Z
    from src.engine.scalping import reversal_source_diagnostics as D

    clock = [100.0]
    monkeypatch.setattr(Z.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        Z.time, "sleep", lambda sec: clock.__setitem__(0, clock[0] + sec)
    )
    monkeypatch.setattr(D, "observation_sequence", lambda item: 0)
    monkeypatch.setattr(
        D,
        "wait_observation",
        lambda item, seq, sec: clock.__setitem__(0, clock[0] + sec),
    )
    monkeypatch.setattr(
        Z, "probe_ws_snapshot", lambda *a, **kw: {"market_data_transport_epoch": 3}
    )
    monkeypatch.setattr(Z, "exact_probe_ws_data", lambda *a, **kw: ({}, "0B_missing"))
    monkeypatch.setattr(
        Z,
        "probe_ws_observation",
        lambda *a, **kw: dict(
            exact_0b_count=0 if case == "empty" else 3,
            exact_0d_count=0 if case == "empty" else 6,
            latest_0b_ms=None if case == "empty" else 1,
            latest_0d_ms=None if case == "empty" else 1,
            first_0b_ms=None if case == "empty" else 0,
        ),
    )
    _, obs, reason = Z.wait_for_exact_probe_ws_data(
        SimpleNamespace(_market_data_transport_epoch=3),
        code="123456",
        route="krx_nxt_integrated",
        after_epoch=100,
        now=lambda: clock[0],
        timeout_sec=15,
        empty_timeout_sec=10,
        min_exact_0b_count=5,
        residence_deadline_epoch=120 if case == "cannot_fit" else 250,
        required_window_sec=120,
        readiness_guard=lambda: (
            "consumer_readiness_generation_changed"
            if case == "generation" and clock[0] >= 117
            else ""
        ),
    )
    assert clock[0] <= (
        118 if case == "generation" else 110.01 if case == "empty" else 115.01
    )
    assert obs["residence_wait_applied"] is (case == "generation")
    if case == "generation":
        assert reason == "consumer_readiness_generation_changed"


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "missing_candidate",
        "wrong_day",
        "wrong_schema",
        "wrong_publication",
        "wrong_authority",
        "frozen_changed",
        "source_invalid",
        "parent_mismatch",
        "active_same_day",
        "active_same_day_corrupt_candidate",
    ],
)
def test_native_origin_rollover_uses_frozen_preparation_role_not_backend_error(
    tmp_path, damage
):
    import subprocess, sys, json
    from pathlib import Path
    from src.engine.scalping import reversal_code_handoff as H

    data = tmp_path / "data"
    policy = data / "policy"
    (policy / "candidates").mkdir(parents=True)
    (policy / "generations").mkdir()
    day = "2026-10-23"
    pointer = dict(
        bundle_sha256="parent",
        effective_date=(
            day
            if damage in {"active_same_day", "active_same_day_corrupt_candidate"}
            else "2026-10-22"
        ),
    )
    (policy / "current.json").write_text(json.dumps(pointer))
    family = dict(
        schema="continuous_reversal_policy_v6",
        effective_date=day,
        effective_mode="next_session",
        publication_date="2026-10-22",
        parent_bundle_sha256="parent",
        code_refresh=dict(
            authority="reviewed_identical_policy_code_refresh",
            activation_parent_origin_root=str(tmp_path / "origin"),
            activation_parent_origin_commit="a" * 40,
        ),
    )
    if damage == "wrong_day":
        family["effective_date"] = "2026-10-24"
    if damage == "wrong_schema":
        family["schema"] = "unknown"
    if damage == "wrong_publication":
        family["publication_date"] = day
    if damage == "wrong_authority":
        family["code_refresh"]["authority"] = "unapproved"
    candidate = dict(
        bundle_sha256="prepared", target_date=day, continuous_reversal=family
    )
    alias = policy / "candidates" / ("policy_" + day + ".json")
    if damage != "missing_candidate":
        alias.write_text(json.dumps(candidate))
    if damage == "active_same_day_corrupt_candidate":
        alias.write_text("{invalid-json")
    frozen = policy / "generations/prepared.json"
    frozen.write_text(
        json.dumps(
            dict(candidate, changed=True) if damage == "frozen_changed" else candidate
        )
    )
    # Execute the actual producer program in a child. Only native validator
    # boundaries are mocked; role/date/generation/parent checks remain real.
    (data / "parent-source.json").write_text("{}")
    runner = """
import sys,json,hashlib
from pathlib import Path
from src.engine.scalping import mechanistic_entry_runtime_policy as N,continuous_reversal_policy_v6 as V,reversal_code_handoff as H
calls=[];damage=sys.argv.pop(3)
N.root=lambda root:Path(root)/'policy'
N._read=lambda path:json.loads(Path(path).read_text())
N.validate=lambda value,**kwargs:None
N._signature=lambda path:None
N._source_hash=lambda name,signature:hashlib.sha256(Path(name).read_bytes()).hexdigest()
def live(*args):
 calls.append('live')
 if damage in {'active_same_day','active_same_day_corrupt_candidate'}:return dict(bundle_sha256='live')
 raise ValueError('v6_contract_code_changed:reversal_code_handoff.py')
def sources(*args):
 calls.append('native_sources')
 if damage=='source_invalid':raise ValueError('native_source_invalid')
def parent(*args,**kwargs):
 calls.append('native_parent')
 assert kwargs['origin_commit']=='a'*40
 return dict(bundle_sha256='different' if damage=='parent_mismatch' else 'parent',target_date='2026-10-22')
def parent_refs(*args):
 calls.append('native_parent_sources')
 p=Path(sys.argv[1])/'parent-source.json'
 return dict(source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest()})
H._validated_origin_receipt=parent_refs
N._load_current_uncached=live;N._validate_bundle_sources=sources;V._attested_activation_parent=parent
""" + H._ORIGIN_SCRIPT + "\nprint('ORIGIN_CALLS='+json.dumps(calls))\n"
    result = subprocess.run(
        [sys.executable, "-B", "-c", runner, str(data), day, damage or "valid"],
        capture_output=True,
        text=True,
    )
    if damage not in {None, "active_same_day", "active_same_day_corrupt_candidate"}:
        assert result.returncode != 0
        assert "ValueError" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        lines = result.stdout.splitlines()
        refs = json.loads(lines[0])
        calls = json.loads(lines[1].split("=", 1)[1])
        assert refs["bundle_sha256"] == (
            "live"
            if damage in {"active_same_day", "active_same_day_corrupt_candidate"}
            else "parent"
        )
        assert calls == (
            ["live"]
            if damage in {"active_same_day", "active_same_day_corrupt_candidate"}
            else ["native_sources", "native_parent", "native_parent_sources"]
        )
        assert str(alias) not in refs["source_hashes"]
        if damage is None:
            assert str(frozen) in refs["source_hashes"]
            assert str(data / "parent-source.json") in refs["source_hashes"]


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "authority",
        "main",
        "supervisor",
        "hold",
        "restart",
        "consumed",
        "selection_scope",
        "receipt_changed",
        "consumer_code",
        "origin",
        "transition",
        "transition_after",
        "p5",
        "parent",
        "parent_sources",
        "parent_race",
    ],
)
def test_native_legacy_parent_scope_repair_preserves_original_and_unchanged_consumer(
    tmp_path, monkeypatch, damage
):
    import json, subprocess
    from pathlib import Path
    from src.engine.scalping import (
        reversal_code_handoff as H,
        continuous_reversal_postclose as P,
    )
    from src.engine.scalping import (
        mechanistic_entry_runtime_policy as N,
        continuous_reversal_policy_v6 as V,
    )
    from src.engine.infrastructure import (
        runtime_release_router as R,
        research_release_transition as X,
    )
    from src.engine.automation import ordered_intraday_deploy as D

    data = tmp_path / "workspace/data"
    policy = N.root(data)
    policy.mkdir(parents=True)
    day = datetime.now(P.KST).date().isoformat()
    from datetime import timedelta

    source = (datetime.fromisoformat(day) - timedelta(days=1)).date().isoformat()
    relative = Path("src/engine/scalping/reversal_code_handoff.py")
    origin = tmp_path / "origin"
    origin.mkdir()
    consumer = tmp_path / "consumer"
    workflow = tmp_path / "workflow"
    code = consumer / relative
    code.parent.mkdir(parents=True)
    code.write_text("legacy producer")
    new = workflow / relative
    new.parent.mkdir(parents=True)
    new.write_text("reviewed native scope producer")
    commits = {origin: "a" * 40, consumer: "b" * 40, workflow: "c" * 40}
    monkeypatch.setattr(H, "__file__", str(new))
    monkeypatch.setattr(H, "LEGACY_PREPARED_PARENT_SCOPE_CODE", P.file_hash(code))
    monkeypatch.setattr(H, "code_hashes", lambda: {str(new): P.file_hash(new)})
    monkeypatch.setattr(R, "git", lambda root, *args: commits[Path(root)])
    monkeypatch.setattr(
        R,
        "validate_release",
        lambda workspace, s: (Path(s["release_root"]), s["git_commit"]),
    )
    selector = data / "runtime/runtime_release_selection.json"
    before = dict(
        schema="runtime_release_selection_v1",
        workspace=str(data.parent),
        release_root=str(origin),
        git_commit=commits[origin],
    )
    selector.write_text(json.dumps(before))
    before_raw = selector.read_bytes()
    pointer = policy / "current.json"
    pointer.write_text(json.dumps(dict(bundle_sha256="parent", effective_date=source)))
    pointer_raw = pointer.read_bytes()
    p5 = data / "report/main_startup_validation" / day / ("1" * 32) / "final.json"
    p5.parent.mkdir(parents=True)
    p5.write_text(
        json.dumps(
            dict(
                schema="main_policy_load_exit_validation_v1",
                status="passed",
                findings=[],
                target_date=day,
                execution_release_root=str(consumer),
                execution_release_commit=commits[consumer],
                child_terminated=True,
                load_check_passed=True,
                protected_sources_unchanged=True,
            )
        )
    )
    transaction = X.Transition(data.parent, "scope-fixture")
    selection = dict(
        before,
        release_root=str(consumer),
        git_commit=commits[consumer],
        approved_by="user",
        approval_scope="after_postclose_deploy_for_next_regular_start",
        actual_pid_consumed=False,
        source_date=source,
        next_operating_date=day,
        candidate_p5_path=str(p5),
        candidate_p5_sha256=P.file_hash(p5),
        predecessor_selection_sha256=X.sha(before_raw),
        previous_selection_backup=str(
            transaction.directory / ("before-" + X.sha(before_raw) + ".bytes")
        ),
    )
    transaction.add(selector, json.dumps(selection).encode())
    with transaction.owner():
        transaction.publish(verify=lambda: None)
    monkeypatch.setattr(
        R,
        "selected_release",
        lambda workspace: (
            Path(json.loads(selector.read_bytes())["release_root"]),
            json.loads(selector.read_bytes())["git_commit"],
        ),
    )
    monkeypatch.setattr(D, "_main_pids", lambda: [123] if damage == "main" else [])
    monkeypatch.setattr(D, "_session_absent", lambda: damage != "supervisor")
    monkeypatch.setattr(V, "_require_closed_postclose_window", lambda *args: None)
    parent_source = data / "parent.json"
    parent_source.write_text("{}")
    parent_sha = P.file_hash(parent_source)
    stale = data / "future-evaluation.json"
    stale.write_text("original bytes")
    stale_sha = P.file_hash(stale)
    receipt = H.path(data, day, commits[consumer], "parent")
    receipt.parent.mkdir(parents=True)
    old = P.seal(
        dict(
            schema=H.SCHEMA,
            authority=H.AUTHORITY,
            target_date=day,
            release_root=str(consumer),
            release_commit=commits[consumer],
            bundle_sha256="parent",
            current_pointer_sha256=P.file_hash(pointer),
            policy_reselected=False,
            provider_called=False,
            origin_root=str(origin),
            origin_commit=commits[origin],
            origin_selection_sha256=X.sha(before_raw),
            code_hashes={str(code): P.file_hash(code)},
            source_hashes={str(stale): stale_sha},
        )
    )
    receipt.write_text(json.dumps(old))
    old_raw = receipt.read_bytes()
    expected = P.file_hash(receipt)
    stale.write_text("semantically same but different physical bytes")

    def parent(*args, **kwargs):
        if damage == "parent_race":
            pointer.write_text("{}")
        return dict(
            bundle_sha256="wrong" if damage == "parent" else "parent",
            target_date=source,
        )

    monkeypatch.setattr(V, "_attested_activation_parent", parent)
    monkeypatch.setattr(
        H,
        "_validated_origin_receipt",
        lambda *args: dict(source_hashes={str(parent_source): parent_sha}),
    )
    # Exercise the actual pre-fix consumer, not a replacement validator.
    legacy_code = subprocess.check_output(
        ["git", "show", "a90be019c:src/engine/scalping/reversal_code_handoff.py"],
        text=True,
    )
    legacy = {"__file__": str(code), "__name__": "legacy_scope_consumer"}
    exec(compile(legacy_code, str(code), "exec"), legacy)
    monkeypatch.setattr(V, "contract_modules", lambda: [])
    bundle = dict(bundle_sha256="parent")
    with pytest.raises(ValueError, match="source_changed"):
        legacy["validate"](bundle, data, original_error=ValueError("original"))
    if damage == "hold":
        (data / "runtime/operator_startup_hold.json").write_text("{}")
    if damage == "restart":
        (data.parent / "restart.flag").write_text("")
    if damage in {"consumed", "selection_scope"}:
        body = json.loads(selector.read_bytes())
        body["actual_pid_consumed" if damage == "consumed" else "approval_scope"] = (
            True if damage == "consumed" else "foreign"
        )
        selector.write_text(json.dumps(body))
    if damage == "receipt_changed":
        expected = "0" * 64
    if damage == "consumer_code":
        code.write_text("changed consumer")
    if damage == "origin":
        body = P.seal(dict(old, origin_commit="d" * 40))
        receipt.write_text(json.dumps(body))
        old_raw = receipt.read_bytes()
        expected = P.file_hash(receipt)
    if damage == "transition":
        body = json.loads(transaction.path.read_bytes())
        body["state"] = "prepared"
        transaction.path.write_text(json.dumps(body))
    if damage == "transition_after":
        after = (
            transaction.directory / transaction.value["entries"][0]["after_snapshot"]
        )
        after.write_text("{}")
    if damage == "p5":
        p5.write_text("{}")
    if damage == "parent_sources":
        parent_source.write_text("changed")
    selection_raw = selector.read_bytes()
    if damage:
        with pytest.raises((ValueError, KeyError)):
            H.repair_prepared_parent_scope(
                data,
                day,
                consumer_root=consumer,
                expected_receipt_sha256=expected,
                confirm="wrong" if damage == "authority" else H.AUTHORITY,
            )
        assert receipt.read_bytes() == old_raw
    else:
        result = H.repair_prepared_parent_scope(
            data,
            day,
            consumer_root=consumer,
            expected_receipt_sha256=expected,
            confirm=H.AUTHORITY,
        )
        assert (
            result["code_hashes"] == old["code_hashes"]
            and result["policy_reselected"] is False
        )
        assert result["source_scope_repair"]["actual_pid_consumed"] is False
        saved = Path(result["source_scope_repair"]["original_receipt"]["path"])
        assert saved.read_bytes() == old_raw
        assert (
            str(stale) not in result["source_hashes"]
            and str(parent_source) in result["source_hashes"]
        )
        assert (
            legacy["validate"](bundle, data, original_error=ValueError("original"))
            == bundle
        )
    assert selector.read_bytes() == selection_raw
    if damage != "parent_race":
        assert pointer.read_bytes() == pointer_raw
    assert stale.read_text() == "semantically same but different physical bytes"


def test_legacy_publication_receipt_is_revalidated_only_as_native_parent_ancestry(tmp_path, monkeypatch):
    test_postclose_midnight_handoff_requires_stopped_exact_native_ancestry(
        tmp_path, monkeypatch, None, observation_day="2026-10-26",
        selected_day="2026-10-25", legacy_undeclared=True
    )


@pytest.mark.parametrize('fault', [None, 'date', 'source', 'origin', 'code', 'source_changed',
    'pointer', 'authority', 'seal', 'consumed', 'live', 'supervisor', 'selection_race', 'proof_race'])
def test_native_activation_rollover_preserves_consumer_and_original_receipt(tmp_path, monkeypatch, fault):
    import json, contextlib
    from pathlib import Path
    from src.engine.scalping import reversal_code_handoff as H, mechanistic_entry_runtime_policy as N
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.automation import ordered_intraday_deploy as D, next_preopen_readiness as Q
    from src.engine.infrastructure import runtime_release_router as R

    data = tmp_path / 'data'; data.mkdir()
    consumer, workflow, attested = (tmp_path / n for n in ['consumer', 'workflow', 'attested'])
    codes = []
    for root in [consumer, workflow, attested]:
        code = root / 'src/engine/scalping/reversal_code_handoff.py'
        code.parent.mkdir(parents=True); code.write_text(root.name); codes.append(code)
    monkeypatch.setattr(H, '__file__', str(codes[1]))
    monkeypatch.setattr(R, 'git', lambda *a: 'c' * 40)
    monkeypatch.setattr(R, 'validate_release', lambda *a: (workflow, 'c' * 40))
    monkeypatch.setattr(R, 'selected_release', lambda *a: (consumer, 'a' * 40))
    monkeypatch.setattr(R, 'runtime_release_set_lock', lambda *a: contextlib.nullcontext())
    monkeypatch.setattr(R, 'scheduled_execution_lease', lambda *a, **kw: contextlib.nullcontext())
    monkeypatch.setattr(Q, 'failed_preopen_recovery', lambda *a, **kw: contextlib.nullcontext())
    monkeypatch.setattr(D, '_main_pids', lambda: [7] if fault == 'live' else [])
    monkeypatch.setattr(D, '_session_absent', lambda: fault != 'supervisor')
    pointer = N.root(data) / 'current.json'; pointer.parent.mkdir(parents=True)
    ident = 'e' * 64
    pointer.write_text(json.dumps(dict(effective_date='2026-10-23', bundle_sha256=ident)))
    selector = data / 'runtime/runtime_release_selection.json'
    selector.write_text(json.dumps(dict(release_root=str(consumer), git_commit='a' * 40,
        approved_by='user', approval_scope='after_postclose_deploy_for_next_regular_start',
        actual_pid_consumed=fault == 'consumed', main_start_authorized=False,
        next_operating_date='2026-10-26', source_date='2026-10-23',
        selected_at_kst='2026-10-25T14:55:33+09:00')))
    source = data / 'frozen-source.json'; source.write_text('{}')
    def receipt(day, root, commit, code):
        return P.seal(dict(schema=H.SCHEMA, authority=H.AUTHORITY, target_date=day,
            release_root=str(root), release_commit=commit, bundle_sha256=ident,
            current_pointer_sha256=P.file_hash(pointer), code_hashes={str(code):P.file_hash(code)},
            source_hashes={str(source):P.file_hash(source)}, policy_reselected=False, provider_called=False,
            actual_pid_consumed=False))
    original = H.path(data, '2026-10-25', 'a' * 40, ident)
    N._atomic_write_json(original, receipt('2026-10-25', consumer, 'a' * 40, codes[0]))
    original_raw = original.read_bytes()
    proof_path = H.path(data, '2026-10-26', 'b' * 40, ident)
    proof = receipt('2026-10-26', attested, 'b' * 40, codes[2])
    proof.update(activation_date='2026-10-25' if fault == 'date' else '2026-10-26',
        source_trading_date='2026-10-22' if fault == 'source' else '2026-10-23',
        origin_root='wrong' if fault == 'origin' else str(consumer), origin_commit='a' * 40,
        origin_selection_sha256=P.file_hash(selector))
    if fault == 'pointer': proof['current_pointer_sha256']='wrong'
    if fault == 'authority': proof['authority']='unapproved'
    proof = P.seal(proof)
    if fault == 'seal': proof['provider_called']=True
    N._atomic_write_json(proof_path, proof)
    if fault == 'code': codes[0].write_text('changed')
    if fault == 'source_changed': source.write_text('{"changed":true}')
    def final_check(*a, **kw):
        if fault == 'selection_race': selector.write_text('{}')
        if fault == 'proof_race': proof_path.write_text('{}')
    monkeypatch.setattr(Q, 'require_failed_preopen_recovery', final_check)
    destination=H.path(data, '2026-10-26', 'a' * 40, ident)
    call=lambda: H.issue_activation_rollover(data, '2026-10-26', verified_receipt=proof_path, confirm=H.AUTHORITY)
    if fault:
        with pytest.raises(ValueError):call()
        assert not destination.exists()
    else:
        result=call()
        assert result['activation_date']=='2026-10-26' and result['target_date']=='2026-10-26'
        assert result['code_hashes']==json.loads(original_raw)['code_hashes']
        assert result['activation_rollover']['original_sha256']==P.file_hash(original)
        assert N._read(destination)==result
    assert original.read_bytes()==original_raw
