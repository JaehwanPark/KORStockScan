"""Existing-owner migration and source-bound economic policy regression tests."""

import copy
import json
from types import SimpleNamespace

import pytest

from src.engine import threshold_cycle_preopen_apply as preopen
from src.engine.scalping import strategy_owner_components as mod
from src.engine.automation import operator_policy_succession as succession
from src.tests.test_score_recovery_net_approval import signed_report, sign


def profiles():
    result = {family: dict(values) for family, values in mod.DEFAULTS.items()}
    for values in result.values():
        for key in values:
            if key.endswith("_ENABLED"):
                values[key] = "true"
    return {family: mod.profile(family, values) for family, values in result.items()}


def economic_report(day, family=mod.WEAK):
    report = signed_report(day, count=30)
    base = profiles()
    challenger = copy.deepcopy(base)
    key = (
        "SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_MIN_MICRO_POSITIVES"
        if family == mod.WEAK
        else "SCALP_LOW_PROFIT_STAGNATION_MIN_HOLD_SEC"
    )
    challenger[family][key] -= mod.STEPS[key]
    for i, row in enumerate(report["rows"]):
        row["strategy_owner_profiles"] = base if i < 10 else challenger
        row["strategy_owner_profile_conflict"] = False
        row["strategy_owner_context_sha256"] = "c" * 64
        # More small net wins beat fewer larger wins. Actual execution prices
        # already incorporate slippage; it is not deducted a second time.
        row["realized_net_pnl_krw"] = 30 if i < 10 else 20
        row["exit_amount_krw"] = (
            row["entry_notional_krw"]
            + row["fees_taxes_krw"]
            + row["realized_net_pnl_krw"]
        )
        row["capital_time_krw_hours"] = 100 if i < 10 else 40
    return sign(report)


def book(family=mod.WEAK):
    return mod.merge_books(
        [
            mod.evidence_book(economic_report(day, family), day)
            for day in ("2026-09-07", "2026-09-08")
        ]
    )


@pytest.fixture
def scope(tmp_path, monkeypatch):
    runtime, locks = tmp_path / "runtime", tmp_path / "locks"
    runtime.mkdir()
    locks.mkdir()
    monkeypatch.setattr(preopen, "RUNTIME_ENV_DIR", runtime)
    monkeypatch.setattr(preopen, "OPERATOR_RUNTIME_ENV_LOCK_DIR", locks)
    rows = []
    for family, values in profiles().items():
        row = {
            "family": family,
            "stage": "entry_pre_submit" if family == mod.WEAK else "holding_exit",
            "enabled": True,
            "lock_id": family + ":original",
            "priority": 12,
            "explicit_close_required": True,
            "lock_until_explicit_close": True,
            "env_overrides": {
                mod.PREFIX + k: str(v).lower() for k, v in values.items()
            },
        }
        (locks / (family + ".json")).write_text(json.dumps(row))
        rows.append(row)
    return runtime, locks, rows


def publish(scope, target="2026-09-09"):
    runtime, locks, rows = scope
    selected, decisions, env = preopen._select_auto_apply_candidates(
        [], ai_review={}, require_ai=True, target_date=target, operator_locks=rows
    )
    manifest = {
        "source_date": "2026-09-08",
        "auto_apply_selected": selected,
        "auto_apply_decisions": decisions,
    }
    preopen._write_runtime_env(target, manifest, env)
    return (
        json.loads((runtime / f"threshold_runtime_env_{target}.json").read_text()),
        decisions,
    )


