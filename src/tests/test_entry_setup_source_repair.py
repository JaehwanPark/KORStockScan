"""Receipt rejection and actual uncached postclose consumption, using tmp data."""
from copy import deepcopy
import hashlib
import json

import pytest

from src.engine.scalping import entry_setup_source_repair as repair
from src.engine.scalping import entry_setup_evidence as E, entry_strategy_policy as S
from src.engine.scalping import ai_action_outcome_calibration as calibration
from src.engine.scalping.ai_decision_trace import _json_bytes
from src.tests.test_entry_strategy_policy import raw, setup, policy
from src.tests.test_mechanistic_entry_runtime_policy import initial


def canonical(capture):
    capture["machine_observation_sha256"] = hashlib.sha256(_json_bytes(
        {k: v for k, v in capture.items() if k != "machine_observation_sha256"})).hexdigest()
    return capture


@pytest.fixture
def case(tmp_path):
    payload = raw()
    payload.update(stock_code="005930", snapshot_id="snapshot", evaluation_attempt_id="attempt",
        broker_route="KRX", watch_origin="MAIN_FIXED_WATCH", watch_admission_id="watch",
        watch_generation_id="generation", strategy_observed_at="2026-10-02T10:33:18+09:00")
    payload["ai_market_snapshot_v1"] = {k: payload[k] for k in (
        "stock_code", "snapshot_id", "broker_route", "effective_venue", "session_bucket")}
    payload["ai_market_snapshot_v1"]["market_data_route"] = "krx_only"
    payload["current"]["fluctuation_pct"] = 0
    payload["features"].update(price_change_10t_pct=0, curr_vs_micro_vwap_bp=0, curr_vs_ma5_bp=0)
    payload["entry_candle_context"]["structure"].update(
        returns_pct={str(n): 0 for n in (1, 3, 5, 10, 20, 60)},
        slopes_pct_per_bar={str(n): 0 for n in (1, 3, 5, 10, 20, 60)},
        regime="range", structure_contract_version="entry_local_breakout_completed_v1",
        local_breakout={"status": "no_confirmed_breakout", "recheck_required": True}, volume_ratio=1)
    evidence, _, _ = S.rebuild(setup(payload), policy())
    evidence.update(setup_state="WAIT_CONFIRMATION", execution_readiness_state="WAIT_CONFIRMATION",
                    recheck_reasons=["SETUP_DISCOVERY_RECHECK", "TRIGGER_CONFIRMATION_RECHECK"])
    evidence["evidence_sha256"] = S.digest({k: v for k, v in evidence.items() if k != "evidence_sha256"})
    assert E.validate_entry_setup_evidence(evidence) == [repair.ERROR]
    bundle = initial(tmp_path / "policy-fixture")
    bundle["machine_policy"] = policy()
    bundle["bundle_sha256"] = S.digest({k: v for k, v in bundle.items() if k != "bundle_sha256"})
    context = {k: payload[k] for k in ("stock_code", "snapshot_id", "evaluation_attempt_id",
        "broker_route", "effective_venue", "session_bucket", "watch_origin",
        "watch_admission_id", "watch_generation_id")}
    context.update(reference_price=10000, reference_price_type="executable_ask",
                   entry_conservative_execution_cost_pct=None, market_data_route="krx_only")
    capture = canonical(dict(schema="mechanistic_entry_observation_v1", captured_at="2026-10-02T10:33:18.1+09:00",
        source_event_stage="entry_machine_only_v1", label_context=context,
        **{k: payload[k] for k in ("watch_origin", "watch_admission_id", "watch_generation_id")},
        bundle_sha256=bundle["bundle_sha256"], redacted=False, provider_called=False,
        runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False, broker_order_forbidden=True,
        source=dict(exact_payload=payload, setup_evidence=evidence,
                    assessment=dict(action="RECHECK", reason="local_breakout_confirmation_required"))))
    archive = tmp_path / "ai_decision_payloads/ai_decision_payloads_2026-10-02.jsonl"
    archive.parent.mkdir(parents=True)
    archive.write_text(json.dumps(capture) + "\n")
    receipt = repair.build_receipt(capture, bundle, source_path=archive,
        source_sha256=repair.file_sha256(archive), source_line=1)
    return capture, bundle, archive, receipt


def test_receipt_reconstructs_only_four_fields_and_preserves_raw_guard(case):
    capture, bundle, archive, receipt = case
    original = deepcopy(capture)
    fixed, proof = repair.consume_receipt(capture, receipt, source_path=archive,
                                         source_sha256=repair.file_sha256(archive))
    assert capture == original
    assert E.validate_entry_setup_evidence(fixed) == []
    assert {k for k in fixed if fixed[k] != capture["source"]["setup_evidence"][k]} == repair.CHANGED_FIELDS
    assert fixed["strategy_raw_input"] == capture["source"]["exact_payload"]
    decision = E.mechanistic_entry_policy_decision(fixed, policy=bundle["machine_policy"])
    assert (decision["action"], decision["reason"]) == ("RECHECK", "local_breakout_confirmation_required")
    assert proof["original_capture_sha256"] == capture["machine_observation_sha256"]
    assert proof["original_validation_errors"] == [repair.ERROR]
    assert proof["runtime_effect"] is False and proof["allowed_runtime_apply"] is False


