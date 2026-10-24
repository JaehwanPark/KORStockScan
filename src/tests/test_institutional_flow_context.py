import gzip
import json

from src.engine.lifecycle.archive import institutional_flow_context_readers as mod


def _write_gzip_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_normalize_institutional_flow_context_builds_source_only_features():
    context = mod.normalize_institutional_flow_context(
        "A005930",
        daily_summary={"smart_money_net": 1200},
        period_summary={"foreign_net": 500, "inst_net": 700},
        intraday_chart_qty={"foreign_net": 30, "inst_net": 40},
        intraday_chart_amt={"foreign_net": 3000, "inst_net": 4000},
        ws_data={
            "received_types": {"0F", "0w"},
            "foreign_broker_net_est_qty": 90,
            "foreign_broker_net_est_delta_qty": 10,
            "prog_net_qty": 100,
            "prog_delta_qty": 20,
            "prog_net_amt": 5000,
        },
    )

    assert context["stock_code"] == "005930"
    assert context["foreign_net_intraday_qty"] == 30
    assert context["institution_net_intraday_qty"] == 40
    assert context["dual_net_buy"] is True
    assert context["institutional_flow_regime"] == "DUAL_ACCUMULATION"
    assert context["institutional_flow_status"] == "OK"
    assert context["runtime_effect"] is False
    assert context["decision_authority"] == "archive_offline_source_only"


def test_retired_resolver_never_collects_with_or_without_token(monkeypatch):
    from src.utils import kiwoom_utils

    def forbidden(*args, **kwargs):
        raise AssertionError("retired resolver attempted REST collection")

    for name in (
        "get_investor_flow_summary_ka10059",
        "get_investor_period_total_ka10061",
    ):
        monkeypatch.setattr(kiwoom_utils, name, forbidden)
    for token in (None, "T"):
        result = mod.resolve_institutional_flow_context(
            "005930", token=token, target_date="2026-10-12"
        )
        assert result["institutional_flow_status"] == "RETIRED_NO_COLLECTION"
        assert result["runtime_effect"] is False


def test_load_pipeline_event_codes_reads_gzip_sibling(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path / "pipeline_events")
    _write_gzip_jsonl(
        tmp_path / "pipeline_events" / "pipeline_events_2026-05-20.jsonl.gz",
        [
            {"stock_code": "A005930", "fields": {}},
            {"fields": {"stock_code": "000660"}},
            {"stock_code": "005930", "fields": {}},
        ],
    )

    assert mod._load_pipeline_event_codes("2026-05-20") == ["005930", "000660"]


def test_retired_current_producer_preserves_prior_and_has_no_authority(
    tmp_path, monkeypatch
):
    import importlib

    current = importlib.import_module("src.engine.institutional_flow_context")
    prior = tmp_path / "prior.json"
    prior.write_text("original")

    def forbidden(*a, **kw):
        raise AssertionError("retired producer accessed storage")

    monkeypatch.setattr(type(prior), "write_text", forbidden)
    monkeypatch.setattr(type(prior), "read_text", forbidden)
    result = current.build_institutional_flow_context_report("2026-10-12")
    assert result["status"] == "retired" and result["allowed_runtime_apply"] is False
