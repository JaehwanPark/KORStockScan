import asyncio
import websockets
import json
import threading
from datetime import datetime

# 💡 [Level 1 & 2 적용] 독립 로거 및 싱글톤 이벤트 버스 임포트
from src.utils.logger import log_error
from src.core.event_bus import EventBus
from src.utils.constants import CONFIG_PATH, DEV_PATH

def _load_system_config():
    """웹소켓 매니저 전용 설정 로더 (의존성 분리)"""
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_error(f"🚨 설정 로드 실패: {e}")
        return {}
    
class KiwoomWSManager:
    def __init__(self, token):
        # 💡 [우아한 아키텍처] 하드코딩 파괴! 설정 파일에서 URI를 동적으로 읽어옵니다.
        conf = _load_system_config()
        # config에 URI가 없으면 안전하게 Mock API를 기본값으로 사용합니다.
        self.uri = conf.get('KIWOOM_WS_URI', 'wss://mockapi.kiwoom.com:10000/api/dostk/websocket')
        
        self.token = token
        self.realtime_data = {}
        self.subscribed_codes = set()
        self.websocket = None
        self.lock = threading.Lock()
        self.loop = None
        
        # 전역 EventBus 인스턴스 획득 및 외부 명령 수신기 장착
        self.event_bus = EventBus()
        self.event_bus.subscribe("COMMAND_WS_REG", self._handle_reg_event)
        # 💡 [추가] 최초 접속인지, 끊겼다가 다시 붙은(재접속) 것인지 구분하는 플래그
        self.is_reconnected = False
        self.condition_dict = {} # 💡 [추가] 일련번호(seq)와 검색식 이름을 매핑할 사전
        
        print(f"🌐 [WS] 웹소켓 매니저 초기화 완료 (Target: {self.uri})")
    
    async def _run_ws(self):
        while True:
            try:
                print(f"🔌 [WS] 키움 서버({self.uri})에 연결을 시도합니다...")
                async with websockets.connect(self.uri, ping_interval=None) as ws:
                    self.websocket = ws
                    print("✅ [WS] 웹소켓 연결 성공!")

                    # 1. 로그인 패킷 전송
                    login_packet = {'trnm': 'LOGIN', 'token': self.token}
                    await ws.send(json.dumps(login_packet))
                    print("🔑 [WS] 로그인 패킷 전송 완료")
                    
                    await asyncio.sleep(1) # 로그인 처리 대기

                    # 🚀 로그인 성공 직후, 조건검색식 목록(ka10171)을 먼저 요청합니다!
                    print("🔍 [WS] HTS 조건검색식 목록(CNSRLST)을 요청합니다.")
                    await ws.send(json.dumps({'trnm': 'CNSRLST'}))

                    # 💡 재접속(Reconnect)인 경우 스나이퍼 엔진에 상태 동기화 명령 하달
                    if self.is_reconnected:
                        print("🔄 [WS] 웹소켓 재접속 감지! EventBus에 상태 동기화 이벤트를 발행합니다.")
                        self.event_bus.publish("WS_RECONNECTED", {})
                    
                    # 최초 접속이 끝났으므로, 이후부터 연결되면 무조건 '재접속'으로 간주
                    self.is_reconnected = True

                    # 2. 계좌 전체 주문체결(00) 감시 명시적 등록
                    exec_reg_packet = {
                        "trnm": "REG",
                        "grp_no": "2",  
                        "refresh": "1",
                        "data": [
                            {
                                "item": [""],   
                                "type": ["00"]  
                            }
                        ]
                    }
                    await ws.send(json.dumps(exec_reg_packet))
                    print("📝 [WS] 🚨 계좌 주문/체결통보(00) 감시망 등록 완료!")

                    # 3. 기존 감시 종목 재등록 (네트워크 끊김 복구용)
                    if self.subscribed_codes:
                        await self._send_reg(list(self.subscribed_codes))

                    # 4. 메시지 수신 무한 루프
                    while True:
                        message = await ws.recv()
                        await self._handle_message(message)

            except websockets.ConnectionClosed:
                print("⚠️ [WS] 연결 끊김! 3초 후 재접속 시도...")
                self.websocket = None
                await asyncio.sleep(3)
            except Exception as e:
                from src.utils.logger import log_error
                log_error(f"🚨 [WS] 예상치 못한 오류: {e}")
                print(f"🚨 [WS] 예상치 못한 오류: {e}")
                self.websocket = None
                await asyncio.sleep(3)

    async def _handle_message(self, message):
        try:
            msg_dict = json.loads(message)
            trnm = msg_dict.get('trnm')
            
            # =========================================================
            # 🏓 [핵심] 생존 신고 (PING/PONG)
            # =========================================================
            if trnm == 'PING':
                if self.websocket:
                    pong_packet = json.dumps({"trnm": "PONG"})
                    await self.websocket.send(pong_packet)
                return
            
            # =========================================================
            # 🚀 [추가 2] 조건검색식 목록 응답 수신 (ka10171)
            # =========================================================
            if trnm == 'CNSRLST':
                data_list = msg_dict.get('data', [])
                target_seqs = []

                # 💡 HTS에서 만든 시간대별 모든 식을 다 찾습니다! (이름은 HTS 저장명에 맞게 추가하세요)
                target_keywords = [
                    "scalp_candid_aggressive_01", # 09:00 ~ 09:30 초단타 후보군 (공격형)
                    "scalp_candid_normal_01", # 09:00 ~ 09:30 초단타 후보군 (일반형)
                    "scalp_strong_01",  # 09:20 ~ 11:00 스캘핑 강세군 (공격형)
                    "scalp_underpress_01",  # 09:40 ~ 13:00 스캘핑 약세군 (수동)
                    "scalp_shooting_01",   # 09:40 ~ 13:30 스캘핑 슈팅스타 (공격형)
                    "scalp_afternoon_01"   # 13:00 ~ 15:30 장중진입_오후재점화
                ]
                # 🚨 주의: 다중 검색식을 찾을 때는 여기서 break를 쓰면 안 됩니다!

                for seq, name in data_list:
                    if any(k in name for k in target_keywords): 
                        target_seqs.append((seq, name))
                        self.condition_dict[str(seq)] = name # 💡 [핵심] 번호와 이름을 기억해 둡니다.
                
                if target_seqs:
                    for target_seq, target_name in target_seqs:
                        print(f"🎯 [WS] 스캘핑 조건식 발견: [{target_name}] (seq: {target_seq}). 실시간 PUSH 감시 요청.")
                        req_packet = {
                            'trnm': 'CNSRREQ', 'seq': str(target_seq), 'search_type': '1', 'stex_tp': 'K'
                        }
                        if self.websocket:
                            await self.websocket.send(json.dumps(req_packet))
                            await asyncio.sleep(0.2) 
                else:
                    print("⚠️ [WS] 타겟 조건검색식을 찾을 수 없습니다.")
                return
            
            # =========================================================
            # 🚀 [추가 3] 조건검색 최초 편입 목록 (ka10173)
            # =========================================================
            if trnm == 'CNSRREQ':
                # 💡 [핵심 방어] 키움 서버가 null(None)을 주더라도 안전하게 빈 리스트([])로 바꿔치기합니다!
                c_data = msg_dict.get('data') or []
                print(f"📊 [WS] 조건검색 최초 편입 종목 수: {len(c_data)}개 (스나이퍼 큐에 투입합니다)")
                for item in c_data:
                    code = item.get('jmcode', '').replace('A', '')
                    self.event_bus.publish("CONDITION_MATCHED", {'code': code, 'type': 'INIT'})
                return
            
            # =========================================================
            # 📈 [기존 트랙] 실시간 주가 / 호가 / 체결 / 조건검색 데이터 처리
            # =========================================================
            if trnm == 'REAL' and 'data' in msg_dict:
                for d in msg_dict['data']:
                    values = d.get('values', {})
                    if not values: continue

                    real_type = d.get('type')
                    
                    # 🚀 실시간 조건검색 편입/이탈 통보 가로채기 (02)
                    if real_type == '02' or d.get('name') == '조건검색':
                        seq = str(values.get('841', '')).strip() # 💡 일련번호 추출
                        code = str(values.get('9001', '')).replace('A', '').strip()
                        insert_type = str(values.get('843', '')).strip() 
                        
                        # 기억해둔 번호로 검색식 이름을 알아냅니다.
                        cnd_name = self.condition_dict.get(seq, '알수없는검색식') 

                        if insert_type == 'I':
                            print(f"🚨 [조건검색 PUSH] {code} 포착! (출처: {cnd_name})")
                            # 💡 스나이퍼에게 출처(이름표)를 함께 보냅니다!
                            self.event_bus.publish("CONDITION_MATCHED", {
                                'code': code, 
                                'type': 'REALTIME', 
                                'condition_name': cnd_name
                            })
                        continue

                    # ===================================================
                    # [트랙 A] 🚨 주문/체결 통보 가로채기 (ORDER_EXECUTED)
                    # ===================================================
                    if real_type == '00' or d.get('name') == '주문체결':
                        status = str(values.get('913', '')).strip()      
                        code = str(values.get('9001', '')).replace('A', '').strip()
                        order_no = str(values.get('9203', '')).strip()   
                        order_type_str = str(values.get('905', '')).strip() 
                        
                        print(f"📩 [WS 주문상태] {code} | 상태: '{status}' | 구분: '{order_type_str}'")

                        if status == '체결':
                            raw_price = str(values.get('910', '0')).replace('+', '').replace('-', '').strip()
                            raw_qty = str(values.get('911', '0')).replace('+', '').replace('-', '').strip()
                            
                            exec_price = int(raw_price) if raw_price.isdigit() and raw_price else 0
                            exec_qty = int(raw_qty) if raw_qty.isdigit() and raw_qty else 0
                            exec_type = 'BUY' if '매수' in order_type_str else 'SELL'
                            
                            print(f"🔔 [WS 실제체결] {code} {exec_type} {exec_qty}주 @ {exec_price}원 (주문번호: {order_no})")
                            
                            if exec_price > 0:
                                self.event_bus.publish("ORDER_EXECUTED", {
                                    'code': code,
                                    'order_no': order_no,
                                    'type': exec_type,
                                    'price': exec_price,
                                    'qty': exec_qty,
                                    'time': datetime.now().strftime('%H:%M:%S')
                                })
                        continue

                    # ===================================================
                    # [트랙 B] 실시간 주가/호가 데이터 처리
                    # ===================================================
                    item_code = d.get('item', '')
                    if item_code and real_type != '00': 
                        with self.lock:
                            # 1. 초기 데이터 구조 생성
                            if item_code not in self.realtime_data:
                                self.realtime_data[item_code] = {
                                    'curr': 0, 'v_pw': 0, 'ask_tot': 0, 'bid_tot': 0, 
                                    'volume': 0, 'time': '', 'fluctuation': 0.0, 'open': 0,
                                    'orderbook': {'asks': [], 'bids': []}
                                }
                            
                            target = self.realtime_data[item_code]

                            # 💡 안전한 파싱 헬퍼 (ValueError 방어막)
                            def safe_int(val, default=0):
                                val_str = str(val).replace('+', '').replace('-', '').strip()
                                return int(val_str) if val_str.isdigit() else default

                            # 데이터 추출 및 할당
                            if '10' in values: target['curr'] = safe_int(values['10'], target['curr'])
                            if '16' in values: target['open'] = safe_int(values['16'], target.get('open', 0))
                            if '13' in values: target['volume'] = safe_int(values['13'], target.get('volume', 0))
                                
                            if '12' in values:
                                try: target['fluctuation'] = float(values['12'].replace('+', ''))
                                except ValueError: pass
                            
                            if '228' in values:
                                try: target['v_pw'] = float(values['228'])
                                except ValueError: pass
                                
                            if '121' in values: target['ask_tot'] = safe_int(values['121'])
                            if '125' in values: target['bid_tot'] = safe_int(values['125'])

                            # '0D' 주식호가잔량 데이터 파싱 (1~5호가)
                            if real_type == '0D':
                                asks, bids = [], []
                                for i in range(1, 6):
                                    ask_p = values.get(str(40 + i))
                                    ask_v = values.get(str(60 + i))
                                    bid_p = values.get(str(50 + i))
                                    bid_v = values.get(str(70 + i))

                                    if ask_p and ask_v:
                                        asks.append({'price': safe_int(ask_p), 'volume': safe_int(ask_v)})
                                    if bid_p and bid_v:
                                        bids.append({'price': safe_int(bid_p), 'volume': safe_int(bid_v)})
                                
                                target['orderbook']['asks'] = asks[::-1]
                                target['orderbook']['bids'] = bids
                            
                            target['time'] = datetime.now().strftime('%H:%M:%S')
                            
                            # 💡 파싱 완료 후 구독자들에게 전파
                            self.event_bus.publish("REALTIME_TICK_ARRIVED", {
                                'code': item_code,
                                'data': target.copy()  
                            })

        except websockets.ConnectionClosed:
            pass
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"🚨 [WS] 메시지 파싱 에러 발생: {e} | Payload: {message[:150]}")

    def start(self):
        def thread_target():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._run_ws())

        threading.Thread(target=thread_target, daemon=True).start()

    async def _send_reg(self, codes):
        try:
            for _ in range(50):
                if self.websocket: break
                await asyncio.sleep(0.1)

            if self.websocket:
                print(f"📝 [WS] 종목 등록(REG) 전송 시도: {codes}")
                reg_packet = {
                    'trnm': 'REG',
                    'grp_no': '1',
                    'refresh': '1',
                    'data': [
                        {'item': codes, 'type': ['0B']},
                        {'item': codes, 'type': ['0D']}
                    ]
                }
                await self.websocket.send(json.dumps(reg_packet))
                self.subscribed_codes.update(codes)
                print(f"📡 [WS] 종목 등록 완료 및 데이터 수신 시작: {codes}")
            else:
                print(f"⚠️ [WS] 연결된 웹소켓이 없어 전송 실패: {codes}")

        except Exception as e:
            log_error(f"🚨 [WS] _send_reg 에러 발생: {e}")
            print(f"🚨 [WS] _send_reg 내부 치명적 에러 발생: {e}")

    def execute_subscribe(self, codes):
        if not codes: return
        if isinstance(codes, str): codes = [codes]

        new_targets = [c for c in codes if c not in self.subscribed_codes]

        if new_targets and self.loop:
            future = asyncio.run_coroutine_threadsafe(self._send_reg(new_targets), self.loop)

            def on_complete(fut):
                try: fut.result()
                except Exception as e:
                    log_error(f"🚨 [WS] 스레드 통신 간 에러 발생: {e}")
                    print(f"🚨 [WS] 스레드 통신 간 에러 발생: {e}")

            future.add_done_callback(on_complete)
    
    def _handle_reg_event(self, payload):
        codes = payload.get("codes", [])
        self.execute_subscribe(codes) 

    def get_latest_data(self, code):
        with self.lock:
            return self.realtime_data.get(code, {})