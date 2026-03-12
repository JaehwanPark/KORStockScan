import logging
import os
import time
from datetime import datetime

import FinanceDataReader as fdr
import sqlite3
import pandas as pd
import numpy as np
import holidays
import requests
from constants import TRADING_RULES # constants.py에 정의된 상수를 가져옵니다.



# --- [신규] 경로 설정 (상대 참조) ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, 'kospi_stock_data.db')

# --- [1. 통합 에러 로깅 및 관제 설정] ---
error_logger = logging.getLogger('KORStockScan_Error')
error_logger.setLevel(logging.ERROR)

if not error_logger.handlers:
    # 파일 기록 설정
    fh = logging.FileHandler('system_errors.log', encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    error_logger.addHandler(fh)

    # 터미널 출력 설정
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('🚨 [%(asctime)s] %(message)s', '%H:%M:%S'))
    error_logger.addHandler(sh)


def log_error(msg, config=None, send_telegram=False):
    """중앙 집중형 에러 관리 함수"""
    error_logger.error(msg)
    if send_telegram and config:
        try:
            token = config.get('TELEGRAM_TOKEN')
            chat_ids = config.get('CHAT_IDS', [])
            alert_msg = f"⚠️ *[KORStockScan 에러 알림]*\n\n🕒 발생: {datetime.now().strftime('%H:%M:%S')}\n📝 내용: {msg}"
            for chat_id in chat_ids:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, data={"chat_id": chat_id, "text": alert_msg, "parse_mode": "Markdown"}, timeout=5)
        except Exception as e:
            error_logger.error(f"텔레그램 전송 실패: {e}")


# --- [2. 키움 API 통신 및 기존 유틸리티 복구] ---
def get_kiwoom_token(config):
    """키움 접근 토큰 발급"""
    url = "https://api.kiwoom.com/oauth2/token"
    params = {
        'grant_type': 'client_credentials',
        'appkey': config.get('KIWOOM_APPKEY'),
        'secretkey': config.get('KIWOOM_SECRETKEY'),
    }
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    try:
        res = requests.post(url, headers=headers, json=params, timeout=10)
        if res.status_code == 200:
            return res.json().get('token')
        else:
            log_error(f"토큰 발급 실패 (HTTP {res.status_code})", config=config, send_telegram=True)
            return None
    except Exception as e:
        log_error(f"토큰 발급 중 시스템 예외: {e}", config=config, send_telegram=True)
        return None


def get_industry_list_ka10101(token, market_type="0"):
    """
    [ka10101] 업종코드 리스트 조회
    market_type: "0":코스피, "1":코스닥, "2":KOSPI200
    반환값 예시: [{'marketCode': '0', 'code': '001', 'name': '종합(KOSPI)', 'group': '1'}, ...]
    """
    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'ka10101'
    }
    payload = {"mrkt_tp": str(market_type)}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        if res.status_code == 200:
            # 명세서 응답 예시에 따라 JSON 배열(List) 형태로 반환됨
            return res.json()
    except Exception as e:
        print(f"🚨 ka10101 업종코드 리스트 조회 실패: {e}")

    return []


