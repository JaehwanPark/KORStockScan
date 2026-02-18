import asyncio
import websockets
import json
import threading

class KiwoomWSManager:
    def __init__(self, token):
        self.uri = 'wss://api.kiwoom.com:10000/api/dostk/websocket'
        self.token = token
        # 종목별 통합 실시간 데이터 저장소
        self.realtime_data = {} 
        self.subscribed_codes = set()
        self.websocket = None
        self.lock = threading.Lock()
        self.loop = None

    async def _run_ws(self):
        try:
            async with websockets.connect(self.uri) as ws:
                self.websocket = ws
                await ws.send(json.dumps({'trnm': 'LOGIN', 'token': self.token}))
                
                while True:
                    msg = await ws.recv()
                    res = json.loads(msg)
                    
                    if res.get('trnm') == 'PING':
                        await ws.send(json.dumps(res))
                    elif res.get('trnm') == 'REAL':
                        for entry in res.get('data', []):
                            dtype = entry.get('type')
                            code = entry.get('item')
                            vals = entry.get('values', {})
                            
                            with self.lock:
                                # 초기화
                                if code not in self.realtime_data:
                                    self.realtime_data[code] = {'curr': 0, 'v_pw': 0.0, 'ask_tot': 1, 'bid_tot': 1}
                                
                                # [0B] 주식체결: 현재가(10), 체결강도(228)
                                if dtype == '0B':
                                    if '10' in vals: 
                                        self.realtime_data[code]['curr'] = abs(int(vals['10']))
                                    if '228' in vals:
                                        self.realtime_data[code]['v_pw'] = float(vals['228'])
                                        
                                # [0D] 주식호가잔량: 총매도잔량(121), 총매수잔량(125)
                                elif dtype == '0D':
                                    if '121' in vals:
                                        self.realtime_data[code]['ask_tot'] = int(vals['121'])
                                    if '125' in vals:
                                        self.realtime_data[code]['bid_tot'] = int(vals['125'])

        except Exception as e:
            print(f"❌ 웹소켓 연결 오류: {e}")

    # ... (start 등 기존 동일) ...

    async def _send_reg(self, codes):
        if self.websocket:
            reg_packet = {
                'trnm': 'REG', 'grp_no': '1', 'refresh': '1',
                # 핵심: '0B'(체결)과 '0D'(호가잔량) 두 가지를 동시 구독 요청
                'data': [{'item': list(codes), 'type': ['0B', '0D']}]
            }
            await self.websocket.send(json.dumps(reg_packet))

    def get_latest_data(self, code):
        """특정 종목의 통합 실시간 데이터를 반환"""
        with self.lock:
            return self.realtime_data.get(code, {})
        
    def start(self):
        """웹소켓 쓰레드 시작"""
        def thread_target():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._run_ws())
        
        threading.Thread(target=thread_target, daemon=True).start()

    async def _send_reg(self, codes):
        if self.websocket and self.websocket.open:
            reg_packet = {
                'trnm': 'REG',
                'grp_no': '1',
                'refresh': '1',  # 기존 등록 유지하며 추가
                'data': [
                    {
                        'item': codes,           # 종목코드 리스트
                        'type': ['0B', '0D']     # 체결강도와 호가잔량을 동시에 구독
                    }
                ]
            }
            await self.websocket.send(json.dumps(reg_packet))

    def subscribe(self, codes):
        """
        감시 대상 종목들을 웹소켓 서버에 실시간 등록(REG) 요청합니다.
        """
        # 1. 방어 로직: 코드가 없으면(None 또는 빈 리스트) 그냥 종료
        if not codes:
            return

        # 2. 단일 종목(문자열)이 들어오면 리스트로 묶어줌
        if isinstance(codes, str):
            codes = [codes]

        # 3. [핵심] 들여쓰기는 if문과 동일한 선상(바깥)에 있어야 합니다!
        new_targets = [c for c in codes if c not in self.subscribed_codes]

        # 4. 신규 타겟이 있고 이벤트 루프가 돌아가고 있다면 등록 전송
        if new_targets and self.loop:
            asyncio.run_coroutine_threadsafe(self._send_reg(new_targets), self.loop)
            self.subscribed_codes.update(new_targets)
            print(f"📡 [WS] 신규 종목 등록 완료: {new_targets}")