def test_behavior_preserving_migration_needs_no_economic_floor(scope):
    runtime, locks, rows = scope
    originals = {p.name: p.read_bytes() for p in locks.glob("*.json")}
    manifest, decisions = publish(scope)
    assert not manifest["selected_families"]  # No new independent tuning owner.
    assert len(decisions) == 2
    assert all(not d["same_stage_owner_claim"] for d in decisions)
    actual = succession.validate_receipt(manifest, runtime, locks)
    for row in rows:
        assert all(actual[k] == v for k, v in row["env_overrides"].items())
    assert originals == {p.name: p.read_bytes() for p in locks.glob("*.json")}
    assert {
        r["owner"] for r in manifest["strategy_owner_components"]["components"]
    } == {"entry_gate_recheck", "holding_exit"}


def test_next_day_carry_and_same_day_freeze(scope):
    first, _ = publish(scope)
    second, _ = publish(scope)
    third, _ = publish(scope, "2026-09-10")
    assert first["env_overrides"] == second["env_overrides"]
    for row in third["strategy_owner_components"]["components"]:
        assert row["state"] == "last_verified_policy_carried"


def test_missing_or_corrupt_component_receipt_fails_verification(scope):
    runtime, locks, _ = scope
    manifest, _ = publish(scope)
    del manifest["strategy_owner_components"]
    with pytest.raises(ValueError, match="receipt_missing"):
        succession.validate_receipt(manifest, runtime, locks)


def test_operator_change_and_actual_env_mismatch_fail_closed(scope):
    runtime, locks, _ = scope
    manifest, _ = publish(scope)
    path = runtime / "threshold_runtime_env_2026-09-09.env"
    path.write_text(
        path.read_text().replace("MIN_SPREAD_TICKS=5.0", "MIN_SPREAD_TICKS=8")
    )
    with pytest.raises(ValueError, match="env_mismatch"):
        succession.validate_receipt(manifest, runtime, locks)


@pytest.mark.parametrize("flag", ["manual_veto", "safety_veto"])
def test_explicit_veto_not_adopted(scope, flag):
    runtime, locks, rows = scope
    rows[0][flag] = True
    kept, decisions, _ = succession.prepare_components(
        rows, {}, runtime, locks, "2026-09-09"
    )
    assert kept == [rows[0]]
    assert len(decisions) == 1


@pytest.mark.parametrize("family", [mod.WEAK, mod.PROFIT])
def test_observed_smaller_frequent_net_wins_can_qualify(family):
    result = mod.evaluate(book(family), family, profiles()[family], "2026-09-09")
    assert result["state"] == "verified_observed_profile"
    assert result["policies"][0]["source_dates"] == ["2026-09-07", "2026-09-08"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("fees_taxes_krw", None),
        ("realized_net_pnl_krw", 999),
        ("right_censored", True),
        ("fill_completion_class", "partial_then_full"),
        ("scale_in_fill_qty", 1),
        ("strategy_owner_profile_conflict", True),
        ("strategy_owner_context_sha256", None),
        ("lifecycle_population_scope", "sim"),
    ],
)
def test_missing_cost_partial_sim_and_context_cannot_enter_economics(field, value):
    report = economic_report("2026-09-08")
    for row in report["rows"]:
        row[field] = value
    assert not mod.evidence_book(sign(report), "2026-09-08")["rows"]


def test_duplicate_id_excluded_entirely():
    report = economic_report("2026-09-08")
    report["rows"] += [report["rows"][0], report["rows"][0]]
    assert (
        report["rows"][0]["main_lifecycle_id"]
        not in mod.evidence_book(sign(report), "2026-09-08")["rows"]
    )


def test_no_unseen_profile_or_daily_only_approval():
    source = mod.evidence_book(economic_report("2026-09-08"), "2026-09-08")
    assert not mod.evaluate(source, mod.WEAK, profiles()[mod.WEAK], "2026-09-09")[
        "policies"
    ]
    source = book()
    for row in source["rows"].values():
        row["profiles"] = profiles()
    assert not mod.evaluate(source, mod.WEAK, profiles()[mod.WEAK], "2026-09-09")[
        "policies"
    ]


