"""Read-only input proof, immutable source labels and native publication guards."""

import base64
import copy
import hashlib
import json
from datetime import datetime
from types import SimpleNamespace
from pathlib import Path
import pytest
from src.engine.ai import offline_comparison_store as S

from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_input_transition as J
from src.engine.scalping import reversal_auxiliary_transition as X
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_intraday as I
from src.engine.scalping import reversal_auxiliary_risk_role_experiment as E
from src.engine.scalping import reversal_auxiliary_research_wire as OLD_W
from src.engine.scalping import reversal_auxiliary_tuning as T
from src.engine.scalping import reversal_auxiliary_research as R
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.tests.test_reversal_extended_policy import FIXTURES


def actual_result(req, logical, arm, passed, rid):
    aliases = J.W.encode(logical)[2]
    raw = dict(
        assessed={aliases[s["ref"]]: True for s in logical["signals"]}, confidence=50
    )
    if passed:
        raw["screen"] = dict(
            verdict="PASS",
            risk="NO_BLOCKING_RISK",
            fact=aliases["observed_machine_signal"],
        )
    else:
        fid = logical["entry_setup_evidence_v1"]["risk_fact_bindings"][
            "OBSERVED_TARGET_PROGRESS_CONCERN"
        ][0]
        raw["screen"] = dict(
            verdict="CAUTION",
            risk="OBSERVED_TARGET_PROGRESS_CONCERN",
            fact=aliases[fid],
        )
    from src.engine.scalping.ai_decision_quality import (
        execute_openai_prompt_v2_candidate,
    )

    projection = execute_openai_prompt_v2_candidate(req, _request_projection_only=True)[
        "provider_request_projection"
    ]
    encoded = json.dumps(raw).encode()
    receipt = dict(
        response_id="fixture-response-" + str(rid),
        provider_output_bytes_b64=base64.b64encode(encoded).decode(),
        provider_output_bytes_sha256=hashlib.sha256(encoded).hexdigest(),
        provider_output_size_bytes=len(encoded),
        parse_status="pass",
        parsed_candidate_payload=raw,
        parsed_candidate_payload_sha256=P.digest(raw),
        provider_request_projection=projection,
        provider_request_projection_sha256=P.digest(projection),
    )
    receipt["attempt_receipt_content_sha256"] = P.digest(receipt)
    return dict(
        result=dict(
            candidate_response=raw,
            provider_attempt_receipt=receipt,
            provider_provenance=dict(
                provider="openai",
                provider_none=False,
                response_id=receipt["response_id"],
            ),
        ),
        transport_invoked=True,
        validation_errors=[],
    )