def get_basic_info_ka10001(token, code):
    """
    [ka10001] 주식기본정보요청 (10054 강제 끊김 방어 3회 재시도 로직 적용)
    """
    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'api-id': 'ka10001',
        'User-Agent': 'Mozilla/5.0'
    }

    # 💡 키움 API ka10001에 맞는 payload (명세서 기준 stk_cd)
    payload = {'stk_cd': code}

    # 🛡️ 3번까지 끈질기게 재시도하는 루프
    for attempt in range(3):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)

            # 1. HTTP 상태 코드가 200(정상)일 때만 파싱 시도
            if res.status_code == 200:
                data = res.json()

                # 🚀 [핵심 수정] return_code가 아예 응답에 없을 수 있으므로, 없을 경우 '0'(정상)으로 간주합니다.
                if str(data.get('return_code', '0')) != '0':
                    print(f"⚠️ [{code}] 기본정보 조회 에러: {data.get('return_msg', '사유 없음')}")
                    return {'Name': code, 'Marcap': 0}

                # 🚀 평면 구조의 JSON에서 직접 데이터를 추출합니다.
                name = data.get('stk_nm', code)

                # 시가총액 필드는 명세서에 따라 'mac' 이며, 값이 빈 문자열("")로 올 수 있으므로 안전하게 변환
                raw_mac = data.get('mac', 0)
                marcap = int(raw_mac) if str(raw_mac).strip() != "" else 0

                return {'Name': name, 'Marcap': marcap}

            else:
                # 429(Too Many Requests), 500(서버 에러) 등 200이 아닌 경우
                print(f"❌ [{code}] HTTP 응답 에러: {res.status_code}")

        except requests.exceptions.ConnectionError:
            # 💡 10054 에러 발생 시 여기서 잡아냅니다!
            print(f"⚠️ [{code}] 키움 서버 연결 끊김. 3초 대기 후 재접속 시도... ({attempt + 1}/3)")
            time.sleep(3)  # 트래픽 분산을 위해 3초 쉬고 다시 때림

        except Exception as e:
            print(f"🚨 [{code}] ka10001 처리 중 알 수 없는 예외 발생: {e}")
            break  # 다른 심각한 에러면 루프 탈출

    # 3번 다 실패했을 때 최후의 방어막 (프로그램이 뻗지 않도록 빈 데이터 반환)
    print(f"❌ [{code}] 3회 재접속 모두 실패. 기본값으로 대체합니다.")
    return {'Name': code, 'Marcap': 0}

def get_daily_ohlcv_ka10081_df(token, code, end_date=""):
    """[ka10081] 주식일봉차트조회요청 - OHLCV 데이터 (실제 명세서 반영 버전)"""
    # 💡 URL이 chart로 변경되었습니다.
    url = "https://api.kiwoom.com/api/dostk/chart"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'ka10081'
    }

    if not end_date:
        end_date = datetime.now().strftime("%Y%m%d")

    # 💡 파라미터 이름이 base_dt 와 upd_stkpc_tp(수정주가) 로 변경되었습니다.
    payload = {
        "stk_cd": str(code),
        "base_dt": end_date,
        "upd_stkpc_tp": "1"
    }

    for attempt in range(3):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)

            if res.status_code == 200:
                data = res.json()

                if str(data.get('return_code', '0')) != '0':
                    print(f"🚨 [키움서버 거절 사유] {data.get('return_msg', '알 수 없는 에러')}")

                # 💡 응답 리스트의 Key가 stk_dt_pole_chart_qry 로 변경되었습니다.
                output = data.get('stk_dt_pole_chart_qry', [])
                if output:
                    df = pd.DataFrame(output)

                    # 💡 명세서에 맞춰 컬럼명을 매핑합니다. (cur_prc -> Close)
                    df = df.rename(columns={
                        'dt': 'Date',
                        'open_pric': 'Open',
                        'high_pric': 'High',
                        'low_pric': 'Low',
                        'cur_prc': 'Close',  # 현재가를 종가로 사용
                        'trde_qty': 'Volume'
                    })

                    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')

                    # 콤마(,) 제어 및 숫자형 변환
                    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').abs()

                    df.set_index('Date', inplace=True)
                    return df.sort_index()
            else:
                print(f"🚨 [HTTP 에러] {res.status_code} - {res.text}")
            break
        except Exception as e:
            print(f"🚨 [파이썬 시스템 에러] {e}")
            time.sleep(2)

    return pd.DataFrame()