def test_other_owner_context_mismatch_prevents_comparison():
    source = book()
    for row in source["rows"].values():
        if row["profiles"][mod.WEAK] != profiles()[mod.WEAK]:
            row["context_sha256"] = "d" * 64
    assert not mod.evaluate(source, mod.WEAK, profiles()[mod.WEAK], "2026-09-09")[
        "policies"
    ]


def test_exact_source_reconstruction_rejects_tampered_book(tmp_path):
    reports = tmp_path / "main_scalping_lifecycle_paired"
    reports.mkdir()
    for day in ("2026-09-07", "2026-09-08"):
        (reports / f"main_scalping_lifecycle_paired_{day}.json").write_text(
            json.dumps(economic_report(day))
        )
    source = book()
    assert mod.verify_research(source, tmp_path, "2026-09-09")["rows"] == source["rows"]
    next(iter(source["rows"].values()))["net"] = 999
    with pytest.raises(ValueError, match="row_mismatch"):
        mod.verify_research(source, tmp_path, "2026-09-09")


def test_runtime_requires_exact_date_context_venue_and_real_scope():
    rules = SimpleNamespace(
        **{k: v for values in profiles().values() for k, v in values.items()}
    )
    policy = mod.evaluate(book(), mod.WEAK, profiles()[mod.WEAK], "2026-09-09")[
        "policies"
    ][0]
    policy["context_sha256"] = mod.context_fingerprint(rules)
    bundle = {
        "schema": mod.SCHEMA,
        "target_date": "2026-09-09",
        "components": [
            {
                "family": mod.WEAK,
                "owner": mod.OWNERS[mod.WEAK],
                "baseline": profiles()[mod.WEAK],
                "policies": [policy],
            }
        ],
    }
    env = {mod.ENV_KEY: json.dumps(bundle)}

    def run(**kwargs):
        return mod.runtime_state(
            rules,
            venue="KRX",
            session="krx_regular",
            environment=env,
            today="2026-09-09",
            **kwargs,
        )

    assert run()["status"] == "verified_scoped_policy"
    assert run(simulated=True)["status"] == "baseline"
    assert (
        mod.runtime_state(
            rules, venue="NXT", session="nxt", environment=env, today="2026-09-09"
        )["status"]
        == "baseline"
    )
    assert (
        mod.runtime_state(
            rules,
            venue="KRX",
            session="krx_regular",
            environment=env,
            today="2026-09-10",
        )["status"]
        == "invalid_policy_baseline_retained"
    )
    rules.UNRELATED_GUARD = 1
    assert run()["status"] == "baseline"


def test_postclose_book_to_preopen_receipt_and_launcher_exports(
    scope, tmp_path, monkeypatch
):
    runtime, locks, rows = scope
    reports = tmp_path / "report"
    producer = reports / "main_scalping_lifecycle_paired"
    producer.mkdir(parents=True)
    for day in ("2026-09-07", "2026-09-08"):
        (producer / f"main_scalping_lifecycle_paired_{day}.json").write_text(
            json.dumps(economic_report(day))
        )
    monkeypatch.setattr(preopen, "REPORT_DIR", reports)
    selected, decisions, env = preopen._select_auto_apply_candidates(
        [],
        ai_review={},
        require_ai=True,
        target_date="2026-09-09",
        operator_locks=rows,
        strategy_owner_component_economics=book(),
    )
    weak = next(
        d["strategy_owner_component"] for d in decisions if d["family"] == mod.WEAK
    )
    assert weak["policies"]
    manifest = {
        "source_date": "2026-09-08",
        "auto_apply_selected": selected,
        "auto_apply_decisions": decisions,
    }
    preopen._write_runtime_env("2026-09-09", manifest, env)
    published = json.loads(
        (runtime / "threshold_runtime_env_2026-09-09.json").read_text()
    )
    exports = succession.validate_receipt(published, runtime, locks)
    assert json.loads(exports[mod.ENV_KEY])["components"][0]["policies"]
    carried, _ = publish(scope, "2026-09-10")
    assert (
        carried["strategy_owner_components"]["components"][0]["policies"]
        == weak["policies"]
    )


