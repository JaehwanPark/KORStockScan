"""Market regime utilities for the sniper engine."""

from src.utils.logger import log_error


MARKET_REGIME = None


def bind_market_regime_dependencies(*, market_regime=None):
    global MARKET_REGIME
    if market_regime is not None:
        MARKET_REGIME = market_regime

def init_market_regime_service():
    global MARKET_REGIME
    try:
        snap = MARKET_REGIME.refresh_if_needed(force=True)
        print(
            f"🌍 [시장환경 초기화] "
            f"risk={snap.risk_state}, "
            f"VIX={snap.vix_close:.2f}, "
            f"WTI_RSI={snap.wti_rsi:.2f}, "
            f"allow_swing={snap.allow_swing_entry}, "
            f"vol_mode={snap.volatility_mode}"
        )
    except Exception as e:
        log_error(f"🚨 시장환경 초기화 실패: {e}")

def should_block_swing_entry_by_market_regime(strategy: str):
    """
    스윙 전략(KOSPI_ML / KOSDAQ_ML / MAIN)에만 적용되는
    시장환경 필터. 스캘핑 전략에는 적용하지 않는다.
    """
    global MARKET_REGIME

    try:
        snap = MARKET_REGIME.refresh_if_needed()
        normalized = str(strategy or "").upper()

        # 스윙 전략만 적용
        if normalized not in ["KOSPI_ML", "KOSDAQ_ML", "MAIN"]:
            return False, ""

        if not snap.allow_swing_entry:
            reason = (
                f"시장환경 보류 | "
                f"risk={snap.risk_state}, "
                f"score={snap.swing_score}, "
                f"VIX={snap.vix_close:.2f}, "
                f"WTI_RSI={snap.wti_rsi:.2f}, "
                f"oil_reversal={snap.oil_reversal}, "
                f"FNG={snap.fng_value:.2f}, "
                f"fng_recovery={snap.fng_recovery}, "
                f"reasons={','.join(snap.reasons)}"
            )
            return True, reason

        return False, ""

    except Exception as e:
        # 시장환경 서비스 장애가 주문엔진 장애가 되면 안 됨
        return False, f"시장환경 조회 실패(보수적 미차단): {e}"

