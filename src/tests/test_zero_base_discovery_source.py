from datetime import datetime
from zoneinfo import ZoneInfo

from src.scanners.zero_base_discovery_source import fetch_discovery_panels
from src.utils.kiwoom_read_request_control import REQUEST_CLASS_SOURCE_ONLY


T0 = datetime(2026, 9, 28, 10, 0, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()


def test_four_exact_route_panels_keep_unobserved_scope_and_shared_budget():
    calls = []

    def fetcher(_token, **kwargs):
        calls.append(kwargs)
        code = "123456_NX" if kwargs["stex_tp"] == "2" else "123456"
        return ([{
            "Code": "123456", "RawInstrumentCode": code, "Name": "TEST",
            "Price": 10000, "Volume": 1000, "ChangeRate": 1.5,
        }], {
            "response_contract_status": "verified_success",
            "read_rate_control_status": "admitted",
            "rest_received_ts_ms": int((T0 + 1) * 1000),
            "response_page_count": 10,
            "continuous_page_limit_reached": True,
        })

    result = fetch_discovery_panels("token", now_epoch=T0, fetcher=fetcher)

    assert [(row["market"], row["venue"]) for row in result["panels"]] == [
        ("KOSPI", "KRX"), ("KOSDAQ", "KRX"),
        ("KOSPI", "NXT"), ("KOSDAQ", "NXT"),
    ]
    assert len(result["observations"]) == 4
    assert {row["source_scope"] for row in result["observations"]} == {"observed_panel"}
    assert all(row["page_limit_reached"] for row in result["panels"])
    assert all(call["request_class"] == REQUEST_CLASS_SOURCE_ONLY for call in calls)
    assert all(call["read_rate_max_wait_sec"] == 3.0 for call in calls)
    assert all(call["limit"] == 200 and call["trde_qty_cnd"] == "0000" for call in calls)
    assert len({row["source_sha256"] for row in result["observations"]}) == 4


def test_failed_or_conflicting_route_is_not_discovered():
    index = 0

    def fetcher(_token, **_kwargs):
        nonlocal index
        index += 1
        if index == 1:
            raise TimeoutError("source timeout")
        code = "123456_NX" if index == 2 else "123456"
        return ([{
            "Code": "123456", "RawInstrumentCode": code, "Name": "TEST",
            "Price": 10000, "Volume": 1000, "ChangeRate": 1.5,
        }], {
            "response_contract_status": "verified_success",
            "read_rate_control_status": "admitted",
            "rest_received_ts_ms": int((T0 + 1) * 1000),
        })

    result = fetch_discovery_panels("token", now_epoch=T0, fetcher=fetcher)

    assert result["panels"][0]["status"] == "source_unavailable"
    assert result["panels"][1]["rejected_count"] == 1
    assert len(result["observations"]) == 2


def test_missing_response_clock_is_not_promoted_as_current_quote():
    def fetcher(_token, **_kwargs):
        return ([{"Code": "123456", "Name": "TEST", "Price": 10000,
                  "Volume": 1000, "ChangeRate": 1.0}], {
            "response_contract_status": "verified_success",
            "read_rate_control_status": "admitted",
        })

    result = fetch_discovery_panels("token", now_epoch=T0, fetcher=fetcher)
    assert not result["observations"]
    assert all(row["status"] == "source_unavailable" for row in result["panels"])