@pytest.fixture
def prepared_input(tmp_path, monkeypatch):
    policy = tmp_path / "policy"
    ledger = tmp_path / "ledger"
    fixture = FIXTURES["manual_extended_a894da51c88c3ef2"]
    sid = "196170|PRE|GE_100000|NXT"
    base = G.definition(J.M.U.V1.ARMS[1], input_version=J.M.U.VERSION)
    current = G.compact_definition(base, research_wire_contract=OLD_W.contract())
    variant = G.definition(
        base["base_arm"],
        input_version=J.M.U.VERSION,
        prompt=base["prompt"] + "Use the supplied numeric path.\n",
    )
    candidate = G.compact_definition(variant, research_wire_contract=OLD_W.contract())
    for value in (base, current):
        G.register(policy, value)
    for value in (base, current, variant, candidate):
        G.register(ledger, value)
    bindings = {
        J.V.scope_id(key, route): current["registry_sha256"]
        for key, route in J.V.scopes()
    }
    mc = {}
    ac = {}
    for key, route in J.V.scopes():
        mc.setdefault(key, dict(routes={}))
        ac.setdefault(key, dict(routes={}))
        mc[key]["routes"][route] = dict(backend="union_v6")
        ac[key]["routes"][route] = dict(
            payload=dict(arm=base["base_arm"], binding=J.M.U.binding(base["base_arm"]))
        )
    bundle = dict(
        bundle_sha256="b" * 64,
        target_date="2026-10-19",
        continuous_reversal=dict(
            family_sha256="f" * 64,
            auxiliary_report_sha256="a" * 64,
            machine_cells=mc,
            auxiliary_cells=ac,
            operating_manifest=dict(
                detector_manifest_hash="d" * 64,
                scopes={sid: list(fixture["event"]["branch_signals"])},
            ),
        ),
    )
    monkeypatch.setattr(I, "inherited", lambda *a: copy.deepcopy(bindings))
    monkeypatch.setattr(N, "load_effective", lambda **kw: bundle)
    N.root(policy).mkdir(parents=True, exist_ok=True)
    cfg = dict(
        risk_role_contract=E.contract("ROLE_VOCAB_PATH"), risk_role_roles=["candidate"]
    )
    monkeypatch.setattr(R, "context", lambda *a: dict(purpose="evaluation", config=cfg))
    P.write(R.root(ledger) / "allowance.json", P.seal({"fixture_grant": True}))
    config_path = R.directory(ledger, "fixture") / "configuration.json"
    P.write(config_path, P.seal({"config": cfg}))
    objects = {}
    requests = {}
    owners = []
    pairs = []
    rows = []
    reuse = []
    source_points = []
    evaluated = []
    for i in range(50):
        snap = copy.deepcopy([fixture["event"], fixture["source"]])
        snap[0]["native_sequence"] += i
        snap[0]["event_id"] = P.digest(["fixture_event", i])
        for signal in snap[0]["branch_signals"].values():
            signal["native_sequence"] = snap[0]["native_sequence"]
        key = J.M.U.opportunity(snap[0])
        snapshot_obj = i + 1
        objects[snapshot_obj] = snap
        outcome = dict(status="WIN" if i % 2 else "FAIL_TIMEOUT")
        point = dict(
            opportunity_key=key,
            scope=sid,
            day="2026-10-07",
            symbol=snap[0]["symbol"],
            snapshot_obj=snapshot_obj,
            outcome=outcome,
        )
        source_points.append(point)
        rows.append(dict(point, source_records_object=999, source_records_ordinal=i))
        pair = dict(
            point,
            current_registry=current["registry_sha256"],
            candidate_registry=candidate["registry_sha256"],
            requests={},
        )
        verdicts = {}
        for role, value in (("current", current), ("candidate", candidate)):
            rid = 1000 + 2 * i + (role == "candidate")
            inp = G.production_request(snap, value)[0]
            req = G.request(snap, value)
            if role == "candidate":
                req = E.transform_request(req, inp, contract=cfg["risk_role_contract"])
                inp = E.project(inp, expected_contract=cfg["risk_role_contract"])
            passed = role == "current" or outcome["status"] == "WIN"
            record = actual_result(req, inp, value["base_arm"], passed, rid)
            obj = 10000 + rid
            objects[obj] = record
            requests[rid] = req
            pair["requests"][role] = rid
            owners.append(
                ("comparison", key, role, outcome["status"], "completed", obj, rid)
            )
            verdicts[role] = "PASS" if passed else "CAUTION"
        reuse.append(
            dict(
                opportunity_key=key,
                scope=sid,
                snapshot_obj=snapshot_obj,
                snapshot_sha256=P.digest(snap),
                current_registry=current["registry_sha256"],
                candidate_registry=candidate["registry_sha256"],
                raw_current_identity=requests[pair["requests"]["current"]][
                    "paired_replay_id"
                ],
                raw_current_request_sha256=P.digest(
                    requests[pair["requests"]["current"]]
                ),
                reused_candidate_request_id=pair["requests"]["candidate"],
                reused_candidate_request_sha256=P.digest(
                    requests[pair["requests"]["candidate"]]
                ),
                reused_candidate_result_obj=10000 + pair["requests"]["candidate"],
                reused_candidate_result_sha256=P.digest(
                    objects[10000 + pair["requests"]["candidate"]]
                ),
                reused_provider_response_id=objects[
                    10000 + pair["requests"]["candidate"]
                ]["result"]["provider_attempt_receipt"]["response_id"],
            )
        )
        pairs.append(pair)
        evaluated.append(dict(pair, verdicts=verdicts, excluded=[]))
    objects[999] = source_points
    campaign = P.seal(
        dict(
            parent_bundle_sha256=bundle["bundle_sha256"],
            source_date="2026-10-07",
            pairs=pairs,
            research={"experiment": "fixture"},
        )
    )
    objects[888] = {k: v for k, v in campaign.items() if k != "artifact_content_sha256"}
    campaign_path = tmp_path / "campaign.json"
    P.write(campaign_path, campaign)
    metrics = {
        role: T.matrix(
            [(p["outcome"]["status"], p["verdicts"][role]) for p in evaluated]
        )
        for role in ("current", "candidate")
    }
    evaluation = P.seal(
        dict(
            parent_bundle_sha256=bundle["bundle_sha256"],
            source_date="2026-10-07",
            campaign_path=str(campaign_path),
            pairs=evaluated,
            resolution_sha256="f" * 64,
            request_completion=True,
            comparison_complete=True,
            request_accounting_complete=True,
        )
    )
    ep = tmp_path / "evaluation.json"
    P.write(ep, evaluation)
    projection = P.seal(
        dict(
            source_parts=[
                dict(records_object=999, records_sha256=P.digest(source_points))
            ]
        )
    )
    pp = tmp_path / "projection.json"
    P.write(pp, projection)
    previous = P.seal(
        dict(source_projection_sha256=projection["artifact_content_sha256"])
    )
    previous_path = tmp_path / "previous.json"
    P.write(previous_path, previous)
    protocol = P.seal(
        dict(
            schema="auxiliary_direct_current_combined_protocol_v1",
            parent_bundle_sha256=bundle["bundle_sha256"],
            input_contract=cfg["risk_role_contract"],
            risk_role_roles=["candidate"],
            fixed_prepared_scope_proposals=[sid],
            bindings=bindings,
            rows=rows,
            candidate_reuse=reuse,
            previous_protocol_sha256=previous["artifact_content_sha256"],
            **P.AUTH,
        )
    )
    pr = tmp_path / "protocol.json"
    P.write(pr, protocol)
    analysis = P.seal(
        dict(
            protocol_sha256=protocol["artifact_content_sha256"],
            by_scope={sid: dict(metrics=metrics)},
            **P.AUTH,
        )
    )
    ap = tmp_path / "analysis.json"
    P.write(ap, analysis)
    report = P.seal(
        dict(
            schema=J.REPORT_SCHEMA,
            research_complete=True,
            observed_current_pointer={"bundle_sha256": bundle["bundle_sha256"]},
            selected_scopes=[sid],
            evaluations=[X.reference(ep)],
            direct_protocol=X.reference(pr),
            independent_analysis=X.reference(ap),
            previous_protocol=X.reference(previous_path),
            source_projection=X.reference(pp),
            **P.AUTH,
        )
    )
    rp = tmp_path / "report.json"
    P.write(rp, report)
    store_root = J.S.store_root(ledger)
    (store_root / "packs").mkdir(parents=True)
    (store_root / "metadata.sqlite3").write_bytes(b"fixture metadata identity")
    pack = store_root / "packs/fixture.pack"
    pack.write_bytes(b"fixture immutable object pack")

    class Cursor(list):
        def fetchone(self):
            return self[0] if self else None

    class Store:
        def __init__(self, root, *, readonly=False):
            assert readonly and Path(root) == ledger
            self.db = SimpleNamespace(execute=self.execute)

        def execute(self, sql, args=()):
            if sql == "BEGIN":
                return Cursor()
            if sql.startswith("SELECT descriptor_obj"):
                return Cursor([(888,)])
            if sql.startswith("SELECT DISTINCT pack"):
                return Cursor([("fixture.pack",)])
            if sql.startswith("SELECT id,hash"):
                return Cursor(
                    (
                        obj,
                        P.digest(objects[obj]),
                        "fixture.pack",
                        0,
                        len(json.dumps(objects[obj])),
                        len(json.dumps(objects[obj])),
                    )
                    for obj in args
                )
            if sql.startswith("SELECT id,identity"):
                by_rid = {row[6]: row for row in owners}
                return Cursor(
                    (
                        rid,
                        requests[rid]["paired_replay_id"],
                        0,
                        0,
                        0,
                        0,
                        by_rid[rid][4],
                        by_rid[rid][5],
                    )
                    for rid in args
                )
            if sql.startswith("SELECT generation,descriptor_obj"):
                return Cursor((gen, 888, len(owners)) for gen in args)
            raise AssertionError(sql)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def get(self, obj):
            return copy.deepcopy(objects[obj])

        def request(self, rid):
            return copy.deepcopy(requests[rid])

        def owners(self, generation):
            return copy.deepcopy(owners)

    monkeypatch.setattr(J.S, "Store", Store)
    monkeypatch.setattr(
        T, "load_campaign", lambda *a, **k: (campaign, None, campaign_path)
    )
    monkeypatch.setattr(T, "validate_campaign", lambda *a: copy.deepcopy(owners))
    monkeypatch.setattr(
        J, "evaluate_readonly", lambda *a, **k: (copy.deepcopy(evaluation), [None] * 3)
    )
    return SimpleNamespace(
        policy=policy,
        ledger=ledger,
        bundle=bundle,
        report=rp,
        sid=sid,
        objects=objects,
        requests=requests,
        owners=owners,
        campaign=campaign,
        evaluation=evaluation,
        analysis=analysis,
        analysis_path=ap,
        report_value=report,
        metrics=metrics,
        candidate=candidate,
        protocol=protocol,
        projection=projection,
        projection_path=pp,
    )