def get_item_info_ka10100(token, code):
    """
    ka10100(종목 기본정보) API를 호출하여 전체 데이터를 반환합니다.
    시가총액 계산용 상장주식수, 종가 및 시장 구분 정보를 모두 포함합니다.
    """
    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'ka10100'
    }
    # 요청 페이로드 키값은 API 규격에 따라 'stk_cd' 또는 'code' 중 정확한 것을 사용하세요.
    payload = {"stk_cd": str(code)}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get('return_code') == 0:
                # API 응답 원본 데이터를 반환합니다.
                return data
    except Exception as e:
        print(f"⚠️ [kiwoom_utils] ka10100 호출 실패: {e}")

    return None

def get_stock_market_ka10100(code, token):
    """기존 함수와 호환성을 유지하면서 통합 함수를 사용합니다."""
    info = get_item_info_ka10100(token, code)
    return info.get('nxtEnable') if info else None


def get_index_daily_ka20006(token, inds_cd="001"):
    """
    [ka20006] 업종일봉조회요청 API를 호출하여 최근 6거래일 지수 데이터를 가져옵니다.
    반환값: (최신 지수, 5거래일 전 지수) - 실패 시 (None, None) 반환
    """
    url = "https://api.kiwoom.com/api/dostk/chart"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'api-id': 'ka20006'
    }

    today_str = datetime.now().strftime("%Y%m%d")
    payload = {
        "inds_cd": str(inds_cd),
        "base_dt": today_str
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            daily_list = data.get('inds_dt_pole_qry', [])

            # 최소 6일치(오늘 포함 5거래일 전) 데이터가 있어야 RS 계산 가능
            if daily_list and len(daily_list) >= 6:
                # 명세서 규칙: 지수 값은 소수점 제거 후 100배 값으로 반환되므로 100.0으로 나눔
                latest_price = int(daily_list[0].get('cur_prc', 0)) / 100.0
                before_price = int(daily_list[5].get('cur_prc', 0)) / 100.0
                return latest_price, before_price
    except Exception as e:
        print(f"⚠️ [kiwoom_utils] ka20006 업종일봉 조회 실패: {e}")

    return None, None

def get_realtime_hot_stocks(token, config=None, as_dict=False):
    """
    [ka00198] 당일 누적 기준 실시간 급등주 검색 (10054 에러 방어 로직 포함)
    - as_dict=True 일 경우: [{'code': '...', 'name': '...', 'price': ..., 'vol': ...}] 형태 반환
    - as_dict=False 일 경우: ['005930', '000660'] 형태 반환 (기존 호환성 유지)
    """
    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'ka00198',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    # 기존: 당일 누적 대장주 위주 포착
    # payload = {'qry_tp': '4'}

    # 💡 변경: 장중 테마 변화 및 오후 급등주 포착용
    payload = {'qry_tp': '3'}
    hot_results = []

    for attempt in range(3):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            data = res.json()

            # 💡 [핵심] str()을 씌워서 숫자로 오든 문자로 오든 무조건 문자 '0'으로 변환해서 비교합니다!
            if res.status_code == 200 and str(data.get('return_code')) == '0':
                item_list = data.get('item_inq_rank', [])

                for item in item_list:
                    stk_cd = str(item.get('stk_cd'))[:6]
                    if stk_cd:
                        if as_dict:
                            # 🚀 스캐너를 위한 상세 데이터 추출
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
                            # 🚀 기존 스나이퍼 엔진 호환성 유지
                            hot_results.append(stk_cd)

                return hot_results
            else:
                err_msg = data.get('return_msg', '상세 사유 없음')
                log_error(f"❌ [급등주 조회 실패] {err_msg}", config=config)
                return []

        except requests.exceptions.ConnectionError:
            print(f"⚠️ 키움 서버 연결 끊김(10054 에러). 2초 후 재시도합니다... ({attempt + 1}/3)")
            time.sleep(2)
        except Exception as e:
            log_error(f"🔥 [급등주 조회] 시스템 예외: {e}", config=config)
            return []

    log_error("❌ [급등주 조회] 3회 재시도 모두 실패하여 스캔을 건너뜁니다.", config=config)
    return []


def get_top_marketcap_stocks(limit=300):
    """
    [FDR 완벽 대체용] KOSPI 시가총액 상위 종목 코드를 가져옵니다.
    네이버 모바일 증권 API가 허용하는 최대 호출량(60개)에 맞춰
    여러 페이지를 안전하게 순회하며 우량주 종목을 수집합니다.
    """
    # 💡 [해결 1] 평범한 크롬 웹 브라우저인 것처럼 신분증(헤더) 위조
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://m.stock.naver.com/'
    }

    target_codes = []
    # 💡 [해결 2] 300개를 한 번에 부르지 않고(400 에러 방지), 60개씩 쪼개서 요청합니다.
    page_size = 60
    max_pages = (limit // page_size) + 1

    for page in range(1, max_pages + 1):
        url = f"https://m.stock.naver.com/api/stocks/marketValue/KOSPI?page={page}&pageSize={page_size}"

        try:
            res = requests.get(url, headers=headers, timeout=10)

            if res.status_code == 200:
                data = res.json()
                stocks = data.get('stocks', [])

                # 더 이상 불러올 종목이 없으면 루프 탈출
                if not stocks:
                    break

                for stock in stocks:
                    code = stock.get('itemCode')
                    name = stock.get('stockName')

                    # 스팩, 우선주, ETF 등 불순물 제거 로직 통과 후 적재
                    if is_valid_stock(code, name):
                        target_codes.append(code)

                        # 목표 개수(300개)를 채우면 즉시 반환
                        if len(target_codes) >= limit:
                            return target_codes
            else:
                print(f"🚨 네이버 API 접근 거절 (HTTP {res.status_code}) - 페이지: {page}")
                break

        except Exception as e:
            print(f"🚨 시가총액 상위 종목 조회 실패: {e}")
            break

        # 💡 [핵심] 네이버 서버 차단 방지를 위한 짧은 휴식 시간
        time.sleep(0.3)

    return target_codes

# --- [3. 보조 계산 및 시각화] ---
def generate_visual_gauge(ratio, label_left="매도", label_right="매수"):
    """수급 비율 바(Bar) 생성"""
    size = 10
    filled = int(round(ratio * size))
    gauge = "▓" * filled + "░" * (size - filled)
    return f"[{label_left} {gauge} {label_right}]"

def analyze_signal_integrated(ws_data, ai_prob, threshold=70):
    """
    [v12.1 정밀 진단 버전] 실시간 데이터와 수치를 결합한 통합 분석 및 상세 사유 반환
    """
    score = ai_prob * 50
    details = [f"AI({ai_prob:.0%})"]
    visuals = ""
    prices = {}

    # 🚀 상세 체크리스트 초기 설정 (반환용)
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

        # 1️⃣ 유동성 필터 및 체크리스트 업데이트
        liquidity_value = (ask_tot + bid_tot) * curr_price
        MIN_LIQUIDITY = 50_000_000
        checklist["유동성 (5천만↑)"] = {"val": f"{liquidity_value / 1e6:.1f}백만", "pass": liquidity_value >= MIN_LIQUIDITY}

        ratio_val = (ask_tot / total) * 100 if total > 0 else 0
        gauge_idx = int(ratio_val / 10)

        visuals += f"📊 잔량비: [{'▓' * gauge_idx:<10}] {ratio_val:.1f}%\n"
        visuals += f"   (매도: {ask_tot:,} / 매수: {bid_tot:,})\n"

        # 2️⃣ 호가잔량비 분석 및 체크리스트 업데이트
        imb_ratio = ask_tot / (bid_tot + 1e-9)
        pass_imb = 1.5 <= imb_ratio <= 5.0
        checklist["호가잔량비 (1.5~5배)"] = {"val": f"{imb_ratio:.2f}배", "pass": pass_imb}

        if pass_imb:
            score += 25
            details.append("호가(적격)")

        # 3️⃣ 체결강도 분석 및 체크리스트 업데이트
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

        # 4️⃣ 최종 결론 로직 (보내주신 로직 그대로 유지)
        if (v_pw < 100 and score < threshold) or (liquidity_value < MIN_LIQUIDITY):
            conclusion = "🚫 *결론: 매수타이밍이 아닙니다*"
        else:
            conclusion = "✅ *결론: 매수를 검토해보십시오*"

    except Exception as e:
        conclusion = "결론: 분석 오류"

    # 🚀 최종적으로 checklist를 6번째 인자로 추가 반환
    return score, " + ".join(details), visuals, prices, conclusion, checklist

def register_manual_stock(code, name, config):
    """
    [스나이퍼 관제탑] 수동 감시 종목을 DB에 등록합니다.
    """
    today = datetime.now().strftime('%Y-%m-%d')

    try:
        conn = sqlite3.connect(DB_NAME)
        sql = """
              INSERT INTO recommendation_history (date, code, name, buy_price, type, status, position_tag)
              VALUES (?, ?, ?, 0, 'MANUAL', 'WATCHING', 'MIDDLE') ON CONFLICT(date, code) DO \
              UPDATE SET
                  status = 'WATCHING', type = 'MANUAL' \
              """
        conn.execute(sql, (today, str(code).zfill(6), name))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"🔥 수동 타겟 DB 등록 오류: {e}")
        return False

