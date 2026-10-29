"""Main holding scope and native observation boundaries for AVG_DOWN."""

from copy import deepcopy
from datetime import datetime
import pytest

from src.engine.scalping import avg_down_rebound as adapter
from src.engine.scalping import main_fixed_watch as fixed


@pytest.mark.parametrize("hour", [8, 10, 16])
def test_holding_uses_original_fixed_admission_across_session_and_restart(hour):
    at = datetime(2026, 10, 15, hour, 20, tzinfo=fixed.session_contract.KST).timestamp()
    route = fixed.session_route(at)
    stock = dict(
        code="005930",
        strategy="SCALPING",
        position_tag="SCALP_BASE",
        watch_origin=fixed.WATCH_ORIGIN,
        watch_admission_id=fixed.new_admission_id(at, route),
        watch_generation_id=fixed.generation_id(at, route),
        status="HOLDING",
    )
    before = deepcopy(stock)
    assert adapter.holding_policy_position_tag(stock) == "SCANNER"
    assert stock == before
    for field in ("code", "watch_admission_id", "watch_generation_id", "position_tag"):
        with pytest.raises(ValueError):
            adapter.holding_policy_position_tag(dict(stock, **{field: "wrong"}))


def test_policy_adapter_does_not_adopt_other_owners():
    assert (
        adapter.holding_policy_position_tag(dict(position_tag="SCALP_BASE"))
        == "SCALP_BASE"
    )
    assert (
        adapter.holding_policy_position_tag(dict(position_tag="EPISODE")) == "EPISODE"
    )


def test_rebound_definition_follows_refinements_but_excludes_momentum_and_breakout():
    from src.engine.scalping import reversal_cumulative_catalog as catalog

    assert adapter._rebound_branch("legacy_dd5_ge_1_2_v1")
    assert adapter._rebound_branch("manual_path_918aff358c3edb8c")
    assert not adapter._rebound_branch("manual_path_35c2d4b8fb178441")
    additions = catalog.GROUPS["samsung|REGULAR|ALL|SOR"]["additions"]
    assert adapter._rebound_branch(additions["A10"])
    assert not adapter._rebound_branch(additions["A14"])
    for original, bid in catalog.GROUPS["samsung|REGULAR|ALL|SOR"]["refinements"][
        "F01"
    ].items():
        assert adapter._rebound_branch(bid) == adapter._rebound_branch(original)


@pytest.mark.parametrize(
    "gap",
    [None, "missing", "expired", "future", "symbol", "item", "continuation", "blocked"],
)
def test_native_read_is_unclaimed_same_scope_fresh_and_uses_current_dispatch(
    monkeypatch, gap
):
    from src.engine.scalping import reversal_source_diagnostics as source
    from src.engine.scalping import continuous_reversal_policy as policy

    event = dict(
        epoch=100.0,
        symbol="005930",
        source_item="005930_AL",
        branch_signals={"branch": {}},
    )
    if gap == "expired":
        event["epoch"] = 94.0
    if gap == "future":
        event["epoch"] = 102.0
    if gap == "symbol":
        event["symbol"] = "000001"
    if gap == "item":
        event["source_item"] = "005930_NX"
    calls = []

    def observe(*args, **kwargs):
        calls.append((args, kwargs))
        return (None if gap == "missing" else (event, {})), {"reason": "ready"}

    monkeypatch.setattr(source, "observe_snapshot", observe)
    monkeypatch.setattr(
        source,
        "claim_snapshot_with_receipt",
        lambda *a, **k: pytest.fail("ADD stole entry claim"),
    )
    monkeypatch.setattr(
        policy, "assess", lambda *a, **k: pytest.fail("ADD wrote Main status")
    )

    def assess(family, snapshot, **kwargs):
        assert family["schema"] == "continuous_reversal_policy_v6"
        return (
            dict(
                action="BLOCK" if gap == "blocked" else "ENTER_NOW",
                policy_version=family["schema"],
                matched_branches=[
                    (
                        "manual_path_35c2d4b8fb178441"
                        if gap == "continuation"
                        else "legacy_dd5_ge_1_2_v1"
                    )
                ],
            ),
            None,
            None,
            None,
        )

    monkeypatch.setattr(policy, "_assess", assess)
    result = adapter.evaluate_native_rebound(
        dict(
            machine_bundle_sha256="a" * 64,
            continuous_reversal=dict(
                schema="continuous_reversal_policy_v6", family_sha256="b" * 64
            ),
        ),
        stock_code="005930",
        ws_data={"last_realtime_type_item": {"0B": "005930_AL"}},
        session="krx_regular",
        now_ts=100.0,
    )
    assert result["should_add"] is (gap is None)
    assert calls[0][0] == ("005930", "SOR", "krx_regular")
    if gap is None:
        assert result["native_signal_expires_at"] == 105.0