def prepare(f):
    return X.prepare(
        f.policy,
        f.report,
        f.bundle,
        ledger_data_root=f.ledger,
        operating_day="2026-10-19",
    )


def test_prepare_and_revalidation_reuse_original_objects_without_registration(
    prepared_input,
):
    f = prepared_input
    original = copy.deepcopy((f.objects, f.requests))
    registry_before = {
        str(p): p.read_bytes() for p in G.directory(f.policy).glob("*.json")
    }
    manifest = prepare(f)
    assert (
        manifest["schema"] == J.SCHEMA
        and manifest["verified_pairs"] == 50
        and manifest["verified_raw_responses"] == 100
    )
    assert set(manifest["changes"]) == {f.sid} and manifest[
        "base_bindings_sha256"
    ] == P.digest(f.protocol["bindings"])
    assert manifest["registry_registered"] is manifest["db_writer_used"] is False
    assert manifest["scopes"][f.sid]["metrics"] == f.metrics
    assert (f.objects, f.requests) == original
    assert registry_before == {
        str(p): p.read_bytes() for p in G.directory(f.policy).glob("*.json")
    }
    assert X.validate_manifest(f.policy, manifest, f.bundle) == manifest
    assert not (G.directory(f.policy) / (manifest["changes"][f.sid] + ".json")).exists()


