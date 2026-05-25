from src.scanners import kosdaq_scanner


def test_build_kosdaq_candidate_map_normalizes_codes_and_skips_empty_rows():
    candidates = kosdaq_scanner.build_kosdaq_candidate_map(
        raw_targets=[
            {"Code": "A005930", "Name": "삼성전자", "Price": "70000", "FluRate": 2.1},
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
    assert candidates["005930"]["spike_rate"] == 31.5
    assert candidates["000660"]["source"] == "SUPERNOVA"
    assert candidates["000660"]["Code"] == "000660"