@pytest.mark.parametrize(
    "reason,source_current,quote_current,expected",
    [
        ("no_matching_pattern", True, True, "shared_main_rebound_not_confirmed"),
        (
            "no_matching_pattern",
            False,
            True,
            "shared_main_rebound_native_source_unavailable",
        ),
        (
            "no_matching_pattern",
            True,
            False,
            "shared_main_rebound_native_source_unavailable",
        ),
        (
            "required_window_incomplete",
            True,
            True,
            "shared_main_rebound_native_source_unavailable",
        ),
        (
            "no_matching_pattern",
            None,
            True,
            "shared_main_rebound_native_source_unavailable",
        ),
    ],
)
def test_observed_false_is_not_a_feed_gap_but_missing_or_stale_still_is(
    monkeypatch, reason, source_current, quote_current, expected
):
    from src.engine.scalping import reversal_source_diagnostics as source

    monkeypatch.setattr(
        source,
        "observe_snapshot",
        lambda *a, **k: (
            None,
            dict(
                reason=reason,
                native_source_current=source_current,
                native_quote_current=quote_current,
            ),
        ),
    )
    result = adapter.evaluate_native_rebound(
        dict(
            machine_bundle_sha256="a" * 64,
            continuous_reversal=dict(family_sha256="b" * 64),
        ),
        stock_code="005930",
        ws_data={"last_realtime_type_item": {"0B": "005930_AL"}},
        session="krx_regular",
        now_ts=100.0,
    )
    assert result["reason"] == expected and result["should_add"] is False
    assert result["native_source_status"] == reason
    assert "native_signal_expires_at" not in result  # No invented signal/permission.


def test_locked_diagnostic_retains_prior_reason_without_granting_current_authority():
    import ast
    from pathlib import Path
    from src.engine import sniper_state_handlers as handlers

    tree = ast.parse(Path(handlers.__file__).read_text())
    owner = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "handle_holding_state"
    )
    branch = next(
        n
        for n in ast.walk(owner)
        if isinstance(n, ast.If)
        and any(
            isinstance(c, ast.Call)
            and getattr(c.func, "id", "") == "_log_holding_pipeline"
            and len(c.args) > 2
            and isinstance(c.args[2], ast.Constant)
            and c.args[2].value == "avg_down_shared_rebound_blocked"
            for c in ast.walk(n)
        )
        and isinstance(n.test, ast.Compare)
    )
    stock = dict(
        _main_rebound_entry_assessed_at=1230.0,
        _main_rebound_entry_assessment=dict(
            reason="shared_main_rebound_input_preflight_blocked",
            preflight_primary_blocker="bbo_future",
            source_timing={"bbo_age_ms": -107.195},
            native_source_status="no_matching_pattern",
        ),
    )
    events = []
    scope = dict(
        stock=stock,
        code="005930",
        now_ts=1240.0,
        gate=dict(allowed=False, reason="add_judgment_locked"),
        _log_holding_pipeline=lambda *a, **kw: events.append(kw),
    )
    exec(
        compile(
            ast.fix_missing_locations(ast.Module(body=[branch], type_ignores=[])),
            "<native-holding-log>",
            "exec",
        ),
        scope,
    )
    assert events[0]["reason"] == "add_judgment_locked"
    assert events[0]["last_assessment_at"] == 1230.0
    assert events[0]["assessment_scope"] == "prior_evaluation_diagnostic"
    assert events[0]["preflight_primary_blocker"] == "bbo_future"
    assert events[0]["source_timing"] == {"bbo_age_ms": -107.195}
    assert events[0]["actual_order_submitted"] is False