@pytest.mark.parametrize(
    "defect", ["metric", "definition", "scope", "root", "code", "parent", "source"]
)
def test_resealed_manifest_mutations_fail_closed(prepared_input, defect):
    f = prepared_input
    m = prepare(f)
    bad = copy.deepcopy(m)
    if defect == "metric":
        bad["scopes"][f.sid]["metrics"]["candidate"]["TP"] += 1
    if defect == "definition":
        bad["registry_definitions"][bad["changes"][f.sid]]["prompt"] += "tampered"
    if defect == "scope":
        bad["changes"]["samsung|AFTER|ALL|SOR"] = bad["changes"][f.sid]
    if defect == "root":
        bad["policy_data_root"] = str(f.ledger)
    if defect == "code":
        bad["input_transition_code_hashes"][
            "reversal_auxiliary_input_transition.py"
        ] = ("0" * 64)
    if defect == "parent":
        bad["expected_parent"] = "0" * 64
    if defect == "source":
        bad["sources"][0]["sha256"] = "0" * 64
    with pytest.raises((ValueError, OSError)):
        X.validate_manifest(f.policy, P.seal(bad), f.bundle)


@pytest.mark.parametrize(
    "defect",
    [
        "receipt",
        "cached_result",
        "snapshot",
        "label",
        "source_ordinal",
        "source_object",
    ],
)
def test_original_source_and_raw_receipts_cannot_be_rewritten(prepared_input, defect):
    f = prepared_input
    if defect == "receipt":
        f.objects[11001]["result"]["provider_attempt_receipt"][
            "provider_output_bytes_sha256"
        ] = ("0" * 64)
    if defect == "cached_result":
        f.objects[11001]["result"]["provider_provenance"]["response_id"] = "changed"
    if defect == "snapshot":
        f.objects[1][0]["native_sequence"] += 100
    if defect == "label":
        f.campaign["pairs"][0]["outcome"] = {"status": "WIN"}
    if defect == "source_ordinal":
        value = copy.deepcopy(f.protocol)
        value["rows"][0]["source_records_ordinal"] = 49
        path = Path(f.report_value["direct_protocol"]["path"])
        P.write(path, P.seal(value))
        report = copy.deepcopy(f.report_value)
        report["direct_protocol"] = X.reference(path)
        P.write(f.report, P.seal(report))
    if defect == "source_object":
        f.objects[999][0]["outcome"] = {"status": "WIN"}
    with pytest.raises((ValueError, KeyError)):
        prepare(f)


