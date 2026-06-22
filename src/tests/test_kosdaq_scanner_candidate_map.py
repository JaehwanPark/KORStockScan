from src.scanners import kosdaq_scanner


def test_build_kosdaq_candidate_map_normalizes_codes_and_skips_empty_rows():
    candidates = kosdaq_scanner.build_kosdaq_candidate_map(
        raw_targets=[
            {"Code": "A005930", "Name": "삼성전자", "Price": "70000", "OpenFluRate": 2.1, "DayFluRate": 7.8},
            {"Code": "", "Name": "빈코드"},
        ],
        supernova_targets=[
            {"code": "005930_AL", "name": "삼성전자", "spike_rate": 31.5},
            {"Code": None, "Name": "누락코드"},
            {"code": "000660.0", "name": "SK하이닉스", "cur_prc": "180000", "flu_rate": 1.2},
        ],
    )

    assert set(candidates) == {"005930", "000660"}
    assert candidates["005930"]["Code"] == "005930"
    assert candidates["005930"]["source"] == "TOP"
    assert candidates["005930"]["flu_rate"] == 2.1
    assert candidates["005930"]["open_flu_rate"] == 2.1
    assert candidates["005930"]["day_flu_rate"] == 7.8
    assert candidates["005930"]["flu_rate_metric"] == "open_flu_rate"
    assert candidates["005930"]["spike_rate"] == 31.5
    assert candidates["000660"]["source"] == "SUPERNOVA"
    assert candidates["000660"]["Code"] == "000660"


def test_kosdaq_runner_picks_are_report_only_not_watchlist():
    picks = [
        {"Code": "123456", "Name": "테스트", "Prob": 0.72, "Position": "MIDDLE"},
    ]

    assert kosdaq_scanner.filter_kosdaq_watchlist_picks(picks) == []
