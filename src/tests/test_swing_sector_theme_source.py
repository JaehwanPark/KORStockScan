from src.engine import swing_sector_theme_source as mod


def test_sector_theme_uses_ka90001_stock_theme_membership(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(mod, "REFERENCE_DIR", tmp_path)

    payload = mod.build_sector_theme_map(
        ["005930", "000660", "000001"],
        target_date="2026-05-20",
        token="token",
        stock_theme_fetcher=lambda token, code: {
            "thema_grp": [{"thema_grp_cd": "100", "thema_nm": "반도체"}] if code != "000001" else [],
            "return_code": 0,
            "return_msg": "정상적으로 처리되었습니다",
        },
        allow_external=False,
    )

    assert payload["mapped_code_count"] == 2
    assert payload["rows_by_code"]["005930"]["theme_tags"] == ["반도체"]
    assert payload["rows_by_code"]["000001"]["theme_source_quality"] == "missing"
    assert (tmp_path / "sector_theme_map_2026-05-20.json").exists()


def test_sector_theme_prefers_stock_theme_lookup_for_default_path(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(mod, "REFERENCE_DIR", tmp_path)
    monkeypatch.setenv("KORSTOCKSCAN_SWING_THEME_KIWOOM_CALL_INTERVAL_SEC", "0")

    calls = {"stock": 0, "group": 0}

    def stock_theme(token, code):
        calls["stock"] += 1
        return {
            "thema_grp": [{"thema_grp_cd": "100", "thema_nm": f"theme-{code}"}],
            "return_code": 0,
            "return_msg": "정상적으로 처리되었습니다",
        }

    def groups(token):
        calls["group"] += 1
        return {"thema_grp": [], "return_code": 0}

    payload = mod.build_sector_theme_map(
        ["005930", "000660"],
        target_date="2026-05-20",
        token="token",
        theme_group_fetcher=None,
        stock_theme_fetcher=stock_theme,
        allow_external=False,
    )

    assert payload["mapped_code_count"] == 2
    assert calls["stock"] == 2
    assert calls["group"] == 0
    assert payload["diagnostics"]["kiwoom"]["lookup_mode"] == "stock_theme_groups_ka90001"


def test_sector_theme_catalog_fallback_does_not_map_membership(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(mod, "REFERENCE_DIR", tmp_path)

    calls = {"groups": 0}

    def groups(token):
        calls["groups"] += 1
        return {
            "thema_grp": [{"thema_grp_cd": "100", "thema_nm": "반도체"}],
            "return_code": 0,
            "return_msg": "정상적으로 처리되었습니다",
        }

    payload = mod.build_sector_theme_map(
        ["005930"],
        target_date="2026-05-20",
        token="token",
        theme_group_fetcher=groups,
        stock_theme_fetcher=None,
        allow_external=False,
    )

    assert calls == {"groups": 1}
    assert payload["diagnostics"]["kiwoom"]["lookup_mode"] == "theme_group_catalog_only_ka90001"
    assert payload["mapped_code_count"] == 0
    assert payload["rows_by_code"]["005930"]["theme_source_quality"] == "missing"


def test_sector_theme_treats_kiwoom_error_as_source_gap(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(mod, "REFERENCE_DIR", tmp_path)

    payload = mod.build_sector_theme_map(
        ["005930"],
        target_date="2026-05-20",
        token="token",
        theme_group_fetcher=lambda token: {"return_code": 1, "return_msg": "잘못된 요청입니다"},
        stock_theme_fetcher=None,
        allow_external=False,
    )

    assert payload["diagnostics"]["kiwoom"]["status"] == "kiwoom_fetch_failed"
    assert payload["mapped_code_count"] == 0
    assert payload["rows_by_code"]["005930"]["theme_source_quality"] == "missing"


def test_sector_theme_external_fallback_only_for_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(mod, "REFERENCE_DIR", tmp_path)

    payload = mod.build_sector_theme_map(
        ["000001"],
        target_date="2026-05-20",
        token=None,
        theme_group_fetcher=lambda token: [],
        stock_theme_fetcher=None,
        external_fetcher=lambda code: {"sector": "IT", "industry": "software", "theme_tags": ["cloud"]},
        allow_external=True,
    )

    row = payload["rows_by_code"]["000001"]
    assert row["sector"] == "IT"
    assert row["theme_tags"] == ["cloud"]
    assert row["theme_source"] == "external_crawl_fallback"
    assert row["theme_source_quality"] == "fallback"


def test_sector_theme_loads_manual_sector_reference_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "CACHE_DIR", tmp_path)
    sector_path = tmp_path / "swing_sector_manual_20260520.csv"
    sector_path.write_text(
        "Issue code,Issue name,Market type,Sector code,Industry\n"
        "005930,Samsung,KOSPI,32601,Manufacture of Semiconductor\n"
        "000660,SK hynix,KOSPI,32601,Manufacture of Semiconductor\n",
        encoding="utf-8",
    )

    payload = mod.build_sector_theme_map(
        ["005930", "000660"],
        target_date="2026-05-20",
        token=None,
        manual_sector_path=sector_path,
        theme_group_fetcher=lambda token: [],
        stock_theme_fetcher=None,
        allow_external=False,
    )

    row = payload["rows_by_code"]["005930"]
    assert payload["sector_mapped_count"] == 2
    assert payload["theme_mapped_count"] == 0
    assert row["sector"] == "Manufacture of Semiconductor"
    assert row["industry"] == "Manufacture of Semiconductor"
    assert row["sector_code"] == "32601"
    assert row["market_type"] == "KOSPI"
    assert row["sector_source"] == "manual_sector_reference"
    assert row["sector_source_quality"] == "ok"