def test_publish_requires_authority_and_parent_cas_before_registering(
    prepared_input, monkeypatch
):
    f = prepared_input
    m = prepare(f)
    writes = []
    monkeypatch.setattr(J, "register_definitions", lambda *a: writes.append(a))
    with pytest.raises(ValueError, match="authority_required"):
        X.publish(f.policy, m, confirm="invalid")
    monkeypatch.setattr(
        I, "current", lambda *a, **k: dict(artifact_content_sha256="f" * 64)
    )
    with pytest.raises(ValueError, match="parent_cas_failed"):
        X.publish(
            f.policy,
            m,
            confirm=I.AUTHORITY,
            now=datetime(2026, 10, 19, 8, tzinfo=I.K.KST),
        )
    assert not writes


def test_authorized_temporary_publish_registers_dependencies_and_stays_idempotent(
    prepared_input,
):
    f = prepared_input
    m = prepare(f)
    clock = datetime(2026, 10, 19, 8, tzinfo=I.K.KST)
    record = X.publish(f.policy, m, confirm=I.AUTHORITY, now=clock)
    assert record["bindings"][f.sid] == m["changes"][f.sid]
    assert X.publish(f.policy, m, confirm=I.AUTHORITY, now=clock) == record
    assert X.validate_published(f.policy, record, f.bundle) == m
    assert G.load(f.policy, m["changes"][f.sid])["production_input_contract"][
        "scope_ids"
    ] == [f.sid]
    assert (
        sum(
            record["bindings"][sid] != ident
            for sid, ident in f.protocol["bindings"].items()
        )
        == 1
    )


def test_empty_scope_request_is_not_a_publishable_manifest(prepared_input):
    f = prepared_input
    m = J.prepare(f.policy, f.report, f.bundle, scopes=[], ledger_data_root=f.ledger)
    assert m["status"] == "not_selected" and m["changes"] == {}
    with pytest.raises(ValueError, match="manifest_invalid"):
        X.validate_manifest(f.policy, m, f.bundle)


def test_source_gap_is_not_inherited_as_new_evidence(prepared_input):
    f = prepared_input
    value = list(f.owners[0])
    value[4] = "planned"
    f.owners[0] = tuple(value)
    with pytest.raises(ValueError, match="response_missing"):
        prepare(f)


def test_warm_verification_cache_skips_replay_and_rechecks_ledger_dependencies(
    prepared_input, monkeypatch
):
    f = prepared_input
    m = prepare(f)
    X.validate_manifest(f.policy, m, f.bundle)
    original = J._build
    calls = []

    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(J, "_build", counted)
    assert X.validate_manifest(f.policy, m, f.bundle) == m and not calls
    db = J.S.store_root(f.ledger) / "metadata.sqlite3"
    db.write_bytes(db.read_bytes() + b" changed")
    assert X.validate_manifest(f.policy, m, f.bundle) == m and not calls
    assert (
        X.validate_manifest(f.policy, m, f.bundle, cached_only=True) == m and not calls
    )
    pack = J.S.store_root(f.ledger) / "packs/fixture.pack"
    pack.write_bytes(pack.read_bytes() + b" changed")
    with pytest.raises(ValueError, match="cache_changed_before_publish"):
        X.validate_manifest(f.policy, m, f.bundle, cached_only=True)
    assert not calls


def test_publication_lock_dependency_change_fails_without_heavy_replay(
    prepared_input, monkeypatch
):
    f = prepared_input
    m = prepare(f)
    X.validate_manifest(f.policy, m, f.bundle)
    calls = []
    registrations = []
    monkeypatch.setattr(
        J, "_build", lambda *a, **k: pytest.fail("heavy replay under publisher lock")
    )
    monkeypatch.setattr(J, "register_definitions", lambda *a: registrations.append(a))
    original = X.fcntl.flock

    def locked(fd, operation):
        calls.append(1)
        if len(calls) == 2:
            db = J.S.store_root(f.ledger) / "metadata.sqlite3"
            db.write_bytes(db.read_bytes() + b" changed under lock")
        return original(fd, operation)

    monkeypatch.setattr(X.fcntl, "flock", locked)
    with pytest.raises(ValueError, match="cache_changed_before_publish"):
        X.publish(
            f.policy,
            m,
            confirm=I.AUTHORITY,
            now=datetime(2026, 10, 19, 8, tzinfo=I.K.KST),
        )
    assert len(calls) == 2 and not registrations


