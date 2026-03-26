import os
import json
import time
import requests
import pandas as pd
import numpy as np
import holidays
from datetime import datetime, timedelta

# 💡 독립 로거 및 전역 상수 사용
from src.utils.logger import log_error
from src.utils.constants import CONFIG_PATH, DEV_PATH, TRADING_RULES  # 필요에 따라 상수를 추가/수정해서 사용

# ==========================================
# 1. API 설정 및 공통 유틸리티
# ==========================================
def get_kiwoom_base_url():
    """
    스마트 URL 스위치 (운영/모의투자 자동 감지)
    config_dev.json 파일의 존재 여부를 파악하여,
    자동으로 모의투자 URL 또는 실투자 URL을 세팅합니다.
    """
      
    # GCP에는 dev_path가 있고, AWS에는 없으므로 알아서 분기됩니다!
    target_path = CONFIG_PATH if os.path.exists(CONFIG_PATH) else DEV_PATH
    
    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            conf = json.load(f)
            # config에 명시된 URL이 있으면 가져오고, 없으면 실투자 URL을 기본값으로 씁니다.
            base_url = conf.get("KIWOOM_BASE_URL", "https://api.kiwoom.com")
            # 최초 1회 로드 시 터미널에 현재 모드를 명확히 출력해줍니다.
            # target_path가 문자열이어도 에러가 나지 않도록 형변환 후 처리
            mode_str = "🧪 [MOCK/DEV]" if "dev" in str(target_path).lower() else "🚀 [PROD/REAL]"
            print(f"⚙️ Kiwoom API 스위치 온: {mode_str} 목적지 -> {base_url}")
            return base_url
    except Exception as e:
        log_error(f"⚠️ 설정 파일 로드 실패: {e}. 실투자 URL로 폴백합니다.")
        print(f"⚠️ 설정 로드 실패. 실투자 기본 URL로 폴백합니다: {e}")
        return "https://api.kiwoom.com"

# 전역 변수로 세팅해두어 함수 호출 때마다 파일을 읽지 않도록 최적화합니다.
KIWOOM_BASE_URL = get_kiwoom_base_url()

def get_api_url(endpoint):
    """엔드포인트를 받아 최종 목적지 URL을 조립합니다."""
    return f"{KIWOOM_BASE_URL}{endpoint}"


def normalize_stock_code(code: str) -> str:
    """종목코드를 6자리 기준으로 정규화합니다. (_AL, A-prefix 허용)"""
    raw = str(code or "").strip().upper()
    raw = raw.replace('.0', '')
    if raw.endswith('_AL'):
        raw = raw[:-3]
    if raw.startswith('A') and len(raw) >= 7:
        raw = raw[1:]
    digits = ''.join(ch for ch in raw if ch.isdigit())
    return digits[-6:].zfill(6) if digits else raw


def get_effective_kiwoom_code(code: str, db=None, is_nxt=None) -> str:
    """최신 거래일의 is_nxt 플래그를 참고해 Kiwoom 요청용 코드를 반환합니다."""
    normalized = normalize_stock_code(code)

    if is_nxt is None:
        try:
            if db is None:
                from src.database.db_manager import DBManager
                db = DBManager()
            is_nxt = db.get_latest_is_nxt(normalized)
        except Exception as e:
            log_error(f"⚠️ get_effective_kiwoom_code DB 조회 실패 [{normalized}]: {e}")
            is_nxt = False

    return f"{normalized}_AL" if bool(is_nxt) else normalized

# ==========================================
# 2. 인증 및 기초 정보 API (Data Fetching Only)
# ==========================================
def get_kiwoom_token(config=None):
    """
    키움 접근 토큰 발급 (환경 자동 감지형)
    - config가 인자로 오면 우선 사용하고, 없으면 환경에 맞는 파일을 직접 로드합니다.
    """
    # 1. 💡 [환경 감지] 인자가 없을 경우 스스로 설정 로드
    if config is None:
        target_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
        print(target_path)
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            log_error(f"❌ 토큰 발급용 설정 로드 실패: {e}")
            return None

    url = get_api_url("/oauth2/token")
    
    # 2. 💡 [보안/정확성] 해당 환경의 키 추출
    app_key = config.get('KIWOOM_APPKEY')
    sec_key = config.get('KIWOOM_SECRETKEY')

    if not app_key or not sec_key:
        log_error("❌ APP_KEY 또는 SECRET_KEY가 설정 파일에 없습니다.")
        return None

    params = {
        'grant_type': 'client_credentials',
        'appkey': app_key,
        'secretkey': sec_key,
    }
    headers = {'Content-Type': 'application/json;charset=UTF-8'}

    try:
        # 3. 💡 [중요] 타임아웃(timeout)을 설정하여 무한 대기(Hang) 방지
        # 서버 응답이 5초 이상 없으면 에러를 뱉고 다음 로직으로 넘어가게 합니다.
        res = requests.post(url, headers=headers, json=params, timeout=5)
        
        if res.status_code == 200:
            token = res.json().get('access_token') or res.json().get('token')
            # 성공 시 로그를 남겨 흐름 파악을 돕습니다.
            # print(f"✅ 토큰 발급 성공 (목적지: {url})")
            return token
        else:
            log_error(f"❌ 토큰 발급 실패 (HTTP {res.status_code}): {res.text}")
            return None
            
    except requests.exceptions.Timeout:
        log_error(f"⏳ 토큰 서버 응답 시간 초과 (5초): {url}")
        return None
    except Exception as e:
        log_error(f"🚨 토큰 발급 중 시스템 예외: {e}")
        return None

def get_account_balance_kt00005(token):
    """
    [kt00005] 체결잔고요청 (SOR 통합 버전)
    KRX 데이터를 우선 적재하고, NXT 데이터 중 중복되는 종목코드는 무시(방어)하여 반환합니다.
    """
    url = get_api_url("/api/dostk/acnt") 
    
    # 💡 KRX를 먼저 조회하고 NXT를 나중에 조회하도록 순서 고정
    target_exchanges = ["KRX", "NXT"]
    
    # 종목코드를 Key로 하여 중복을 제거할 딕셔너리
    aggregated_balances = {}

    for ex in target_exchanges:
        payload = {"dmst_stex_tp": ex}

        results = fetch_kiwoom_api_continuous(
            url=url, 
            token=token, 
            api_id='kt00005', 
            payload=payload, 
            use_continuous=True
        )

        if not results:
            continue

        for res in results:
            data_list = res.get('stk_cntr_remn', [])

            for item in data_list:
                def to_i(v): 
                    if not v: return 0
                    try:
                        clean_v = str(v).replace(',', '').replace('+', '').strip()
                        return int(float(clean_v)) 
                    except (ValueError, TypeError):
                        return 0

                def to_f(v): 
                    if not v: return 0.0
                    try:
                        clean_v = str(v).replace(',', '').replace('+', '').strip()
                        return float(clean_v)
                    except (ValueError, TypeError):
                        return 0.0

                cur_qty = to_i(item.get('cur_qty'))
                
                if cur_qty > 0:
                    raw_code = str(item.get('stk_cd', '')).strip()
                    clean_code = raw_code.replace('A', '') if raw_code.startswith('A') else raw_code
                    
                    # 💡 [핵심] KRX가 먼저 등록되므로, 딕셔너리에 없는 경우에만 신규 등록 (NXT 중복 방어)
                    if clean_code not in aggregated_balances:
                        aggregated_balances[clean_code] = {
                            'code': clean_code,
                            'name': str(item.get('stk_nm', '')).strip(),
                            'qty': cur_qty,
                            'buy_price': to_i(item.get('buy_uv')),        
                            'current_price': to_i(item.get('cur_prc')),   
                            'eval_profit': to_i(item.get('evltv_prft')),  
                            'profit_rate': to_f(item.get('pl_rt'))
                        }
                        
    # 딕셔너리의 Value들만 뽑아서 리스트 형태로 반환
    return list(aggregated_balances.values())