@pytest.mark.parametrize(
    "quote_at,expected", [(1792538068.638, "fresh"), (1792538070.0, "future")]
)
def test_both_holding_dispatches_capture_physical_clock_after_snapshot(
    quote_at, expected
):
    import ast
    from pathlib import Path
    from types import SimpleNamespace
    from src.engine.scalping.ai_market_snapshot import _source_row

    source = Path(__file__).parents[1] / "engine" / "kiwoom_sniper_v2.py"
    tree = ast.parse(source.read_text())
    calls = []
    for parent in ast.walk(tree):
        for field, body in ast.iter_fields(parent):
            if not isinstance(body, list):
                continue
            for index, node in enumerate(body):
                if not (
                    isinstance(node, ast.Expr)
                    and isinstance(node.value, ast.Call)
                    and getattr(node.value.func, "id", "") == "handle_holding_state"
                ):
                    continue
                call = node.value
                if not any(k.arg == "now_ts" for k in call.keywords):
                    continue
                calls.append((body[index - 1], node))
    assert len(calls) == 2
    for assignment, node in calls:
        captured = []

        def holding(*args, **kwargs):
            assert kwargs["now_dt"].timestamp() == kwargs["now_ts"]
            captured.append(
                _source_row(
                    value=dict(bid=26200, ask=26250),
                    source="native-clock-replay",
                    observed_epoch=quote_at,
                    now_epoch=kwargs["now_ts"],
                )
            )

        scope = dict(
            time=SimpleNamespace(time=lambda: 1792538068.764918),
            datetime=datetime,
            stock={},
            code="006800",
            ws_data={},
            admin_id=1,
            current_market_regime="BULL",
            radar=None,
            ai_engine=None,
            holding_ai_engine=None,
            now_ts=1792538068.5308046,
            now=datetime.fromtimestamp(1792538068.5308046),
            handle_holding_state=holding,
        )
        exec(
            compile(
                ast.fix_missing_locations(
                    ast.Module(body=[assignment, node], type_ignores=[])
                ),
                "<native-holding-dispatch>",
                "exec",
            ),
            scope,
        )
        assert captured[0]["quality"] == expected
        assert (captured[0]["age_ms"] >= 0) is (expected == "fresh")


def _krx_aftermarket_fixture(now):
    from src.engine.scalping import holding_path_vote_policy as vote

    day = now.date().isoformat()
    ws = {
        "last_realtime_type_ts": {
            "0B": now.timestamp() - 0.1,
            "0D": now.timestamp() - 0.2,
        },
        "last_realtime_type_item": {"0B": "036930", "0D": "036930"},
        "last_realtime_type_market_suffix": {"0B": "", "0D": ""},
        "last_realtime_type_market_route": {"0B": "krx_only", "0D": "krx_only"},
        "last_realtime_type_effective_venue": {"0B": "KRX", "0D": "KRX"},
    }
    receipt = dict(
        status="verified_incumbent_loaded",
        source_date="2026-10-29",
        target_date=day,
        bundle_sha256="a" * 64,
        add_rebound_source_scope=vote.krx_aftermarket_add_scope(day),
    )
    return ws, receipt