def get_daily_data_ka10005_df(token, code):
    """
    [ka10005] 실전투자 API를 호출하여 FDR과 동일한 형태의 일봉 DataFrame을 반환합니다.
    """
    # 💡 실전투자 도메인 적용
    url = 'https://api.kiwoom.com/api/dostk/mrkcond'
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'next-key': '',
        'api-id': 'ka10005'
    }
    data = {'stk_cd': str(code)}

    try:
        res = requests.post(url, headers=headers, json=data, timeout=10)
        if res.status_code == 200:
            market_data = res.json()
            daily_list = market_data.get('stk_ddwkmm', [])

            if not daily_list:
                return pd.DataFrame()

            # 1. DataFrame 생성 및 컬럼명 변경 (FDR 포맷에 맞춤)
            df = pd.DataFrame(daily_list)
            df.rename(columns={
                'date': 'Date',
                'open_pric': 'Open',
                'high_pric': 'High',
                'low_pric': 'Low',
                'close_pric': 'Close',
                'trde_qty': 'Volume'
            }, inplace=True)

            # 2. 필요한 컬럼만 추출
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

            # 3. 데이터 정제 (빈 문자열 처리 및 기호 제거)
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = df[col].replace('', np.nan)
                df[col] = df[col].astype(str).str.replace(r'[+-]', '', regex=True).astype(float)

            # 4. 날짜 포맷 변경 및 인덱스 설정
            df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
            df.set_index('Date', inplace=True)

            # 5. 시간순 정렬 (과거 -> 최신)
            df.sort_index(ascending=True, inplace=True)

            return df

    except Exception as e:
        print(f"🚨 키움 API 데이터 변환 실패 ({code}): {e}")

    return pd.DataFrame()