def get_industry_list_ka10101(token, market_type="0"):
    """
    [ka10101] 업종코드 리스트 조회
    market_type: "0":코스피, "1":코스닥, "2":KOSPI200
    반환값 예시: [{'marketCode': '0', 'code': '001', 'name': '종합(KOSPI)', 'group': '1'}, ...]
    """
    url = get_api_url("/api/dostk/stkinfo")
    payload = {"mrkt_tp": str(market_type)}

    # 💡 [핵심] 공통 래퍼 함수 적용 (1회성 조회이므로 use_continuous=False)
    results = fetch_kiwoom_api_continuous(
        url=url, 
        token=token, 
        api_id='ka10101', 
        payload=payload, 
        use_continuous=False
    )

    # 응답이 실패하여 빈 리스트가 넘어온 경우
    if not results:
        return []

    # 💡 래퍼 함수는 모든 응답을 리스트(all_results)에 담아서 반환합니다.
    # 명세서상 ka10101의 JSON 응답 자체가 배열(List) 형태이므로, 
    # 첫 번째 응답 덩어리인 results[0]을 그대로 반환하면 기존 로직과 100% 호환됩니다.
    return results[0]

def get_basic_info_ka10001(token, code):
    """[ka10001] 주식기본정보요청 (1회성 조회)"""
    url = get_api_url("/api/dostk/stkinfo")
    payload = {'stk_cd': code}
    
    # 공통 함수 호출 (연속조회 안함)
    results = fetch_kiwoom_api_continuous(url, token, 'ka10001', payload, use_continuous=False)
    
    if not results:
        return {'Name': code, 'Marcap': 0}
        
    data = results[0] # 첫 번째 응답값
    
    name = data.get('stk_nm', code)
    raw_mac = data.get('mac', 0)
    marcap = int(raw_mac) if str(raw_mac).strip() != "" else 0
    
    return {'Name': name, 'Marcap': marcap}


def get_daily_ohlcv_ka10081_df(token, code, end_date=""):
    """[ka10081] 주식일봉차트조회요청 (과거 데이터 연속조회 지원)"""
    url = get_api_url("/api/dostk/chart")
    if not end_date:
        end_date = datetime.now().strftime("%Y%m%d")
        
    payload = {
        "stk_cd": str(code),
        "base_dt": end_date,
        "upd_stkpc_tp": "1"
    }
    
    # 💡 [핵심] use_continuous=True를 넘겨서 100일 이상 과거 데이터까지 쭉 긁어옵니다.
    results = fetch_kiwoom_api_continuous(url, token, 'ka10081', payload, use_continuous=False)
    
    if not results:
        return pd.DataFrame()
        
    # 여러 페이지(연속조회)의 응답 리스트를 하나의 DataFrame으로 합침
    all_data = []
    for res in results:
        output = res.get('stk_dt_pole_chart_qry', [])
        all_data.extend(output)
        
    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data)

    df = df.rename(columns={
        'dt': 'Date',
        'open_pric': 'Open',
        'high_pric': 'High',
        'low_pric': 'Low',
        'cur_prc': 'Close',  
        'trde_qty': 'Volume'
    })

    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')

    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').abs()

    df.set_index('Date', inplace=True)
    
    # 가장 오래된 과거(오름차순) 순으로 정렬하여 반환
    return df.sort_index()

def get_item_info_ka10100(token, code):
    """
    [ka10100] 종목 기본정보 API 호출
    시가총액 계산용 상장주식수, 종가 및 시장 구분 정보를 모두 포함하여 반환합니다.
    """
    url = get_api_url("/api/dostk/stkinfo")
    payload = {"stk_cd": str(code)}

    # 💡 [핵심] 1회성 조회를 위해 use_continuous=False 적용
    results = fetch_kiwoom_api_continuous(
        url=url, 
        token=token, 
        api_id='ka10100', 
        payload=payload, 
        use_continuous=False
    )

    # 💡 정상 응답 시 첫 번째 데이터(원본 JSON 딕셔너리) 그대로 반환
    if results:
        return results[0]
        
    return None

def get_index_daily_ka20006(token, inds_cd="001"):
    """
    [ka20006] 업종일봉조회요청 API를 호출하여 최근 6거래일 지수 데이터를 가져옵니다.
    반환값: (최신 지수, 5거래일 전 지수) - 실패 시 (None, None) 반환
    """
    url = get_api_url("/api/dostk/chart")
    today_str = datetime.now().strftime("%Y%m%d")
    payload = {
        "inds_cd": str(inds_cd),
        "base_dt": today_str
    }

    # 💡 [핵심] 1회성 조회를 위해 use_continuous=False 적용
    results = fetch_kiwoom_api_continuous(
        url=url, 
        token=token, 
        api_id='ka20006', 
        payload=payload, 
        use_continuous=False
    )

    if results:
        data = results[0]
        daily_list = data.get('inds_dt_pole_qry', [])

        # 최소 6일치(오늘 포함 5거래일 전) 데이터가 있어야 RS(상대강도) 등 계산 가능
        if daily_list and len(daily_list) >= 6:
            # 명세서 규칙: 지수 값은 소수점 제거 후 100배 값으로 반환되므로 100.0으로 나눔
            latest_price = int(daily_list[0].get('cur_prc', 0)) / 100.0
            before_price = int(daily_list[5].get('cur_prc', 0)) / 100.0
            return latest_price, before_price

    return None, None

def get_realtime_hot_stocks_ka00198(token, config=None, as_dict=True):
    """
    [ka00198] 실시간 종목조회 순위 데이터 전체 파싱
    - 빅데이터 순위, 순위 변동, 등락율 등 모든 필드 보존
    """
    url = get_api_url("/api/dostk/stkinfo")
    payload = {'qry_tp': '3'} # 당일 누적 기준

    results = fetch_kiwoom_api_continuous(
        url=url, token=token, api_id='ka00198', payload=payload, use_continuous=False
    )

    hot_results = []
    if results and (data := results[0].get('item_inq_rank', [])):
        def to_i(v): 
            if not v: return 0
            try:
                # 콤마와 부호를 제거한 뒤 float으로 먼저 바꾸고 int로 최종 변환
                clean_v = str(v).replace(',', '').replace('+', '').replace('-', '').strip()
                return int(float(clean_v)) 
            except (ValueError, TypeError):
                return 0

        def to_f(v): 
            if not v: return 0.0
            try:
                return float(str(v).replace(',', '').replace('+', '').strip())
            except (ValueError, TypeError):
                return 0.0

        for item in data:
            stk_cd = str(item.get('stk_cd', ''))[:6]
            if not stk_cd: continue
            
            # 🚀 모든 응답 데이터를 딕셔너리로 패키징
            stock_info = {
                'code': stk_cd,
                'name': item.get('stk_nm', ''),
                'rank': to_i(item.get('bigd_rank')),        # 빅데이터 순위
                'rank_chg': to_i(item.get('rank_chg')),     # 순위 등락폭
                'rank_sign': item.get('rank_chg_sign'),     # 순위 등락 부호 (1:상승, 2:하락 등)
                'price': to_i(item.get('past_curr_prc')),   # 현재가
                'flu_rate': to_f(item.get('base_comp_chgr')), # 기준가 대비 등락율
                'prev_flu': to_f(item.get('prev_base_chgr')), # 직전 대비 등락율
                'time': item.get('tm', ''),                 # 데이터 시각
            }
            
            if as_dict:
                hot_results.append(stock_info)
            else:
                hot_results.append(stk_cd)

    return hot_results

