import asyncio
import websockets
import json
import threading
from datetime import datetime

class KiwoomWSManager:
    def __init__(self, token, on_execution_callback=None):
        self.uri = 'wss://api.kiwoom.com:10000/api/dostk/websocket'
        self.token = token
        self.realtime_data = {}
        self.subscribed_codes = set()
        self.websocket = None
        self.lock = threading.Lock()
        self.loop = None
        self.on_execution_callback = on_execution_callback

    async def _run_ws(self):
        while True:
            try:
                print("🔌 [WS] 키움 서버에 연결을 시도합니다...")
                # ping_interval=None으로 설정하여 키움 서버의 PING 패킷을 수동으로 처리합니다.
                async with websockets.connect(self.uri, ping_interval=None) as ws:
                    self.websocket = ws
                    print("✅ [WS] 웹소켓 연결 성공!")

                    # 1. 로그인 패킷 전송
                    login_packet = {'trnm': 'LOGIN', 'token': self.token}
                    await ws.send(json.dumps(login_packet))
                    print("🔑 [WS] 로그인 패킷 전송 완료")
                    
                    await asyncio.sleep(1) # 로그인 처리 대기

                    # 🚀 2. 계좌 전체 주문체결(00) 감시 명시적 등록
                    exec_reg_packet = {
                        "trnm": "REG",
                        "grp_no": "2",  # 기존 호가 감시(1)와 충돌하지 않도록 그룹번호 2 사용
                        "refresh": "1",
                        "data": [
                            {
                                "item": [""],   # 전체 종목
                                "type": ["00"]  # 주문/체결 통보
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
                print(f"🚨 [WS] 예상치 못한 오류: {e}")
                self.websocket = None
                await asyncio.sleep(3)

    async def _handle_message(self, message):
        try:
            msg_dict = json.loads(message)
            trnm = msg_dict.get('trnm')
            
            # 🛡️ [생존 신고] 키움 서버의 PING에 PONG으로 응답하여 연결 끊김 방지
            if trnm == 'PING':
                if self.websocket:
                    await self.websocket.send(message)
                return
            
            if trnm == 'REAL' and 'data' in msg_dict:
                for d in msg_dict['data']:
                    values = d.get('values', {})
                    if not values: continue

                    real_type = d.get('type')
                    
                    # ===================================================
                    # [트랙 A] 🚨 주문/체결 통보 가로채기
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
                            
                            if exec_price > 0 and self.on_execution_callback:
                                self.on_execution_callback({
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
                            # 1. 초기 데이터 구조 생성 (신규 종목 진입 시)
                            if item_code not in self.realtime_data:
                                self.realtime_data[item_code] = {
                                    'curr': 0, 
                                    'v_pw': 0, 
                                    'ask_tot': 0, 
                                    'bid_tot': 0, 
                                    'time': '',
                                    'fluctuation': 0.0,
                                    'open': 0,  # 💡 시가 데이터 추가
                                    'orderbook': {'asks': [], 'bids': []} # 🚀 [필수 교정] 초기화 시 포함되어야 함
                                }
                            
                            target = self.realtime_data[item_code]

                            # 10: 현재가
                            if '10' in values:
                                raw_curr = values['10'].replace('+', '').replace('-', '')
                                target['curr'] = int(raw_curr) if raw_curr.isdigit() else target['curr']
                            
                            # 16: 시가
                            if '16' in values:
                                raw_open = values['16'].replace('+', '').replace('-', '')
                                target['open'] = int(raw_open) if raw_open.isdigit() else target.get('open', 0)
                                
                            # 12: 전일 대비 등락률
                            if '12' in values:
                                raw_rate = values['12'].replace('+', '')
                                try: target['fluctuation'] = float(raw_rate)
                                except ValueError: pass
                            
                            # 228: 체결강도
                            if '228' in values:
                                target['v_pw'] = float(values['228'])
                                
                            # 121: 매도호가 총잔량
                            if '121' in values:
                                target['ask_tot'] = int(values['121'])
                                
                            # 125: 매수호가 총잔량
                            if '125' in values:
                                target['bid_tot'] = int(values['125'])

                            # 🚀 [신규 추가] '0D' 주식호가잔량 데이터 파싱
                            if real_type == '0D':
                                asks = []
                                bids = []
                                # 1호가부터 5호가까지만 추출 (Gemini 토큰 절약 및 핵심 데이터 집중)
                                # 키움 FID 규칙: 매도호가(41~50), 매수호가(51~60), 매도잔량(61~70), 매수잔량(71~80)
                                for i in range(1, 6):
                                    ask_p = values.get(str(40 + i))
                                    ask_v = values.get(str(60 + i))
                                    bid_p = values.get(str(50 + i))
                                    bid_v = values.get(str(70 + i))

                                    if ask_p and ask_v:
                                        asks.append({
                                            'price': abs(int(ask_p.replace('+', '').replace('-', ''))), 
                                            'volume': int(ask_v)
                                        })
                                    if bid_p and bid_v:
                                        bids.append({
                                            'price': abs(int(bid_p.replace('+', '').replace('-', ''))), 
                                            'volume': int(bid_v)
                                        })
                                
                                # 매도호가는 역순(5호가 -> 1호가)이 보기 편하므로 뒤집어줌
                                target['orderbook']['asks'] = asks[::-1]
                                target['orderbook']['bids'] = bids
                            
                            target['time'] = datetime.now().strftime('%H:%M:%S')

        except Exception as e:
            pass # 불필요한 에러 로그 방지

    def start(self):
        def thread_target():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._run_ws())

        threading.Thread(target=thread_target, daemon=True).start()

    async def _send_reg(self, codes):
        try:
            for _ in range(50):
                if self.websocket:
                    break
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
            print(f"🚨 [WS] _send_reg 내부 치명적 에러 발생: {e}")

    def subscribe(self, codes):
        if not codes: return
        if isinstance(codes, str): codes = [codes]

        new_targets = [c for c in codes if c not in self.subscribed_codes]

        if new_targets and self.loop:
            future = asyncio.run_coroutine_threadsafe(self._send_reg(new_targets), self.loop)

            def on_complete(fut):
                try:
                    fut.result()
                except Exception as e:
                    print(f"🚨 [WS] 스레드 통신 간 에러 발생: {e}")

            future.add_done_callback(on_complete)

    def get_latest_data(self, code):
        with self.lock:
            return self.realtime_data.get(code, {})