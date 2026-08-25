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
    monkeypatch.setattr(
        kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}"
    )

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


def test_unfilled_order_snapshot_ka10075_preserves_exchange_fields(monkeypatch):
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
        return [
            {
                "oso": [
                    {
                        "stk_cd": "A440110",
                        "stk_nm": "TEST",
                        "io_tp_nm": "+매수",
                        "ord_qty": "8",
                        "oso_qty": "3",
                        "ord_pric": "166300",
                        "ord_no": "0059624",
                        "orig_ord_no": "0000000",
                        "stex_tp": "1",
                        "stex_tp_txt": "KRX",
                        "sor_yn": "N",
                    }
                ],
                "return_code": 0,
            }
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)
    monkeypatch.setattr(
        kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}"
    )

    rows = kiwoom_utils.get_unfilled_order_snapshot_ka10075(
        "token",
        stk_cd="440110",
        stex_tp="0",
    )

    assert calls == [
        {
            "url": "https://example.test/api/dostk/acnt",
            "token": "token",
            "api_id": "ka10075",
            "payload": {
                "all_stk_tp": "1",
                "trde_tp": "0",
                "stk_cd": "440110",
                "stex_tp": "0",
            },
            "use_continuous": True,
        }
    ]
    assert rows[0]["code"] == "440110"
    assert rows[0]["ord_no"] == "0059624"
    assert rows[0]["qty"] == 8
    assert rows[0]["remaining_qty"] == 3
    assert rows[0]["unit_price"] == 166300
    assert rows[0]["stex_tp"] == "1"
    assert rows[0]["stex_tp_txt"] == "KRX"
    assert rows[0]["sor_yn"] == "N"


def test_unfilled_order_snapshot_ignores_zero_execution_price_placeholder(
    monkeypatch,
):
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [
            {
                "oso": [
                    {
                        "stk_cd": "005930",
                        "io_tp_nm": "+매수",
                        "ord_qty": "5",
                        "oso_qty": "5",
                        "cntr_pric": "0",
                        "ord_pric": "276000",
                        "ord_no": "0004596",
                    }
                ],
                "return_code": 0,
            }
        ],
    )

    rows = kiwoom_utils.get_unfilled_order_snapshot_ka10075("token")

    assert rows[0]["unit_price"] == 276000


def test_unfilled_order_snapshot_uses_order_price_for_partial_fill_identity(
    monkeypatch,
):
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [
            {
                "oso": [
                    {
                        "stk_cd": "005930",
                        "io_tp_nm": "+매수",
                        "ord_qty": "5",
                        "oso_qty": "3",
                        "cntr_pric": "275500",
                        "ord_pric": "276000",
                        "ord_no": "0004596",
                    }
                ],
                "return_code": 0,
            }
        ],
    )

    rows = kiwoom_utils.get_unfilled_order_snapshot_ka10075("token")

    assert rows[0]["unit_price"] == 276000
    assert rows[0]["remaining_qty"] == 3


def test_kt00007_preserves_open_quantity_and_official_original_order_key(
    monkeypatch,
):
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [
            {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "stk_cd": "A005930",
                        "io_tp_nm": "현금매수",
                        "ord_qty": "5",
                        "ord_remnq": "5",
                        "cntr_uv": "0",
                        "ord_uv": "274500",
                        "ord_no": "0004597",
                        "ori_ord": "0001234",
                    }
                ],
                "return_code": 0,
            }
        ],
    )

    rows = kiwoom_utils.get_order_reference_snapshot_kt00007("token")

    assert rows[0]["unit_price"] == 274500
    assert rows[0]["remaining_qty"] == 5
    assert rows[0]["orig_ord_no"] == "0001234"


def test_kt00007_partial_fill_uses_order_price_for_open_order_identity(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [
            {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "stk_cd": "A005930",
                        "io_tp_nm": "현금매수",
                        "ord_qty": "5",
                        "cntr_qty": "2",
                        "ord_remnq": "3",
                        "cntr_uv": "275500",
                        "ord_uv": "276000",
                        "ord_no": "0004597",
                        "ori_ord": "0001234",
                    }
                ],
                "return_code": 0,
            }
        ],
    )

    rows = kiwoom_utils.get_order_reference_snapshot_kt00007("token")

    assert rows[0]["unit_price"] == 276000
    assert rows[0]["remaining_qty"] == 3


def test_kt00007_completed_fill_keeps_execution_price_identity(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: [
            {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "stk_cd": "A005930",
                        "io_tp_nm": "현금매수",
                        "ord_qty": "5",
                        "cntr_qty": "5",
                        "ord_remnq": "0",
                        "cntr_uv": "275500",
                        "ord_uv": "276000",
                        "ord_no": "0004597",
                        "ori_ord": "0001234",
                    }
                ],
                "return_code": 0,
            }
        ],
    )

    rows = kiwoom_utils.get_order_reference_snapshot_kt00007("token")

    assert rows[0]["unit_price"] == 275500
    assert rows[0]["remaining_qty"] == 0