def is_trading_day():
    """
    외부 API 통신 없이 오프라인 연산만으로 한국 주식시장 개장일인지 확인합니다.
    """
    today_dt = datetime.now().date()

    # 1. 주말 필터링 (5: 토요일, 6: 일요일)
    if today_dt.weekday() >= 5:
        return False, "주말"

    # 2. 한국 법정 공휴일 (대체공휴일 포함)
    kr_holidays = holidays.KR()
    if today_dt in kr_holidays:
        return False, f"공휴일({kr_holidays.get(today_dt)})"

    # 3. 주식시장 특별 휴장일 (근로자의 날)
    if today_dt.month == 5 and today_dt.day == 1:
        return False, "근로자의 날"

    # 4. 주식시장 특별 휴장일 (연말 폐장일)
    if today_dt.month == 12 and today_dt.day == 31:
        return False, "연말 폐장일"

    return True, "정상거래일"

def is_valid_stock(code, name, token=None, current_price=0):
    """
    [공통 필터] 불순물 종목 및 저가주를 완벽하게 걸러냅니다.
    스팩(SPAC), ETF(KODEX 포함), ETN, 우선주, 리츠 등을 제외하여 순수 상장 주식만 매매 엔진에 전달합니다.
    """
    name_upper = name.upper()
    min_price_limit = TRADING_RULES.get('MIN_PRICE', 5000)

    # ==========================================
    # 🚨 1. 가격 필터링 (동전주/저가주 제외)
    # ==========================================
    # 방법 A: 스캐너에서 가격을 넘겨준 경우 (초고속 컷오프)
    if current_price > 0:
        if current_price < min_price_limit:
            return False
            
    # 방법 B: 가격은 안 넘어왔지만 token이 있는 경우 (API 직접 호출)
    elif token:
        try:
            # 같은 모듈 내의 일봉 차트 함수 호출
            df = get_daily_ohlcv_ka10081_df(token, code)
            if not df.empty:
                # 가장 최근 날짜의 종가를 가져옵니다
                last_price = df['Close'].iloc[-1]
                if last_price < min_price_limit:
                    return False
        except Exception as e:
            # 통신 에러 시 봇이 멈추지 않도록 일단 통과시킵니다 (실시간 웹소켓이 나중에 걸러줌)
            pass 

    # ==========================================
    # 2. 이름 기반 필터링 (KODEX 포함 제외 목록)
    # ==========================================
    invalid_keywords = [
        '스팩', 'ETF', 'ETN', 'TIGER', 'KBSTAR', 'KODEX', 
        'KINDEX', 'ARIRANG', 'KOSEF', '리츠', 'HANARO'
    ]
    
    for keyword in invalid_keywords:
        if keyword in name_upper:
            return False

    # 3. 우선주 필터링 (이름 끝자리 및 코드 번호 규칙)
    if name.endswith(('우', '우B', '우C')):
        return False

    if len(str(code)) == 6 and str(code)[-1] != '0':
        return False

    # 4. 파생상품 및 기타 예외 처리
    derivative_keywords = ['선물', '레버리지', '블룸버그', 'VIX', '인버스']
    for keyword in derivative_keywords:
        if keyword in name_upper:
            return False

    return True

