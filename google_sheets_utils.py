import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

class GoogleSheetsManager:
    def __init__(self, json_key_path, spreadsheet_name):
        # 인증 설정
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(json_key_path, scope)
        self.client = gspread.authorize(self.creds)
        
        # 스프레드시트 열기 (없으면 에러 발생하므로 미리 생성 필요)
        self.sheet = self.client.open(spreadsheet_name).get_worksheet(0)

    def record_signal(self, stock_name, buy_price, score, sell_price):
        """
        신호 발생 데이터를 스프레드시트의 새 행에 추가합니다.
        """
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # 행 데이터 구성: 날짜, 종목명, 매수가, 확신지수, 매도가
            row = [now, stock_name, buy_price, score, sell_price]
            self.sheet.append_row(row)
            print(f"📊 [Sheets] 기록 완료: {stock_name}")
        except Exception as e:
            print(f"❌ [Sheets] 기록 실패: {e}")