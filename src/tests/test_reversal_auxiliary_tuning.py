"""Real shared-store comparisons and auxiliary-only handoff boundaries."""

import copy
import json
from datetime import datetime
import pytest
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_tuning as T
from src.engine.scalping import reversal_auxiliary_intraday as I
from src.engine.scalping import continuous_reversal_policy_v5 as V
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_operating_runtime as R
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.ai import offline_comparison_store as S
from src.tests.test_reversal_operating_policy import (
    parent,
    replay,
    transport,
    authorize_initial,
    PC,
)
from src.tests.test_continuous_reversal_policy_v3 import native


@pytest.fixture
def setup(replay, monkeypatch):
    root, parent, machine = replay
    PC.prepare_inputs(root, "2026-10-07", machine, parent)
    PC.L.calls(PC, root, "2026-10-07", transport=transport, call_limit=5)
    authorize_initial(root, parent)
    aux = PC.auxiliary_report(
        root, "2026-10-07", "2026-10-07", parent, publish_policy=False
    )
    issued = json.loads((PC.directory(root, "2026-10-07") / "machine.json").read_text())
    b = V.stage(
        root,
        "2026-10-07",
        "2026-10-07",
        issued,
        aux,
        target_date="2026-10-08",
        release_commit="a" * 40,
    )
    # Freeze a new evaluation against the now-authorized actual machine list.
    machine = P.seal(
        dict(
            machine,
            parent_bundle_sha256=b["bundle_sha256"],
            operating_manifest=b["continuous_reversal"]["operating_manifest"],
        )
    )
    P.write(PC.directory(root, "2026-10-07") / "machine-comparison.json", machine)
    monkeypatch.setattr(N, "load_effective", lambda **kw: b)
    sid = "samsung|REGULAR|ALL|SOR"
    value = G.definition(
        G.A.V1.ARMS[-1],
        prompt=G.A.PROMPT
        + "Use observed adverse evidence, not a compulsory new confirmation.\n",
        hypothesis="Context is not observed failure",
    )
    ident = G.register(root, value)
    T.configure(root, candidate=ident, scopes=[sid], seed="fixed-test", max_pairs=50)
    return root, b, machine, sid, value


def test_registry_immutable_ascii_and_historical_request_parity(setup):
    root, b, m, sid, v = setup
    with S.Store(root) as store:
        p = store.get(m["partitions"][0]["records_object"])[0]
        snap = store.get(p["snapshot_obj"])
    for arm in G.A.V1.ARMS:
        old = G.definition(arm)
        assert G.request(snap, old) == PC.request(snap, arm)
    bad = dict(v, prompt="잘못된 문구")
    bad["registry_sha256"] = P.digest(
        {k: x for k, x in bad.items() if k != "registry_sha256"}
    )
    with pytest.raises(ValueError):
        G.register(root, bad)
    with pytest.raises(ValueError):
        G.load(root, "../x")


def test_explicit_input_rebind_preserves_prompt_scope_and_budget(setup):
    root, b, m, sid, v = setup
    from src.engine.scalping import reversal_extended_union as E

    original = T.config(root)
    with S.Store(root) as store:
        store.db.execute(
            "INSERT INTO attempt_budgets VALUES(?,?)",
            ("already-spent", "postclose_auxiliary:2026-10-07"),
        )
        store.commit()
        budget_before = store.db.execute(
            "SELECT * FROM attempt_budgets ORDER BY 1,2"
        ).fetchall()
    receipt = T.rebind_candidate_input(
        root,
        input_version=E.VERSION,
        expected_config_sha256=original["artifact_content_sha256"],
    )
    updated = T.config(root)
    replacement = G.load(root, updated["candidate_registry"])
    assert replacement["input_version"] == E.VERSION
    for key in ("prompt", "hypothesis", "development_keys", "base_arm"):
        assert replacement[key] == v[key]
    for key in ("scopes", "seed", "max_pairs"):
        assert updated[key] == original[key]
    assert G.load(root, v["registry_sha256"]) == v
    assert receipt["budget_reset"] is receipt["live_policy_changed"] is False
    assert receipt["runtime_effect"] is receipt["allowed_runtime_apply"] is False
    with S.Store(root) as store:
        assert (
            store.db.execute("SELECT * FROM attempt_budgets ORDER BY 1,2").fetchall()
            == budget_before
        )
    with pytest.raises(ValueError, match="parent_changed"):
        T.rebind_candidate_input(
            root,
            input_version=E.VERSION,
            expected_config_sha256=original["artifact_content_sha256"],
        )


def test_input_rebind_rejects_different_prompt_contract(setup, monkeypatch):
    root, b, m, sid, v = setup
    from src.engine.scalping import reversal_extended_union as E

    original = T.config(root)
    monkeypatch.setattr(E, "PROMPT", E.PROMPT + "Changed shared rule.\n")
    with pytest.raises(ValueError, match="rebind_unsupported"):
        T.rebind_candidate_input(
            root,
            input_version=E.VERSION,
            expected_config_sha256=original["artifact_content_sha256"],
        )
    assert T.config(root) == original


