import asyncio
import websockets
import json
import threading
import time # 🚀 [추가] 시간 측정을 위해 필요
import kiwoom_utils # 🚀 [추가] 통합 에러 로깅을 위해 필요

class KiwoomWSManager:
    def __init__(self, token):
        self.uri = 'wss://api.kiwoom.com:10000/api/dostk/websocket'
        self.token = token
        self.realtime_data = {} 
        self.subscribed_codes = set()
        self.websocket = None
        self.lock = threading.Lock()
        self.loop = None
        self.last_recv_time = time.time() # 🚀 [추가] 마지막 데이터 수신 시간 초기화

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
                    self.last_recv_time = time.time() # 🚀 [추가] 메시지가 들어올 때마다 타임스탬프 갱신
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
            # 🚀 [추가] 치명적 오류 발생 시 로깅 추가
            kiwoom_utils.log_error(f"❌ [WS] 치명적 오류 발생 (연결 끊김): {e}", send_telegram=True)

    def start(self):
        def thread_target():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._run_ws())
        
        threading.Thread(target=thread_target, daemon=True).start()

    # 🚀 [추가] 좀비 상태 체크 함수
    def check_health(self, config=None):
        """
        웹소켓 좀비 상태 체크 (15초 이상 데이터 없으면 에러 로깅)
        """
        gap = time.time() - self.last_recv_time
        if gap > 15:
            kiwoom_utils.log_error(f"⚠️ [WS] 웹소켓 데이터 수신 중단 감지 ({int(gap)}초 경과)", 
                                   config=config, send_telegram=True)
            return False
        return True

    async def _send_reg(self, codes):
        try:
            print(f"👉 [WS] 내부 _send_reg 전송 로직 진입: {codes}")
            
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
                kiwoom_utils.log_error(f"⚠️ [WS] 연결된 웹소켓이 없어 전송 실패: {codes}")
                
        except Exception as e:
            kiwoom_utils.log_error(f"🚨 [WS] _send_reg 내부 치명적 에러 발생: {e}", send_telegram=True)

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
                    kiwoom_utils.log_error(f"🚨 [WS] run_coroutine_threadsafe 실행 중 에러 발견: {e}", send_telegram=True)
            future.add_done_callback(on_complete)

    def get_latest_data(self, code):
        with self.lock:
            return self.realtime_data.get(code, {})