def test_claimed_archive_hash_cannot_hide_a_changed_physical_file(case):
    capture, _, archive, receipt = case
    sealed = repair.file_sha256(archive)
    with archive.open("a") as stream:
        stream.write('{"unrelated_record": true}\n')
    # The original capture line still matches; the claimed whole-file seal does not.
    with pytest.raises(ValueError, match="source_repair_archive_hash_changed"):
        repair.consume_receipt(capture, receipt, source_path=archive, source_sha256=sealed)


def test_archive_change_between_hash_and_line_read_is_rejected(case, monkeypatch):
    capture, _, archive, receipt = case
    original = repair.file_sha256
    sealed = original(archive)
    changed = False
    def race(path):
        nonlocal changed
        digest = original(path)
        if path == archive and not changed:
            changed = True
            with archive.open("a") as stream:
                stream.write('{"concurrent_append": true}\n')
        return digest
    monkeypatch.setattr(repair, "file_sha256", race)
    with pytest.raises(ValueError, match="source_repair_archive_hash_changed"):
        repair.consume_receipt(capture, receipt, source_path=archive, source_sha256=sealed)


@pytest.mark.parametrize("mutation", ["digest", "kernel", "authority", "source", "line", "setup", "action", "bundle", "extra"])
def test_rehashed_receipt_tampering_is_rejected(case, mutation):
    capture, _, archive, receipt = case
    receipt = deepcopy(receipt)
    if mutation == "kernel": receipt["kernel_seals"]["entry_setup_evidence.py"] = "0" * 64
    elif mutation == "authority": receipt["allowed_runtime_apply"] = True
    elif mutation == "source": receipt["source_location"]["physical_sha256"] = "0" * 64
    elif mutation == "line": receipt["source_location"]["line"] = 2
    elif mutation == "setup": receipt["repaired_setup_evidence"]["setup_state"] = "READY"
    elif mutation == "action": receipt["machine_action"] = "ENTER_NOW"
    elif mutation == "bundle": receipt["original_bundle"]["machine_policy"]["thresholds"]["maximum_spread_bp"] = 1
    elif mutation == "extra": receipt["extra_authority"] = "runtime"
    if mutation != "digest":
        receipt["content_sha256"] = S.digest({k: v for k, v in receipt.items() if k != "content_sha256"})
    else: receipt["content_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        repair.consume_receipt(capture, receipt, source_path=archive,
                               source_sha256=repair.file_sha256(archive))


@pytest.mark.parametrize("mutation", ["canonical", "provider", "order", "scope", "identity", "watch", "raw", "future", "additional_defect", "recorded_enter", "guard"])
def test_capture_defects_cannot_be_repaired(case, mutation):
    capture, bundle, archive, _ = case
    capture = deepcopy(capture)
    if mutation == "canonical": capture["machine_observation_sha256"] = "0" * 64
    elif mutation == "provider": capture["provider_called"] = True
    elif mutation == "order": capture["actual_order_submitted"] = True
    elif mutation == "scope": capture["label_context"]["effective_venue"] = "NXT"
    elif mutation == "identity": capture["label_context"]["snapshot_id"] = "other"
    elif mutation == "watch": capture["watch_admission_id"] = "other"
    elif mutation == "raw": capture["source"]["exact_payload"]["current"]["price"] += 1
    elif mutation == "future": capture["captured_at"] = "2026-10-02T10:33:17+09:00"
    elif mutation == "additional_defect": capture["source"]["setup_evidence"]["structure_phase"] = "invented"
    elif mutation == "recorded_enter": capture["source"]["assessment"]["action"] = "ENTER_NOW"
    elif mutation == "guard":
        capture["source"]["exact_payload"]["features"]["large_sell_print_detected"] = True
        old = capture["source"]["setup_evidence"]
        old["strategy_raw_input"] = deepcopy(capture["source"]["exact_payload"])
        old["strategy_raw_sha256"] = S.digest(old["strategy_raw_input"])
        old["evidence_sha256"] = S.digest({k: v for k, v in old.items() if k != "evidence_sha256"})
    if mutation != "canonical": canonical(capture)
    with pytest.raises(ValueError):
        repair.build_receipt(capture, bundle, source_path=archive,
                            source_sha256=repair.file_sha256(archive), source_line=1)


