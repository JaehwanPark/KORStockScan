import pandas as pd
from sqlalchemy import text

try:
    from .common_v2 import engine, AI_PRED_PATH, select_daily_candidates
except ImportError:
    from common_v2 import engine, AI_PRED_PATH, select_daily_candidates

def resolve_exit_price(open_p, high_p, low_p, close_p, tp_price, sl_price, hold_day, max_hold=3):
    # 갭 우선 처리 (실전 슬리피지 반영)
    if open_p >= tp_price:
        return open_p, 'TP_GAP'
    if open_p <= sl_price:
        return open_p, 'SL_GAP'

    hit_tp = high_p >= tp_price
    hit_sl = low_p <= sl_price

    # 같은 날 둘 다 닿으면 보수적으로 손절(SL) 우선
    if hit_tp and hit_sl:
        return sl_price, 'AMBIG_SL_FIRST'
    if hit_tp:
        return tp_price, 'TP'
    if hit_sl:
        return sl_price, 'SL'
    if hold_day >= max_hold:
        return close_p, 'TIME'
    return None, None

def run_backtest_v2(
    top_k_bull=3,           # (유지) 상승장 하루 최대 3종목
    top_k_bear=1,           # (유지) 하락장 보수적 접근
    floor_bull=0.35,        # 💡 (수정) 0.42 -> 0.35: Base 모델 컷오프 대폭 완화 (랭커에게 권한 위임)
    floor_bear=0.40,        # 💡 (수정) 0.48 -> 0.40: 하락장 컷오프 완화
    roundtrip_fee_rate=0.0023, 
    tp=0.055,               # 4.5% -> 5.5% (익절 폭 확대)
    sl_bull=0.040,          # 4.5% -> 4.0% (손절 폭 소폭 축소)
    sl_bear=0.035,          # 💡 (수정) 0.025 -> 0.035: 하락장 손절폭 완화
    max_hold_days=4,        # TIME 아웃 17건을 구제하기 위해 보유 기간 하루 연장
    output_path=None,
    save=True,
):
    print("🚀 실전 정밀 Backtest 시작 (파라미터 튜닝 V2)")

    df_pred = pd.read_csv(AI_PRED_PATH)
    df_pred['date'] = pd.to_datetime(df_pred['date']).dt.normalize()
    df_pred['code'] = df_pred['code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(6)

    # 💡 투트랙 필터링 적용 (score: 랭커 상대점수 / prob_col: Base 절대확률)
    picks = select_daily_candidates(
        df_pred,
        score_col='score',
        prob_col='hybrid_mean', 
        date_col='date',
        top_k_bull=top_k_bull,
        top_k_bear=top_k_bear,
        floor_bull=floor_bull,
        floor_bear=floor_bear
    )

    if picks.empty:
        print("❌ 선택된 시그널이 없습니다.")
        return pd.DataFrame()

    print(f"✅ 필터링된 최종 시그널 수: {len(picks)}")

    # 시그널 이후의 주가 추이를 DB에서 Fetch
    min_date = picks['date'].min().strftime('%Y-%m-%d')
    codes = tuple(sorted(picks['code'].unique()))
    code_str = f"('{codes[0]}')" if len(codes) == 1 else str(codes)

    query = f"""
        SELECT quote_date, stock_code, open_price, high_price, low_price, close_price
        FROM daily_stock_quotes
        WHERE quote_date >= '{min_date}'
          AND stock_code IN {code_str}
        ORDER BY stock_code ASC, quote_date ASC
    """
    with engine.connect() as conn:
        px = pd.read_sql(text(query), conn)

    if px.empty:
        print("❌ DB에서 미래 가격 데이터를 불러오지 못했습니다.")
        return pd.DataFrame()

    px['quote_date'] = pd.to_datetime(px['quote_date']).dt.normalize()
    px['stock_code'] = px['stock_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(6)

    results = []
    for _, row in picks.iterrows():
        sig_date = row['date']
        code = row['code']
        regime = row.get('bull_regime', 0)

        # 시그널 다음날부터 최대 보유기간까지 데이터
        future = px[(px['stock_code'] == code) & (px['quote_date'] > sig_date)].head(max_hold_days).copy()
        if len(future) < 1:
            continue

        buy_price = future.iloc[0]['open_price']
        if pd.isna(buy_price) or buy_price <= 0:
            continue

        tp_price = buy_price * (1.0 + tp)
        sl_price = buy_price * (1.0 - (sl_bull if regime == 1 else sl_bear))

        exit_price, exit_reason, hold_days = None, None, 0

        for i in range(len(future)):
            hold_days = i + 1
            day = future.iloc[i]

            exit_price, exit_reason = resolve_exit_price(
                open_p=day['open_price'],
                high_p=day['high_price'],
                low_p=day['low_price'],
                close_p=day['close_price'],
                tp_price=tp_price,
                sl_price=sl_price,
                hold_day=hold_days,
                max_hold=max_hold_days
            )
            if exit_price is not None:
                break

        if exit_price is None:
            continue

        gross_ret = (exit_price / buy_price) - 1.0
        net_ret = gross_ret - roundtrip_fee_rate

        results.append({
            'date': sig_date,
            'code': code,
            'name': row.get('name', ''),
            'score': row['score'],
            'hybrid_mean': row.get('hybrid_mean', 0),
            'bull_regime': regime,
            'hold_days': hold_days,
            'buy_price': buy_price,
            'exit_price': exit_price,
            'gross_ret': gross_ret,
            'net_ret': net_ret,
            'exit_reason': exit_reason
        })

    res = pd.DataFrame(results)
    if res.empty:
        print("❌ 체결 결과가 없습니다.")
        return res

    win_rate = (res['net_ret'] > 0).mean()
    avg_ret = res['net_ret'].mean()
    med_ret = res['net_ret'].median()
    total_ret = res['net_ret'].sum()

    print("\n=============================================")
    print("📊 [Backtest V2 최종 결과]")
    print("---------------------------------------------")
    print(f"총 트레이드 수 : {len(res)}")
    print(f"승률(Net)      : {win_rate:.2%}")
    print(f"평균 수익률    : {avg_ret:.2%}")
    print(f"중앙값 수익률  : {med_ret:.2%}")
    print(f"단순 누적 수익 : {total_ret:.2%}")
    print("---------------------------------------------")
    print("[매도 사유 분포]")
    print(res['exit_reason'].value_counts().to_string())
    print("=============================================\n")

    if save:
        save_path = output_path or AI_PRED_PATH.replace('ai_predictions_v2.csv', 'backtest_trades_v2.csv')
        res.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"✅ 거래 내역 저장 완료: {save_path}")
    return res

if __name__ == "__main__":
    run_backtest_v2()