def get_investor_daily_ka10059_df(token, code, base_dt=None):
    """[ka10059] 수급 데이터 (재시도 로직 및 누락 방어 적용)"""
    if not base_dt:
        base_dt = datetime.now().strftime("%Y%m%d")
    else:
        base_dt = base_dt.replace("-", "")

    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'api-id': 'ka10059'
    }
    payload = {"dt": base_dt, "stk_cd": str(code), "amt_qty_tp": "2", "trde_tp": "0", "unit_tp": "1"}

    # 💡 [방어막 1] 빈 데이터가 반환될 때를 대비한 기본 뼈대 DataFrame 생성
    empty_df = pd.DataFrame(columns=['Retail_Net', 'Foreign_Net', 'Inst_Net'])
    empty_df.index.name = 'Date'

    # 💡 [핵심] 최대 3번까지 재시도
    max_retries = 3
    for attempt in range(max_retries):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                res_json = res.json()
                data = res_json.get('stk_invsr_orgn', [])
                if data:
                    df = pd.DataFrame(data)
                    df.rename(columns={'dt': 'Date', 'ind_invsr': 'Retail_Net', 'frgnr_invsr': 'Foreign_Net',
                                       'orgn': 'Inst_Net'}, inplace=True)

                    # 💡 [방어막 2] API 응답에 특정 수급 주체가 누락되었을 경우 0으로 강제 채움
                    for col in ['Date', 'Retail_Net', 'Foreign_Net', 'Inst_Net']:
                        if col not in df.columns:
                            df[col] = 0

                    df = df[['Date', 'Retail_Net', 'Foreign_Net', 'Inst_Net']]
                    for col in ['Retail_Net', 'Foreign_Net', 'Inst_Net']:
                        df[col] = pd.to_numeric(
                            df[col].astype(str).str.replace('+', '', regex=False).str.replace(',', '', regex=False),
                            errors='coerce').fillna(0)
                    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
                    df.set_index('Date', inplace=True)
                    return df
            break  # 성공하거나 명확한 빈 응답이면 루프 탈출

        except requests.exceptions.ConnectionError:
            # 💡 10054 ConnectionResetError 발생 시 처리
            print(f"🚨 [{code}] 연결 끊김 (수급). {attempt + 1}/{max_retries} 재시도 중... 3초 대기")
            time.sleep(3)
        except Exception as e:
            print(f"🚨 ka10059 수급 데이터 호출 실패 ({code}): {e}")
            break

    # 💡 [방어막 3] 실패 시 컬럼 구조가 갖춰진 빈 DataFrame 반환 (KeyError 완벽 차단)
    return empty_df


