# Main-only 전체 퇴역 구현 검토 — 2026-10-08

사용자가 에피소드·위젯 전체 제거, 반복 코드리뷰/보완, 배포·재기동과 불필요 임시/과거 파일 정리를 승인했다. 과거 체결 잔여는 사용자 수동관리이며 계좌 조회·매도·broker flat을 작업의 조건으로 두지 않는다.

공통 journal은 원 owner/fill/terminal을 변경하지 않고 수동관리 지시만 한 번 append한다. Main 자동 실행 투영은 Main 수량만 사용하고 구 owner의 pending intent를 실행/차단 권한으로 사용하지 않는다. Main 정책과 부모, DB·수동 veto·hard/order guard는 유지한다. 전용 production 코드/설치 payload/test를 제거하고 Main 공통 digest, packet source validation, adverse flow, 시장일, 재기동 flag, native Main/manual custody를 살아 있는 역할 package로 옮겼다.

리뷰에서 남은 취소대기/수량 연구의 간접 import, 삭제된 handoff를 참조하는 restart wrapper, 동결 재생의 파일 생성, 장후 intake NameError와 옛 checklist 복원 발행을 발견해 보완했다. read-only journal 조회는 hash-chain 및 전후 파일 세대 검증을 수행하며 실제 주문 예약은 flock을 유지한다. frozen replay는 기록된 common journal과 명시적 부재만 읽는다. 과거 strict/controller/finalization은 기존 13개 stage의 원 바이트를 검증하며 미래 stage는 6개 Main 구성만 발행한다.

Kiwoom official reference HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`은 실제 조회 SHA를 evidence JSON과 대조한다. 공식 specs/core/realtime/패킷/schema/Postman을 확인했다. API wire/FID/auth/호출 제한 변경은 없다. 로컬 retired-owner guard와 전용 WS writer 제거만 수행한다.

검증·배포·삭제 결과는 이하 최종 영수증으로 보완한다. 자연 다음 장후/기동은 예정 시각 전에는 관측되지 않은 상태다.