def test_label_and_analysis_resealing_cannot_replace_original_source(
    prepared_input, monkeypatch
):
    f = prepared_input
    f.campaign["pairs"][0]["outcome"] = {"status": "WIN"}
    evaluation = copy.deepcopy(f.evaluation)
    evaluation["pairs"][0]["outcome"] = {"status": "WIN"}
    evaluation = P.seal(evaluation)
    path = Path(f.report_value["evaluations"][0]["path"])
    P.write(path, evaluation)
    analysis = copy.deepcopy(f.analysis)
    analysis["by_scope"][f.sid]["metrics"]["current"]["TP"] += 1
    analysis = P.seal(analysis)
    P.write(f.analysis_path, analysis)
    report = copy.deepcopy(f.report_value)
    report["evaluations"] = [X.reference(path)]
    report["independent_analysis"] = X.reference(f.analysis_path)
    P.write(f.report, P.seal(report))
    monkeypatch.setattr(
        J, "evaluate_readonly", lambda *a, **k: (evaluation, [None] * 3)
    )
    with pytest.raises(ValueError, match="source_snapshot_or_label_changed"):
        prepare(f)


def test_snapshot_and_reused_hash_resealing_cannot_replace_original_source(
    prepared_input,
):
    f = prepared_input
    changed = copy.deepcopy(f.objects[1])
    changed[0]["native_sequence"] += 999
    f.objects[77777] = changed
    f.campaign["pairs"][0]["snapshot_obj"] = 77777
    protocol = copy.deepcopy(f.protocol)
    protocol["candidate_reuse"][0]["snapshot_obj"] = 77777
    protocol["candidate_reuse"][0]["snapshot_sha256"] = P.digest(changed)
    protocol = P.seal(protocol)
    path = Path(f.report_value["direct_protocol"]["path"])
    P.write(path, protocol)
    analysis = P.seal(
        dict(f.analysis, protocol_sha256=protocol["artifact_content_sha256"])
    )
    P.write(f.analysis_path, analysis)
    report = copy.deepcopy(f.report_value)
    report["direct_protocol"] = X.reference(path)
    report["independent_analysis"] = X.reference(f.analysis_path)
    P.write(f.report, P.seal(report))
    with pytest.raises(ValueError, match="source_snapshot_or_label_changed"):
        prepare(f)


def test_readonly_evaluator_uses_local_adapters_without_global_patches(
    tmp_path, monkeypatch
):
    entered = []

    class Store:
        def __init__(self, root, *, readonly=False):
            entered.append(readonly)
            assert readonly

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

    monkeypatch.setattr(S, "Store", Store)

    def evaluator(data_root, day, *, campaign_path=None):
        with S.Store(data_root):
            for i in range(3):
                P.write(Path(data_root) / str(i), {"value": i})
        return {"calculated": True}

    monkeypatch.setattr(T, "evaluate", evaluator)
    original_store = S.Store
    original_write = P.write
    result, writes = J.evaluate_readonly(tmp_path, "2026-10-07", campaign_path="unused")
    assert result == {"calculated": True} and len(writes) == 3 and entered == [True]
    assert S.Store is original_store and P.write is original_write
    assert list(tmp_path.iterdir()) == []