def get_margin_daily_ka10013_df(token, code, base_dt=None):
    """[ka10013] 신용 잔고율 데이터 (재시도 로직 및 누락 방어 적용)"""
    if not base_dt:
        base_dt = datetime.now().strftime("%Y%m%d")
    else:
        base_dt = base_dt.replace("-", "")

    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'api-id': 'ka10013'
    }
    payload = {"stk_cd": str(code), "dt": base_dt, "qry_tp": "1"}

    # 💡 [방어막 1] 빈 데이터가 반환될 때를 대비한 기본 뼈대 DataFrame 생성
    empty_df = pd.DataFrame(columns=['Margin_Rate'])
    empty_df.index.name = 'Date'

    max_retries = 3
    for attempt in range(max_retries):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                res_json = res.json()
                data = res_json.get('crd_trde_trend', [])
                if data:
                    df = pd.DataFrame(data)
                    df.rename(columns={'dt': 'Date', 'remn_rt': 'Margin_Rate'}, inplace=True)

                    # 💡 [방어막 2] API 응답에 Margin_Rate(신용잔고율)가 누락되었을 경우 0으로 강제 채움
                    if 'Margin_Rate' not in df.columns:
                        df['Margin_Rate'] = 0

                    df = df[['Date', 'Margin_Rate']]
                    df['Margin_Rate'] = pd.to_numeric(df['Margin_Rate'].astype(str).replace('', '0'),
                                                      errors='coerce').fillna(0)
                    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
                    df.set_index('Date', inplace=True)
                    return df
            break

        except requests.exceptions.ConnectionError:
            print(f"🚨 [{code}] 연결 끊김 (신용). {attempt + 1}/{max_retries} 재시도 중... 3초 대기")
            time.sleep(3)
        except Exception as e:
            print(f"🚨 ka10013 신용 데이터 호출 실패 ({code}): {e}")
            break

    # 💡 [방어막 3] 실패 시 컬럼 구조가 갖춰진 빈 DataFrame 반환 (KeyError 완벽 차단)
    return empty_df

def get_market_regime(token=None):
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
            url = "https://api.kiwoom.com/api/dostk/mrkcond"
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
            print(f"🚨 키움 ka20006 우회 조회 실패: {e2}")

    # 둘 다 실패하면 보수적으로 BEAR(하락장) 모드 전환하여 리스크 관리
    return 'BEAR'


