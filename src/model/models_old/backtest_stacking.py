import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# ==========================================
# 1. 디렉토리 및 DB 경로 설정
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

PRED_FILE = os.path.join(DATA_DIR, "ai_predictions.csv")

# 🎯 PostgreSQL 연결 설정
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://quant_admin:quant_password_123!@localhost:5432/korstockscan",
)
engine = create_engine(DB_URL)


# ==========================================
# 2. 백테스트 메인 로직
# ==========================================
def run_backtest(threshold=0.70, fee_rate=0.0023):
    # fee_rate: 0.23% (증권사 수수료 + 증권거래세 등 보수적 반영)
    print(f"🚀 스태킹 앙상블 정밀 백테스트 시작 (임계값: {threshold})")

    try:
        df_pred = pd.read_csv(PRED_FILE)
    except Exception as e:
        print(f"❌ 예측 결과 파일(ai_predictions.csv)을 찾을 수 없습니다: {e}")
        return

    # 설정한 임계값 이상의 시그널만 필터링
    signals = df_pred[df_pred["Stacking_Prob"] >= threshold].copy()
    signals["Date"] = pd.to_datetime(signals["Date"])

    if signals.empty:
        print("[-] 해당 임계값을 넘는 매수 시그널이 없어 백테스트를 종료합니다.")
        return

    print(f"✅ 총 {len(signals)}개의 매수 타점이 필터링되었습니다.")
    print("[1/2] 실제 가격 변동 추적을 위해 PostgreSQL DB를 조회합니다...")

    # 시그널이 발생한 날짜 이후의 가격 데이터를 DB에서 한 번에 긁어오기 위한 준비
    min_date = signals["Date"].min().strftime("%Y-%m-%d")
    target_codes = tuple(signals["Code"].unique())

    # 코드가 1개일 경우 SQL IN 절 문법 오류 방지
    code_str = f"('{target_codes[0]}')" if len(target_codes) == 1 else str(target_codes)

    # 💡 DB 스키마 완벽 반영 (소문자)
    query = f"""
        SELECT quote_date, stock_code, open_price, high_price, low_price, close_price 
        FROM daily_stock_quotes 
        WHERE quote_date >= '{min_date}' 
        AND stock_code IN {code_str}
        ORDER BY stock_code, quote_date ASC
    """

    with engine.connect() as conn:
        df_prices = pd.read_sql(text(query), conn)

    df_prices["quote_date"] = pd.to_datetime(df_prices["quote_date"])

    print("[2/2] 타점별 3일 단기 스윙 시뮬레이션(수수료 차감) 진행 중...")
    results = []

    # 각 매수 시그널을 순회하며 실제 수익률 시뮬레이션
    for _, row in signals.iterrows():
        sig_date = row["Date"]
        code = row["Code"]

        # 시그널 발생 다음날부터 3영업일 데이터 추출
        future_prices = df_prices[
            (df_prices["stock_code"] == code) & (df_prices["quote_date"] > sig_date)
        ].head(3)

        if len(future_prices) < 1:
            continue  # 다음날 상장폐지나 거래정지 시 패스

        buy_price = future_prices.iloc[0]["open_price"]
        if buy_price == 0:
            continue

        yield_pct = 0.0
        sell_reason = ""
        hold_days = 0

        for i in range(len(future_prices)):
            hold_days = i + 1
            curr_day = future_prices.iloc[i]

            # 1. 고가가 목표가(+4.5%) 도달 시 즉시 익절
            if (curr_day["high_price"] / buy_price) >= 1.045:
                yield_pct = 0.045 - fee_rate
                sell_reason = "목표달성(+4.5%)"
                break

            # 2. 저가가 손절가(-3.0%) 도달 시 즉시 손절 (장중 휩소 감안)
            if (curr_day["low_price"] / buy_price) <= 0.970:
                yield_pct = -0.030 - fee_rate
                sell_reason = "손절(-3.0%)"
                break

            # 3. 3일차까지 목표가/손절가 안 오면 3일차 종가에 미련 없이 청산 (Time Stop)
            if i == 2:
                yield_pct = (curr_day["close_price"] / buy_price) - 1.0 - fee_rate
                sell_reason = "기간청산(3일)"
                break

        results.append(
            {
                "Date": sig_date.strftime("%Y-%m-%d"),
                "Code": code,
                "Prob": row["Stacking_Prob"],
                "Hold_Days": hold_days,
                "Yield_Pct": yield_pct,
                "Reason": sell_reason,
            }
        )

    df_res = pd.DataFrame(results)

    if df_res.empty:
        print("[-] 검증 가능한 시뮬레이션 결과가 없습니다.")
        return

    # ==========================================
    # 3. 통계 및 결과 출력
    # ==========================================
    win_trades = df_res[df_res["Yield_Pct"] > 0]
    loss_trades = df_res[df_res["Yield_Pct"] <= 0]

    win_rate = len(win_trades) / len(df_res) * 100
    avg_yield = df_res["Yield_Pct"].mean() * 100
    sum_yield = df_res["Yield_Pct"].sum() * 100

    print("\n=============================================")
    print(f" 📊 [실전 3일 단기 스윙 백테스트 결과] ")
    print("      (슬리피지/제세금 0.23% 보수적 반영) ")
    print("---------------------------------------------")
    print(f" 총 매수 타점   :  {len(df_res)} 회")
    print(
        f" 실전 승률      :  {win_rate:.2f}% ({len(win_trades)}승 / {len(loss_trades)}패)"
    )
    print(f" 평균 수익률    :  {avg_yield:.2f}% (건당)")
    print(f" 단순 누적 수익 :  {sum_yield:.2f}%")
    print("---------------------------------------------")

    reason_counts = df_res["Reason"].value_counts()
    print(" [매도 사유별 통계]")
    for reason, count in reason_counts.items():
        print(f"  - {reason}: {count}회 ({count/len(df_res)*100:.1f}%)")

    print("=============================================\n")


if __name__ == "__main__":
    # 앞서 모델 훈련 시 확인했던 '스위트 스팟' 임계값 0.70 으로 실행
    run_backtest(threshold=0.70)