def test_warm_cache_tracks_canonical_baseline_source_and_compatibility_files(
    prepared_input, monkeypatch
):
    from src.engine.scalping import reversal_auxiliary_compatibility as C

    f = prepared_input
    source = (
        N.root(f.policy)
        / "sources"
        / (
            "reversal-"
            + f.bundle["continuous_reversal"]["auxiliary_report_sha256"]
            + ".json"
        )
    )
    P.write(
        source,
        P.seal(
            dict(
                auxiliary_registry_bindings=f.protocol["bindings"],
                auxiliary_reader_code_hashes={"old": "a" * 64},
            )
        ),
    )
    evidence = f.policy / "baseline-evidence.json"
    P.write(evidence, P.seal({"status": "pass"}))
    frozen = f.policy / "frozen-reader.py"
    frozen.write_text("historical_reader = True\n")
    receipt = dict(evidence_path=str(evidence), frozen_readers=[dict(path=str(frozen))])
    compatibility = C.path(f.policy, f.bundle, source, I.code_hashes())
    P.write(compatibility, P.seal(receipt))
    monkeypatch.setattr(C, "validate", lambda *args: receipt)
    m = prepare(f)
    X.validate_manifest(f.policy, m, f.bundle)
    expected = {str(source), str(evidence), str(frozen), str(compatibility)}
    assert expected <= {r["path"] for r in m["sources"]}
    evidence.unlink()
    with pytest.raises(OSError):
        X.validate_manifest(f.policy, m, f.bundle)


def test_non_improving_scopes_do_not_gain_a_publishable_manifest(
    prepared_input, monkeypatch
):
    f = prepared_input
    monkeypatch.setattr(T, "improves", lambda *args: False)
    m = prepare(f)
    assert (
        m["status"] == "not_selected"
        and m["changes"] == {}
        and m["registry_definitions"] == {}
    )
    assert m["unselected_scopes"][f.sid] == "same_point_pass_win_rate_not_improved"
    assert (
        not X.folder(f.policy).joinpath(m["artifact_content_sha256"] + ".json").exists()
    )


def test_selected_metadata_mutation_fails_without_full_replay(
    prepared_input, monkeypatch
):
    f = prepared_input
    m = prepare(f)
    X.validate_manifest(f.policy, m, f.bundle)
    monkeypatch.setattr(
        J, "_build", lambda *a, **k: pytest.fail("selected mutation must fail directly")
    )
    f.requests[1000]["paired_replay_id"] = "altered-request-identity"
    db = J.S.store_root(f.ledger) / "metadata.sqlite3"
    db.write_bytes(db.read_bytes() + b" selected metadata changed")
    with pytest.raises(ValueError, match="selected_ledger_metadata_changed"):
        X.validate_manifest(f.policy, m, f.bundle)


def test_continuous_unrelated_writes_do_not_block_or_misattribute_snapshot(
    prepared_input, monkeypatch
):
    f = prepared_input
    m = prepare(f)
    X.validate_manifest(f.policy, m, f.bundle)
    monkeypatch.setattr(
        J, "_build", lambda *a, **k: pytest.fail("unrelated inserts must not replay")
    )
    before = copy.deepcopy(J._VERIFIED)
    counter = [0]

    def changed(_):
        counter[0] += 1
        return ("unrelated-insert", counter[0])

    monkeypatch.setattr(J, "_database_signature", changed)
    for _ in range(3):
        assert X.validate_manifest(f.policy, m, f.bundle) == m
    assert counter[0] == 9 and J._VERIFIED == before


def test_cold_semantic_proof_survives_volatile_budget_resolution_metadata(
    prepared_input, monkeypatch
):
    f = prepared_input
    m = prepare(f)
    changed = P.seal(
        dict(
            f.evaluation,
            resolution_sha256="e" * 64,
            policy_generation={"new_runtime_metadata": True},
        )
    )
    monkeypatch.setattr(J, "evaluate_readonly", lambda *a, **k: (changed, [None] * 3))
    J._VERIFIED.clear()
    assert X.validate_manifest(f.policy, m, f.bundle) == m


def test_warm_cache_preserves_baseline_symlink_identity(prepared_input):
    f = prepared_input
    source = (
        N.root(f.policy)
        / "sources"
        / (
            "reversal-"
            + f.bundle["continuous_reversal"]["auxiliary_report_sha256"]
            + ".json"
        )
    )
    first = f.policy / "baseline-one.json"
    second = f.policy / "baseline-two.json"
    value = P.seal(
        dict(
            auxiliary_registry_bindings=f.protocol["bindings"],
            auxiliary_reader_code_hashes=I.code_hashes(),
        )
    )
    P.write(first, value)
    P.write(second, value)
    source.parent.mkdir(parents=True, exist_ok=True)
    source.symlink_to(first)
    m = prepare(f)
    X.validate_manifest(f.policy, m, f.bundle)
    assert str(source) in m["baseline_dependency_paths"]
    source.unlink()
    source.symlink_to(second)
    with pytest.raises(ValueError):
        X.validate_manifest(f.policy, m, f.bundle)


