#!/usr/bin/env python3
"""
Smoke test for market regime external data sources.

Checks:
1. yfinance import
2. raw yfinance response shape for VIX / WTI
3. normalized YahooMarketDataProvider output
4. fear_and_greed import and response payload
5. optional cache/fallback check mode
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


def test_yfinance_raw():
    print("\n🔍 Testing yfinance raw download")
    try:
        import yfinance as yf
    except Exception as e:
        print(f"   ❌ yfinance import failed: {e}")
        return False

    ok = True
    for ticker in ("^VIX", "CL=F"):
        print(f"\n   [{ticker}]")
        try:
            df = yf.download(
                tickers=ticker,
                period="1mo",
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            print(f"   columns_type: {type(df.columns).__name__}")
            print(f"   columns: {list(df.columns)}")
            print(f"   rows: {len(df)}")
            if df is None or df.empty:
                print("   ❌ empty dataframe")
                ok = False
                continue
            print("   tail:")
            print(df.tail(3).to_string())
        except Exception as e:
            print(f"   ❌ download failed: {e}")
            ok = False
    return ok


def test_provider_normalized():
    print("\n🔍 Testing YahooMarketDataProvider normalized output")
    try:
        from src.market_regime.data_provider import YahooMarketDataProvider
    except Exception as e:
        print(f"   ❌ provider import failed: {e}")
        return False

    provider = YahooMarketDataProvider()
    ok = True
    cases = [
        ("VIX", provider.fetch_vix_daily),
        ("WTI", provider.fetch_wti_daily),
        ("BRENT", provider.fetch_brent_daily),
    ]

    for name, fn in cases:
        print(f"\n   [{name}]")
        try:
            df = fn()
            print(f"   rows: {len(df)}")
            print(f"   columns: {list(df.columns)}")
            has_close = "close" in df.columns
            has_date = "date" in df.columns
            print(f"   has_date={has_date}, has_close={has_close}")
            if df is None or df.empty or not has_close:
                print("   ❌ normalized dataframe invalid")
                ok = False
                continue
            print("   tail:")
            print(df.tail(3).to_string(index=False))
        except Exception as e:
            print(f"   ❌ provider fetch failed: {e}")
            ok = False

    return ok


def test_fear_and_greed_package():
    print("\n🔍 Testing fear_and_greed package")
    try:
        import fear_and_greed
    except Exception as e:
        print(f"   ❌ fear_and_greed import failed: {e}")
        return False

    try:
        fg = fear_and_greed.get()
        value = getattr(fg, "value", None)
        desc = getattr(fg, "description", None)
        last_update = getattr(fg, "last_update", None)
        print(f"   value: {value}")
        print(f"   description: {desc}")
        print(f"   last_update: {last_update}")
        if value is None:
            print("   ❌ value is missing")
            return False
        print("   ✅ fear_and_greed response OK")
        return True
    except Exception as e:
        print(f"   ❌ fear_and_greed.get() failed: {e}")
        return False


def test_cache_fallback_mode():
    print("\n🔍 Testing market regime cache/fallback mode")
    try:
        from src.market_regime.service import MarketRegimeService
    except Exception as e:
        print(f"   ❌ service import failed: {e}")
        return False

    try:
        service = MarketRegimeService(refresh_minutes=0)
        cache_path = service._cache_path
        print(f"   cache_path: {cache_path}")

        snapshot = service.refresh_if_needed(force=True)
        session_date = service._resolve_session_date()
        cache_exists = cache_path.exists()
        print(
            f"   first_refresh risk={snapshot.risk_state}, score={snapshot.swing_score}"
        )
        print(f"   cache_exists={cache_exists}, session_date={session_date}")

        if cache_exists:
            try:
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
                print(f"   cache_keys: {sorted(payload.keys())}")
                print(f"   cached_session_date: {payload.get('cached_session_date')}")
            except Exception as e:
                print(f"   ⚠️ cache_read_failed: {e}")

        cached_before = service._cached_session_snapshot()
        if cached_before is None:
            print("   ⚠️ no session cache available yet; fallback test skipped")
            return cache_exists

        original_fetch_vix = service.provider.fetch_vix_daily
        original_fetch_wti = service.provider.fetch_wti_daily
        service.provider.fetch_vix_daily = lambda: __import__("pandas").DataFrame()
        service.provider.fetch_wti_daily = lambda: __import__("pandas").DataFrame()
        try:
            fallback_snapshot = service.refresh_if_needed(force=True)
        finally:
            service.provider.fetch_vix_daily = original_fetch_vix
            service.provider.fetch_wti_daily = original_fetch_wti

        used_fallback = any(
            "refresh 실패 폴백 사용" in reason for reason in fallback_snapshot.reasons
        )
        print(
            f"   fallback_risk={fallback_snapshot.risk_state}, score={fallback_snapshot.swing_score}"
        )
        print(f"   fallback_used={used_fallback}")
        print(f"   fallback_reasons={fallback_snapshot.reasons}")

        if not used_fallback:
            print("   ❌ fallback reason not detected")
            return False

        print("   ✅ cache/fallback mode OK")
        return True

    except Exception as e:
        print(f"   ❌ cache/fallback test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Market regime external data test")
    parser.add_argument(
        "--check-cache",
        action="store_true",
        help="also verify session cache creation and fallback behavior",
    )
    args = parser.parse_args()

    print("🚀 Starting market regime external data test")
    raw_ok = test_yfinance_raw()
    provider_ok = test_provider_normalized()
    fng_ok = test_fear_and_greed_package()
    cache_ok = True
    if args.check_cache:
        cache_ok = test_cache_fallback_mode()

    print("\n📌 Summary")
    print(f"   yfinance raw: {'OK' if raw_ok else 'FAIL'}")
    print(f"   provider normalized: {'OK' if provider_ok else 'FAIL'}")
    print(f"   fear_and_greed: {'OK' if fng_ok else 'FAIL'}")
    if args.check_cache:
        print(f"   cache/fallback: {'OK' if cache_ok else 'FAIL'}")

    if raw_ok and provider_ok and fng_ok and cache_ok:
        print("\n✅ All checks passed.")
        return 0

    print("\n⚠️ One or more checks failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