def get_daily_data_ka10005_df(token, code):
    """
    [ka10005] 실전투자 API를 호출하여 FDR과 동일한 형태의 일봉 DataFrame을 반환합니다.
    """
    url = get_api_url("/api/dostk/mrkcond")
    payload = {'stk_cd': str(code)}

    # 💡 [핵심] 1회성 조회 래퍼 함수 적용
    results = fetch_kiwoom_api_continuous(
        url=url, 
        token=token, 
        api_id='ka10005', 
        payload=payload, 
        use_continuous=False
    )

    if not results:
        return pd.DataFrame()

    market_data = results[0]
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

def get_investor_daily_ka10059_df(token, code, base_dt=None):
    """[ka10059] 수급 데이터 (투신, 연기금, 사모펀드 등 세부 주체 확장)"""
    
    # SOR 일 경우 _AL 코드로 변환
    req_code = get_effective_kiwoom_code(code)
    
    if not base_dt:
        base_dt = datetime.now().strftime("%Y%m%d")
    else:
        base_dt = base_dt.replace("-", "")

    url = get_api_url("/api/dostk/stkinfo")
    payload = {"dt": base_dt, "stk_cd": str(req_code), "amt_qty_tp": "2", "trde_tp": "0", "unit_tp": "1"}

    # 💡 [방어막 1] 확장된 컬럼 뼈대
    target_cols = [
        'Retail_Net', 'Foreign_Net', 'Inst_Net', 
        'Fin_Net', 'Trust_Net', 'Pension_Net', 'Private_Net'
    ]
    empty_df = pd.DataFrame(columns=target_cols)
    empty_df.index.name = 'Date'

    results = fetch_kiwoom_api_continuous(
        url=url, token=token, api_id='ka10059', payload=payload, use_continuous=False
    )

    if not results: return empty_df

    all_data = []
    for res in results:
        all_data.extend(res.get('stk_invsr_orgn', []))

    if not all_data: return empty_df

    df = pd.DataFrame(all_data)
    
    # 💡 [핵심 교정] 세부 기관 주체 완벽 매핑
    df.rename(columns={
        'dt': 'Date', 
        'ind_invsr': 'Retail_Net', 
        'frgnr_invsr': 'Foreign_Net', 
        'orgn': 'Inst_Net',
        'fnnc_invt': 'Fin_Net',      # 금융투자 (보통 단타 성향)
        'invtrt': 'Trust_Net',       # 투신 (실적주 주도 세력)
        'penfnd_etc': 'Pension_Net', # 연기금 (중장기 추세)
        'samo_fund': 'Private_Net'   # 사모펀드 (작전/급등주 배후)
    }, inplace=True)

    # 누락된 컬럼 0으로 채우기
    for col in target_cols:
        if col not in df.columns:
            df[col] = 0

    df = df[['Date'] + target_cols]
    
    # 문자열 정수로 파싱 (+, 콤마 제거)
    for col in target_cols:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace('+', '', regex=False).str.replace(',', '', regex=False),
            errors='coerce'
        ).fillna(0)
        
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
    df.set_index('Date', inplace=True)
    
    df = df[~df.index.duplicated(keep='first')]
    return df.sort_index()

def get_margin_daily_ka10013_df(token, code, base_dt=None):
    """[ka10013] 신용 잔고율 데이터 (공통 래퍼 함수 및 누락 방어 적용)"""

    # SOR 일 경우 _AL 코드로 변환
    req_code = get_effective_kiwoom_code(code)
    
    if not base_dt:
        base_dt = datetime.now().strftime("%Y%m%d")
    else:
        base_dt = base_dt.replace("-", "")

    url = get_api_url("/api/dostk/stkinfo")
    payload = {"stk_cd": str(req_code), "dt": base_dt, "qry_tp": "1"}

    empty_df = pd.DataFrame(columns=['Margin_Rate'])
    empty_df.index.name = 'Date'

    # 💡 [핵심] 래퍼 함수 적용 (연속조회 True)
    results = fetch_kiwoom_api_continuous(
        url=url, 
        token=token, 
        api_id='ka10013', 
        payload=payload, 
        use_continuous=False
    )

    if not results:
        return empty_df

    all_data = []
    for res in results:
        all_data.extend(res.get('crd_trde_trend', []))

    if not all_data:
        return empty_df

    df = pd.DataFrame(all_data)
    df.rename(columns={'dt': 'Date', 'remn_rt': 'Margin_Rate'}, inplace=True)

    if 'Margin_Rate' not in df.columns:
        df['Margin_Rate'] = 0

    df = df[['Date', 'Margin_Rate']]
    df['Margin_Rate'] = pd.to_numeric(
        df['Margin_Rate'].astype(str).replace('', '0'), errors='coerce'
    ).fillna(0)
    
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
    df.set_index('Date', inplace=True)
    
    df = df[~df.index.duplicated(keep='first')]
    return df.sort_index()

def get_top_fluctuation_ka10027(token, mrkt_tp="000", trde_qty_cnd="0100", limit=50):
    """
    [ka10027] 전일대비등락률상위요청
    - mrkt_tp: "000"(전체), "001"(코스피), "101"(코스닥)
    - trde_qty_cnd: "0100"(10만주 이상) 등
    """
    url = get_api_url("/api/dostk/rkinfo")
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

    # 💡 [핵심] 1회성 스캐너 조회 (429 에러 방어 탑재)
    results = fetch_kiwoom_api_continuous(
        url=url, 
        token=token, 
        api_id='ka10027', 
        payload=payload, 
        use_continuous=False
    )

    cleaned_list = []
    
    if results:
        data = results[0]
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

    return cleaned_list

def get_top_open_fluctuation_ka10028(token, mrkt_tp="000", trde_qty_cnd="0100", limit=50):
    """
    [ka10028] 시가대비 등락률 상위 요청 (장중 진짜 주도주 포착용)
    - URL: /api/dostk/stkinfo
    - 시가(Open) 대비 상승폭이 가장 큰, '오늘 당장의 붉은 기둥(양봉)'을 뿜는 종목 추출
    """
    url = get_api_url("/api/dostk/stkinfo")
    payload = {
        "sort_tp": "1",           # 1: 시가 기준
        "trde_qty_cnd": trde_qty_cnd, 
        "mrkt_tp": mrkt_tp,
        "updown_incls": "1",      # 상하한가 포함
        "stk_cnd": "0",           # 0: 전체 (필요시 4: 우선주+관리주 제외 로 변경 추천)
        "crd_cnd": "0",
        "trde_prica_cnd": "0",
        "flu_cnd": "1",            # 1: 상위
        "stex_tp": "3"
    }

    results = fetch_kiwoom_api_continuous(
        url=url, token=token, api_id='ka10028', payload=payload, use_continuous=False
    )

    cleaned_list = []
    
    if results and (data := results[0].get('open_pric_pre_flu_rt', [])):
        # 💡 [핵심 교정] 소수점이 포함된 문자열도 안전하게 정수로 변환하도록 수정
        def to_i(v): 
            if not v: return 0
            try:
                # 콤마와 부호를 제거한 뒤 float으로 먼저 바꾸고 int로 최종 변환
                clean_v = str(v).replace(',', '').replace('+', '').replace('-', '').strip()
                return int(float(clean_v)) 
            except (ValueError, TypeError):
                return 0

        def to_f(v): 
            if not v: return 0.0
            try:
                return float(str(v).replace(',', '').replace('+', '').strip())
            except (ValueError, TypeError):
                return 0.0

        for item in data[:limit]:
            code = str(item.get('stk_cd', '')).strip()[:6]
            if not code: continue
            name = item.get('stk_nm')

            # 가격 데이터 파싱
            curr_price = to_i(item.get('cur_prc'))
            open_price = to_i(item.get('open_pric'))
            high_price = to_i(item.get('high_pric'))
            low_price = to_i(item.get('low_pric'))
            
            # 💡 [핵심] 시가 대비 얼마나 올랐는지(%)를 직접 계산 (명세서의 open_pric_pre는 원화 단위 차이일 수 있으므로 안전하게 직접 계산)
            if open_price > 0:
                open_flu_rate = round(((curr_price - open_price) / open_price) * 100, 2)
            else:
                open_flu_rate = 0.0

            # 🚀 스캐너 호환성을 위해 기존 키(FluRate)에 '시가대비 등락률'을 덮어씌움
            cleaned_list.append({
                'Code': code, 
                'Name': name, 
                'Price': curr_price,
                'OpenPrice': open_price,
                'HighPrice': high_price,
                'LowPrice': low_price,
                'FluRate': open_flu_rate,           # 💡 스캐너 병합용 메인 키 (이제 시가대비 상승률로 작동!)
                'DayFluRate': to_f(item.get('flu_rt')), # 전일대비 등락률도 보존
                'OpenDiff': to_i(item.get('open_pric_pre')), # 시가대비 상승액
                'Volume': to_i(item.get('now_trde_qty')), 
                'CntrStr': to_f(item.get('cntr_str')),
                'PreSig': item.get('pred_pre_sig', ''),
                'Source': 'OPEN_TOP_RANK'
            })

    return cleaned_list


