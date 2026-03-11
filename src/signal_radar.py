import time
import requests
import pandas as pd
import FinanceDataReader as fdr
from datetime import datetime

# 기존 유틸리티에서 로깅 등 순수 도구만 빌려옵니다.
import kiwoom_utils 

class SniperRadar:
    """
    KORStockScan 통합 레이더 (정보국)
    1차 스캔(투망) -> 2차 검증(현미경) -> 최종 타겟 선정을 전담합니다.
    """
    def __init__(self, token):
        self.token = token
        self.headers_rkinfo = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {self.token}',
            'User-Agent': 'Mozilla/5.0'
        }
        self.headers_mrkcond = self.headers_rkinfo.copy()

    # ==========================================
    # 🕸️ [1단계: 투망] 시장 전체 이상 징후 포착
    # ==========================================
    def scan_volume_spike_ka10023(self, mrkt_tp="101"):
        """[ka10023] 최근 n분간 거래량이 급증한 종목 스캔 (현재가 포함)"""
        self.headers_rkinfo['api-id'] = 'ka10023'
        url = "https://api.kiwoom.com/api/dostk/rkinfo"
        
        payload = {
            "mrkt_tp": mrkt_tp, "updown_tp": "1", "tm_tp": "5",
            "trde_qty_tp": "50", "stk_cnd": "0", "stex_tp": "3"
        }
        
        candidates = []
        try:
            res = requests.post(url, headers=self.headers_rkinfo, json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json().get('req_vol_sdnin', [])
                for item in data:
                    # 💡 가격 추출 (사용자 제안 반영)
                    raw_p = str(item.get('cur_prc', '0')).replace('+', '').replace('-', '')
                    curr_price = int(raw_p) if raw_p.isdigit() else 0

                    candidates.append({
                        'code': item['stk_cd'],
                        'name': item['stk_nm'],
                        'spike_rate': float(item.get('sdnin_rt', 0).replace('+', '')),
                        'Price': curr_price,  # 🚀 스캐너를 위해 'Price' 키로 통일
                        'cur_prc': curr_price # 하위 호환성 유지
                    })
        except Exception as e:
            kiwoom_utils.log_error(f"[Radar] 거래량 급증 스캔 실패: {e}")
        return candidates

    def scan_orderbook_spike_ka10021(self):
        """[ka10021] 호가창에 갑자기 거대 물량이 쌓인 종목 스캔"""
        self.headers_rkinfo['api-id'] = 'ka10021'
        url = "https://api.kiwoom.com/api/dostk/rkinfo"
        
        # 명세서 기준: 코스닥(101), 매수호가급증(1), 5분(5), 5만주이상(50)
        payload = {
            "mrkt_tp": "101", "rt_tp": "1", "tm_tp": "5",
            "trde_qty_tp": "50", "stk_cnd": "0", "stex_tp": "1"
        }
        
        # API 통신 후 결과 리스트 반환 (생략: 위 ka10023과 동일 구조)
        return []

    # ==========================================
    # 🔬 [2단계: 현미경] 후보군 심층 수급 검증
    # ==========================================
    def check_program_buying_ka90008(self, code):
        """[ka90008] 실시간 프로그램 순매수 강도 확인"""
        self.headers_mrkcond['api-id'] = 'ka90008'
        url = "https://api.kiwoom.com/api/dostk/mrkcond"
        payload = {"amt_qty_tp": "2", "stk_cd": str(code)}
        
        try:
            res = requests.post(url, headers=self.headers_mrkcond, json=payload, timeout=3)
            if res.status_code == 200:
                data = res.json().get('prm_trde_trend', [])
                if data:
                    raw_net = data[0].get('prm_netprps_qty', '0')
                    net_buy_qty = int(raw_net.replace('+', '').replace('-', ''))
                    return True if ('+' in raw_net and net_buy_qty > 10000) else False
        except Exception: pass
        return False

    def check_execution_strength_ka10046(self, code):
        """[ka10046] 체결강도 상승 추세 확인"""
        self.headers_mrkcond['api-id'] = 'ka10046'
        url = "https://api.kiwoom.com/api/dostk/mrkcond"
        payload = {"stk_cd": str(code)}
        
        try:
            res = requests.post(url, headers=self.headers_mrkcond, json=payload, timeout=3)
            if res.status_code == 200:
                data = res.json().get('cntr_str_trend', [])
                if data:
                    s5, s20 = float(data[0].get('cntr_str_5min', 0)), float(data[0].get('cntr_str_20min', 0))
                    return s5 > s20 and s5 > 110.0
        except Exception: pass
        return False
    
    def get_tick_history_ka10003(self, code, limit=10):
        """
        [ka10003] 주식체결정보요청 - AI 분석용 최근 틱(Tick) 스냅샷 추출
        """
        self.headers_mrkcond['api-id'] = 'ka10003'
        # TR 요청의 경우 보통 stkinfo 엔드포인트를 사용하지만, 기존 설정된 url을 사용합니다.
        url = "https://api.kiwoom.com/api/dostk/stkinfo" 
        
        payload = {"stk_cd": str(code)}
        ticks = []
        
        try:
            res = requests.post(url, headers=self.headers_mrkcond, json=payload, timeout=3)
            if res.status_code == 200:
                data = res.json()
                
                # 🚀 알려주신 명세의 'cntr_infr' 배열 추출
                tick_list = data.get('cntr_infr', []) 
                
                for item in tick_list[:limit]:
                    raw_price = str(item.get('cur_prc', '0'))
                    
                    # 부호로 매수/매도 주도권 파악 (키움 데이터 종특 활용)
                    direction = "BUY" if "+" in raw_price else "SELL" if "-" in raw_price else "NEUTRAL"
                    
                    ticks.append({
                        'time': item.get('tm', ''),
                        'price': abs(int(raw_price.replace('+', '').replace('-', ''))),
                        'volume': int(item.get('cntr_trde_qty', '0')),
                        'dir': direction
                    })
        except Exception as e:
            kiwoom_utils.log_error(f"🚨 [Radar] 틱 체결 데이터 호출 실패 ({code}): {e}")
            
        return ticks

    # ==========================================
    # 🎯 [최종: 융합 및 지시] 메인 스캐너로 넘길 타겟 추출
    # ==========================================
    def find_supernova_targets(self, mrkt_tp="101"):
        """초신성 수급 폭발 타겟 추출 (현재가 포함 반환)"""
        final_targets = []
        vol_spikes = self.scan_volume_spike_ka10023(mrkt_tp=mrkt_tp)
        
        for stock in vol_spikes:
            if self.check_program_buying_ka90008(stock['code']) and self.check_execution_strength_ka10046(stock['code']):
                # 🚀 'cur_prc'와 'Price'가 담긴 stock 객체 그대로 전달
                final_targets.append(stock)
                kiwoom_utils.log_error(f"🚨 [Radar] 완벽한 수급 조짐 포착: {stock['name']} ({stock['code']})")
        return final_targets

    def get_top_fluctuation_ka10027(self, mrkt_tp="000", limit=50):
        """[ka10027] 전일대비 등락률 상위 종목 조회"""
        self.headers_rkinfo['api-id'] = 'ka10027'
        url = "https://api.kiwoom.com/api/dostk/rkinfo"
        payload = {
            "mrkt_tp": mrkt_tp, "sort_tp": "1", "trde_qty_cnd": "0100",
            "stk_cnd": "0", "crd_cnd": "0", "updown_incls": "1",
            "pric_cnd": "0", "trde_prica_cnd": "0", "stex_tp": "3"
        }

        cleaned_list = []
        try:
            res = requests.post(url, headers=self.headers_rkinfo, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if str(data.get('return_code', '0')) != '0':
                    kiwoom_utils.log_error(f"⚠️ [ka10027] 응답 에러: {data.get('return_msg')}")
                    return []

                items = data.get('pred_pre_flu_rt_upper', [])
                for item in items[:limit]:
                    raw_p = str(item.get('cur_prc', '0')).replace('+', '').replace('-', '')
                    price = int(raw_p) if raw_p.isdigit() else 0
                    
                    cleaned_list.append({
                        'Code': str(item.get('stk_cd', '')).strip()[:6],
                        'Name': item.get('stk_nm'),
                        'Price': price,
                        'ChangeRate': float(str(item.get('flu_rt', '0')).replace('+', '').replace('-', '')),
                        'Volume': int(item.get('now_trde_qty', 0)),
                        'CntrStr': float(item.get('cntr_str', 0.0))
                    })
        except Exception as e:
            kiwoom_utils.log_error(f"🚨 [ka10027] 호출 예외: {e}")
        return cleaned_list


    def get_realtime_hot_stocks_ka00198(self, config=None, as_dict=False):
        """[ka00198] 실시간 급등주 검색"""
        headers_stkinfo = self.headers_rkinfo.copy()
        headers_stkinfo.update({'api-id': 'ka00198', 'cont-yn': 'N', 'next-key': ''})
        url = "https://api.kiwoom.com/api/dostk/stkinfo"
        
        hot_results = []
        for attempt in range(3):
            try:
                res = requests.post(url, headers=headers_stkinfo, json={'qry_tp': '3'}, timeout=10)
                data = res.json()
                if res.status_code == 200 and str(data.get('return_code')) == '0':
                    for item in data.get('item_inq_rank', []):
                        stk_cd = str(item.get('stk_cd'))[:6]
                        if not stk_cd: continue
                        if as_dict:
                            hot_results.append({
                                'code': stk_cd, 'name': item.get('stk_nm', ''),
                                'price': abs(int(item.get('past_curr_prc', 0))),
                                'vol': int(item.get('acml_vol', 0))
                            })
                        else: hot_results.append(stk_cd)
                    return hot_results
            except Exception: time.sleep(2)
        return []


    def analyze_signal_integrated(self, ws_data, ai_prob, threshold=70):
        """[v13 정밀 진단 버전] 실시간 데이터와 수치를 결합한 통합 분석 및 상세 사유 반환"""
        score = ai_prob * 50
        details = [f"AI({ai_prob:.0%})"]
        visuals = ""
        prices = {}

        checklist = {
            "AI 확신도 (75%↑)": {"val": f"{ai_prob:.1%}", "pass": ai_prob >= 0.75},
            "유동성 (5천만↑)": {"val": "데이터 대기", "pass": False},
            "체결강도 (100%↑)": {"val": "데이터 대기", "pass": False},
            "호가잔량비 (1.5~5배)": {"val": "데이터 대기", "pass": False}
        }

        if not ws_data or ws_data.get('curr', 0) == 0:
            return 0, "데이터 부족", "", prices, "결론: 데이터 수신 중", checklist

        try:
            curr_price = ws_data['curr']
            prices = {'curr': curr_price, 'buy': curr_price, 'sell': int(curr_price * 1.03), 'stop': int(curr_price * 0.97)}

            ask_tot = ws_data.get('ask_tot', 1)
            bid_tot = ws_data.get('bid_tot', 1)
            total = ask_tot + bid_tot

            liquidity_value = (ask_tot + bid_tot) * curr_price
            MIN_LIQUIDITY = 50_000_000
            checklist["유동성 (5천만↑)"] = {"val": f"{liquidity_value / 1e6:.1f}백만", "pass": liquidity_value >= MIN_LIQUIDITY}

            ratio_val = (ask_tot / total) * 100 if total > 0 else 0
            gauge_idx = int(ratio_val / 10)

            visuals += f"📊 잔량비: [{'▓' * gauge_idx:<10}] {ratio_val:.1f}%\n"
            visuals += f"   (매도: {ask_tot:,} / 매수: {bid_tot:,})\n"

            imb_ratio = ask_tot / (bid_tot + 1e-9)
            pass_imb = 1.5 <= imb_ratio <= 5.0
            checklist["호가잔량비 (1.5~5배)"] = {"val": f"{imb_ratio:.2f}배", "pass": pass_imb}

            if pass_imb:
                score += 25
                details.append("호가(적격)")

            v_pw = ws_data.get('v_pw', 0.0)
            visuals += f"⚡ 체결강도: {v_pw:.1f}%\n"

            pass_v_pw = v_pw >= 100
            checklist["체결강도 (100%↑)"] = {"val": f"{v_pw:.1f}%", "pass": pass_v_pw}

            if v_pw >= 110:
                score += 25
                details.append("수급(강)")
            elif v_pw >= 100:
                score += 15
                details.append("수급(중)")

            if (v_pw < 100 and score < threshold) or (liquidity_value < MIN_LIQUIDITY):
                conclusion = "🚫 *결론: 매수타이밍이 아닙니다*"
            else:
                conclusion = "✅ *결론: 매수를 검토해보십시오*"

        except Exception as e:
            conclusion = "결론: 분석 오류"

        return score, " + ".join(details), visuals, prices, conclusion, checklist

    def get_market_regime(self, token=None):
        """현재 시장 상태 판별 (BULL/BEAR)"""
        try:
            df = fdr.DataReader('KS11')
            if not df.empty and len(df) >= 20:
                cur, ma20 = float(df['Close'].iloc[-1]), float(df['Close'].tail(20).mean())
                return 'BULL' if cur >= ma20 else 'BEAR'
        except Exception as e:
            kiwoom_utils.log_error(f"⚠️ FDR 지수 조회 실패, 우회 시도: {e}")

        if token:
            try:
                url = "https://api.kiwoom.com/api/dostk/mrkcond"
                res = requests.post(url, headers=self.headers_mrkcond, json={"upjong_cd": "001", "api-id": "ka20006"}, timeout=10)
                if res.status_code == 200:
                    val = res.json().get('inds_dt_pole_qry', [])
                    if len(val) >= 20:
                        df_k = pd.DataFrame(val)
                        df_k['p'] = pd.to_numeric(df_k['cur_prc'].astype(str).str.replace(',', ''), errors='coerce')
                        return 'BULL' if df_k['p'].iloc[0] >= df_k['p'].head(20).mean() else 'BEAR'
            except Exception: pass
        return 'BEAR'

    def get_top_marketcap_stocks(self, limit=300):
        """네이버 API 우회 시총 상위 종목 수집 (구조 정합성 교정)"""
        headers = {'User-Agent': 'Mozilla/5.0...', 'Referer': 'https://m.stock.naver.com/'}
        target_list = [] # 💡 코드 리스트가 아닌 딕셔너리 리스트로 변경
        page_size = 60
        max_pages = (limit // page_size) + 1

        for page in range(1, max_pages + 1):
            url = f"https://m.stock.naver.com/api/stocks/marketValue/KOSPI?page={page}&pageSize={page_size}"
            try:
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 200:
                    stocks = res.json().get('stocks', [])
                    if not stocks: break
                    for s in stocks:
                        code, name = s.get('itemCode'), s.get('stockName')
                        raw_p = str(s.get('closePrice', '0')).replace(',', '')
                        curr_p = int(raw_p) if raw_p.isdigit() else 0

                        # 💡 [교정] 초고속 필터 적용 및 표준 딕셔너리 반환
                        if kiwoom_utils.is_valid_stock(code, name, current_price=curr_p):
                            target_list.append({'Code': code, 'Name': name, 'Price': curr_p})
                            if len(target_list) >= limit: return target_list
            except Exception as e:
                kiwoom_utils.log_error(f"🚨 네이버 수집 실패: {e}")
                break
            time.sleep(0.3)
        return target_list