@pytest.mark.parametrize(
    "defect",
    [
        None,
        "missing_scope",
        "stale_date",
        "bad_hash",
        "wrong_owner",
        "wrong_prompt",
        "wrong_scope_type",
        "operator_off",
        "rollout_invalid",
        "other_guard",
        "wrong_item",
        "wrong_quote_route",
        "conflicting_venue",
        "stale_trade",
        "future_quote",
        "wrong_family",
    ],
)
def test_krx_aftermarket_source_scope_requires_exact_provenance_and_guards(
    monkeypatch, defect
):
    from zoneinfo import ZoneInfo
    from src.engine.scalping import entry_setup_live_policy as entry
    from src.engine.scalping import entry_setup_scalping_rollout as rollout
    from src.engine.scalping import mechanistic_entry_runtime_policy as machine

    now = datetime(2026, 10, 30, 16, 20, tzinfo=ZoneInfo("Asia/Seoul"))
    ws, receipt = _krx_aftermarket_fixture(now)
    if defect == "missing_scope":
        receipt.pop("add_rebound_source_scope")
    if defect == "stale_date":
        receipt["target_date"] = "2026-10-29"
    if defect == "bad_hash":
        receipt["bundle_sha256"] = "bad"
    if defect == "wrong_scope_type":
        receipt["add_rebound_source_scope"]["source_only"] = 1
    if defect == "wrong_item":
        ws["last_realtime_type_item"]["0B"] = "036930_AL"
    if defect == "wrong_quote_route":
        ws["last_realtime_type_market_route"]["0D"] = "nxt_only"
    if defect == "conflicting_venue":
        ws["last_realtime_type_effective_venue"]["0B"] = "NXT"
    if defect == "stale_trade":
        ws["last_realtime_type_ts"]["0B"] = now.timestamp() - 4
    if defect == "future_quote":
        ws["last_realtime_type_ts"]["0D"] = now.timestamp() + 1
    monkeypatch.setattr(
        entry, "_enabled_by_operator", lambda **kw: defect != "operator_off"
    )
    monkeypatch.setattr(
        entry,
        "_runtime_probe_contract_errors",
        lambda **kw: ["runtime_contract_exact_rollout_scope_missing"]
        + (
            ["runtime_contract_target_date_mismatch"] if defect == "other_guard" else []
        ),
    )
    monkeypatch.setattr(
        rollout,
        "load_auto_promotion",
        lambda **kw: {"valid": defect != "rollout_invalid"},
    )
    monkeypatch.setattr(rollout, "load_rollout", lambda **kw: None)
    monkeypatch.setattr(
        machine,
        "load_effective",
        lambda **kw: {
            "bundle_sha256": "b" * 64,
            "continuous_reversal": {
                "schema": (
                    "old"
                    if defect == "wrong_family"
                    else "continuous_reversal_policy_v6"
                )
            },
        },
    )
    result = adapter.resolve_krx_aftermarket_source(
        stock_code="036930",
        ws_data=ws,
        now=now,
        position_tag="EPISODE" if defect == "wrong_owner" else "SCANNER",
        receipt=receipt,
        configured_prompt_version=(
            "wrong"
            if defect == "wrong_prompt"
            else entry.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
    )
    assert (result is not None) == (defect is None)
    if result:
        assert result["status"] == "add_rebound_krx_aftermarket_source_only"
        assert result["holding_vote_bundle_sha256"] == receipt["bundle_sha256"]


@pytest.mark.parametrize(
    "defect", [None, "wrong_venue", "wrong_market", "missing_cell", "missing_manifest"]
)
def test_krx_aftermarket_native_signal_uses_exact_cell_and_route(monkeypatch, defect):
    from src.engine.scalping import reversal_source_diagnostics as source
    from src.engine.scalping import continuous_reversal_policy as policy

    event = dict(
        epoch=100.0,
        symbol="036930",
        source_item="036930",
        venue="NXT" if defect == "wrong_venue" else "KRX",
        market="REGULAR" if defect == "wrong_market" else "AFTER",
        confirmation_price=181100,
        branch_signals={"branch": {}},
    )
    family = dict(
        schema="continuous_reversal_policy_v6",
        family_sha256="f" * 64,
        machine_cells=(
            {}
            if defect == "missing_cell"
            else {
                "036930|AFTER|GE_100000": {"routes": {"KRX": {"backend": "union_v6"}}}
            }
        ),
        operating_manifest={
            "scopes": (
                {}
                if defect == "missing_manifest"
                else {"036930|AFTER|GE_100000|KRX": ["branch"]}
            )
        },
    )
    monkeypatch.setattr(
        source, "observe_snapshot", lambda *a, **k: ((event, {}), {"reason": "ready"})
    )
    monkeypatch.setattr(
        policy,
        "_assess",
        lambda *a, **k: (
            dict(action="ENTER_NOW", policy_version="v6", matched_branches=["branch"]),
            None,
            None,
            None,
        ),
    )
    monkeypatch.setattr(adapter, "_rebound_branch", lambda branch: True)
    result = adapter.evaluate_native_rebound(
        dict(
            continuous_reversal=family,
            machine_bundle_sha256="b" * 64,
            add_rebound_source_scope={"source_only": True},
        ),
        stock_code="036930",
        ws_data={"last_realtime_type_item": {"0B": "036930"}},
        session="krx_nxt_aftermarket",
        now_ts=101,
    )
    assert result["should_add"] is (defect is None)


def test_krx_aftermarket_scope_uses_krx_operator_veto_not_nxt(monkeypatch):
    from zoneinfo import ZoneInfo
    from src.engine.scalping import entry_setup_live_policy as entry
    from src.engine.scalping import entry_setup_scalping_rollout as rollout
    from src.engine.scalping import mechanistic_entry_runtime_policy as machine

    now = datetime(2026, 10, 30, 16, 20, tzinfo=ZoneInfo("Asia/Seoul"))
    ws, receipt = _krx_aftermarket_fixture(now)
    krx_key = entry._cohort_env_key(entry.DEFAULT_COHORT)
    nxt_key = entry._cohort_env_key(("NXT", "NXT_AFTERMARKET"))
    assert krx_key != nxt_key
    monkeypatch.setenv(krx_key, "1")
    monkeypatch.setenv(nxt_key, "0")
    monkeypatch.setattr(
        entry,
        "_runtime_probe_contract_errors",
        lambda **kw: ["runtime_contract_exact_rollout_scope_missing"],
    )
    monkeypatch.setattr(rollout, "load_auto_promotion", lambda **kw: {"valid": True})
    monkeypatch.setattr(rollout, "load_rollout", lambda **kw: None)
    monkeypatch.setattr(
        machine,
        "load_effective",
        lambda **kw: dict(
            bundle_sha256="b" * 64,
            continuous_reversal={"schema": "continuous_reversal_policy_v6"},
        ),
    )
    args = dict(
        stock_code="036930",
        ws_data=ws,
        now=now,
        position_tag="SCANNER",
        receipt=receipt,
        configured_prompt_version=entry.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
    )
    assert adapter.resolve_krx_aftermarket_source(**args) is not None
    monkeypatch.setenv(krx_key, "0")
    assert adapter.resolve_krx_aftermarket_source(**args) is None