def test_prepare_reuses_shared_requests_and_ignores_unrelated_arms(setup):
    root, b, m, sid, v = setup
    c = T.prepare(root, "2026-10-07", m, b)
    assert (
        c["expected_pairs"] > 0
        and c["expected_owner_requests"] == 2 * c["expected_pairs"]
    )
    with S.Store(root) as store:
        count = store.db.execute("SELECT count(*) FROM requests").fetchone()[0]
    assert T.prepare(root, "2026-10-07", m, b) == c
    with S.Store(root) as store:
        assert store.db.execute("SELECT count(*) FROM requests").fetchone()[0] == count
    T.calls(root, "2026-10-07", transport=transport)
    result = T.evaluate(root, "2026-10-07")
    assert (
        result["paired_metrics_ready"]
        and result["scopes"][sid]["paired_points"] == c["expected_pairs"]
    )
    assert result["scopes"][sid]["current"]["pass_win_rate"] == 1
    assert not result["scopes"][sid]["improved"]
    assert (
        T.calls(
            root, "2026-10-07", transport=lambda *a, **k: pytest.fail("cache called")
        )["new_calls"]
        == 0
    )


def test_zero_budget_has_no_transport_and_no_false_winrate(setup):
    root, b, m, sid, v = setup
    c = T.prepare(root, "2026-10-07", m, b)
    with S.Store(root) as store:
        for i in range(100):
            store.db.execute(
                "INSERT OR IGNORE INTO attempt_budgets VALUES(?,?)",
                ("spent-" + str(i), "postclose_auxiliary:2026-10-07"),
            )
        store.commit()
    assert (
        T.calls(
            root, "2026-10-07", transport=lambda *a, **kw: pytest.fail("over budget")
        )["new_calls"]
        == 0
    )
    result = T.evaluate(root, "2026-10-07")
    assert result["scopes"][sid]["candidate"]["pass_win_rate"] is None
    assert not result["scopes"][sid]["improved"]
    # A later evaluation date does not replenish the old observations' budget.
    next_machine = P.seal(
        dict(m, source_date="2026-10-08", publication_date="2026-10-08")
    )
    T.prepare(root, "2026-10-08", next_machine, b)
    later = T.calls(
        root, "2026-10-08", transport=lambda *a, **kw: pytest.fail("old source reset")
    )
    assert later["new_calls"] == 0
    # A cached old-date attempt is not a new-date call just because it ran
    # after midnight. Its original cap still prevents retrying old requests.
    assert later["call_budget"]["used_after"] == 0


def test_cumulative_marker_cannot_authorize_unregistered_machine_membership(setup):
    root, b, m, sid, _ = setup
    changed = copy.deepcopy(m)
    changed["operating_manifest"]["scopes"][sid] = []
    changed = P.seal(dict(changed, cumulative_selection={sid: {"status": "selected"}}))
    with pytest.raises(ValueError, match="cumulative_selection_authority_missing"):
        T.prepare(root, "2026-10-07", changed, b)
    assert not (T.directory(root, "2026-10-07") / "latest-campaign.json").exists()


def test_later_evaluation_charges_both_dates_without_repeating_calls(setup):
    root, b, m, sid, v = setup
    next_machine = P.seal(
        dict(m, source_date="2026-10-08", publication_date="2026-10-08")
    )
    campaign = T.prepare(root, "2026-10-08", next_machine, b)
    assert campaign["expected_pairs"] > 0
    result = T.calls(root, "2026-10-08", transport=transport)
    assert result["new_calls"] > 0
    assert result["call_budget"]["used_after"] >= result["new_calls"]
    assert (
        result["observation_date_budgets"]["postclose_auxiliary:2026-10-07"]
        >= result["new_calls"]
    )
    assert T.evaluate(root, "2026-10-08")["paired_metrics_ready"]
    cached = T.calls(
        root,
        "2026-10-08",
        transport=lambda *a, **kw: pytest.fail("repeated completed call"),
    )
    assert cached["new_calls"] == 0
    assert cached["call_budget"]["used_after"] == result["call_budget"]["used_after"]
    assert cached["observation_date_budgets"] == result["observation_date_budgets"]


def test_sampling_ignores_label_and_excludes_development(setup):
    root, b, m, sid, v = setup
    c = T.prepare(root, "2026-10-07", m, b)
    with S.Store(root) as store:
        revised = copy.deepcopy(m)
        for part in revised["partitions"]:
            points = store.get(part["records_object"])
            for p in points:
                p["outcome"] = {"status": "FAIL_TIMEOUT"}
            part["records_object"] = store.put(points)
            part["records_sha256"] = P.digest(points)
        store.commit()
    revised = P.seal(revised)
    new = T.prepare(root, "2026-10-07", revised, b)
    assert new["selector"]["selected_keys"] == c["selector"]["selected_keys"]
    assert all(p["outcome"]["status"] == "FAIL_TIMEOUT" for p in new["pairs"])