def test_unfilled_order_snapshot_meta_distinguishes_empty_success_from_failure(
    monkeypatch,
):
    response = [{"oso": [], "return_code": 0}]
    calls = []

    def fake_fetch(**kwargs):
        calls.append(kwargs)
        return (
            response,
            {"api_id": "ka10075", "page_count": 1, "rest_received_ts_ms": 123},
        )

    monkeypatch.setattr(
        kiwoom_utils,
        "_fetch_kiwoom_api_continuous_with_meta",
        fake_fetch,
    )
    monkeypatch.setattr(
        kiwoom_utils, "get_api_url", lambda path: f"https://example.test{path}"
    )

    rows, meta = kiwoom_utils.get_unfilled_order_snapshot_ka10075_with_meta("token")

    assert rows == []
    assert meta["request_succeeded"] is True
    assert meta["response_codes"] == ["0"]
    assert meta["received_count"] == 0
    assert calls[-1]["payload"] == {
        "all_stk_tp": "0",
        "trde_tp": "0",
        "stk_cd": "",
        "stex_tp": "0",
    }

    response[:] = [{"return_code": 17, "return_msg": "rejected"}]
    rows, meta = kiwoom_utils.get_unfilled_order_snapshot_ka10075_with_meta("token")

    assert rows == []
    assert meta["request_succeeded"] is False
    assert meta["response_codes"] == ["17"]


def test_ka10075_meta_surfaces_dropped_raw_order_identity(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "_fetch_kiwoom_api_continuous_with_meta",
        lambda **_kwargs: (
            [
                {
                    "oso": [
                        {
                            "stk_cd": "",
                            "ord_no": "0000456",
                            "ord_qty": "5",
                            "ord_remnq": "5",
                            "io_tp_nm": "매도",
                            "stex_tp": "1",
                        }
                    ],
                    "return_code": 0,
                }
            ],
            {"api_id": "ka10075", "page_count": 1},
        ),
    )

    rows, meta = kiwoom_utils.get_unfilled_order_snapshot_ka10075_with_meta("token")

    assert rows == []
    assert meta["raw_order_row_count"] == 1
    assert meta["normalized_order_row_count"] == 0
    assert meta["normalization_gap_count"] == 1
    assert meta["normalization_contract_complete"] is False


def test_ka10075_meta_surfaces_malformed_numeric_and_side_contract(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "_fetch_kiwoom_api_continuous_with_meta",
        lambda **_kwargs: (
            [
                {
                    "oso": [
                        {
                            "stk_cd": "005930",
                            "ord_no": "0000456",
                            "ord_qty": "1e2",
                            "ord_remnq": "5",
                            "io_tp_nm": "UNKNOWN",
                            "stex_tp": "1",
                        }
                    ],
                    "return_code": 0,
                }
            ],
            {"api_id": "ka10075", "page_count": 1},
        ),
    )

    rows, meta = kiwoom_utils.get_unfilled_order_snapshot_ka10075_with_meta("token")

    assert len(rows) == 1
    assert meta["normalization_gap_count"] == 0
    assert meta["contract_incomplete_count"] == 1
    assert meta["normalization_contract_complete"] is False


def test_order_snapshot_meta_rejects_missing_status_and_list_shape(monkeypatch):
    responses = iter(
        (
            ([{"oso": []}], {"api_id": "ka10075", "page_count": 1}),
            ([{"return_code": 0}], {"api_id": "ka10075", "page_count": 1}),
            ([None], {"api_id": "ka10075", "page_count": 1}),
        )
    )
    monkeypatch.setattr(
        kiwoom_utils,
        "_fetch_kiwoom_api_continuous_with_meta",
        lambda **_kwargs: next(responses),
    )

    for _ in range(3):
        rows, meta = kiwoom_utils.get_unfilled_order_snapshot_ka10075_with_meta("token")
        assert rows == []
        assert meta["request_succeeded"] is False
        assert meta["normalization_contract_complete"] is False


def test_s15_kt00005_strict_meta_rejects_one_malformed_venue(monkeypatch):
    responses = iter(
        (
            [
                {
                    "return_code": 0,
                    "stk_cntr_remn": [
                        {
                            "stk_cd": "A123456",
                            "stk_nm": "TEST",
                            "cur_qty": "5",
                            "buy_uv": "10000",
                        }
                    ],
                }
            ],
            [
                {
                    "return_code": 0,
                    "stk_cntr_remn": [
                        {
                            "stk_cd": "A654321",
                            "stk_nm": "BAD",
                            "cur_qty": "1e2",
                            "buy_uv": "10000",
                        }
                    ],
                }
            ],
        )
    )
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: next(responses),
    )

    rows, exchanges, meta = kiwoom_utils.get_account_balance_kt00005_with_meta("token")

    assert rows == [{"code": "123456", "name": "TEST", "qty": 5, "buy_price": 10_000}]
    assert exchanges == {"KRX"}
    assert meta["normalization_contract_complete"] is False


def test_s15_kt00005_strict_meta_rejects_duplicate_symbol_venue(monkeypatch):
    responses = iter(
        (
            [
                {
                    "return_code": 0,
                    "stk_cntr_remn": [
                        {
                            "stk_cd": "A123456",
                            "stk_nm": "ONE",
                            "cur_qty": "5",
                            "buy_uv": "10000",
                        },
                        {
                            "stk_cd": "A123456",
                            "stk_nm": "TWO",
                            "cur_qty": "4",
                            "buy_uv": "10000",
                        },
                    ],
                }
            ],
            [{"return_code": 0, "stk_cntr_remn": []}],
        )
    )
    monkeypatch.setattr(
        kiwoom_utils,
        "fetch_kiwoom_api_continuous",
        lambda **_kwargs: next(responses),
    )

    rows, exchanges, meta = kiwoom_utils.get_account_balance_kt00005_with_meta("token")

    assert rows == []
    assert exchanges == {"NXT"}
    assert meta["normalization_contract_complete"] is False


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
