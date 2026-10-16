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
    stock = dict(code="005930", strategy="SCALPING", position_tag="SCALP_BASE",
        watch_origin=fixed.WATCH_ORIGIN, watch_admission_id=fixed.new_admission_id(at, route),
        watch_generation_id=fixed.generation_id(at, route), status="HOLDING")
    before = deepcopy(stock)
    assert adapter.holding_policy_position_tag(stock) == "SCANNER"
    assert stock == before
    for field in ("code", "watch_admission_id", "watch_generation_id", "position_tag"):
        with pytest.raises(ValueError):
            adapter.holding_policy_position_tag(dict(stock, **{field: "wrong"}))


def test_policy_adapter_does_not_adopt_other_owners():
    assert adapter.holding_policy_position_tag(dict(position_tag="SCALP_BASE")) == "SCALP_BASE"
    assert adapter.holding_policy_position_tag(dict(position_tag="EPISODE")) == "EPISODE"


def test_rebound_definition_follows_refinements_but_excludes_momentum_and_breakout():
    from src.engine.scalping import reversal_cumulative_catalog as catalog
    assert adapter._rebound_branch("legacy_dd5_ge_1_2_v1")
    assert adapter._rebound_branch("manual_path_918aff358c3edb8c")
    assert not adapter._rebound_branch("manual_path_35c2d4b8fb178441")
    additions = catalog.GROUPS["samsung|REGULAR|ALL|SOR"]["additions"]
    assert adapter._rebound_branch(additions["A10"])
    assert not adapter._rebound_branch(additions["A14"])
    for original, bid in catalog.GROUPS["samsung|REGULAR|ALL|SOR"]["refinements"]["F01"].items():
        assert adapter._rebound_branch(bid) == adapter._rebound_branch(original)


@pytest.mark.parametrize("gap", [None, "missing", "expired", "future", "symbol", "item", "continuation", "blocked"])
def test_native_read_is_unclaimed_same_scope_fresh_and_uses_current_dispatch(monkeypatch, gap):
    from src.engine.scalping import reversal_source_diagnostics as source
    from src.engine.scalping import continuous_reversal_policy as policy
    event = dict(epoch=100., symbol="005930", source_item="005930_AL", branch_signals={"branch": {}})
    if gap == "expired": event["epoch"] = 94.
    if gap == "future": event["epoch"] = 102.
    if gap == "symbol": event["symbol"] = "000001"
    if gap == "item": event["source_item"] = "005930_NX"
    calls = []
    def observe(*args, **kwargs):
        calls.append((args, kwargs))
        return (None if gap == "missing" else (event, {})), {"reason": "ready"}
    monkeypatch.setattr(source, "observe_snapshot", observe)
    monkeypatch.setattr(source, "claim_snapshot_with_receipt", lambda *a, **k: pytest.fail("ADD stole entry claim"))
    monkeypatch.setattr(policy, "assess", lambda *a, **k: pytest.fail("ADD wrote Main status"))
    def assess(family, snapshot, **kwargs):
        assert family["schema"] == "continuous_reversal_policy_v6"
        return dict(action="BLOCK" if gap == "blocked" else "ENTER_NOW",
                    policy_version=family["schema"], matched_branches=["manual_path_35c2d4b8fb178441"
                        if gap == "continuation" else "legacy_dd5_ge_1_2_v1"]), None, None, None
    monkeypatch.setattr(policy, "_assess", assess)
    result = adapter.evaluate_native_rebound(dict(machine_bundle_sha256="a" * 64,
        continuous_reversal=dict(schema="continuous_reversal_policy_v6", family_sha256="b" * 64)),
        stock_code="005930", ws_data={"last_realtime_type_item": {"0B": "005930_AL"}},
        session="krx_regular", now_ts=100.)
    assert result["should_add"] is (gap is None)
    assert calls[0][0] == ("005930", "SOR", "krx_regular")
    if gap is None:
        assert result["native_signal_expires_at"] == 105.
