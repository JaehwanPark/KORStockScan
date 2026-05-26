from src.utils import kiwoom_utils


def test_order_reference_snapshot_2nd_pass_uses_finalized_params(monkeypatch):
    calls = []

    def fake_fetch(*, url, token, api_id, payload, use_continuous):
        calls.append(
            {
                "url": url,
                "token": token,
                "api_id": api_id,
                "payload": dict(payload),
                "use_continuous": use_continuous,
            }
        )
        if api_id == "kt00007":
            return [
                {
                    "trde_dt": "20260415",
                    "acnt_ord_cntr_prps_dtl": [
                        {
                            "stk_cd": "A189300",
                            "stk_nm": "인텔리안테크",
                            "io_tp_nm": "현금매수",
                            "ord_qty": "7",
                            "cntr_qty": "7",
                            "ord_uv": "133600",
                            "cntr_uv": "133610",
                            "ord_no": "0412345",
                            "ori_ord": "0000000",
                        }
                    ],
                }
            ]
        return [
            {
                "dt": "20260415",
                "list": [
                    {
                        "stk_cd": "189300",
                        "stk_nm": "인텔리안테크",
                        "io_tp_nm": "+매수",
                        "ord_qty": "7",
                        "cntr_qty": "7",
                        "ord_pric": "133600",
                        "cntr_pric": "133610",
                        "ord_no": "0412345",
                        "orig_ord_no": "0000000",
                    }
                ],
            }
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)
    monkeypatch.setattr(kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}")

    rows = kiwoom_utils.get_order_reference_snapshot_2nd_pass(
        "token",
        qry_tp="0",
        stk_bond_tp="0",
    )

    assert len(calls) == 2
    assert {item["api_id"] for item in calls} == {"kt00007", "ka10076"}
    kt_call = next(item for item in calls if item["api_id"] == "kt00007")
    ka_call = next(item for item in calls if item["api_id"] == "ka10076")
    assert kt_call["url"] == "https://example.test/api/dostk/acnt"
    assert kt_call["payload"] == {
        "ord_dt": "",
        "qry_tp": "1",
        "stk_bond_tp": "0",
        "sell_tp": "0",
        "stk_cd": "",
        "fr_ord_no": "",
        "dmst_stex_tp": "%",
    }
    assert ka_call["url"] == "https://example.test/api/dostk/acnt"
    assert ka_call["payload"] == {
        "stk_cd": "",
        "qry_tp": "0",
        "sell_tp": "0",
        "ord_no": "",
        "stex_tp": "0",
    }
    assert len(rows) == 1
    assert rows[0]["code"] == "189300"
    assert rows[0]["side"] == "매수"
    assert rows[0]["qty"] == 7
    assert rows[0]["unit_price"] == 133610
    assert rows[0]["ord_no"] == "0412345"
    assert rows[0]["orig_ord_no"] == "0000000"


def test_find_order_reference_match_by_code_side_qty_price():
    rows = [
        {
            "code": "189300",
            "side": "매수",
            "qty": 7,
            "unit_price": 133610,
            "ord_no": "0412345",
            "orig_ord_no": "0000000",
        },
        {
            "code": "189300",
            "side": "매도",
            "qty": 7,
            "unit_price": 133610,
            "ord_no": "0412350",
            "orig_ord_no": "0412345",
        },
    ]

    match = kiwoom_utils.find_order_reference_match(
        rows,
        code="189300",
        side="매수",
        qty=7,
        unit_price=133611,
        max_price_diff=1,
    )

    assert match is not None
    assert match["ord_no"] == "0412345"