def test_pair_corruption_rejected_before_calls(setup):
    root, b, m, _, _ = setup
    c = T.prepare(root, "2026-10-07", m, b)
    with S.Store(root) as store:
        row = next(iter(store.owners(c["artifact_content_sha256"])))
        store.db.execute(
            "UPDATE members SET outcome=? WHERE id=?", ("FAIL_STOP", row[7])
        )
        store.commit()
    with pytest.raises(ValueError, match="membership"):
        T.calls(
            root, "2026-10-07", transport=lambda *a, **kw: pytest.fail("corrupt pair")
        )


def test_metrics_and_all_blocked_null():
    a = T.matrix([("WIN", "PASS"), ("FAIL_STOP", "PASS"), ("WIN", "VETO")])
    b = T.matrix([("WIN", "PASS"), ("FAIL_STOP", "VETO"), ("WIN", "CAUTION")])
    assert a["TP"] == 1 and a["FP"] == 1 and a["FN"] == 1 and a["TN"] == 0
    assert T.improves(a, b)
    assert not T.improves(a, T.matrix([("WIN", "VETO")]))
    assert T.matrix([])["pass_win_rate"] is None


def overlay(root, b, bindings, at, previous=None):
    record = P.seal(
        dict(
            schema=I.SCHEMA,
            authority=I.AUTHORITY,
            day=at.date().isoformat(),
            effective_from=at.isoformat(),
            base_bundle_sha256=b["bundle_sha256"],
            base_family_sha256=b["continuous_reversal"]["family_sha256"],
            detector_manifest_hash=b["continuous_reversal"]["operating_manifest"][
                "detector_manifest_hash"
            ],
            previous_overlay_sha256=previous,
            bindings=bindings,
            code_hashes=I.code_hashes(),
            revoked_overlays=[],
        )
    )
    P.write(
        I.root(root) / "generations" / (record["artifact_content_sha256"] + ".json"),
        record,
    )
    P.write(I.root(root) / "current.json", record)
    return record


def test_overlay_uses_signal_clock_preserves_machine_and_old_requests(setup):
    root, b, m, sid, v = setup
    c = T.prepare(root, "2026-10-07", m, b)
    with S.Store(root) as store:
        snap = store.get(c["pairs"][0]["snapshot_obj"])
    epoch = snap[0]["epoch"]
    at = datetime.fromtimestamp(epoch - 1, I.K.KST)
    baseline = V.assess(
        b["continuous_reversal"],
        snap,
        symbol=snap[0]["symbol"],
        session=snap[0]["market"],
    )
    family_before = copy.deepcopy(b["continuous_reversal"])
    states_before = dict(R._STATES)
    ordinary = G.definition(
        b["continuous_reversal"]["auxiliary_cells"][baseline[0]["cell_key"]]["routes"][
            baseline[0]["route"]
        ]["payload"]["arm"]
    )
    G.register(root, ordinary)
    overlay(root, b, {sid: ordinary["registry_sha256"]}, at)
    assert I.apply_request(root, b, snap, baseline) == baseline
    first = overlay(root, b, {sid: v["registry_sha256"]}, at)
    updated = I.apply_request(
        root,
        dict(
            continuous_reversal=b["continuous_reversal"],
            machine_bundle_sha256=b["bundle_sha256"],
        ),
        snap,
        baseline,
    )
    assert (
        updated[2] == v["prompt"]
        and updated[0]["scope_execution_hash"] == baseline[0]["scope_execution_hash"]
    )
    assert b["continuous_reversal"] == family_before and R._STATES == states_before
    policy = dict(continuous_reversal_assessment=updated[0])
    I.validate_decision(root, policy, b, now=epoch + 1)
    next_value = G.definition(
        v["base_arm"], prompt=v["prompt"] + "Do not invent future evidence.\n"
    )
    G.register(root, next_value)
    overlay(
        root,
        b,
        {sid: next_value["registry_sha256"]},
        datetime.fromtimestamp(epoch + 2, I.K.KST),
        first["artifact_content_sha256"],
    )
    I.validate_decision(root, policy, b, now=epoch + 3)
    I.validate_submit(
        root, dict(entry_mechanistic_policy_decision=updated[0]), now=epoch + 3
    )
    with pytest.raises(ValueError):
        I.validate_decision(root, policy, b, now=epoch + 6)
    with pytest.raises(ValueError):
        I.validate_submit(
            root, dict(entry_mechanistic_policy_decision=updated[0]), now=epoch + 6
        )
    latest = I.read(I.root(root) / "current.json")
    latest = P.seal(dict(latest, revoked_overlays=[first["artifact_content_sha256"]]))
    P.write(I.root(root) / "current.json", latest)
    with pytest.raises(ValueError, match="revoked"):
        I.validate_submit(
            root, dict(entry_mechanistic_policy_decision=updated[0]), now=epoch + 3
        )