def scan_volume_spike_ka10023(token, mrkt_tp="000"):
    """[ka10023] 최근 n분간 거래량이 급증한 종목 스캔 (현재가 포함)"""
    url = get_api_url("/api/dostk/rkinfo")
    payload = {
        "mrkt_tp": mrkt_tp,    # 000: 전체, 001: 코스피, 101: 코스닥
        "tm_tp": "1",          # 💡 [수정] 1: 분단위 조회
        "tm": "5",             # 💡 [추가] 5분 입력 (최근 5분간 급증)
        "sort_tp": "1",        # 1: 급증량 기준
        "trde_qty_tp": "50",   # 50: 5만주 이상
        "stk_cnd": "4",        # 4:관리종목,우선주제외
        "pric_tp": "6",        # 6:5천원이상
        "stex_tp": "3"         # 3: 통합(KRX+NXT)
    }
    
    # 💡 [핵심] 1회성 스캐너 조회 (429 에러 방어 탑재)
    results = fetch_kiwoom_api_continuous(
        url=url, 
        token=token, 
        api_id='ka10023', 
        payload=payload, 
        use_continuous=False
    )

    candidates = []
    
    if results:
        # 💡 [핵심 교정] 명세서에 맞게 'req_vol_sdnin' ➡️ 'trde_qty_sdnin' 으로 수정
        data = results[0].get('trde_qty_sdnin', [])
        
        for item in data:
            # 💡 가격 추출 (사용자 제안 반영)
            raw_p = str(item.get('cur_prc', '0')).replace('+', '').replace('-', '')
            curr_price = int(raw_p) if raw_p.isdigit() else 0
            
            # 💡 등락률 추출 (안전한 파싱)
            raw_flu = str(item.get('flu_rt', '0')).replace('+', '')
            flu_rate = float(raw_flu) if raw_flu.replace('.', '', 1).replace('-', '', 1).isdigit() else 0.0
            
            candidates.append({
                'code': item['stk_cd'],
                'name': item['stk_nm'],
                'spike_rate': float(str(item.get('sdnin_rt', '0')).replace('+', '')),
                'flu_rate': flu_rate, # 💡 [추가] 당일 등락률 포함
                'Price': curr_price,  # 🚀 스캐너를 위해 'Price' 키로 통일
                'cur_prc': curr_price # 하위 호환성 유지
            })
            
    return candidates

def scan_orderbook_spike_ka10021(token, mrkt_tp="101"):
    """[ka10021] 호가창에 갑자기 거대 물량이 쌓인 종목 스캔"""
    url = get_api_url("/api/dostk/rkinfo")
    # 명세서 기준: 코스닥(101), 매수호가급증(1), 5분(5), 5만주이상(50)
    payload = {
        "mrkt_tp": mrkt_tp, "trde_tp": "1", "tm_tp": "5",
        "trde_qty_tp": "50", "stk_cnd": "0", "stex_tp": "1"
    }
    
    # 💡 1회성 조회 래퍼 적용 (429 자동 방어)
    results = fetch_kiwoom_api_continuous(
        url=url, token=token, api_id='ka10021', payload=payload, use_continuous=False
    )
    
    candidates = []
    
    if results:
        data = results[0].get('req_vol_sdnin', [])
        for item in data:
            # 💡 가격 추출 및 정제
            raw_p = str(item.get('cur_prc', '0')).replace('+', '').replace('-', '')
            curr_price = int(raw_p) if raw_p.isdigit() else 0
            
            candidates.append({
                'code': item.get('stk_cd', ''),
                'name': item.get('stk_nm', ''),
                'spike_rate': float(str(item.get('sdnin_rt', '0')).replace('+', '')),
                'Price': curr_price,  # 🚀 스캐너를 위해 'Price' 키로 통일
                'cur_prc': curr_price # 하위 호환성 유지
            })
            
    return candidates


def _get_prev_business_day_str(ref_dt=None):
    """한국 주말/공휴일을 제외한 직전 영업일(YYYYMMDD)을 반환합니다."""
    if ref_dt is None:
        ref_dt = datetime.now()

    try:
        kr_holidays = holidays.KR()
    except Exception:
        kr_holidays = set()

    d = ref_dt.date() - timedelta(days=1)
    while d.weekday() >= 5 or d in kr_holidays:
        d -= timedelta(days=1)
    return d.strftime('%Y%m%d')


def check_program_buying_ka90008(token, code, date_str=None, retry_prev_if_zero=True):
    """[ka90008] 프로그램 수급 전일 스냅샷/fallback 조회
    - 실시간 source of truth는 WS '0w'
    - 기본 date는 직전 영업일
    - today로 조회했는데 올제로면 직전 영업일로 1회 재시도
    """
    url = get_api_url("/api/dostk/mrkcond")
    target_date = str(date_str or _get_prev_business_day_str())
    payload = {"amt_qty_tp": "2", "stk_cd": str(code), "date": target_date}

    results = fetch_kiwoom_api_continuous(
        url=url, token=token, api_id='ka90008', payload=payload, use_continuous=False
    )

    def to_int(v):
        if v in (None, ""):
            return 0
        try:
            return int(str(v).replace(',', '').replace('+', '').strip())
        except Exception:
            return 0

    res_data = {
        'base_date': target_date,
        'is_buying': False, 'net_amt': 0, 'net_qty': 0,
        'buy_amt': 0, 'sell_amt': 0, 'buy_qty': 0, 'sell_qty': 0,
        'net_irds_amt': 0
    }

    if results and (data := results[0].get('prm_trde_trend', [])):
        item = data[0]
        res_data.update({
            'net_amt': to_int(item.get('prm_netprps_amt')),
            'net_qty': to_int(item.get('prm_netprps_qty')),
            'buy_amt': to_int(item.get('prm_buy_amt')),
            'sell_amt': to_int(item.get('prm_sell_amt')),
            'buy_qty': to_int(item.get('prm_buy_qty')),
            'sell_qty': to_int(item.get('prm_sell_qty')),
            'net_irds_amt': to_int(item.get('prm_netprps_amt_irds')),
        })
        res_data['is_buying'] = res_data['net_amt'] > 50 and res_data['net_qty'] > 10000

    if retry_prev_if_zero and date_str:
        is_all_zero = (
            res_data['net_amt'] == 0 and res_data['net_qty'] == 0 and
            res_data['buy_amt'] == 0 and res_data['sell_amt'] == 0 and
            res_data['buy_qty'] == 0 and res_data['sell_qty'] == 0
        )
        today_str = datetime.now().strftime('%Y%m%d')
        prev_bd = _get_prev_business_day_str()
        if is_all_zero and str(date_str) == today_str and target_date != prev_bd:
            return check_program_buying_ka90008(
                token=token,
                code=code,
                date_str=prev_bd,
                retry_prev_if_zero=False
            )

    return res_data


