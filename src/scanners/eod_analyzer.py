import sys
import os
import json
import numpy as np
import pandas as pd
import holidays
from pathlib import Path
from datetime import datetime

# 1. KORStockScan 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.database.db_manager import DBManager
from src.database.models import RecommendationHistory
from src.core.event_bus import EventBus
from src.utils.constants import CONFIG_PATH, DEV_PATH

def load_config():
    """환경에 맞는 설정 파일(JSON)을 로드합니다."""
    target_path = CONFIG_PATH if os.path.exists(CONFIG_PATH) else DEV_PATH
    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"🚨 설정 파일 로드 실패: {e}")
        return {}

def get_next_business_day():
    """한국 휴일 반영 다음 영업일 계산"""
    today = datetime.now().date()
    kr_hols = holidays.KR(years=[today.year, today.year + 1])
    hol_dates = np.array([np.datetime64(d) for d in kr_hols.keys()], dtype='datetime64[D]')
    today_np = np.datetime64(today)
    next_bday_np = np.busday_offset(today_np, 1, holidays=hol_dates)
    return pd.to_datetime(next_bday_np).date()

def save_eod_top5_as_nextday_watching(db_manager, top5):
    """AI가 뽑은 EOD TOP5를 다음 영업일 WATCHING으로 저장"""
    target_date = get_next_business_day()
    saved_count = 0

    with db_manager.get_session() as session:
        for item in (top5 or [])[:5]:
            code = str(item.get("stock_code", "")).replace(".0", "").strip().zfill(6)
            name = str(item.get("stock_name", "")).strip()
            if not code or not name:
                continue

            try:
                close_price = int(float(item.get("close_price", 0) or 0))
            except Exception:
                close_price = 0

            try:
                prob = float(item.get("confidence", 0.0) or 0.0)
            except Exception:
                prob = 0.0

            record = session.query(RecommendationHistory).filter_by(
                rec_date=target_date,
                stock_code=code
            ).first()

            if record:
                record.stock_name = name
                record.buy_price = close_price
                record.trade_type = 'MAIN'
                record.strategy = 'KOSPI_ML'
                record.status = 'WATCHING'
                record.position_tag = 'EOD_TOP5'
                record.prob = prob
            else:
                record = RecommendationHistory(
                    rec_date=target_date,
                    stock_code=code,
                    stock_name=name,
                    buy_price=close_price,
                    trade_type='MAIN',
                    strategy='KOSPI_ML',
                    status='WATCHING',
                    position_tag='EOD_TOP5',
                    prob=prob
                )
                session.add(record)

            saved_count += 1

    return saved_count, target_date


def extract_eod_candidates(db_manager):
    """장 마감 후 내일의 주도주 후보 15종목을 추출합니다. (쌍끌이 양매수 + VCP 압축)"""
    print("🔍 [데이터 추출] 외인/기관 쌍끌이 매집 및 VCP 압축 종목을 정밀 스캔합니다...")
    
    query = """
    WITH RecentDates AS (
        SELECT DISTINCT quote_date FROM daily_stock_quotes ORDER BY quote_date DESC LIMIT 5
    )
    SELECT * FROM daily_stock_quotes 
    WHERE quote_date IN (SELECT quote_date FROM RecentDates)
    """
    import pandas as pd
    df = pd.read_sql(query, db_manager.engine)
    if df.empty: return ""

    candidates = []
    grouped = df.groupby('stock_code')

    for code, group in grouped:
        group = group.sort_values('quote_date').reset_index(drop=True)
        if len(group) < 3: continue

        today_data = group.iloc[-1]
        
        # 1. 시가총액 단위 보정 및 우량주 필터 (5천원 이상, 1000억 이상)
        marcap = today_data.get('marcap', 0)
        min_marcap = 100_000_000_000 if marcap > 1000000 else 1000

        if today_data.get('close_price', 0) < 5000 or marcap < min_marcap:
            continue
        
        # 2. 20일선 완벽 지지 (이탈 종목 칼같이 컷아웃)
        ma20 = today_data.get('ma20', 0)
        if pd.isna(ma20) or ma20 == 0 or today_data['close_price'] < ma20:
            continue
            
        # 3. RSI 골든존 (50 ~ 70: 힘은 붙었으나 과열되지 않은 상태)
        rsi = today_data.get('rsi', 0)
        if pd.isna(rsi) or not (50 <= rsi <= 70):
            continue

        # 4. 💎 쌍끌이 양매수 (가장 강력한 필터: 외인 AND 기관 모두 순매수)
        last_3_days = group.iloc[-3:]
        foreign_sum = last_3_days['foreign_net'].sum()
        inst_sum = last_3_days['inst_net'].sum()
        
        # 둘 중 하나라도 팔았거나 0이면 가차 없이 버림!
        if foreign_sum <= 0 or inst_sum <= 0:
            continue 

        # 5. 거래량 응축 (5일 평균 대비 150% 이하로 숨죽인 녀석들만)
        avg_vol = group['volume'].mean()
        vol_ratio = today_data['volume'] / avg_vol if avg_vol > 0 else 1.0
        if vol_ratio > 1.5: 
            continue 

        # 볼린저밴드 수축도 계산
        bbu = today_data.get('bbu', 0)
        bbl = today_data.get('bbl', 0)
        bb_width = (bbu - bbl) / today_data['close_price'] if bbu > 0 and today_data['close_price'] > 0 else 999
        
        total_smart_money = foreign_sum + inst_sum

        candidates.append({
            'code': code,
            'name': today_data.get('stock_name', code),
            'close_price': today_data['close_price'],
            'foreign_sum': foreign_sum,
            'inst_sum': inst_sum,
            'total_smart_money': total_smart_money, 
            'rsi': rsi,
            'macd_hist': today_data.get('macd_hist', 0),
            'bb_width': bb_width,
            'vol_ratio': vol_ratio
        })

    candidates_df = pd.DataFrame(candidates)
    if candidates_df.empty: 
        print("⚠️ 오늘 시장에서는 쌍끌이 매집 및 응축 조건에 부합하는 A급 종목이 없습니다.")
        return ""
    
    # 정렬: 1순위 볼린저밴드 수축(좁을수록 좋음), 2순위 메이저 수급 많은 순
    candidates_df = candidates_df.sort_values(by=['bb_width', 'total_smart_money'], ascending=[True, False]).head(15)
    
    print(f"✨ [정밀 스캔 완료] 조건에 완벽히 부합하는 {len(candidates_df)}개의 A급 타겟을 AI에게 전달합니다.")
    
    report_text = ""
    for idx, row in candidates_df.iterrows():
        report_text += f"🔹 [{row['name']}] ({row['code']})\n"
        report_text += f" - 종가: {int(row['close_price']):,}원 (RSI: {row['rsi']:.1f}, BB폭: {row['bb_width']*100:.1f}%)\n"
        report_text += f" - 3일 누적 쌍끌이: 외인 {int(row['foreign_sum']):,}주 / 기관 {int(row['inst_sum']):,}주\n"
        report_text += f" - 거래량 상태: 5일 평균대비 {row['vol_ratio']*100:.0f}%\n"
        report_text += f" - MACD 히스토그램: {row['macd_hist']:.2f}\n\n"
    
    return report_text

