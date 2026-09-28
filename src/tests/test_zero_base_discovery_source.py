from datetime import datetime
from zoneinfo import ZoneInfo

from src.scanners.zero_base_discovery_source import fetch_discovery_panels
from src.utils import kiwoom_utils
from src.utils.kiwoom_read_request_control import REQUEST_CLASS_SOURCE_ONLY


T0 = datetime(2026, 9, 28, 10, 0, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()


def empty_activity(_token, **_kwargs):
    return [], {
        "response_contract_status": "verified_success",
        "read_rate_control_status": "admitted",
        "rest_received_ts_ms": int((T0 + 1) * 1000),
    }


def test_integrated_panels_keep_unobserved_scope_and_shared_budget():
    calls = []

    def fetcher(_token, **kwargs):
        calls.append(kwargs)
        base = "123450" if kwargs["mrkt_tp"] == "001" else "123460"
        code = base + "_AL"
        return ([{
            "Code": base, "RawInstrumentCode": code, "Name": "TEST",
            "Price": 10000, "Volume": 1000, "ChangeRate": 1.5,
        }], {
            "response_contract_status": "verified_success",
            "read_rate_control_status": "admitted",
            "rest_received_ts_ms": int((T0 + 1) * 1000),
            "response_page_count": 10,
            "continuous_page_limit_reached": True,
        })

    result = fetch_discovery_panels("token", now_epoch=T0, fetcher=fetcher,
                                    activity_fetcher=empty_activity)

    assert [(row["kind"], row["market"], row["venue"]) for row in result["panels"]] == [
        ("activity", "KOSPI", "SOR"), ("activity", "KOSDAQ", "SOR"),
        ("gainers", "KOSPI", "SOR"), ("gainers", "KOSDAQ", "SOR"),
    ]
    assert len(result["observations"]) == 2
    assert all(row["route"] == "krx_nxt_integrated" for row in result["observations"])
    assert all(call["stex_tp"] == "3" for call in calls)
    assert {row["source_scope"] for row in result["observations"]} == {"observed_panel"}
    assert all(row["page_limit_reached"] for row in result["panels"][2:])
    assert all(call["request_class"] == REQUEST_CLASS_SOURCE_ONLY for call in calls)
    assert all(call["read_rate_max_wait_sec"] == 3.0 for call in calls)
    assert all(call["limit"] == 200 and call["trde_qty_cnd"] == "0000" for call in calls)
    assert len({row["source_sha256"] for row in result["observations"]}) == 2


def test_failed_or_conflicting_route_is_not_discovered():
    index = 0

    def fetcher(_token, **_kwargs):
        nonlocal index
        index += 1
        if index == 1:
            raise TimeoutError("source timeout")
        code = "123456_NX"
        return ([{
            "Code": "123456", "RawInstrumentCode": code, "Name": "TEST",
            "Price": 10000, "Volume": 1000, "ChangeRate": 1.5,
        }], {
            "response_contract_status": "verified_success",
            "read_rate_control_status": "admitted",
            "rest_received_ts_ms": int((T0 + 1) * 1000),
        })

    result = fetch_discovery_panels("token", now_epoch=T0, fetcher=fetcher,
                                    activity_fetcher=empty_activity)

    assert result["panels"][2]["status"] == "source_unavailable"
    assert result["panels"][3]["rejected_count"] == 1
    assert result["observations"] == []


def test_missing_response_clock_is_not_promoted_as_current_quote():
    def fetcher(_token, **_kwargs):
        return ([{"Code": "123456", "Name": "TEST", "Price": 10000,
                  "Volume": 1000, "ChangeRate": 1.0}], {
            "response_contract_status": "verified_success",
            "read_rate_control_status": "admitted",
        })

    result = fetch_discovery_panels("token", now_epoch=T0, fetcher=fetcher,
                                    activity_fetcher=empty_activity)
    assert not result["observations"]
    assert all(row["status"] == "source_unavailable" for row in result["panels"][2:])


def test_premarket_reads_nxt_panels_with_exact_nx_route():
    epoch = datetime(2026, 9, 28, 8, 10,
                     tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    calls = []

    def fetcher(_token, **kwargs):
        calls.append(kwargs)
        base = "123450" if kwargs["mrkt_tp"] == "001" else "123460"
        return ([{"Code": base, "RawInstrumentCode": base + "_NX",
                  "Name": "TEST", "Price": 10000, "Volume": 1000,
                  "ChangeRate": 1.5}], {
            "response_contract_status": "verified_success",
            "read_rate_control_status": "admitted",
            "rest_received_ts_ms": int((epoch + 1) * 1000),
        })

    result = fetch_discovery_panels("token", now_epoch=epoch, fetcher=fetcher,
                                    activity_fetcher=lambda *_args, **_kwargs: ([], {
                                        "response_contract_status": "verified_success",
                                        "read_rate_control_status": "admitted",
                                        "rest_received_ts_ms": int((epoch + 1) * 1000),
                                    }))
    assert len(result["observations"]) == 2
    assert all(row["venue"] == "NXT" and row["route"] == "nxt_only"
               for row in result["observations"])
    assert all(call["stex_tp"] == "2" for call in calls)


def test_recent_volume_panel_precedes_gainer_without_duplicate_generation():
    def activity(_token, **kwargs):
        assert kwargs["stex_tp"] == "3"
        return ([{"Code": "123450", "RawInstrumentCode": "123450_AL",
                 "Name": "ACTIVE", "Price": 10000, "Volume": 10000,
                 "ChangeRate": 1.0, "SurgeQty": 5000, "PreSig": "2"}], {
            "response_contract_status": "verified_success",
            "read_rate_control_status": "admitted",
            "rest_received_ts_ms": int((T0 + 1) * 1000),
        })

    def gainers(_token, **_kwargs):
        return ([{"Code": "123450", "RawInstrumentCode": "123450_AL",
                 "Name": "ACTIVE", "Price": 10000, "Volume": 10000,
                 "ChangeRate": 1.0}], {
            "response_contract_status": "verified_success",
            "read_rate_control_status": "admitted",
            "rest_received_ts_ms": int((T0 + 2) * 1000),
        })

    result = fetch_discovery_panels("token", now_epoch=T0, fetcher=gainers,
                                    activity_fetcher=activity)
    assert len(result["observations"]) == 1
    assert result["observations"][0]["source_kind"] == "activity"
    assert result["observations"][0]["route"] == "krx_nxt_integrated"
    assert result["panels"][0]["eligible_count"] == 1
    assert result["panels"][2]["eligible_count"] == 1


def test_activity_adapter_keeps_source_only_contract_and_equity_filter(monkeypatch):
    calls = []

    def transport(**kwargs):
        calls.append(kwargs)
        return ([{"return_code": 0, "trde_qty_sdnin": [
            {"stk_cd": "123450_AL", "stk_nm": "ACTIVE", "cur_prc": "+10000",
             "flu_rt": "+1.20", "now_trde_qty": "6000", "sdnin_qty": "+5000",
             "pred_pre_sig": "2"},
            {"stk_cd": "0010F0_AL", "stk_nm": "NON EQUITY", "cur_prc": "+10000",
             "flu_rt": "+2.00", "now_trde_qty": "6000", "sdnin_qty": "+5000"},
        ]}], {"read_rate_control_status": "admitted",
              "rest_received_ts_ms": int((T0 + 1) * 1000)})

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", transport)
    rows, meta = kiwoom_utils.get_zero_base_volume_surge_ka10023(
        "token", mrkt_tp="001", stex_tp="3")
    assert len(rows) == 1
    assert rows[0]["RawInstrumentCode"] == "123450_AL"
    assert meta["response_contract_status"] == "verified_success"
    assert calls[0]["api_id"] == "ka10023"
    assert calls[0]["payload"] == {
        "mrkt_tp": "001", "sort_tp": "1", "tm_tp": "1", "tm": "5",
        "trde_qty_tp": "5", "stk_cnd": "4", "pric_tp": "0", "stex_tp": "3",
    }
    assert calls[0]["request_class"] == REQUEST_CLASS_SOURCE_ONLY
    assert calls[0]["use_continuous"] is False


def test_transition_does_not_fetch_panels():
    epoch = datetime(2026, 9, 28, 15, 40,
                     tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    result = fetch_discovery_panels(
        "token", now_epoch=epoch,
        fetcher=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("transition panel must not be fetched")
        ),
    )
    assert result["source_status"] == "integrated_buy_session_unavailable"
    assert result["observations"] == []