def test_actual_uncached_consumer_requires_opt_in_and_retains_cost_gap(case, monkeypatch):
    capture, _, archive, receipt = case
    monkeypatch.setattr(calibration, "_hierarchy_cost_profiles", lambda *args: {})
    options = dict(target_date="2026-10-02", independent_machine=True, minimum_source_date="2026-09-29")
    root = archive.parent.parent
    original_bytes = archive.read_bytes()
    rows, counts = calibration._load_machine_observation_rows_uncached(root, **options)
    assert rows == [] and counts["invalid_capture"] == 1
    rows, counts = calibration._load_machine_observation_rows_uncached(root, **options,
        source_setup_repairs={capture["machine_observation_sha256"]: receipt})
    assert len(rows) == 1 and counts["source_setup_repair_accepted"] == 1
    row = rows[0]
    for key in ("stock_code", "watch_origin", "watch_admission_id", "watch_generation_id", "evaluation_attempt_id"):
        assert row[key] == capture["label_context"][key]
    assert row["decision_trace_id"] == capture["machine_observation_sha256"]
    assert row["machine_action"] == "RECHECK" and row["entry_quality_contract_valid"] is False
    assert calibration._machine_path_value(row)[0] is None
    assert row["comparison"]["conservative_execution_cost_pct"] is None
    assert row["source_setup_repair"]["receipt_sha256"] == receipt["content_sha256"]
    assert archive.read_bytes() == original_bytes
    # The public/cache path has no repair opt-in and still excludes the source.
    public, _ = calibration.load_machine_observation_rows(root, **options)
    assert public == []
    bad = deepcopy(receipt); bad["kernel_seals"] = {}
    bad["content_sha256"] = S.digest({k: v for k, v in bad.items() if k != "content_sha256"})
    rows, counts = calibration._load_machine_observation_rows_uncached(root, **options,
        source_setup_repairs={capture["machine_observation_sha256"]: bad})
    assert rows == [] and counts["source_setup_repair_rejected"] == 1


def test_archive_change_and_moved_receipt_are_rejected(case):
    capture, _, archive, receipt = case
    archive.write_text(archive.read_text() + "\n")
    with pytest.raises(ValueError, match="binding_invalid"):
        repair.consume_receipt(capture, receipt, source_path=archive,
                               source_sha256=repair.file_sha256(archive))
    with pytest.raises(ValueError, match="binding_invalid"):
        repair.consume_receipt(capture, receipt, source_path=archive.with_name("other.jsonl"),
                               source_sha256=receipt["source_location"]["physical_sha256"])


def test_repair_lane_cannot_start_price_provider_or_ai_join(case):
    capture, _, archive, receipt = case
    options = dict(target_date="2026-10-02", minimum_source_date="2026-09-29",
                   source_setup_repairs={capture["machine_observation_sha256"]: receipt})
    with pytest.raises(ValueError, match="offline_independent"):
        calibration._load_machine_observation_rows_uncached(archive.parent.parent, **options)
    with pytest.raises(ValueError, match="offline_independent"):
        calibration._load_machine_observation_rows_uncached(archive.parent.parent, **options,
            independent_machine=True, completed_price_fetcher=lambda *args: pytest.fail("provider called"))


def test_bounded_replay_verifies_original_cache_population_and_filters_routes(case, monkeypatch):
    capture, bundle, archive, receipt = case
    valid = deepcopy(capture)
    valid["source"]["setup_evidence"] = receipt["repaired_setup_evidence"]
    canonical(valid)
    archive.write_text(json.dumps(capture) + "\n" + json.dumps(valid) + "\n")
    root = archive.parent.parent
    parent = root / "runtime/mechanistic_entry_policy/generations" / (bundle["bundle_sha256"] + ".json")
    parent.parent.mkdir(parents=True); parent.write_text(json.dumps(bundle))
    calls = []
    def cache_owner(**kwargs):
        calls.append(kwargs)
        price = dict(stock_code="005930", effective_venue="KRX", session_bucket="KRX_REGULAR",
            source_request_code="005930", timestamp="2026-10-02T10:34:00+09:00", price=10000,
            close=10000, high=10000, low=10000, completed_bar_only=True)
        return [price, {**price, "source_request_code": "005930_NX"},
                {**price, "effective_venue": "NXT"}], {"status": "verified_cache_reused"}, {"005930"}
    monkeypatch.setattr(calibration, "_machine_completed_price_rows_locked", cache_owner)
    before_iterator = calibration.iter_jsonl
    before_loader = calibration._machine_completed_price_rows
    result = repair.replay_archive_subset(data_root=root, dates=("2026-10-02",), stock_code="005930",
        scope=("KRX", "KRX_REGULAR"), repair_trace=capture["machine_observation_sha256"])
    assert len(calls) == 1
    assert [c["machine_observation_sha256"] for c in calls[0]["observations"]] == [valid["machine_observation_sha256"]]
    assert calls[0]["fetcher"] is None and calls[0]["as_of"] is None
    assert result["baseline_count"] == 1 and result["repaired_count"] == 2 and result["native_count"] == 1
    assert result["baseline_census"]["completed_price_rows"] == 1
    assert result["repaired_census"]["completed_price_rows"] == 1
    assert result["existing_rows_unchanged"] is True
    assert calibration.iter_jsonl is before_iterator
    assert calibration._machine_completed_price_rows is before_loader
    assert not (root / "report/machine_observation_projection").exists()