def test_malformed_book_does_not_prevent_baseline_migration(scope):
    _, _, rows = scope
    _, decisions, _ = preopen._select_auto_apply_candidates(
        [],
        ai_review={},
        require_ai=True,
        target_date="2026-09-09",
        operator_locks=rows,
        strategy_owner_component_economics={"schema": "invalid"},
    )
    assert len(decisions) == 2
    assert all(
        d["economic_source_blocker"] == "owner_component_economic_source_invalid"
        for d in decisions
    )
    assert all(not d["strategy_owner_component"]["policies"] for d in decisions)


def test_pre_authorization_and_off_veto_do_not_migrate(scope):
    runtime, locks, rows = scope
    kept, decisions, _ = succession.prepare_components(
        rows, {}, runtime, locks, "2026-09-08"
    )
    assert kept == rows and not decisions
    rows[0]["env_overrides"][
        mod.PREFIX + "SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_ENABLED"
    ] = "false"
    kept, decisions, _ = succession.prepare_components(
        rows, {}, runtime, locks, "2026-09-09"
    )
    assert kept == [rows[0]]


def test_component_source_and_policy_runtime_projections_are_journal_compatible():
    from src.engine.scalping.main_lifecycle_paired import _validated_pipeline_transition
    from src.tests.test_main_lifecycle_paired import _pipeline_event, TARGET_DATE

    stock = {
        "id": 701,
        "name": "TEST",
        "code": "005930",
        "scanner_generation_id": "TEST:r1",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    payload = json.dumps(profiles(), sort_keys=True, separators=(",", ":"))
    event = _pipeline_event(
        stock=stock,
        pipeline="ENTRY_PIPELINE",
        source_stage="ai_confirmed",
        second=1,
        fields={
            "action": "BUY",
            "strategy_owner_profiles": payload,
            "strategy_owner_context_sha256": "c" * 64,
        },
    )
    transition, error, mapped = _validated_pipeline_transition(
        event, target_date=TARGET_DATE
    )
    assert mapped and error is None
    assert transition["data"]["strategy_owner_profiles"] == payload
    assert transition["data"]["strategy_owner_context_sha256"] == "c" * 64


@pytest.mark.parametrize("conflict", [False, True])
def test_lifecycle_materialization_preserves_or_quarantines_profile_identity(conflict):
    from src.engine.scalping.main_lifecycle_paired import _LifecycleAccumulator
    from src.tests.test_main_lifecycle_paired import _complete_lifecycle

    rows = _complete_lifecycle("owner-profile", include_scale=False)
    accumulator = _LifecycleAccumulator.from_transition(rows[0])
    for row in rows:
        if row["stage"] in {"entry_decision", "holding"}:
            row["data"].update(
                strategy_owner_profiles=json.dumps(profiles()),
                strategy_owner_context_sha256="c" * 64,
            )
            if conflict and row["stage"] == "holding":
                row["data"]["strategy_owner_context_sha256"] = "d" * 64
        accumulator.consume(row)
    result = accumulator.finalize()
    assert result["strategy_owner_profiles"] == profiles()
    assert result["strategy_owner_profile_conflict"] is conflict


def test_baseline_only_is_not_reported_as_future_automatic_first_use():
    source = book()
    for row in source["rows"].values():
        row["profiles"] = profiles()
    result = mod.evaluate(source, mod.WEAK, profiles()[mod.WEAK], "2026-09-09")
    assert result["state"] == "baseline_only_no_observed_challenger"
    assert result["unseen_profile_live_authority"] is False
    assert result["maintenance_review_due"] is True


def test_safety_revert_retains_existing_veto_path(scope):
    runtime, locks, rows = scope
    remaining, decisions, _ = succession.prepare_components(
        rows, {}, runtime, locks, "2026-09-09", safety_reverts={mod.WEAK}
    )
    assert remaining == [rows[0]]
    assert {d["family"] for d in decisions} == {mod.PROFIT}


def test_changed_scope_dates_do_not_create_frequency_uplift():
    source = book()
    for row in source["rows"].values():
        if row["profiles"][mod.WEAK] != profiles()[mod.WEAK]:
            row["date"] = "2026-09-04"
    source["sources"]["2026-09-04"] = "e" * 64
    assert not mod.evaluate(source, mod.WEAK, profiles()[mod.WEAK], "2026-09-09")[
        "policies"
    ]


def test_daily_rolling_merge_preserves_exact_component_books():
    from src.engine import daily_threshold_cycle_report as daily

    daily_books = [
        mod.evidence_book(economic_report(day), day)
        for day in ("2026-09-07", "2026-09-08")
    ]
    result = daily._aggregate_metric_dicts(
        [
            {"buy_score65_74": {"strategy_owner_component_economics": b}}
            for b in daily_books
        ]
    )
    merged = result["buy_score65_74"]["strategy_owner_component_economics"]
    assert merged == mod.merge_books(daily_books)


def test_runtime_summary_separates_managed_component_from_independent_selection(
    tmp_path,
):
    from src.engine.runtime_approval_summary import _runtime_selection_by_family

    path = tmp_path / "apply.json"
    component = {
        "family": mod.WEAK,
        "owner": mod.OWNERS[mod.WEAK],
        "policies": [],
        "state": "baseline_migrated",
    }
    path.write_text(
        json.dumps(
            {
                "target_date": "2026-09-09",
                "auto_apply_decisions": [{"strategy_owner_component": component}],
            }
        )
    )
    result = _runtime_selection_by_family(
        {"date": "2026-09-09", "runtime_apply": {"apply_manifest": str(path)}}
    )
    assert result[mod.WEAK]["managed_by_existing_owner"] is True
    assert result[mod.WEAK]["selected"] is False
    assert result[mod.WEAK]["pid_consumption_verified"] is False


def test_nonfinite_diagnostic_context_does_not_raise_in_live_logger():
    rules = SimpleNamespace(
        **{k: v for values in profiles().values() for k, v in values.items()}
    )
    rules.UNRELATED_GUARD = float("nan")
    state = mod.runtime_state(rules, venue="KRX", session="krx_regular", environment={})
    assert state["context_sha256"] is None
    assert state["applied_families"] == []


@pytest.mark.parametrize("micro_state,blocked", [(None, True), ("neutral", False)])
def test_scoped_weak_relief_does_not_relax_source_quality(
    monkeypatch, micro_state, blocked
):
    from src.engine import sniper_state_handlers as runtime

    rules = SimpleNamespace(
        **{k: v for values in profiles().values() for k, v in values.items()}
    )
    monkeypatch.setattr(runtime, "TRADING_RULES", rules)
    policy = mod.evaluate(book(), mod.WEAK, profiles()[mod.WEAK], "2026-09-09")[
        "policies"
    ][0]
    policy["context_sha256"] = mod.context_fingerprint(rules)
    bundle = {
        "schema": mod.SCHEMA,
        "target_date": "2026-09-09",
        "components": [
            {
                "family": mod.WEAK,
                "owner": mod.OWNERS[mod.WEAK],
                "baseline": profiles()[mod.WEAK],
                "policies": [policy],
            }
        ],
    }
    monkeypatch.setattr(
        runtime,
        "_strategy_owner_component_state",
        lambda stock: mod.runtime_state(
            rules,
            venue="KRX",
            session="krx_regular",
            environment={mod.ENV_KEY: json.dumps(bundle)},
            today="2026-09-09",
        ),
    )
    verdict = runtime._evaluate_real_weak_pullback_entry_block(
        strategy="SCALPING",
        stock={"name": "TEST"},
        latency_gate={
            "latency_state": "CAUTION",
            "decision": "ALLOW_NORMAL",
            "conditional_1tick_real_override_context": {"buy_pressure_ok": True},
        },
        pre_ai_fields={"strength_momentum_risk_state": "weak_momentum_context"},
        guard_fields={},
        orderbook_fields={"orderbook_micro_state": micro_state},
    )
    assert verdict["blocked"] is blocked
    if blocked:
        assert verdict["reason"] == "weak_pullback_micro_source_unavailable"


@pytest.mark.parametrize(
    "session",
    ["nxt_entry_window", "nxt_premarket", "nxt_regular_overlap", "nxt_aftermarket"],
)
def test_real_nxt_sessions_survive_source_and_exact_runtime_binding(session):
    books = []
    for day in ("2026-09-07", "2026-09-08"):
        report = economic_report(day)
        for row in report["rows"]:
            row["venue"] = "NXT"
            row["session_bucket"] = session
        daily = mod.evidence_book(sign(report), day)
        assert len(daily["rows"]) == 30
        books.append(daily)
    result = mod.evaluate(
        mod.merge_books(books), mod.WEAK, profiles()[mod.WEAK], "2026-09-09"
    )
    policy = result["policies"][0]
    assert policy["session"] == session
    rules = SimpleNamespace(
        **{k: v for values in profiles().values() for k, v in values.items()}
    )
    policy["context_sha256"] = mod.context_fingerprint(rules)
    bundle = {
        "schema": mod.SCHEMA,
        "target_date": "2026-09-09",
        "components": [
            {
                "family": mod.WEAK,
                "owner": mod.OWNERS[mod.WEAK],
                "baseline": profiles()[mod.WEAK],
                "policies": [policy],
            }
        ],
    }
    env = {mod.ENV_KEY: json.dumps(bundle)}
    assert (
        mod.runtime_state(
            rules, venue="NXT", session=session, environment=env, today="2026-09-09"
        )["status"]
        == "verified_scoped_policy"
    )
    assert (
        mod.runtime_state(
            rules, venue="NXT", session="nxt", environment=env, today="2026-09-09"
        )["status"]
        == "baseline"
    )
    assert (
        mod.runtime_state(
            rules, venue="KRX", session=session, environment=env, today="2026-09-09"
        )["status"]
        == "baseline"
    )


@pytest.mark.parametrize(
    "venue,session",
    [
        ("NXT", "unknown"),
        ("NXT", "krx_regular"),
        ("KRX", "nxt_aftermarket"),
        (None, None),
        ("NXT", []),
    ],
)
def test_component_unknown_or_cross_venue_session_is_rejected(venue, session):
    assert mod.valid_scope(venue, session) is False


def test_runtime_stock_scope_preserves_exact_nxt_and_rejects_conflicts():
    assert mod.stock_scope(
        {"effective_venue": "NXT", "market_session_bucket": "nxt_aftermarket"}
    ) == ("NXT", "nxt_aftermarket")
    assert mod.stock_scope(
        {"effective_venue": "NXT", "venue": "KRX", "market_session_bucket": "nxt"}
    ) == (None, None)
    assert mod.stock_scope({"effective_venue": "NXT"}) == (None, None)


def test_contract_validation_does_not_mutate_profile_state():
    from src.engine.scalping.main_lifecycle_paired import _LifecycleAccumulator
    from src.tests.test_main_lifecycle_paired import _complete_lifecycle

    rows = _complete_lifecycle("owner-immutable-contract-check")
    accumulator = _LifecycleAccumulator.from_transition(rows[0])
    row = next(row for row in rows if row["stage"] == "entry_decision")
    row["data"].update(
        strategy_owner_profiles=json.dumps(profiles()),
        strategy_owner_context_sha256="c" * 64,
    )
    accumulator._stage_contract_error(row)
    assert accumulator.strategy_owner_profiles is None
