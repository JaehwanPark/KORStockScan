# 제출 원천 영수증 결함 리뷰 — 2026-09-29

## 범위와 원천

- `005930`의 09:09:06 사전 경제성 관측은 공유 REST 읽기 제한으로 HTTP 전송 전에 보류됐다. 기존 `kt00011_empty`는 브로커 빈 응답처럼 보이지만 실제 전송 횟수는 0이다. 같은 시도에서 09:09:11 실제 예산 조회는 `return_code=0`, 현금 주문가능 계약 `valid`였다.
- 기계 `ENTER_NOW`와 보조 AI `PASS`의 원본 JSON 평가는 유효하다. 후속 pipeline 이벤트가 동일 dict를 Python repr로 기록하여 sentinel의 JSON 전용 검사에서 허위 schema 결손이 발생했다.
- 제출은 별도 `entry_split_probe_admission_deferred` / `residual_source_path_unavailable` 경로에서 `returned_false`로 끝났다. broker 수락과 실제 주문은 없다. 당시 첫 사례는 이전 PID `1149836`에서 발생했다. 새 PID `1161612`에서도 방향 원천 보류 사례가 있으므로, 현행 경로의 원시 WS 체결 자료와 가공 입력 묶음 차이를 검토했다.

## 공식 Kiwoom 확인

- 2026-09-29 09:49 KST에 공식 `Kiwoom-Securities/Kiwoom-REST-API` HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 원격 확인했다.
- 해당 revision의 `kiwoom_docs`는 부재한다. `kiwoom/_data/kiwoom_api_spec.json`의 `kt00011`, `kiwoom/specs.py`, `kiwoom/core/client.py`, `postman/kiwoom-openapi.postman_collection.json`의 운영·모의 요청을 대조했다. `kt00011`은 `POST /api/dostk/acnt`, `api-id=kt00011`, 필수 `stk_cd`, 선택 `uv`(원), 계좌·종목별 주문가능 금액/수량 및 return code를 제공한다. 연속조회 헤더는 공통 계약이며 이 로컬 호출은 단일 페이지다.
- 이번 수정은 endpoint, body/header, 인증, return-code/금액/수량 파싱, 실제 주문 호출, continuation 또는 호출 한도를 바꾸지 않는다. source-only 전송 전 보류에 기존 transport metadata의 원인을 연결한다.

## 수정과 안전 경계

1. 사전 관측용 `kt00011` 조회에 기존 transport metadata를 받아, HTTP 0회인 내부 읽기 보류를 `kt00011_source_read_deferred:<reason>`으로 식별한다. 실제 sizing 호출은 기존 조회·실패 차단을 유지한다.
2. pipeline provenance 병합 뒤 보조 AI 평가 dict를 JSON으로 직렬화한다. sentinel은 크기 제한을 둔 과거 Python literal 영수증도 안전하게 읽고, nullable soft-policy hash의 wire alias를 같은 null로 판독한다. 파싱 불가·의미 불일치는 계속 결손이다.
3. 다주 신규 SCALPING probe-first 경로는 원시 WS에 가공된 방향 필드가 없을 때에만 현재 수신 체결로 기존 feature packet을 재계산한다. 실제 체결 수신 시각, trusted aggressor, 신선도, 음의 방향, 독립 방향 그룹과 후속 account/order guard는 그대로 요구한다. stale/결손에서는 probe와 잔여 주문을 계속 보류한다.
4. 제안됐던 3,000,000원 고정 예산 대체는 사용자가 철회했다. 구현하지 않았으며 계좌/종목별 주문가능량 결손 시 주문 차단은 유지된다.

## 검증과 미수용 항목

- 표적 회귀: 사전 관측의 전송 전 보류와 실제 sizing 불변, 과거 보조 AI repr/PASS 및 malformed 거절, pipeline 최종 직렬화, 현재 WS 체결 재계산과 stale 거절, probe-first 일반 경로를 검증한다.
- 코드 리뷰는 원천·경제성·제출 경로의 분모를 분리한다. 본 수정은 기계 정책, AI verdict, 주문 수량, 가격, provider, bot state, 안전 가드 또는 계좌 fallback을 변경하지 않는다.
- 릴리스 선택, 재기동, 실제 PID 소비, 자연 probe 제출/미제출과 비용 후 성과는 별도 운영 영수증으로만 수용한다. 코드 통과만으로 실제 주문 증가나 경제적 개선을 주장하지 않는다.
