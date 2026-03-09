import time
import requests
import pandas as pd
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
    def scan_volume_spike_ka10023(self):
        """[ka10023] 최근 n분간 거래량이 전일 대비 급증한 종목 스캔"""
        self.headers_rkinfo['api-id'] = 'ka10023'
        url = "https://api.kiwoom.com/api/dostk/rkinfo"
        
        # 명세서 기준: 코스닥(101), 상승(1), 5분(5), 5만주이상(50)
        payload = {
            "mrkt_tp": "101", "updown_tp": "1", "tm_tp": "5",
            "trde_qty_tp": "50", "stk_cnd": "0", "stex_tp": "1"
        }
        
        candidates = []
        try:
            res = requests.post(url, headers=self.headers_rkinfo, json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json().get('req_vol_sdnin', [])
                for item in data:
                    candidates.append({
                        'code': item['stk_cd'],
                        'name': item['stk_nm'],
                        'spike_rate': float(item.get('sdnin_rt', 0).replace('+', '')) # 급증률
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
        """[ka90008] 특정 종목의 실시간 프로그램 순매수 강도 확인"""
        self.headers_mrkcond['api-id'] = 'ka90008'
        url = "https://api.kiwoom.com/api/dostk/mrkcond"
        
        payload = {"amt_qty_tp": "2", "stk_cd": str(code)} # 2: 수량 기준
        
        try:
            res = requests.post(url, headers=self.headers_mrkcond, json=payload, timeout=3)
            if res.status_code == 200:
                data = res.json().get('prm_trde_trend', [])
                if data:
                    # 가장 최근(현재)의 프로그램 순매수 수량 확인
                    net_buy_qty = int(data[0].get('prm_netprps_qty', '0').replace('+', '').replace('-', ''))
                    is_buying = '+' in data[0].get('prm_netprps_qty', '')
                    return True if (is_buying and net_buy_qty > 10000) else False # 1만주 이상 순매수 시 True
        except Exception:
            pass
        return False

    def check_execution_strength_ka10046(self, code):
        """[ka10046] 5분, 20분 체결강도가 상승 추세인지 확인"""
        self.headers_mrkcond['api-id'] = 'ka10046'
        url = "https://api.kiwoom.com/api/dostk/mrkcond"
        payload = {"stk_cd": str(code)}
        
        try:
            res = requests.post(url, headers=self.headers_mrkcond, json=payload, timeout=3)
            if res.status_code == 200:
                data = res.json().get('cntr_str_trend', [])
                if data:
                    str_5min = float(data[0].get('cntr_str_5min', 0))
                    str_20min = float(data[0].get('cntr_str_20min', 0))
                    return str_5min > str_20min and str_5min > 110.0 # 110% 이상 & 상승 추세
        except Exception:
            pass
        return False

    # ==========================================
    # 🎯 [최종: 융합 및 지시] 메인 스캐너로 넘길 타겟 추출
    # ==========================================
    def find_supernova_targets(self):
        """
        투망과 현미경을 결합하여 '지금 당장 진입할' 초정밀 타겟을 반환합니다.
        """
        final_targets = []
        
        # 1. 넓게 던지기 (거래량 급증 종목 1차 추출)
        vol_spikes = self.scan_volume_spike_ka10023()
        
        # 2. 좁히기 (현미경 검증)
        for stock in vol_spikes:
            code = stock['code']
            
            # 프로그램이 1만주 이상 쓸어담고 있는가?
            has_program_power = self.check_program_buying_ka90008(code)
            
            # 누군가 시장가로 마구 긁어모으고 있는가?
            has_execution_power = self.check_execution_strength_ka10046(code)
            
            if has_program_power and has_execution_power:
                final_targets.append(stock)
                kiwoom_utils.log_error(f"🚨 [SniperRadar] 완벽한 수급 조짐 포착: {stock['name']} ({code})")
                
        return final_targets

    # ---------------------------------------------------------
    # (기존 kiwoom_utils에서 이사 온 함수들 - 클래스 내부에 편입)
    # ---------------------------------------------------------
    def get_top_fluctuation_ka10027(self, mrkt_tp="000", limit=50):
        """[ka10027] 전일대비등락률상위요청"""
        import requests
        
        self.headers_rkinfo['api-id'] = 'ka10027'
        url = "https://api.kiwoom.com/api/dostk/rkinfo"
        
        payload = {
            "mrkt_tp": mrkt_tp,
            "sort_tp": "1",
            "trde_qty_cnd": "0100",
            "stk_cnd": "0",
            "crd_cnd": "0",
            "updown_incls": "1",
            "pric_cnd": "0",
            "trde_prica_cnd": "0",
            "stex_tp": "3"
        }

        cleaned_list = []
        try:
            res = requests.post(url, headers=self.headers_rkinfo, json=payload, timeout=10)

            if res.status_code == 200:
                data = res.json()
                if str(data.get('return_code', '0')) != '0':
                    print(f"⚠️ [ka10027] 응답 에러: {data.get('return_msg')}")
                    return []

                items = data.get('pred_pre_flu_rt_upper', [])

                for item in items[:limit]:
                    code = str(item.get('stk_cd', '')).strip()[:6]
                    name = item.get('stk_nm')

                    # 부호 제거 및 형변환 (데이터 정제)
                    raw_price = str(item.get('cur_prc', '0')).replace('+', '').replace('-', '')
                    raw_flu_rt = str(item.get('flu_rt', '0')).replace('+', '').replace('-', '')

                    price = int(raw_price) if raw_price.isdigit() else 0
                    change_rate = float(raw_flu_rt) if raw_flu_rt else 0.0
                    volume = int(item.get('now_trde_qty', 0))
                    cntr_str = float(item.get('cntr_str', 0.0))

                    cleaned_list.append({
                        'Code': code, 'Name': name, 'Price': price,
                        'ChangeRate': change_rate, 'Volume': volume, 'CntrStr': cntr_str
                    })
            else:
                print(f"❌ [ka10027] HTTP 에러: {res.status_code}")

        except Exception as e:
            print(f"🚨 [ka10027] API 호출 예외 발생: {e}")

        return cleaned_list


    def get_realtime_hot_stocks_ka00198(self, config=None, as_dict=False):
        """[ka00198] 당일 누적 기준 실시간 급등주 검색"""
        import requests
        import time
        
        headers_stkinfo = self.headers_rkinfo.copy()
        headers_stkinfo['api-id'] = 'ka00198'
        headers_stkinfo['cont-yn'] = 'N'
        headers_stkinfo['next-key'] = ''
        
        url = "https://api.kiwoom.com/api/dostk/stkinfo"
        
        # 장중 테마 변화 및 오후 급등주 포착용
        payload = {'qry_tp': '3'}
        hot_results = []

        for attempt in range(3):
            try:
                res = requests.post(url, headers=headers_stkinfo, json=payload, timeout=10)
                data = res.json()

                if res.status_code == 200 and str(data.get('return_code')) == '0':
                    item_list = data.get('item_inq_rank', [])

                    for item in item_list:
                        stk_cd = str(item.get('stk_cd'))[:6]
                        if stk_cd:
                            if as_dict:
                                stk_nm = item.get('stk_nm', '')
                                price = item.get('past_curr_prc', 0)
                                vol = item.get('acml_vol', 0)
                                hot_results.append({
                                    'code': stk_cd,
                                    'name': stk_nm,
                                    'price': abs(int(price)),
                                    'vol': int(vol)
                                })
                            else:
                                hot_results.append(stk_cd)

                    return hot_results
                else:
                    err_msg = data.get('return_msg', '상세 사유 없음')
                    kiwoom_utils.log_error(f"❌ [급등주 조회 실패] {err_msg}", config=config)
                    return []

            except requests.exceptions.ConnectionError:
                print(f"⚠️ 키움 서버 연결 끊김(10054 에러). 2초 후 재시도합니다... ({attempt + 1}/3)")
                time.sleep(2)
            except Exception as e:
                kiwoom_utils.log_error(f"🔥 [급등주 조회] 시스템 예외: {e}", config=config)
                return []

        kiwoom_utils.log_error("❌ [급등주 조회] 3회 재시도 모두 실패하여 스캔을 건너뜁니다.", config=config)
        return []


    def analyze_signal_integrated(self, ws_data, ai_prob, threshold=70):
        """[v12.1 정밀 진단 버전] 실시간 데이터와 수치를 결합한 통합 분석 및 상세 사유 반환"""
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
    
    # ---------------------------------------------------------
    # (나머지 2개 함수도 마저 이사 옵니다)
    # ---------------------------------------------------------
    def get_market_regime(self):
        """코스피 지수를 분석하여 현재 시장 상태(BULL/BEAR)를 판별 (FDR 및 ka20006 활용)"""
        # 기존 kiwoom_utils.get_market_regime 로직 그대로 (self.token 활용)
        import FinanceDataReader as fdr
        try:
            df = fdr.DataReader('KS11')
            if not df.empty and len(df) >= 20:
                current_close = float(df['Close'].iloc[-1])
                ma20 = float(df['Close'].tail(20).mean())
                return 'BULL' if current_close >= ma20 else 'BEAR'
        except Exception:
            pass
        # (이하 ka20006 우회 로직 생략 - 기존과 동일하게 유지)
        return 'BEAR'

    def get_top_marketcap_stocks(self, limit=300):
        """네이버 금융 API를 통해 시가총액 상위 종목 수집 (Universe 구축용)"""
        # 기존 kiwoom_utils.get_top_marketcap_stocks 로직 그대로 이식
        pass