def get_program_flow_realtime(token, code, ws_data=None):
    """실시간 프로그램 수급은 WS '0w'를 우선, 없으면 ka90008 전일 스냅샷으로 fallback."""
    ws_data = ws_data or {}
    received_types = set(ws_data.get('received_types', []))
    has_ws_program = (
        '0w' in received_types or
        any(int(ws_data.get(k, 0) or 0) != 0 for k in ('prog_net_qty', 'prog_delta_qty', 'prog_net_amt', 'prog_delta_amt'))
    )

    if has_ws_program:
        net_qty = int(ws_data.get('prog_net_qty', 0) or 0)
        delta_qty = int(ws_data.get('prog_delta_qty', 0) or 0)
        net_amt = int(ws_data.get('prog_net_amt', 0) or 0)
        delta_amt = int(ws_data.get('prog_delta_amt', 0) or 0)
        return {
            'source': 'WS_0w',
            'base_date': '',
            'is_buying': net_qty > 0 and net_amt > 0,
            'net_amt': net_amt,
            'net_qty': net_qty,
            'buy_amt': 0,
            'sell_amt': 0,
            'buy_qty': 0,
            'sell_qty': 0,
            'net_irds_amt': delta_amt,
            'delta_qty': delta_qty,
            'delta_amt': delta_amt,
        }

    snap = check_program_buying_ka90008(token, code)
    snap['source'] = 'KA90008_PREV_BD'
    snap['delta_qty'] = 0
    snap['delta_amt'] = int(snap.get('net_irds_amt', 0) or 0)
    return snap


def check_execution_strength_ka10046(token, code):
    """[ka10046] 체결강도 및 거래대금 상세 데이터 패키지 반환"""
    url = get_api_url("/api/dostk/mrkcond")
    payload = {"stk_cd": str(code)}
    
    results = fetch_kiwoom_api_continuous(
        url=url, token=token, api_id='ka10046', payload=payload, use_continuous=False
    )
    
    # 💡 기본 반환 규격 (에러 방어용)
    res_data = {
        'is_strong': False, 'strength': 0.0,
        's5': 0.0, 's20': 0.0, 's60': 0.0,
        'acc_amt': 0, 'trde_qty': 0, 'flu_rt': 0.0
    }
    
    if results and (data := results[0].get('cntr_str_tm', [])):
        item = data[0]
        def to_i(v): 
            if not v: return 0
            try:
                # 콤마와 부호를 제거한 뒤 float으로 먼저 바꾸고 int로 최종 변환
                clean_v = str(v).replace(',', '').replace('+', '').replace('-', '').strip()
                return int(float(clean_v)) 
            except (ValueError, TypeError):
                return 0

        def to_f(v): 
            if not v: return 0.0
            try:
                return float(str(v).replace(',', '').replace('+', '').strip())
            except (ValueError, TypeError):
                return 0.0
        
        res_data.update({
            'strength': to_f(item.get('cntr_str')),      # 실시간 체결강도
            's5': to_f(item.get('cntr_str_5min')),       # 5분 체결강도
            's20': to_f(item.get('cntr_str_20min')),     # 20분 체결강도
            's60': to_f(item.get('cntr_str_60min')),     # 60분 체결강도
            'acc_amt': to_i(item.get('acc_trde_prica')), # 누적거래대금
            'trde_qty': to_i(item.get('trde_qty')),      # 현재 거래량
            'flu_rt': to_f(item.get('flu_rt')),          # 등락율
        })
        
        # 💡 [전략] 단기 수급이 중기 수급을 골든크로스 할 때 '강력'으로 판정
        res_data['is_strong'] = res_data['s5'] > res_data['s20'] and res_data['s5'] > 110.0
    
    time.sleep(0.3) # 💡 API 연속 호출 방지 위해 약간의 딜레이 추가
            
    return res_data
    
def get_tick_history_ka10003(token, code, limit=10):
    """
    [ka10003] 주식체결정보요청 - 가격 흐름을 기반으로 한 진짜 체결 방향 역추적
    """
    url = get_api_url("/api/dostk/stkinfo")
    payload = {"stk_cd": str(code)}
    
    results = fetch_kiwoom_api_continuous(
        url=url, token=token, api_id='ka10003', payload=payload, use_continuous=False
    )
    
    ticks = []
    
    if results and (data := results[0]) and (tick_list := data.get('cntr_infr', [])):
        def to_i(v): 
            if not v: return 0
            try:
                # 콤마와 부호를 제거한 뒤 float으로 먼저 바꾸고 int로 최종 변환
                clean_v = str(v).replace(',', '').replace('+', '').replace('-', '').strip()
                return int(float(clean_v)) 
            except (ValueError, TypeError):
                return 0

        def to_f(v): 
            if not v: return 0.0
            try:
                return float(str(v).replace(',', '').replace('+', '').strip())
            except (ValueError, TypeError):
                return 0.0
        # 💡 최근 체결 순으로 들어오므로, 역순으로 순회하며 이전 틱과 비교
        for i in range(len(tick_list)):
            if i >= limit: break
            
            item = tick_list[i]
            # 💡 [명세서 반영] 부호는 제거하고 순수 정수 가격만 추출
            current_price = to_i(item.get('cur_prc'))
            volume = to_i(item.get('cntr_trde_qty'))
            
            # 💡 [핵심] 진짜 체결 방향 추론 (다음 인덱스 i+1 이 시간상 더 과거의 틱)
            direction = "NEUTRAL"
            if i + 1 < len(tick_list):
                past_price = to_i(tick_list[i+1].get('cur_prc'))
                if current_price > past_price:
                    direction = "BUY"  # 가격이 올랐으므로 매수 주도
                elif current_price < past_price:
                    direction = "SELL" # 가격이 내렸으므로 매도 주도
            
            ticks.append({
                'time': item.get('tm', ''),
                'price': current_price,
                'volume': volume,
                'dir': direction,                           # 🚀 완벽하게 교정된 진짜 체결 방향
                'flu_rate': to_f(item.get('pre_rt')),       # 대비율
                'strength': to_f(item.get('cntr_str')),     # 체결강도
                'acc_vol': to_i(item.get('acc_trde_qty'))   # 누적거래량
            })
            
    return ticks


# 📝 TODO: 추후 RSI/MACD 보조지표 계산이 필요할 경우, 
# AI 속도 최적화를 위해 걸어둔 limit=5를 30~50으로 넉넉하게 늘려줄 것.
def get_minute_candles_ka10080(token, code, limit=10):
    """
    [REST API] ka10080: 주식분봉차트조회
    - 시간 역순 배열 방지 및 AI/지표 연산용 무결점 데이터 정제
    """
    url = get_api_url("/api/dostk/chart")
    base_dt = datetime.now().strftime('%Y%m%d')
    payload = {
        'stk_cd': str(code),
        'tic_scope': '1',       # 1분봉
        'upd_stkpc_tp': '1',    # 수정주가 반영
        'base_dt': base_dt      # 당일 기준
    }
    
    results = fetch_kiwoom_api_continuous(
        url=url, token=token, api_id='ka10080', payload=payload, use_continuous=False
    )
    
    refined_candles = []
    
    if results and (data := results[0]) and (candle_list := data.get('stk_min_pole_chart_qry', [])):
        # 💡 [안전 장치] 키움 특유의 콤마(,)와 부호(+,-)를 모두 지우는 헬퍼 함수
        def to_i(v): 
            if not v: return 0
            try:
                # 콤마와 부호를 제거한 뒤 float으로 먼저 바꾸고 int로 최종 변환
                clean_v = str(v).replace(',', '').replace('+', '').replace('-', '').strip()
                return int(float(clean_v)) 
            except (ValueError, TypeError):
                return 0

        # 최신 분봉부터 limit 개수만큼 자르기
        recent_candles = candle_list[:limit]
        
        for candle in recent_candles:
            raw_time = str(candle.get('cntr_tm', ''))
            
            # 시간 포맷팅 방어 로직 (14자리 YYYYMMDDHHMMSS 혹은 6자리 HHMMSS 모두 대응)
            if len(raw_time) >= 14:
                formatted_time = f"{raw_time[8:10]}:{raw_time[10:12]}:{raw_time[12:14]}"
            elif len(raw_time) >= 6:
                formatted_time = f"{raw_time[-6:-4]}:{raw_time[-4:-2]}:{raw_time[-2:]}"
            else:
                formatted_time = raw_time
                
            refined_candles.append({
                "체결시간": formatted_time,
                "시가": to_i(candle.get("open_pric")),
                "고가": to_i(candle.get("high_pric")),
                "저가": to_i(candle.get("low_pric")),
                "현재가": to_i(candle.get("cur_prc")),
                "거래량": to_i(candle.get("trde_qty"))
            })
            
        # 🚀 [핵심 교정] 과거 -> 최신(현재) 시간순으로 배열을 뒤집어서 반환!
        # 이렇게 해야 AI 엔진(recent_candles[-1])과 지표 연산(이동평균선 등)이 정상 작동합니다.
        return refined_candles[::-1]
        
    return refined_candles

