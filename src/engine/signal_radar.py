import requests
import pandas as pd
import pandas_ta as ta
import FinanceDataReader as fdr

# 기존 유틸리티에서 로깅 등 순수 도구만 빌려옵니다.
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.core.event_bus import EventBus
from src.utils.constants import TRADING_RULES  # 필요에 따라 상수를 추가/수정해서 사용
from src.engine.sniper_condition_handlers_big_bite import (
    detect_big_bite_trigger,
    build_tick_data_from_ws,
)

class SniperRadar:
    """
    KORStockScan 통합 레이더 (정보국)
    """
    def __init__(self, token):
        self.access_token = token
        self._big_bite_state = {}
        
        # 💡 [핵심] EventBus 인스턴스 획득 및 실시간 데이터 구독
        self.event_bus = EventBus()
        self.event_bus.subscribe("REALTIME_TICK_ARRIVED", self._on_realtime_tick)
    
    # ==========================================
    # ⚡ [핵심] 실시간 이벤트 처리기 (Event Handler)
    # ==========================================
    def _on_realtime_tick(self, payload):
        """웹소켓에서 'REALTIME_TICK_ARRIVED' 이벤트가 올 때마다 자동 실행됩니다."""
        code = payload.get('code')
        ws_data = payload.get('data')

        if not ws_data or ws_data.get('curr', 0) == 0:
            return

        # 1. 수급 점수 계산
        market_leader_score = self.calculate_market_leader_score(ws_data)

        # 2. 임시 AI 확신도 (나중에 Gemini/OpenAI 모듈 응답으로 교체될 부분)
        dummy_ai_prob = 0.85 

        # 3. 통합 신호 분석 (순수 데이터만 반환받음)
        score, prices, conclusion, checklist, metrics = SniperRadar.analyze_signal_integrated(ws_data, dummy_ai_prob)

        # 3-1. Big-Bite 보조 신호 계산 (진입 판단에 직접 결합하지 않음)
        big_bite_hit = False
        big_bite_info = None
        try:
            tick_data = build_tick_data_from_ws(ws_data)
            big_bite_hit, big_bite_info = detect_big_bite_trigger(
                code=code,
                tick_data=tick_data,
                ws_data=ws_data,
                runtime_state=self._big_bite_state,
            )
        except Exception as exc:
            log_error(f"⚠️ [Big-Bite] 보조 신호 계산 실패 ({code}): {exc}")

        metrics["big_bite_hit"] = bool(big_bite_hit)
        metrics["big_bite_info"] = big_bite_info or {}

        # 4. 🚀 [조건 충족 시 타점 계산 및 이벤트 발행]
        if score >= 70:  # 매수 기준 통과
            market_trend = self.get_market_regime(self.access_token)
            
            target_price, drop_pct = self.get_smart_target_price(
                curr_price=prices['curr'],
                v_pw=metrics['v_pw'],
                ai_score=dummy_ai_prob,
                market_trend=market_trend,
                ask_tot=metrics['ask_tot'],
                bid_tot=metrics['bid_tot']
            )

            # 💡 매매 엔진과 텔레그램이 받아볼 수 있도록 새로운 이벤트를 허공에 쏩니다!
            self.event_bus.publish("TRADE_SIGNAL_DETECTED", {
                "code": code,
                "target_price": target_price,
                "score": score,
                "conclusion": conclusion,
                "metrics": metrics,       # 텔레그램이 받아서 게이지바를 그릴 순수 데이터
                "checklist": checklist
            })
        
    # ==========================================
    # 🎯 [최종: 융합 및 지시] 메인 스캐너로 넘길 타겟 추출
    # ==========================================
    def find_supernova_targets(self, mrkt_tp="000"):
        """
        [V13.5 최종형] AI 가동 전 데이터 정제 및 수급 수치 결합
        """
        final_targets = []
        
        # 1. 원시 데이터 수집
        vol_spikes = kiwoom_utils.scan_volume_spike_ka10023(self.access_token, mrkt_tp=mrkt_tp)
        if not vol_spikes: return []

        # [효율화] 급증률 상위 정렬
        vol_spikes.sort(key=lambda x: x.get('spike_rate', 0), reverse=True)
        
        for stock in vol_spikes[:15]: 
            code = stock['code']
            flu = stock.get('flu_rate', 0.0)
            spike = stock.get('spike_rate', 0.0)

            if flu <= 0 or flu >= 25: continue

            # 2. 수급의 질 정밀 검증
            # 💡 [핵심 교정 1] 이제 딕셔너리를 반환하므로 결과 객체를 통째로 받습니다.
            prm_res = kiwoom_utils.check_program_buying_ka90008(self.access_token, code)
            exe_res = kiwoom_utils.check_execution_strength_ka10046(self.access_token, code) # 💡 고도화 버전 호출

            # 💡 [하이브리드 필터] 프로그램 매수 + 체결강도 골든크로스 + 최소 거래대금 30억
            if prm_res['is_buying'] and exe_res['is_strong'] and exe_res['acc_amt'] > 3000:
                
                # AI를 위한 풍부한 컨텍스트 생성
                stock['analysis_note'] = (
                    f"수급점수 상위. 프로그램 {prm_res['net_amt']}M 유입, "
                    f"체결강도(5분) {exe_res['s5']}%로 급증 중. 누적대금 {exe_res['acc_amt']}M."
                )
                
                # 💡 [최종형 점수 계산] 거래량/가격/프로그램/체결강도를 모두 버무린 초신성 점수
                stock['priority_score'] = (
                    (spike / 100) + (flu * 1.5) + (prm_res['net_amt'] / 30) + (exe_res['s5'] / 50)
                )
                
                final_targets.append(stock)
                log_info(f"🎯 [Supernova] {stock['name']} 준비 완료 (점수: {stock['priority_score']:.1f} | 수급: {prm_res['net_amt']}M)")

        # [효율화] 최종 우선순위 정렬
        final_targets.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        return final_targets
    
    # ==========================================
    # 🧠 엔진 코어 (UI 로직 제거 및 순수 데이터 반환)
    # ==========================================
    @staticmethod
    def analyze_signal_integrated(ws_data, ai_prob, threshold=70):
        """[v13 정밀 진단] 문자열 UI 생성 로직을 걷어내고 순수 분석 지표 딕셔너리를 반환합니다."""
        score = ai_prob * 50
        prices = {}
        metrics = {} # 텔레그램 매니저에게 전달할 원시 데이터

        checklist = {
            "AI 확신도 (75%↑)": {"val": f"{ai_prob:.1%}", "pass": ai_prob >= 0.75},
            "유동성 (3억↑)": {"val": "대기", "pass": False},
            "체결강도 (100%↑)": {"val": "대기", "pass": False},
            "호가잔량비 (1.5~5배)": {"val": "대기", "pass": False}
        }

        try:
            curr_price = ws_data['curr']
            prices = {'curr': curr_price, 'buy': curr_price, 'sell': int(curr_price * 1.03), 'stop': int(curr_price * 0.97)}

            ask_tot = ws_data.get('ask_tot', 1)
            bid_tot = ws_data.get('bid_tot', 1)
            total = ask_tot + bid_tot

            # 유동성 검사
            liquidity_value = total * curr_price
            checklist["유동성 (5억↑)"] = {"val": f"{liquidity_value / 1e8:.1f}억", "pass": liquidity_value >= getattr(TRADING_RULES, 'MIN_SCALP_LIQUIDITY', 500_000_000)}

            # 호가잔량 검사
            imb_ratio = ask_tot / (bid_tot + 1e-9)
            pass_imb = 1.5 <= imb_ratio <= 5.0
            checklist["호가잔량비 (1.5~5배)"] = {"val": f"{imb_ratio:.2f}배", "pass": pass_imb}
            
            if pass_imb: score += 25

            # 체결강도 검사
            v_pw = ws_data.get('v_pw', 0.0)
            pass_v_pw = v_pw >= 100
            checklist["체결강도 (100%↑)"] = {"val": f"{v_pw:.1f}%", "pass": pass_v_pw}

            if v_pw >= 110: score += 25
            elif v_pw >= 100: score += 15

            # UI 문자열 대신 UI를 그릴 수 있는 뼈대 데이터 반환
            ratio_val = (ask_tot / total) * 100 if total > 0 else 0
            metrics = {
                "ratio_val": ratio_val,
                "ask_tot": ask_tot,
                "bid_tot": bid_tot,
                "v_pw": v_pw
            }

            if (v_pw < 100 and score < threshold) or (liquidity_value < getattr(TRADING_RULES, 'MIN_SCALP_LIQUIDITY', 500_000_000)):
                conclusion = "🚫 매수타이밍이 아닙니다"
            else:
                conclusion = "✅ 매수를 검토해보십시오"

        except Exception as e:
            conclusion = "결론: 분석 오류"

        return score, prices, conclusion, checklist, metrics

    def get_smart_target_price(self, curr_price, v_pw=100, ai_score=50, market_trend='NORMAL', ask_tot=0, bid_tot=0):
        """
        [스캘핑 4.0] 수급강도 + AI 확신도 + 호가잔량비율 + 라운드피겨 회피가 모두 적용된 궁극의 타점 계산기
        """
        if curr_price <= 0: return 0, 0.0
        
        final_ai_score = ai_score * 100 if ai_score <= 1.0 else ai_score
        
        # ==========================================
        # 💡 [아이디어 1] AI 초강세(90점 이상) -> 돌파 추격매수
        # ==========================================
        if final_ai_score >= 90:
            # 눌림목을 기다리지 않고 현재가(또는 바로 위 호가)로 직진하여 즉시 체결시킵니다.
            return curr_price, 0.0 
            
        # 1. 기본 설정 (수급강도 기준)
        if v_pw >= 200:
            drop_percent, tick_count = 0.2, 3
        elif v_pw >= 150:
            drop_percent, tick_count = 0.35, 4
        else:
            drop_percent, tick_count = 0.5, 5
            
        # 2. 🚀 가속 페달: AI 확신도 반영 (75~89점 구간)
        if final_ai_score >= 85:
            drop_percent = max(0.1, drop_percent - 0.15) 
            tick_count = max(1, tick_count - 1)
        elif final_ai_score <= 50: 
            drop_percent += 0.5   
            tick_count += 3

        # ==========================================
        # 💡 [아이디어 2] 호가창 잔량 비율(Orderbook Imbalance) 필터링
        # ==========================================
        if ask_tot > 0 and bid_tot > 0:
            if ask_tot >= bid_tot * 1.5:
                # 매도벽이 두터움 = 세력이 뚫고 올라갈 진짜 상승 신호
                # 너무 아래에 깔면 안 사지므로 타점을 위로 살짝 올림
                drop_percent = max(0.1, drop_percent - 0.2)
                tick_count = max(1, tick_count - 2)
            elif bid_tot >= ask_tot * 1.5:
                # 매수벽이 두터움 = 개미 꼬시기용 가짜 지지선일 확률 높음
                # 훅 빠질 수 있으므로 타점을 더 깊게(안전하게) 내림
                drop_percent += 0.4
                tick_count += 4

        # 3. 🛑 브레이크: 시장 지수 반영
        if market_trend == 'BAD':
            drop_percent += 0.5
            tick_count += 3

        # 4. 가격 계산 (퍼센트 방식 vs 틱 방식 중 더 안전한/낮은 가격)
        pct_price = kiwoom_utils.get_target_price_by_percent(curr_price, drop_percent)
        
        tick_price = curr_price
        for _ in range(int(tick_count)):
            tick = kiwoom_utils.get_tick_size(tick_price - 1) # 현재가보다 낮은 가격에서 시작하여 하나씩 호가 단위 내리기
            tick_price -= tick
            
        final_target = min(pct_price, tick_price)
        
        # ==========================================
        # 💡 [아이디어 3] 라운드 피겨(Round Figure) 회피 로직
        # ==========================================
        # 1만, 5만, 10만원 등 심리적 저항선 '바로 아래'는 악성 매물대이므로 피합니다.
        if 9800 <= final_target <= 9990:
            final_target = 9750   # 1만원 저항 회피 -> 아예 깊게 대기
        elif 49000 <= final_target <= 49950:
            final_target = 48800  # 5만원 저항 회피
        elif 98000 <= final_target <= 99900:
            final_target = 97500  # 10만원 저항 회피
            
        return int(final_target), round(drop_percent, 2)

    def calculate_micro_indicators(self, candles):
        """
        [V14.0 고도화] 최근 1분봉 데이터를 바탕으로 스캘핑용 단기 지표 정밀 계산
        - pandas_ta를 활용한 RSI(14) 및 MACD(12,26,9) 지원
        - 시계열 정방향(과거->최신) 배열 완벽 대응
        """
        # 💡 데이터가 부족하면 현재가 기반의 기본값(Fallback) 반환
        if not candles or len(candles) < 5:
            last_close = candles[-1]['현재가'] if candles else 0
            return {
                "MA5": last_close, "Micro_VWAP": last_close, 
                "RSI": 50.0, "MACD": 0.0, "MACD_Signal": 0.0, "MACD_Hist": 0.0
            }

        # 1. 딕셔너리 리스트를 Pandas DataFrame으로 변환 (연산 속도 극대화)
        df = pd.DataFrame(candles)
        
        # 2. MA5 (5분 이동평균선)
        df['MA5'] = df['현재가'].rolling(window=5).mean()

        # 3. Micro-VWAP (최근 5분 거래량 가중 평균 주가)
        df['Typical_Price'] = (df['고가'] + df['저가'] + df['현재가']) / 3
        df['Price_Vol'] = df['Typical_Price'] * df['거래량']
        
        roll_price_vol = df['Price_Vol'].rolling(window=5).sum()
        roll_vol = df['거래량'].rolling(window=5).sum()
        
        df['Micro_VWAP'] = roll_price_vol / roll_vol
        df['Micro_VWAP'] = df['Micro_VWAP'].fillna(df['현재가']) # 분모가 0일 경우 방어

        # 4. RSI (14) - 데이터가 15개 이상일 때 정상 계산됨
        if len(df) >= 15:
            df['RSI'] = ta.rsi(df['현재가'], length=14)
        else:
            df['RSI'] = 50.0

        # 5. MACD (12, 26, 9) - 데이터가 30개 이상일 때 안정적
        macd_col, hist_col, sig_col = None, None, None
        if len(df) >= 30:
            macd_df = ta.macd(df['현재가'], fast=12, slow=26, signal=9)
            if macd_df is not None and not macd_df.empty:
                df = pd.concat([df, macd_df], axis=1)
                # pandas_ta의 동적 컬럼명 매핑 (보통 MACD_12_26_9 형식)
                macd_col = macd_df.columns[0] 
                hist_col = macd_df.columns[1] 
                sig_col = macd_df.columns[2]  

        # 🚀 가장 최근(마지막) 분봉의 지표값만 추출
        latest = df.iloc[-1]

        # MACD 값 안전 추출 로직
        macd_val = latest[macd_col] if macd_col and macd_col in latest else 0.0
        hist_val = latest[hist_col] if hist_col and hist_col in latest else 0.0
        sig_val = latest[sig_col] if sig_col and sig_col in latest else 0.0

        return {
            "MA5": int(latest['MA5']) if pd.notna(latest['MA5']) else int(latest['현재가']),
            "Micro_VWAP": int(latest['Micro_VWAP']) if pd.notna(latest['Micro_VWAP']) else int(latest['현재가']),
            "RSI": round(latest['RSI'], 2) if pd.notna(latest['RSI']) else 50.0,
            "MACD": round(macd_val, 2),
            "MACD_Signal": round(sig_val, 2),
            "MACD_Hist": round(hist_val, 2) # 💡 MACD 히스토그램(오실레이터)이 양수면 단기 상승 추세!
        }

    def calculate_market_leader_score(self, ws_data):
        """
        [v12.4] 주도주 판별을 위한 수급 점수 계산기
        """
        if not ws_data:
            return 0
        
        # 1. 전일 대비 등락률 (변동성)
        fluctuation = float(ws_data.get('fluctuation', 0))
        
        # 2. 체결강도 (수급의 질)
        volume_power = float(ws_data.get('v_pw', 0))
        
        # 3. 호가 잔량 대금 (유동성 규모)
        # (매도잔량 + 매수잔량) * 현재가
        ask_tot = ws_data.get('ask_tot', 0)
        bid_tot = ws_data.get('bid_tot', 0)
        curr_p = ws_data.get('curr', 0)
        liquidity = (ask_tot + bid_tot) * curr_p / 100_000_000 # 억 단위
        
        # 스캘핑용 가중치 공식: 
        # (등락률 * 10) + (체결강도 * 0.5) + (유동성 * 1.2)
        score = (fluctuation * 10) + (volume_power * 0.5) + (liquidity * 1.2)
        
        return round(score, 2)
    
    def get_market_regime(self, token=None):
        """
        코스피 지수를 분석하여 현재 시장 상태(BULL/BEAR)를 판별합니다.
        (1차: FinanceDataReader, 2차: 키움 ka20006 API 우회)
        기준: 코스피 현재가가 20일 이동평균선 위에 있으면 BULL, 아래면 BEAR
        """
        # 1차: FDR 사용 (코스피 지수 KS11)
        try:
            df = fdr.DataReader('KS11')
            if not df.empty and len(df) >= 20:
                current_close = float(df['Close'].iloc[-1])
                ma20 = float(df['Close'].tail(20).mean())
                return 'BULL' if current_close >= ma20 else 'BEAR'
        except Exception as e:
            print(f"⚠️ FDR 코스피 조회 실패. 키움 ka20006 API로 우회합니다: {e}")

        # 2차: 키움 ka20006 (업종일봉조회요청) 사용
        if token:
            try:
                url = kiwoom_utils.get_api_url("/api/dostk/mrkcond")
                headers = {
                    'Content-Type': 'application/json;charset=UTF-8',
                    'authorization': f'Bearer {token}',
                    'cont-yn': 'N',
                    'api-id': 'ka20006'
                }
                payload = {"upjong_cd": "001"} # 001: 코스피
                res = requests.post(url, headers=headers, json=payload, timeout=10)
                if res.status_code == 200:
                    res_json = res.json()
                    for key, val in res_json.items():
                        if isinstance(val, list) and len(val) >= 20 and 'cur_prc' in val[0]:
                            df_k = pd.DataFrame(val)
                            df_k['cur_prc'] = pd.to_numeric(df_k['cur_prc'].astype(str).str.replace(',', '', regex=False).str.replace('+', '', regex=False).str.replace('-', '', regex=False), errors='coerce')
                            current_close = df_k['cur_prc'].iloc[0]
                            ma20 = df_k['cur_prc'].head(20).mean()
                            return 'BULL' if current_close >= ma20 else 'BEAR'
            except Exception as e2:
                log_error(f"ka20006 처리 중 예외 발생: {e2}")
                print(f"🚨 키움 ka20006 우회 조회 실패: {e2}")
        # 둘 다 실패하면 보수적으로 BEAR(하락장) 모드 전환하여 리스크 관리
        return 'BEAR'
