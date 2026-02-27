import asyncio
import websockets
import json
import threading

class KiwoomWSManager:
    def __init__(self, token):
        self.uri = 'wss://api.kiwoom.com:10000/api/dostk/websocket'
        self.token = token
        self.realtime_data = {} 
        self.subscribed_codes = set()
        self.websocket = None
        self.lock = threading.Lock()
        self.loop = None

    async def _run_ws(self):
        try:
            print("🔌 [WS] 키움 서버에 연결을 시도합니다...")
            async with websockets.connect(self.uri) as ws:
                self.websocket = ws
                print("✅ [WS] 웹소켓 연결 성공!")
                
                # 로그인 패킷 전송
                login_packet = {'trnm': 'LOGIN', 'token': self.token}
                await ws.send(json.dumps(login_packet))
                print("🔑 [WS] 로그인 패킷 전송 완료")
                
                while True:
                    msg = await ws.recv()
                    res = json.loads(msg)
                    
                    trnm = res.get('trnm')
                    if trnm not in ['PING', 'REAL']:
                        print(f"📥 [WS 서버 응답] {res}")
                    
                    if trnm == 'PING':
                        await ws.send(json.dumps(res))
                    elif trnm == 'REAL':
                        for entry in res.get('data', []):
                            dtype = entry.get('type')
                            code = entry.get('item')
                            vals = entry.get('values', {})
                            
                            with self.lock:
                                if code not in self.realtime_data:
                                    self.realtime_data[code] = {'curr': 0, 'v_pw': 0.0, 'ask_tot': 1, 'bid_tot': 1}
                                
                                # [0B] 체결데이터 (현재가, 체결강도)
                                if dtype == '0B':
                                    if '10' in vals: self.realtime_data[code]['curr'] = abs(int(vals['10']))
                                    if '228' in vals: self.realtime_data[code]['v_pw'] = float(vals['228'])
                                # [0D] 호가데이터 (총매도, 총매수 잔량)
                                elif dtype == '0D':
                                    if '121' in vals: self.realtime_data[code]['ask_tot'] = int(vals['121'])
                                    if '125' in vals: self.realtime_data[code]['bid_tot'] = int(vals['125'])

        except Exception as e:
            print(f"❌ [WS] 치명적 오류 발생 (연결 끊김): {e}")

    def start(self):
        def thread_target():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._run_ws())
        
        threading.Thread(target=thread_target, daemon=True).start()

    async def _send_reg(self, codes):
        try:
            # 💡 진입 즉시 로그를 찍어 코루틴이 살았는지 죽었는지 확인합니다.
            print(f"👉 [WS] 내부 _send_reg 전송 로직 진입: {codes}")
            
            for _ in range(50):
                if self.websocket:  # .open 제거 (라이브러리 버전 호환성 문제 완벽 해결)
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
            # 💡 [핵심] 코루틴 내부에서 에러가 터지면 무조건 터미널에 출력합니다!
            print(f"🚨 [WS] _send_reg 내부 치명적 에러 발생: {e}")

    def subscribe(self, codes):
        if not codes: return
        if isinstance(codes, str): codes = [codes]
        
        new_targets = [c for c in codes if c not in self.subscribed_codes]
        # print(f"👉 [WS] subscribe 호출됨 - 신규 등록 대상: {new_targets}")
        
        if new_targets and self.loop:
            # 코루틴을 백그라운드 루프에 던집니다.
            future = asyncio.run_coroutine_threadsafe(self._send_reg(new_targets), self.loop)
            
            # 💡 [핵심] 퓨처(Future) 결과를 감시하다가 에러가 났으면 멱살을 잡고 끌어옵니다.
            def on_complete(fut):
                try:
                    fut.result()
                except Exception as e:
                    print(f"🚨 [WS] run_coroutine_threadsafe 실행 중 에러 삼킴 발견: {e}")
            future.add_done_callback(on_complete)

    def get_latest_data(self, code):
        with self.lock:
            return self.realtime_data.get(code, {})