if __name__ == "__main__":
    print("🌙 [종가베팅 분석기] 장 마감 후 데이터 기반 분석 시작...")
    
    # 1. 설정 및 DB 로드
    CONF = load_config()
    db = DBManager()
    
    # 2. 데이터 추출
    candidates_text = extract_eod_candidates(db)
    
    if not candidates_text:
        print("⚠️ 조건을 만족하는 주도주 후보군이 없습니다. (오늘 장이 매우 안 좋았거나 데이터 갱신 필요)")
        sys.exit(0)
        
    print("✅ 1차 필터링 완료! Gemini 3.0 Pro 수석 애널리스트에게 분석을 요청합니다...")
    
    # 3. AI 분석 엔진 호출을 위한 API Key 확보
    api_keys = [v for k, v in CONF.items() if k.startswith("GEMINI_API_KEY")]
    
    if not api_keys:
        print("🚨 설정 파일(json)에 GEMINI_API_KEY가 없습니다.")
        sys.exit(1)
        
    try:
        from src.engine.ai_engine import GeminiSniperEngine
        ai_engine = GeminiSniperEngine(api_keys=api_keys)
        
        # 💡 장 마감 분석 전용 프롬프트 및 gemini-3.0-pro 호출
        bundle = ai_engine.generate_eod_tomorrow_bundle(candidates_text)
        final_report = bundle.get("report", "")
        top5 = bundle.get("top5", [])

        if top5:
            saved_count, target_date = save_eod_top5_as_nextday_watching(db, top5)
            final_report = (
                f"{final_report}\n\n"
                f"🗂️ **[DB 예약 완료]** 다음 영업일 `{target_date}` WATCHING 대상으로 "
                f"`{saved_count}개` 저장했습니다."
            )
        else:
            final_report = (
                f"{final_report}\n\n"
                f"⚠️ **[DB 예약 스킵]** 구조화된 TOP5가 비어 있어 저장하지 않았습니다."
            )
        
        print("\n" + "="*50)
        print(final_report)
        print("="*50 + "\n")
        
        # 4. 텔레그램으로 전송
        event_bus = EventBus()
        import src.notify.telegram_manager # 텔레그램 리스너 연결 및 봇 초기화
        
        event_bus.publish(
            'TELEGRAM_BROADCAST',
            {
                'message': final_report,
                'audience': 'VIP_ALL',
                'parse_mode': 'Markdown'
            }
        )
        print("🚀 텔레그램 VIP 채널로 마감 브리핑 전송 완료!")
        
    except Exception as e:
        print(f"🚨 AI 분석 또는 전송 중 에러 발생: {e}")