def get_top_fluctuation_ka10027(token, mrkt_tp="000", trde_qty_cnd="0100", limit=50):
    """
    [ka10027] 전일대비등락률상위요청
    - mrkt_tp: "000"(전체), "001"(코스피), "101"(코스닥)
    - trde_qty_cnd: "0100"(10만주 이상) 등
    """
    url = "https://api.kiwoom.com/api/dostk/rkinfo"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'api-id': 'ka10027',
        'User-Agent': 'Mozilla/5.0'
    }
    payload = {
        "mrkt_tp": mrkt_tp,
        "sort_tp": "1",
        "trde_qty_cnd": trde_qty_cnd,
        "stk_cnd": "0",
        "crd_cnd": "0",
        "updown_incls": "1",
        "pric_cnd": "0",
        "trde_prica_cnd": "0",
        "stex_tp": "3"
    }

    cleaned_list = []
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)

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

def get_tick_size(price):
    """한국 주식시장 호가 단위 계산기 (2023년 코스피/코스닥 통합 규정)"""
    if price < 2000: return 1
    if price < 5000: return 5
    if price < 20000: return 10
    if price < 50000: return 50
    if price < 200000: return 100
    if price < 500000: return 500
    return 1000

def get_price_ticks_down(curr_price, ticks=2):
    """현재가에서 지정한 틱(호가) 수만큼 정확히 내린 가격을 계산합니다."""
    price = curr_price
    for _ in range(ticks):
        # 가격이 내려갈 때의 호가 단위는 '현재 가격보다 1원이라도 낮을 때'의 기준을 따라야 함
        tick = get_tick_size(price - 1)
        price -= tick
    return price

def get_target_price_by_percent(curr_price, drop_percent=0.5):
    """
    [스캘핑 전용] 현재가에서 목표 퍼센트(%)만큼 하락한 가격을 
    한국 주식시장 호가 규격에 딱 맞춰서 계산해 줍니다.
    
    예: 19,900원에서 0.5% 하락(-99.5원) -> 19,800원으로 자동 맞춤
    """
    if curr_price <= 0: return 0
    
    # 1. 퍼센트를 적용한 이상적인 목표가 계산
    ideal_target = curr_price * (1 - (drop_percent / 100.0))
    
    # 2. 현재가에서 호가를 하나씩 내리면서 목표가에 가장 근접한 실제 호가를 찾음
    price = curr_price
    while price > ideal_target:
        tick = get_tick_size(price - 1)
        price -= tick
        
    return price

def get_smart_target_price(curr_price, v_pw=100, ai_prob=0.8, market_trend='NORMAL'):
    """
    [스캘핑 3.0] 수급강도 + AI 확신도 + 시장 지수 결합형 타점 계산기
    """
    if curr_price <= 0: return 0, 0.0
    
    # AI 확신도를 0~100 단위로 변환
    ai_score = ai_prob * 100 if ai_prob <= 1.0 else ai_prob
    
    # 1. 기본 설정 (수급강도 기준)
    if v_pw >= 200:
        drop_percent, tick_count = 0.2, 3
    elif v_pw >= 150:
        drop_percent, tick_count = 0.35, 4
    else:
        drop_percent, tick_count = 0.5, 5
        
    # 2. 🚀 가속 페달: AI 확신도 반영
    if ai_score >= 85:
        drop_percent = max(0.1, drop_percent - 0.15) 
        tick_count = max(1, tick_count - 1)
    elif ai_score <= 50: # DROP에 가까운 경우
        drop_percent += 0.5   
        tick_count += 3

    # 3. 🛑 브레이크: 시장 지수 반영
    if market_trend == 'BAD':
        drop_percent += 0.5
        tick_count += 3

    # 4. 가격 계산
    pct_price = get_target_price_by_percent(curr_price, drop_percent)
    
    tick_price = curr_price
    for _ in range(int(tick_count)):
        tick = get_tick_size(tick_price - 1)
        tick_price -= tick
        
    final_target = min(pct_price, tick_price)
    
    # 💡 수정 완료: 최종 타점과 함께, 최종적으로 결정된 눌림목(drop_percent)을 리턴합니다.
    return final_target, round(drop_percent, 2)