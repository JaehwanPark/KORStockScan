import json
import requests

print("🚨 파일이 정상적으로 실행되었습니다! (이 문구조차 안 뜨면 실행 방식 문제)") # 이 줄을 추가!

def run_telegram_test():
    print("🔍 텔레그램 알림 발송 테스트를 시작합니다...")
    
    # 1. 설정 파일 로드
    try:
        with open('config_prod.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ 'config_prod.json' 파일을 찾을 수 없습니다.")
        return
    except json.JSONDecodeError:
        print("❌ 'config_prod.json' 파일의 형식이 잘못되었습니다.")
        return

    # 2. 토큰 및 ID 확보
    token = config.get('TELEGRAM_TOKEN')
    chat_ids = config.get('CHAT_IDS', [])
    admin_id = config.get('ADMIN_ID')

    if not token:
        print("❌ 설정 파일에 'TELEGRAM_TOKEN'이 없습니다.")
        return

    # 관리자 ID도 발송 대상에 포함하여 중복 제거
    target_ids = set(chat_ids)
    if admin_id:
        target_ids.add(admin_id)

    if not target_ids:
        print("❌ 설정 파일에 'CHAT_IDS' 또는 'ADMIN_ID'가 없습니다.")
        return

    print(f"✅ 토큰 확인: {token[:8]}... (보안상 일부 생략)")
    print(f"✅ 발송 대상 ID: {list(target_ids)}")
    print("-" * 40)

    # 3. 테스트 메시지 발송
    for chat_id in target_ids:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": "🤖 *[KORStockScan 테스트]*\n이 메시지가 보인다면 텔레그램 연동은 100% 정상입니다!\n\n장중 알림이 오지 않는다면 엔진의 매수/매도 조건이 아직 충족되지 않은 것입니다.",
            "parse_mode": "Markdown"
        }
        
        try:
            res = requests.post(url, data=payload, timeout=10)
            data = res.json()
            
            if res.status_code == 200 and data.get("ok"):
                print(f"🟢 [성공] ID {chat_id}로 메시지 발송 완료!")
            else:
                print(f"🔴 [실패] ID {chat_id} 발송 에러: {data.get('description')}")
                
        except Exception as e:
            print(f"💥 통신 에러 발생: {e}")

if __name__ == "__main__":
    run_telegram_test()