def test_next_session_carries_effective_registered_prompt(setup, monkeypatch):
    root, b, m, sid, v = setup
    at = datetime(2026, 10, 7, 12, tzinfo=I.K.KST)
    overlay(root, b, {sid: v["registry_sha256"]}, at)
    T.prepare(root, "2026-10-07", m, b)
    result = T.auxiliary_report(
        root, "2026-10-07", "2026-10-07", b, publish_policy=False
    )
    assert result["auxiliary_registry_bindings"][sid] == v["registry_sha256"]
    assert result["scope_census"]["new_ready"] == 128
    issued = json.loads((PC.directory(root, "2026-10-07") / "machine.json").read_text())
    monkeypatch.setattr(V.V4, "transition_parent", lambda *a: b)
    next_bundle = V.stage(
        root,
        "2026-10-07",
        "2026-10-07",
        issued,
        result,
        target_date="2026-10-08",
        release_commit="a" * 40,
    )
    assert I.inherited(root, next_bundle)[sid] == v["registry_sha256"]
    V.validate_sources(next_bundle, root)


def test_publish_requires_improvement_parent_and_preserves_initial_list(
    setup, monkeypatch
):
    root, b, m, sid, v = setup
    T.prepare(root, "2026-10-07", m, b)
    actual = T.evaluate(root, "2026-10-07")
    path = T.directory(root, "2026-10-07") / "evaluation.json"
    clock = datetime(2026, 10, 8, 10, tzinfo=I.K.KST)
    assert (
        I.publish(root, path, expected_parent=None, confirm=I.AUTHORITY, now=clock)[
            "status"
        ]
        == "incumbent_kept"
    )
    report = copy.deepcopy(actual)
    report["scopes"][sid].update(
        improved=True,
        current=T.matrix([("WIN", "PASS"), ("FAIL_STOP", "PASS")]),
        candidate=T.matrix([("WIN", "PASS"), ("FAIL_STOP", "VETO")]),
    )
    report = P.seal(report)
    P.write(path, report)
    P.write(
        T.directory(root, "2026-10-07")
        / "evaluations"
        / (report["artifact_content_sha256"] + ".json"),
        report,
    )
    monkeypatch.setattr(
        T, "evaluate", lambda *a: report
    )  # Publisher unit: reducer is tested independently.
    machine_before = copy.deepcopy(b["continuous_reversal"]["machine_cells"])
    with pytest.raises(ValueError, match="parent_cas"):
        I.publish(root, path, expected_parent="f" * 64, confirm=I.AUTHORITY, now=clock)
    result = I.publish(root, path, expected_parent=None, confirm=I.AUTHORITY, now=clock)
    assert result["changes"][sid] == v["registry_sha256"]
    assert (
        I.publish(root, path, expected_parent=None, confirm=I.AUTHORITY, now=clock)
        == result
    )
    assert b["continuous_reversal"]["machine_cells"] == machine_before
    rolled = I.rollback(
        root,
        expected_parent=result["artifact_content_sha256"],
        reason="contract failure",
        confirm=I.AUTHORITY,
        now=clock,
    )
    assert result["artifact_content_sha256"] in rolled["revoked_overlays"]
    assert rolled["bindings"][sid] != v["registry_sha256"]


def test_sampled_failure_does_not_reopen_initial_machine_adoption(setup):
    root, b, m, sid, v = setup
    manifest = copy.deepcopy(b["continuous_reversal"]["operating_manifest"])
    T.prepare(root, "2026-10-07", m, b)
    result = T.auxiliary_report(
        root, "2026-10-07", "2026-10-07", b, publish_policy=False
    )
    assert result["comparison_complete"] is False
    issued = json.loads((PC.directory(root, "2026-10-07") / "machine.json").read_text())
    assert issued["operating_manifest"] == manifest
    assert result["scope_census"]["new_ready"] == 128 and result["scope_pending"] == []


@pytest.mark.parametrize("change", ["latest", "canonical", "evaluation"])
def test_auxiliary_publication_keeps_exact_verified_campaign(
    setup, monkeypatch, change
):
    root, parent, machine, _, _ = setup
    day = "2026-10-07"
    first = T.prepare(root, day, machine, parent)
    successor = T.prepare(
        root, day, P.seal(dict(machine, source_revision="new_generation")), parent
    )
    latest = T.directory(root, day) / "latest-campaign.json"
    P.write(latest, first)
    original = T.evaluate

    def changed_pointer(data_root, source_day, *, campaign_path=None):
        # Another producer may advance latest after publication admission.
        P.write(latest, successor)
        if change == "canonical":
            P.write(
                T.directory(root, day)
                / "campaigns"
                / (first["artifact_content_sha256"] + ".json"),
                successor,
            )
        result = original(data_root, source_day, campaign_path=campaign_path)
        if change == "evaluation":
            result = P.seal(
                dict(result, campaign_sha256=successor["artifact_content_sha256"])
            )
        return result

    monkeypatch.setattr(T, "evaluate", changed_pointer)
    output = PC.directory(root, day) / "auxiliary.json"
    before = output.read_bytes()
    if change != "latest":
        with pytest.raises(ValueError, match="auxiliary_tuning_generation_changed"):
            T.auxiliary_report(root, day, day, parent, publish_policy=False)
        assert output.read_bytes() == before
        return
    report = T.auxiliary_report(root, day, day, parent, publish_policy=False)
    evaluation = T.read(report["source_receipts"][0]["path"])
    assert evaluation["campaign_sha256"] == first["artifact_content_sha256"]
    assert report["resolution_sha256"] == evaluation["resolution_sha256"]
    assert T.read(latest) == successor
    assert report["runtime_effect"] is False
    assert report["actual_order_submitted"] is False