def test_real_sqlite_fingerprint_snapshot_ignores_unrelated_insert_and_detects_selected_change(
    tmp_path,
):
    request = dict(
        paired_replay_id="selected-fixture",
        candidate_input={"observed": 1},
        candidate={"model": "fixture"},
        control={},
        stage="entry",
    )
    with S.Store(tmp_path) as st:
        rid, _ = st.add_request(request)
        result = st.put({"actual_result": "fixture"})
        st.db.execute(
            "UPDATE requests SET state='completed',result_obj=? WHERE id=?",
            (result, rid),
        )
        member = st.add_member("comparison", "point", "current", rid, "WIN")
        st.bind_generation(
            "fixture-generation", {"group": [member]}, {"descriptor": "fixture"}, 1
        )
    with S.Store(tmp_path, readonly=True) as st:
        ids = [r[0] for r in st.db.execute("SELECT id FROM objects ORDER BY id")]
        metadata = dict(
            object_ids=ids, request_ids=[rid], generations=["fixture-generation"]
        )
        st.db.execute("BEGIN")
        expected = J._ledger_fingerprint(st, metadata)
        with S.Store(tmp_path) as writer:
            writer.add_request(dict(request, paired_replay_id="unrelated-fixture"))
        assert J._ledger_fingerprint(st, metadata) == expected
    with S.Store(tmp_path, readonly=True) as st:
        assert J._ledger_fingerprint(st, metadata) == expected
    with S.Store(tmp_path) as writer:
        writer.db.execute("UPDATE requests SET state='failed' WHERE id=?", (rid,))
    with S.Store(tmp_path, readonly=True) as st:
        assert J._ledger_fingerprint(st, metadata) != expected


def test_warm_cache_keeps_the_read_research_allowance_receipt(prepared_input):
    f = prepared_input
    m = prepare(f)
    X.validate_manifest(f.policy, m, f.bundle)
    grant = R.root(f.ledger) / "allowance.json"
    assert str(grant) in {ref["path"] for ref in m["sources"]}
    grant.unlink()
    with pytest.raises(OSError):
        X.validate_manifest(f.policy, m, f.bundle)


def test_inherited_registry_parent_closure_is_identical_after_reader_cache_warms(
    prepared_input, monkeypatch
):
    f = prepared_input
    parent = G.load(f.ledger, f.candidate["research_registry_sha256"])
    G.register(f.policy, parent)
    G.register(f.policy, f.candidate)
    inherited = {sid: f.candidate["registry_sha256"] for sid in f.protocol["bindings"]}
    source = (
        N.root(f.policy)
        / "sources"
        / (
            "reversal-"
            + f.bundle["continuous_reversal"]["auxiliary_report_sha256"]
            + ".json"
        )
    )
    P.write(
        source,
        P.seal(
            dict(
                auxiliary_registry_bindings=inherited,
                auxiliary_reader_code_hashes=I.code_hashes(),
            )
        ),
    )
    overlay = P.seal(
        dict(
            schema=I.SCHEMA,
            authority=I.AUTHORITY,
            day="2026-10-19",
            effective_from="2026-10-19T07:00:00+09:00",
            base_bundle_sha256=f.bundle["bundle_sha256"],
            base_family_sha256=f.bundle["continuous_reversal"]["family_sha256"],
            detector_manifest_hash="d" * 64,
            bindings=f.protocol["bindings"],
            code_hashes=I.code_hashes(),
        )
    )
    P.write(
        I.root(f.policy)
        / "generations"
        / (overlay["artifact_content_sha256"] + ".json"),
        overlay,
    )
    P.write(I.root(f.policy) / "current.json", overlay)
    calls = [0]

    def cached_inherited(*args):
        calls[0] += 1
        if calls[0] == 1:
            G.load(f.policy, f.candidate["registry_sha256"])
        return inherited

    monkeypatch.setattr(I, "inherited", cached_inherited)
    manifest = prepare(f)
    assert (
        str(G.directory(f.policy) / (parent["registry_sha256"] + ".json"))
        in manifest["baseline_dependency_paths"]
    )
    J._VERIFIED.clear()
    assert (
        X.validate_manifest(f.policy, manifest, f.bundle) == manifest and calls[0] >= 2
    )