def get_top_marketcap_stocks(self, limit=300):
    """네이버 API 우회 시총 상위 종목 수집 (구조 정합성 교정)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://m.stock.naver.com/',
        'Accept': 'application/json, text/plain, */*'
    }
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
                    if is_valid_stock(code, name, current_price=curr_p):
                        target_list.append({'Code': code, 'Name': name, 'Price': curr_p})
                        if len(target_list) >= limit: return target_list
        except Exception as e:
            log_error(f"🚨 네이버 수집 실패: {e}")
            break
        time.sleep(0.3)
    return target_list

# =====================================================================
# 🛡️ 공통 API 호출 래퍼 (429 방어 + 연속조회 통합)
# =====================================================================
# 💡 함수 정의부에 use_continuous: bool = False 가 반드시 포함되어야 합니다!
def fetch_kiwoom_api_continuous(url: str, token: str, api_id: str, payload: dict, max_retries: int = 3, use_continuous: bool = False) -> list:
    """
    키움 오픈API 공통 호출 함수 (연속조회 지원)
    - use_continuous=True: next-key가 끝날 때까지 무한정 과거 데이터를 긁어옵니다.
    - use_continuous=False: 1회성 조회만 수행합니다. (ka10001 등에 사용)
    """
    all_results = []
    cont_yn = 'N'
    next_key = ''
    
    while True:
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': api_id,
        }

        retry_count = 0
        response = None
        
        # 💡 [핵심 방어] 429 에러 발생 시 백오프(Back-off) 후 재시도
        while retry_count < max_retries:
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                
                if response.status_code == 200:
                    break  # 성공 시 재시도 루프 탈출
                elif response.status_code == 429:
                    wait_sec = (retry_count + 1) * 3
                    print(f"⚠️ [{api_id}] 429 요청 제한! {wait_sec}초 대기 후 재시도... ({retry_count+1}/{max_retries})")
                    time.sleep(wait_sec)
                    retry_count += 1
                else:
                    log_error(f"❌ [{api_id}] HTTP 에러 {response.status_code}: {response.text}")
                    break  # 치명적 에러는 즉시 중단
                    
            except requests.exceptions.ConnectionError:
                log_error(f"⚠️ [{api_id}] 연결 끊김. 3초 대기 후 재접속... ({retry_count+1}/{max_retries})")
                time.sleep(3)
                retry_count += 1
            except Exception as e:
                log_error(f"🚨 [{api_id}] 알 수 없는 예외: {e}")
                break

        if response is None or response.status_code != 200:
            log_error(f"🚨 [{api_id}] 최대 재시도 초과 또는 실패. 조회를 중단합니다.")
            break
            
        res_json = response.json()
        
        # return_code 체크 (정상이 아니면 경고 후 응답값 저장)
        if str(res_json.get('return_code', '0')) != '0':
            log_error(f"⚠️ [{api_id}] API 거절 사유: {res_json.get('return_msg', '알 수 없는 에러')}")
            
        all_results.append(res_json)
        
        # 💡 연속조회 모드가 아니면 첫 응답 후 바로 종료
        if not use_continuous:
            break
            
        cont_yn = response.headers.get('cont-yn', 'N')
        next_key = response.headers.get('next-key', '')
        
        if cont_yn != 'Y':
            break  # 더 이상 페이지가 없으면 탈출
            
        time.sleep(0.5)  # 연속조회 시 서버 배려를 위한 딜레이(실전서버)
        # time.sleep(1.2)  # 연속조회 시 서버 배려를 위한 딜레이(모의투자서버)

    return all_results
# ==========================================
# 3. 오프라인 순수 유틸리티 (외부 통신 없음)
# ==========================================

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
    min_price_limit = TRADING_RULES.MIN_PRICE

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
            log_error(f"is_valid_stock 처리 중 예외 발생: {e} (코드: {code})")
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

def get_target_price_up(curr_price, up_percent=0.5):
    """
    [스캘핑 전용] 현재가에서 목표 퍼센트(%)만큼 상승한 가격을
    한국 주식시장 호가 규격에 딱 맞춰서 계산해 줍니다.

    예: 19,900원에서 0.5% 상승(+99.5원) -> 20,000원으로 자동 맞춤
    """
    if curr_price <= 0:
        return 0

    # 1. 퍼센트를 적용한 이상적인 목표가 계산
    ideal_target = curr_price * (1 + (up_percent / 100.0))

    # 2. 현재가에서 호가를 하나씩 올리면서 목표가에 가장 근접한 실제 호가를 찾음
    price = curr_price
    while price < ideal_target:
        tick = get_tick_size(price)
        price += tick

    return price

def get_investor_flow_summary_ka10059(token, code, base_dt=None):
    """[ka10059] 외인/기관/세부 기관 수급 요약"""
    df = get_investor_daily_ka10059_df(token, code, base_dt=base_dt)
    res = {
        "foreign_net": 0,
        "inst_net": 0,
        "retail_net": 0,
        "fin_net": 0,
        "trust_net": 0,
        "pension_net": 0,
        "private_net": 0,
        "smart_money_net": 0,
    }
    if df.empty:
        return res

    latest = df.iloc[-1]
    res["foreign_net"] = int(latest.get("Foreign_Net", 0))
    res["inst_net"] = int(latest.get("Inst_Net", 0))
    res["retail_net"] = int(latest.get("Retail_Net", 0))
    res["fin_net"] = int(latest.get("Fin_Net", 0))
    res["trust_net"] = int(latest.get("Trust_Net", 0))
    res["pension_net"] = int(latest.get("Pension_Net", 0))
    res["private_net"] = int(latest.get("Private_Net", 0))
    res["smart_money_net"] = res["foreign_net"] + res["inst_net"]
    return res


def summarize_ticks_for_realtime_ka10003(token, code, limit=20):
    """[ka10003] 최근 체결정보를 실시간 분석용 매수/매도 편향 요약으로 변환"""
    ticks = get_tick_history_ka10003(token, code, limit=limit)
    res = {
        "trade_qty_signed_now": 0,
        "buy_exec_qty": 0,
        "sell_exec_qty": 0,
        "buy_ratio_now": 0.0,
        "buy_ratio_1m": 0.0,
        "buy_ratio_3m": 0.0,
        "tape_bias": "중립",
    }
    if not ticks:
        return res

    buy_qty = sum(int(t.get("volume", 0)) for t in ticks if t.get("dir") == "BUY")
    sell_qty = sum(int(t.get("volume", 0)) for t in ticks if t.get("dir") == "SELL")
    total = buy_qty + sell_qty

    res["buy_exec_qty"] = buy_qty
    res["sell_exec_qty"] = sell_qty
    if total > 0:
        res["buy_ratio_now"] = (buy_qty / total) * 100.0
        res["buy_ratio_1m"] = res["buy_ratio_now"]
        res["buy_ratio_3m"] = res["buy_ratio_now"]

    if buy_qty > sell_qty:
        res["tape_bias"] = "매수 우세"
        res["trade_qty_signed_now"] = buy_qty - sell_qty
    elif sell_qty > buy_qty:
        res["tape_bias"] = "매도 우세"
        res["trade_qty_signed_now"] = -(sell_qty - buy_qty)

    return res


def _coerce_int(value, default=0):
    try:
        return int(float(str(value).replace(",", "").replace("+", "").strip()))
    except Exception:
        return default


def _coerce_float(value, default=0.0):
    try:
        return float(str(value).replace(",", "").replace("+", "").strip())
    except Exception:
        return default


def _window_average(history, value_key, last_n):
    if not history:
        return 0.0
    values = []
    for item in list(history)[-last_n:]:
        if isinstance(item, dict):
            values.append(_coerce_float(item.get(value_key), 0.0))
        else:
            values.append(_coerce_float(item, 0.0))
    values = [v for v in values if v != 0.0]
    return float(sum(values) / len(values)) if values else 0.0


def _window_signed_ratio(history, last_n):
    if not history:
        return 0.0, 0, 0, 0
    series = list(history)[-last_n:]
    buy_qty = sum(abs(_coerce_int(item.get("qty", 0))) for item in series if _coerce_int(item.get("qty", 0)) > 0)
    sell_qty = sum(abs(_coerce_int(item.get("qty", 0))) for item in series if _coerce_int(item.get("qty", 0)) < 0)
    signed_now = _coerce_int(series[-1].get("qty", 0)) if series else 0
    total = buy_qty + sell_qty
    ratio = (buy_qty / total) * 100.0 if total > 0 else 0.0
    return ratio, signed_now, buy_qty, sell_qty


def _build_daily_setup_desc(ctx):
    curr_price = ctx.get("curr_price", 0)
    ma5 = ctx.get("ma5", 0)
    ma20 = ctx.get("ma20", 0)
    prev_high = ctx.get("prev_high", 0)
    vol_ratio = ctx.get("vol_ratio", 0.0)
    near_20d_high_pct = ctx.get("near_20d_high_pct", 0.0)

    if curr_price > 0 and prev_high > 0 and curr_price >= prev_high:
        return "전일 고점 돌파 시도"
    if ma5 > 0 and ma20 > 0 and ma5 >= ma20 and curr_price >= ma20:
        return "정배열 / 상승추세"
    if ma20 > 0 and curr_price >= ma20 and vol_ratio >= 120:
        return "20일선 위 거래량 동반"
    if near_20d_high_pct >= -2.0:
        return "20일 신고가 근접"
    if ma20 > 0 and curr_price < ma20:
        return "중립 또는 약세"
    return "박스 또는 눌림 구간"
    

def build_realtime_analysis_context(
    token,
    code,
    ws_data=None,
    strat_label="AUTO",
    position_status="NONE",
    avg_price=0,
    pnl_pct=0.0,
    trailing_pct=0.0,
    stop_pct=0.0,
    target_price=0,
    target_reason="",
    score=0.0,
    conclusion="",
    quant_metrics=None,
):
    """ai_engine.generate_realtime_report()용 표준 realtime_ctx 생성"""
    ws_data = ws_data or {}
    quant_metrics = quant_metrics or {}

    curr_price = _coerce_int(ws_data.get("curr"), 0)
    fluctuation = _coerce_float(ws_data.get("fluctuation"), 0.0)
    today_vol = _coerce_int(ws_data.get("volume"), 0)
    ask_tot = _coerce_int(ws_data.get("ask_tot"), 0)
    bid_tot = _coerce_int(ws_data.get("bid_tot"), 0)
    orderbook = ws_data.get("orderbook") or {}
    asks = orderbook.get("asks") or []
    bids = orderbook.get("bids") or []
    best_ask = _coerce_int(asks[-1].get("price") if asks else 0, 0)
    best_bid = _coerce_int(bids[0].get("price") if bids else 0, 0)

    strength_pack = check_execution_strength_ka10046(token, code)
    program_pack = get_program_flow_realtime(token, code, ws_data)
    investor_pack = get_investor_flow_summary_ka10059(token, code)
    tick_pack = summarize_ticks_for_realtime_ka10003(token, code, limit=20)
    minute_candles = get_minute_candles_ka10080(token, code, limit=40)
    daily_df = get_daily_ohlcv_ka10081_df(token, code)

    if curr_price <= 0:
        curr_price = _coerce_int(strength_pack.get("acc_amt"), 0)
    if today_vol <= 0:
        today_vol = _coerce_int(strength_pack.get("trde_qty"), 0)
    if fluctuation == 0.0:
        fluctuation = _coerce_float(strength_pack.get("flu_rt"), 0.0)

    vol_ratio = 0.0
    today_turnover = _coerce_int(strength_pack.get("acc_amt"), 0)
    ma5 = ma20 = ma60 = 0.0
    prev_high = prev_low = 0
    near_20d_high_pct = 0.0
    drawdown_from_high_pct = 0.0

    if not daily_df.empty:
        work_df = daily_df.sort_index().copy()
        if "Volume" in work_df.columns and len(work_df) >= 20:
            vol_base = float(work_df["Volume"].tail(20).mean() or 0.0)
            if vol_base > 0 and today_vol > 0:
                vol_ratio = (today_vol / vol_base) * 100.0
        if len(work_df) >= 5:
            ma5 = float(work_df["Close"].tail(5).mean())
        if len(work_df) >= 20:
            ma20 = float(work_df["Close"].tail(20).mean())
        if len(work_df) >= 60:
            ma60 = float(work_df["Close"].tail(60).mean())
        if len(work_df) >= 2:
            prev_high = _coerce_int(work_df.iloc[-1].get("High", 0))
            prev_low = _coerce_int(work_df.iloc[-1].get("Low", 0))
        if len(work_df) >= 20 and curr_price > 0:
            high_20 = float(work_df["High"].tail(20).max() or 0.0)
            if high_20 > 0:
                near_20d_high_pct = ((curr_price / high_20) - 1.0) * 100.0

    vwap_price = 0
    box_high = box_low = 0
    intraday_high = intraday_low = 0
    open_price = _coerce_int(ws_data.get("open"), 0)
    if minute_candles:
        total_turnover = 0
        total_volume = 0
        highs = []
        lows = []
        closes = []
        for candle in minute_candles:
            c_close = _coerce_int(candle.get("현재가") or candle.get("Close"), 0)
            c_high = _coerce_int(candle.get("고가") or candle.get("High"), 0)
            c_low = _coerce_int(candle.get("저가") or candle.get("Low"), 0)
            c_open = _coerce_int(candle.get("시가") or candle.get("Open"), 0)
            c_vol = abs(_coerce_int(candle.get("거래량") or candle.get("Volume"), 0))
            if open_price <= 0 and c_open > 0:
                open_price = c_open
            if c_close > 0 and c_vol > 0:
                total_turnover += c_close * c_vol
                total_volume += c_vol
            if c_high > 0: highs.append(c_high)
            if c_low > 0: lows.append(c_low)
            if c_close > 0: closes.append(c_close)
        if total_volume > 0:
            vwap_price = int(total_turnover / total_volume)
        if highs:
            intraday_high = max(highs)
            if curr_price > 0:
                drawdown_from_high_pct = ((curr_price / intraday_high) - 1.0) * 100.0
        if lows:
            intraday_low = min(lows)
        last_5 = minute_candles[-5:]
        box_high = max((_coerce_int(c.get("고가") or c.get("High"), 0) for c in last_5), default=0)
        lows_5 = [_coerce_int(c.get("저가") or c.get("Low"), 0) for c in last_5 if _coerce_int(c.get("저가") or c.get("Low"), 0) > 0]
        box_low = min(lows_5) if lows_5 else 0

    if curr_price > 0 and target_price <= 0:
        up_pct = 3.0 if str(strat_label).upper() in {"KOSPI_ML", "KOSDAQ_ML", "SWING"} else 1.0
        target_price = get_target_price_up(curr_price, up_pct)
        target_reason = target_reason or f"기본 목표가(+{up_pct:.1f}%)"

    if stop_pct <= 0.0:
        stop_pct = 2.0 if str(strat_label).upper() in {"KOSPI_ML", "KOSDAQ_ML", "SWING"} else 0.8
    if trailing_pct <= 0.0:
        trailing_pct = 4.0 if str(strat_label).upper() in {"KOSPI_ML", "KOSDAQ_ML", "SWING"} else 1.5

    ma5_status = "정보없음"
    ma20_status = "정보없음"
    ma60_status = "정보없음"
    if ma5 > 0 and curr_price > 0:
        ma5_status = "5일선 상회" if curr_price >= ma5 else "5일선 하회"
    if ma20 > 0 and curr_price > 0:
        ma20_status = "20일선 상회" if curr_price >= ma20 else "20일선 하회"
    if ma60 > 0 and curr_price > 0:
        ma60_status = "60일선 상회" if curr_price >= ma60 else "60일선 하회"

    orderbook_imbalance = (ask_tot / bid_tot) if bid_tot > 0 else (999.0 if ask_tot > 0 else 0.0)
    tick_size = get_tick_size(curr_price) if curr_price > 0 else 1
    spread_tick = 0
    if best_ask > 0 and best_bid > 0 and tick_size > 0:
        spread_tick = max(0, int(round((best_ask - best_bid) / tick_size)))

    v_pw_now = _coerce_float(ws_data.get("v_pw"), 0.0) or _coerce_float(strength_pack.get("strength"), 0.0)
    v_pw_1m = _coerce_float(strength_pack.get("s5"), 0.0)
    v_pw_3m = _coerce_float(strength_pack.get("s20"), 0.0)
    v_pw_5m = _coerce_float(strength_pack.get("s60"), 0.0)

    if not open_price:
        open_price = curr_price

    if curr_price > 0 and open_price > 0:
        if curr_price >= open_price:
            open_position_desc = f"시가 상회 (+{((curr_price/open_price)-1)*100:.2f}%)"
        else:
            open_position_desc = f"시가 하회 ({((curr_price/open_price)-1)*100:.2f}%)"
    else:
        open_position_desc = "정보없음"

    if curr_price > 0 and intraday_high > 0:
        if curr_price >= intraday_high:
            high_breakout_status = "당일 고가 돌파"
        elif curr_price >= intraday_high * 0.997:
            high_breakout_status = "고가 재도전 구간"
        else:
            high_breakout_status = "고가 하단"
    else:
        high_breakout_status = "정보없음"

    if vwap_price > 0 and curr_price > 0:
        vwap_status = "상회" if curr_price >= vwap_price else "하회"
    else:
        vwap_status = "정보없음"

    if ask_tot > bid_tot and tick_pack.get("buy_ratio_now", 0.0) >= 55.0:
        ask_absorption_status = "매도벽 소화 시도"
    elif bid_tot > ask_tot and tick_pack.get("buy_ratio_now", 0.0) < 45.0:
        ask_absorption_status = "매수벽 우세 / 하락 방어"
    else:
        ask_absorption_status = "중립 또는 혼조"

    trend_score = _coerce_float(quant_metrics.get("trend_score"), 0.0)
    flow_score = _coerce_float(quant_metrics.get("flow_score"), 0.0)
    orderbook_score = _coerce_float(quant_metrics.get("orderbook_score"), 0.0)
    timing_score = _coerce_float(quant_metrics.get("timing_score"), 0.0)
    if trend_score == 0.0 and score:
        trend_score = min(100.0, max(0.0, float(score)))
    if flow_score == 0.0:
        flow_score = min(100.0, max(0.0, 50.0 + (program_pack.get("net_qty", 0) / 10000.0)))
    if orderbook_score == 0.0:
        orderbook_score = 60.0 if bid_tot >= ask_tot else 45.0
    if timing_score == 0.0:
        timing_score = min(100.0, max(0.0, 50.0 + (v_pw_now - 100.0))) if v_pw_now > 0 else 50.0

    ctx = {
        "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_stage": "INTRADAY",
        "strat_label": strat_label,
        "position_status": position_status,
        "avg_price": _coerce_int(avg_price, 0),
        "pnl_pct": _coerce_float(pnl_pct, 0.0),
        "curr_price": curr_price,
        "fluctuation": fluctuation,
        "target_price": _coerce_int(target_price, 0),
        "target_reason": target_reason,
        "trailing_pct": _coerce_float(trailing_pct, 0.0),
        "stop_pct": _coerce_float(stop_pct, 0.0),
        "trend_score": trend_score,
        "flow_score": flow_score,
        "orderbook_score": orderbook_score,
        "timing_score": timing_score,
        "score": _coerce_float(score, 0.0),
        "conclusion": conclusion,
        "today_vol": today_vol,
        "vol_ratio": vol_ratio,
        "today_turnover": today_turnover,
        "v_pw_now": v_pw_now,
        "v_pw_1m": v_pw_1m,
        "v_pw_3m": v_pw_3m,
        "v_pw_5m": v_pw_5m,
        "buy_ratio_now": _coerce_float(tick_pack.get("buy_ratio_now"), 0.0),
        "buy_ratio_1m": _coerce_float(tick_pack.get("buy_ratio_1m"), 0.0),
        "buy_ratio_3m": _coerce_float(tick_pack.get("buy_ratio_3m"), 0.0),
        "trade_qty_signed_now": _coerce_int(tick_pack.get("trade_qty_signed_now"), 0),
        "prog_net_qty": _coerce_int(ws_data.get("prog_net_qty"), 0) or _coerce_int(program_pack.get("net_qty"), 0),
        "prog_delta_qty": _coerce_int(ws_data.get("prog_delta_qty"), 0),
        "foreign_net": _coerce_int(investor_pack.get("foreign_net"), 0),
        "inst_net": _coerce_int(investor_pack.get("inst_net"), 0),
        "smart_money_net": _coerce_int(investor_pack.get("smart_money_net"), 0),
        "best_ask": best_ask,
        "best_bid": best_bid,
        "ask_tot": ask_tot,
        "bid_tot": bid_tot,
        "orderbook_imbalance": orderbook_imbalance,
        "spread_tick": spread_tick,
        "tape_bias": tick_pack.get("tape_bias", "중립"),
        "ask_absorption_status": ask_absorption_status,
        "vwap_price": vwap_price,
        "vwap_status": vwap_status,
        "open_position_desc": open_position_desc,
        "high_breakout_status": high_breakout_status,
        "box_high": box_high,
        "box_low": box_low,
        "daily_setup_desc": _build_daily_setup_desc({
            "curr_price": curr_price,
            "ma5": ma5,
            "ma20": ma20,
            "prev_high": prev_high,
            "vol_ratio": vol_ratio,
            "near_20d_high_pct": near_20d_high_pct,
        }),
        "ma5_status": ma5_status,
        "ma20_status": ma20_status,
        "ma60_status": ma60_status,
        "prev_high": prev_high,
        "prev_low": prev_low,
        "near_20d_high_pct": near_20d_high_pct,
        "drawdown_from_high_pct": drawdown_from_high_pct,
    }
    return ctx