@pytest.mark.parametrize("defect", ["missing", "date", "parent", "machine"])
def test_auxiliary_publication_rejects_invalid_campaign_before_evaluation(
    setup, monkeypatch, defect
):
    root, parent, machine, _, _ = setup
    day = "2026-10-07"
    campaign = T.prepare(root, day, machine, parent)
    out = T.directory(root, day)
    if defect == "missing":
        (out / "campaigns" / (campaign["artifact_content_sha256"] + ".json")).unlink()
    else:
        field = {
            "date": "source_date",
            "parent": "parent_bundle_sha256",
            "machine": "machine_report_sha256",
        }[defect]
        campaign = P.seal(
            dict(campaign, **{field: "2026-10-08" if defect == "date" else "f" * 64})
        )
        P.write(out / "latest-campaign.json", campaign)
        P.write(
            out / "campaigns" / (campaign["artifact_content_sha256"] + ".json"),
            campaign,
        )
    monkeypatch.setattr(
        T, "evaluate", lambda *a, **kw: pytest.fail("invalid admission")
    )
    output = PC.directory(root, day) / "auxiliary.json"
    before = output.read_bytes()
    with pytest.raises(FileNotFoundError if defect == "missing" else ValueError):
        T.auxiliary_report(root, day, day, parent, publish_policy=False)
    assert output.read_bytes() == before


def test_configured_calls_never_fall_back_to_legacy_full_queue(setup, monkeypatch):
    root, b, m, sid, v = setup
    monkeypatch.setattr(
        PC.L, "calls", lambda *a, **kw: pytest.fail("legacy full queue")
    )
    with pytest.raises(FileNotFoundError):
        PC.calls(root, "2026-10-07", transport=transport)


def test_registered_live_provider_payload_matches_offline_contract(setup, monkeypatch):
    from types import SimpleNamespace
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine import ai_engine_openai as E
    from src.utils import constants

    root, b, m, sid, v = setup
    monkeypatch.setattr(constants, "DATA_DIR", root)
    with S.Store(root) as store:
        point = store.get(m["partitions"][0]["records_object"])[0]
        snapshot = store.get(point["snapshot_obj"])
    offline = G.request(snapshot, v)
    candidate = offline["candidate"]
    calls = []
    engine = _build_engine()

    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            output_text=json.dumps(transport(offline, 30)["candidate_response"])
        )

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=create))
    metadata = {
        "entry_setup_live_policy_selected_prompt_version": G.binding(v)[
            "prompt_version"
        ],
        "entry_ai_role": "auxiliary_risk_screen_pass_veto_no_promotion",
    }
    engine._call_openai_safe(
        candidate["system_prompt"],
        json.dumps(
            offline["candidate_input"],
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ),
        model_override=candidate["model"],
        schema_name=E.ENTRY_RISK_ADJUDICATION_SCHEMA,
        endpoint_name="analyze_target",
        metadata_extra=metadata,
        transport_mode_override="http",
        response_schema_override=candidate["response_schema"],
        auxiliary_registry_sha256=v["registry_sha256"],
    )
    assert len(calls) == 1
    sent = calls[0]
    assert sent["instructions"] == candidate["system_prompt"]
    assert sent["input"] == json.dumps(
        offline["candidate_input"],
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert (
        sent["model"] == candidate["model"]
        and sent["max_output_tokens"] == candidate["max_output_tokens"]
    )
    assert sent["reasoning"] == {"effort": candidate["reasoning_effort"]}
    assert sent["text"]["format"]["schema"] == candidate["response_schema"]
    assert sent["text"]["format"]["name"] == candidate["schema_name"]
    assert "temperature" not in sent
    request = E.OpenAIResponseRequest(
        prompt=v["prompt"],
        user_input="{}",
        require_json=True,
        context_name="test",
        model_name=candidate["model"],
        temperature=None,
        max_output_tokens=1024,
        reasoning_effort="none",
        schema_name=E.ENTRY_RISK_ADJUDICATION_SCHEMA,
        endpoint_name="analyze_target",
        request_id="test",
        symbol="005930",
        cache_key="-",
        submitted_at_perf=0,
        timeout_ms=5000,
        metadata={"auxiliary_registry_sha256": v["registry_sha256"]},
    )
    with pytest.raises(ValueError, match="rewrite_forbidden"):
        engine._build_invalid_prompt_retry_request(request)


def test_terminal_source_resolution_preserves_campaign_and_durable_budget(setup):
    root, b, m, sid, v = setup
    revised = copy.deepcopy(m)
    with S.Store(root) as store:
        for part in revised["partitions"]:
            points = copy.deepcopy(store.get(part["records_object"]))
            eligible = [p for p in points if p["scope"] == sid]
            if len(eligible) > 1:
                eligible[0]["outcome"] = {
                    "status": "SOURCE_GAP",
                    "reason": "path_end_before_horizon",
                }
            part["records_object"] = store.put(points)
            part["records_sha256"] = P.digest(points)
    revised = P.seal(revised)
    campaign = T.prepare(root, "2026-10-07", revised, b)
    before = (T.directory(root, "2026-10-07") / "latest-campaign.json").read_bytes()
    T.calls(root, "2026-10-07", transport=transport)
    with S.Store(root) as store:
        spent = store.db.execute(
            "SELECT * FROM attempt_budgets ORDER BY 1,2"
        ).fetchall()
    result = T.evaluate(root, "2026-10-07")
    revision = json.loads(
        (
            T.directory(root, "2026-10-07")
            / "resolutions"
            / (result["resolution_sha256"] + ".json")
        ).read_text()
    )
    dead = [
        r for r in revision["rows"] if r["label_state"] == "irrecoverable_frozen_source"
    ]
    assert dead and all(
        s in {"completed", "excluded_before_attempt"}
        for r in dead
        for s in r["request_accounting"].values()
    )
    assert result["request_accounting_complete"] and result["comparison_complete"]
    assert (
        T.calls(
            root,
            "2026-10-07",
            transport=lambda *a, **kw: pytest.fail(
                "terminal campaign recalled provider"
            ),
        )["new_calls"]
        == 0
    )
    assert (
        T.evaluate(root, "2026-10-07")["artifact_content_sha256"]
        == result["artifact_content_sha256"]
    )
    with S.Store(root) as store:
        assert (
            store.db.execute("SELECT * FROM attempt_budgets ORDER BY 1,2").fetchall()
            == spent
        )
    assert (
        T.directory(root, "2026-10-07") / "latest-campaign.json"
    ).read_bytes() == before


def _prepare_common_contract_repair(setup):
    root, bundle, machine, scope, value = setup
    N._atomic_write_json(
        N.root(root) / "current.json", {"bundle_sha256": bundle["bundle_sha256"]}
    )
    # Register the unchanged selected defaults as normal bootstrap would do.
    I.effective_bindings(root, bundle, day="2026-10-08")
    now = datetime(2026, 10, 8, 10, 0, tzinfo=P.KST)
    manifest = I.prepare_contract_repair(root, bundle, expected_parent=None, now=now)
    return root, bundle, now, manifest


def test_common_support_repair_preparation_is_read_only_and_publication_is_exact(setup):
    root, bundle, now, manifest = _prepare_common_contract_repair(setup)
    before = {str(p): P.file_hash(p) for p in root.rglob("*.json")}
    assert (
        I.prepare_contract_repair(root, bundle, expected_parent=None, now=now)
        == manifest
    )
    assert before == {str(p): P.file_hash(p) for p in root.rglob("*.json")}
    pointer_before = (N.root(root) / "current.json").read_bytes()
    original = copy.deepcopy(bundle)
    overlay = I.publish_contract_repair(
        root,
        manifest,
        expected_parent=None,
        confirm=I.CONTRACT_REPAIR_AUTHORITY,
        now=now,
    )
    assert (
        bundle == original
        and (N.root(root) / "current.json").read_bytes() == pointer_before
    )
    assert set(overlay["bindings"]) == set(manifest["old_bindings"])
    assert (
        overlay["contract_repair_manifest_sha256"]
        == manifest["artifact_content_sha256"]
    )
    for old, new in manifest["registry_mapping"].items():
        previous = G.load(root, old)
        issued = G.load(root, new["registry_sha256"])
        assert issued["prompt"] == previous["prompt"] + I.COMMON_SUPPORT_CLARIFICATION
        assert {
            k: v for k, v in issued.items() if k not in {"prompt", "registry_sha256"}
        } == {
            k: v for k, v in previous.items() if k not in {"prompt", "registry_sha256"}
        }
    assert I.at_confirmation(root, bundle, now.timestamp() - 0.001) is None
    assert I.at_confirmation(root, bundle, now.timestamp()) == overlay
    assert (
        I.publish_contract_repair(
            root,
            manifest,
            expected_parent=None,
            confirm=I.CONTRACT_REPAIR_AUTHORITY,
            now=now,
        )
        == overlay
    )


@pytest.mark.parametrize(
    "defect", ["prompt", "model", "scope", "source", "parent", "authority"]
)
def test_common_support_repair_rejects_changed_preparation_before_pointer_write(
    setup, defect
):
    root, bundle, now, manifest = _prepare_common_contract_repair(setup)
    candidate = copy.deepcopy(manifest)
    if defect in {"prompt", "model"}:
        first = next(iter(candidate["registry_mapping"].values()))
        first["prompt" if defect == "prompt" else "model"] = "changed"
    elif defect == "scope":
        candidate["new_bindings"].pop(next(iter(candidate["new_bindings"])))
    elif defect == "source":
        candidate["source_hashes"][next(iter(candidate["source_hashes"]))] = "0" * 64
    elif defect == "parent":
        candidate["expected_parent"] = "0" * 64
    elif defect == "authority":
        candidate["authority"] = I.AUTHORITY
    candidate = P.seal(candidate)
    with pytest.raises(ValueError):
        I.publish_contract_repair(
            root,
            candidate,
            expected_parent=None,
            confirm=I.CONTRACT_REPAIR_AUTHORITY,
            now=now,
        )
    assert not (I.root(root) / "current.json").exists()


def test_published_common_support_repair_rejects_tampered_overlay(setup):
    root, bundle, now, manifest = _prepare_common_contract_repair(setup)
    overlay = I.publish_contract_repair(
        root,
        manifest,
        expected_parent=None,
        confirm=I.CONTRACT_REPAIR_AUTHORITY,
        now=now,
    )
    modified = copy.deepcopy(overlay)
    modified["bindings"][next(iter(modified["bindings"]))] = next(
        iter(manifest["old_bindings"].values())
    )
    with pytest.raises(ValueError, match="contract_repair_overlay_changed"):
        I.validate_record(root, P.seal(modified), bundle)


def test_common_support_repair_rollback_restores_old_bindings_and_revokes_claim_generation(
    setup,
):
    from datetime import timedelta

    root, bundle, now, manifest = _prepare_common_contract_repair(setup)
    overlay = I.publish_contract_repair(
        root,
        manifest,
        expected_parent=None,
        confirm=I.CONTRACT_REPAIR_AUTHORITY,
        now=now,
    )
    original_file = (
        I.root(root) / "generations" / (overlay["artifact_content_sha256"] + ".json")
    )
    original_bytes = original_file.read_bytes()
    rolled = I.rollback(
        root,
        expected_parent=overlay["artifact_content_sha256"],
        reason="reviewed contract repair rollback",
        confirm=I.AUTHORITY,
        now=now + timedelta(seconds=2),
    )
    assert rolled["bindings"] == manifest["old_bindings"]
    assert "contract_repair_manifest_sha256" not in rolled
    assert "contract_repair_authority" not in rolled
    assert (
        rolled["rollback_contract_repair_manifest_sha256"]
        == manifest["artifact_content_sha256"]
    )
    assert overlay["artifact_content_sha256"] in rolled["revoked_overlays"]
    assert original_file.read_bytes() == original_bytes
    assert I.at_confirmation(root, bundle, now.timestamp() + 1) == overlay
    assert I.current(root, bundle, day="2026-10-08") == rolled
    refs = I.lineage_sources(root, bundle, rolled)
    manifest_file = (
        I.root(root)
        / "contract_repairs"
        / (manifest["artifact_content_sha256"] + ".json")
    )
    assert str(manifest_file.resolve()) in {r["path"] for r in refs}


def test_contract_repair_warm_digest_reads_zero_full_sources_and_rejects_preserved_mtime_change(
    setup, monkeypatch
):
    import os

    root, bundle, now, manifest = _prepare_common_contract_repair(setup)
    N._cached_source_hash.cache_clear()
    I._CONTRACT_REPAIR_SOURCE_DIGESTS.clear()
    actual = I.hashlib.file_digest
    hashed = []

    def counted(stream, algorithm):
        hashed.append(str(stream.name))
        return actual(stream, algorithm)

    monkeypatch.setattr(I.hashlib, "file_digest", counted)
    I.validate_contract_repair_manifest(
        root, manifest, bundle, force_source_hashes=True
    )
    assert set(manifest["source_hashes"]) <= set(hashed)
    hashed.clear()
    I.validate_contract_repair_manifest(root, manifest, bundle)
    assert not hashed
    source = next(name for name in manifest["source_hashes"] if "/generations/" in name)
    path = I.Path(source)
    stat = path.stat()
    content = path.read_bytes()
    replacement = content.replace(b"next_session", b"next_sessioN", 1)
    assert len(content) == len(replacement) and replacement != content
    path.write_bytes(replacement)
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert (
        path.stat().st_ino == stat.st_ino
        and path.stat().st_mtime_ns == stat.st_mtime_ns
    )
    with pytest.raises(ValueError, match="contract_repair_source_changed"):
        I.validate_contract_repair_manifest(root, manifest, bundle)
    assert source in hashed


def test_contract_repair_truncated_source_never_reuses_warm_verification(setup):
    root, bundle, now, manifest = _prepare_common_contract_repair(setup)
    I.validate_contract_repair_manifest(root, manifest, bundle)
    source = next(name for name in manifest["source_hashes"] if "/generations/" in name)
    I.Path(source).write_bytes(b"{")
    with pytest.raises(ValueError, match="contract_repair_source_changed"):
        I.validate_contract_repair_manifest(root, manifest, bundle)


def test_contract_repair_preserves_current_custom_overlay_and_old_claim_binding(setup):
    from datetime import timedelta

    root, bundle, machine, scope, value = setup
    N._atomic_write_json(
        N.root(root) / "current.json", {"bundle_sha256": bundle["bundle_sha256"]}
    )
    first_clock = datetime(2026, 10, 8, 10, tzinfo=P.KST)
    bindings = I.effective_bindings(root, bundle, day="2026-10-08")
    bindings[scope] = value["registry_sha256"]
    first = P.seal(
        dict(
            schema=I.SCHEMA,
            authority=I.AUTHORITY,
            day="2026-10-08",
            effective_from=first_clock.isoformat(),
            base_bundle_sha256=bundle["bundle_sha256"],
            base_family_sha256=bundle["continuous_reversal"]["family_sha256"],
            detector_manifest_hash=bundle["continuous_reversal"]["operating_manifest"][
                "detector_manifest_hash"
            ],
            previous_overlay_sha256=None,
            bindings=bindings,
            changes={scope: value["registry_sha256"]},
            independent_scopes=[scope],
            code_hashes=I.code_hashes(),
            revoked_overlays=[],
            actual_pid_consumed=False,
            actual_order_submitted=False,
        )
    )
    I.validate_record(root, first, bundle)
    N._atomic_write_json(
        I.root(root) / "generations" / (first["artifact_content_sha256"] + ".json"),
        first,
    )
    I.write_day_pointer(root, first)
    N._atomic_write_json(I.root(root) / "current.json", first)
    clock = first_clock + timedelta(seconds=2)
    manifest = I.prepare_contract_repair(
        root, bundle, expected_parent=first["artifact_content_sha256"], now=clock
    )
    assert manifest["old_bindings"][scope] == value["registry_sha256"]
    second = I.publish_contract_repair(
        root,
        manifest,
        expected_parent=first["artifact_content_sha256"],
        confirm=I.CONTRACT_REPAIR_AUTHORITY,
        now=clock,
    )
    assert second["previous_overlay_sha256"] == first["artifact_content_sha256"]
    assert second["independent_scopes"] == [scope]
    assert (
        G.load(root, second["bindings"][scope])["prompt"]
        == value["prompt"] + I.COMMON_SUPPORT_CLARIFICATION
    )
    assert I.at_confirmation(root, bundle, first_clock.timestamp() + 1) == first
    assert I.at_confirmation(root, bundle, clock.timestamp()) == second


def test_contract_repair_changed_native_pointer_after_preparation_has_no_publication(
    setup,
):
    root, bundle, clock, manifest = _prepare_common_contract_repair(setup)
    N._atomic_write_json(N.root(root) / "current.json", {"bundle_sha256": "0" * 64})
    with pytest.raises(ValueError, match="preparation_changed"):
        I.publish_contract_repair(
            root,
            manifest,
            expected_parent=None,
            confirm=I.CONTRACT_REPAIR_AUTHORITY,
            now=clock,
        )
    assert not (I.root(root) / "current.json").exists()
    assert not (I.root(root) / "contract_repairs").exists()


@pytest.mark.parametrize("kind", ["evaluations", "resolutions"])
def test_repeated_evaluation_preserves_content_addressed_original_bytes(setup, kind):
    root, b, m, sid, v = setup
    T.prepare(root, "2026-10-07", m, b)
    T.calls(root, "2026-10-07", transport=transport)
    first = T.evaluate(root, "2026-10-07")
    identity = (
        first["artifact_content_sha256"]
        if kind == "evaluations"
        else first["resolution_sha256"]
    )
    path = T.directory(root, "2026-10-07") / kind / (identity + ".json")
    body = json.loads(path.read_bytes())
    original = (json.dumps(body, sort_keys=True, indent=7) + "\n").encode()
    path.write_bytes(original)
    with S.Store(root) as store:
        budget = store.db.execute(
            "SELECT * FROM attempt_budgets ORDER BY 1,2"
        ).fetchall()
    T.evaluate(root, "2026-10-07")
    assert path.read_bytes() == original
    with S.Store(root) as store:
        assert (
            store.db.execute("SELECT * FROM attempt_budgets ORDER BY 1,2").fetchall()
            == budget
        )


def test_evaluation_snapshot_conflict_and_alias_are_not_overwritten(setup):
    root, b, m, sid, v = setup
    T.prepare(root, "2026-10-07", m, b)
    T.calls(root, "2026-10-07", transport=transport)
    first = T.evaluate(root, "2026-10-07")
    path = (
        T.directory(root, "2026-10-07")
        / "evaluations"
        / (first["artifact_content_sha256"] + ".json")
    )
    original = json.loads(path.read_bytes())
    from src.engine.scalping import continuous_reversal_postclose as P

    path.write_text(
        json.dumps(
            P.seal(
                dict(original, comparison_complete=not original["comparison_complete"])
            )
        )
    )
    before = path.read_bytes()
    with pytest.raises(ValueError, match="immutable_conflict"):
        T.evaluate(root, "2026-10-07")
    assert path.read_bytes() == before
    target = path.with_suffix(".preserved")
    path.rename(target)
    path.symlink_to(target)
    with pytest.raises(ValueError, match="snapshot_alias"):
        T.evaluate(root, "2026-10-07")
    assert path.is_symlink() and target.read_bytes() == before
