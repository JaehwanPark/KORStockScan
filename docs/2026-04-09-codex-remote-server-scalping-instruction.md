# 2026-04-09 Codex Remote Server Scalping Instruction

## 목적

이 문서는 `https://songstockscan.ddns.net` 기준 원격 자동매매 서버에 대해, `스캘핑 매매` 관점에서 Codex가 바로 수행할 수 있는 작업지시서다.

최종 목표는 `기대값/순이익 극대화`다.
현재 단계는 `1단계: 음수 leakage 제거`이며, 특히 오늘 관측된 `주문전 차단 구조`와 `리포트 정합성 문제`를 우선 정리한다.

원격서버는 동시에 `비교군` 역할도 갖기 때문에, 모든 튜닝을 한 번에 넣지 않는다.
`전략 의미를 바꾸지 않는 정합성/안정화 패치`는 우선 적용하고, `전략 기대값을 바꾸는 실험성 튜닝`은 한 축만 선택 적용한다.

## 적용 범위

- 대상 서버: `https://songstockscan.ddns.net`
- 대상 전략: `스캘핑`
- 제외 범위:
  - 스윙 전략 전반
  - `fallback` 수량 배율 추가 변경
  - `AI threshold` 전반 완화
  - `overbought` 전반 완화
  - 다중 축 동시 튜닝

## 작업 원칙

1. 원격서버는 `비교군` 가치가 있으므로, `버그성 패치`와 `실험성 튜닝`을 분리한다.
2. `profit_rate NULL -> 0` 같은 fallback 정규화 값은 비교 기준에 넣지 않는다.
3. 손익 해석은 `실현손익`만이 아니라 `미진입 기회비용`까지 포함한다.
4. 스캘핑 튜닝은 `거래를 줄이는 것`이 아니라 `기대값 개선`이 목적이다.
5. 실험성 변경은 반드시 `한 축만` 적용하고, 나머지는 유지한다.

## 우선 적용 대상 A. 정합성/안정화 패치

### A1. 예수금 조회 안정화

목표:
- `주문가능금액 0원` 오탐으로 인한 `매수수량 0주`, `불필요한 쿨다운`, `기회 상실` 방지

적용 요구사항:
- `get_deposit()`에 `재시도` 추가
- 최근 정상 주문가능금액 `fallback` 유지
- 예외/응답 이상 원인을 로그로 남김
- `deposit=0` 단발성 시 즉시 장시간 쿨다운에 들어가지 않도록 완화

완료 기준:
- 일시 API 실패가 `실제 잔고 0원`처럼 처리되지 않음
- `blocked_zero_qty`류 케이스가 줄고, 로그로 근거 추적 가능

### A2. 체결 race / 주문번호 backfill 정합성

목표:
- 초고속 부분체결이 먼저 와도 `EXEC_IGNORED` 없이 정상 인식

적용 요구사항:
- pending entry state staging 유지
- `ORDER_NOTICE` 기반 주문번호 backfill 유지
- 조기 체결 이후에도 fill state가 덮어써지지 않음

완료 기준:
- WS 체결이 주문 제출 직후/직전에 와도 정상 매칭
- `no matching active order`성 로그가 재발하지 않음

### A3. 성능 리포트 NULL 손익 방어

목표:
- `recommendation_history`의 미완료 후보나 `profit_rate NULL` 행 때문에 리포트가 왜곡되거나 500 오류가 나지 않도록 함

적용 요구사항:
- `손익 계산`은 `COMPLETED + valid profit_rate` 행만 사용
- `WATCHING/OPEN` 등 미완료 행은 운영 카운트에는 남겨도 손익 계산에서 제외
- `NULL -> 0`을 손익 해석용 기준으로 사용하지 않음

완료 기준:
- `performance_tuning`이 미완료/NULL 행이 섞여도 안정적으로 출력
- 평균 손익, 승패 계산에 미완료 행이 끼지 않음

## 선택 적용 대상 B. 실험성 튜닝 1개

### B1. latency guard 완화 canary

목표:
- 오늘 스캘핑 음수 기여의 핵심인 `AI BUY 후 미진입` 중 `latency guard miss`를 줄여 `기회비용 음수`를 완화

배경:
- 오늘 missed case의 주병목은 `latency_block`
- `희림`, `삼성E&A`, `비츠로셀`, `APS`, `현대제철`, `한텍`이 같은 계열 표본
- `missed_entry_counterfactual`에서도 `MISSED_WINNER` 비중이 높게 확인됨

적용 원칙:
- `latency` 관련 기준만 한 축 완화
- `fallback` 수량, `AI threshold`, `overbought`, `liquidity`는 동시에 건드리지 않음
- 변경 폭은 소폭만 허용

권장 방식:
- `REJECT_DANGER` 판정 일부를 `ALLOW_FALLBACK`으로 내리는 좁은 canary
- 또는 `ws_age_ms` / `spread_ratio` 기준을 아주 소폭만 완화
- 적용 후 `09:30~12:00` 구간에서 `latency miss 수`, `실체결 수`, `missed winner 감소 여부`를 추적

완료 기준:
- `latency_block` 빈도 감소
- `order_bundle_submitted` 또는 실제 체결 표본 증가
- 손실이 아닌 `기회비용 감소` 관점에서도 개선 근거 확보

## 이번 턴에서 하지 말 것

1. `fallback` 수량 배율 추가 조정
2. `AI score threshold` 전면 완화
3. `overbought` 가드 완화
4. `liquidity` 기준 변경
5. 둘 이상의 실험축 동시 적용
6. 비교 리포트에서 `profit_rate NULL -> 0` 값을 기준값처럼 사용

## 산출물 요구사항

Codex는 작업 후 아래 산출물을 남긴다.

1. 코드 변경 파일 목록
2. 변경 목적 요약
3. 테스트/검증 결과
4. 원격서버에 실제 적용한 변경과 `보류한 변경` 분리 기록
5. 실험성 튜닝을 적용했다면 아래를 반드시 기록
   - 변경한 임계값
   - 적용 이유
   - 롤백 조건
   - 모니터링 포인트

## 검증 요구사항

### 필수 검증
- 관련 파일 `py_compile`
- 해당 테스트 파일 실행
- `performance_tuning` 응답 200 확인
- `trade_review` / `entry_pipeline_flow` / `post_sell_feedback` 기본 응답 확인

### 운영 검증
- `주문가능금액 0원` 오탐 재현 여부 점검
- `EXEC_IGNORED` 재발 여부 점검
- `AI BUY -> entry_armed -> budget_pass -> order_bundle_submitted` 퍼널 개선 여부 확인
- `latency_block` 감소 여부 확인

## 완료 보고 형식

Codex는 최종 보고를 아래 형식으로 짧게 정리한다.

1. `적용한 정합성 패치`
2. `적용한 실험성 튜닝`
3. `이번에 의도적으로 적용하지 않은 항목`
4. `검증 결과`
5. `익일 모니터링 포인트`

## 한 줄 실행 요약

- 먼저 `예수금/체결/리포트 정합성`을 고친다.
- 그 다음 전략 변경은 `latency guard 완화` 한 축만 실험한다.
- `fallback 추가조정`, `AI threshold 완화`, `overbought 완화`는 이번 턴에서 하지 않는다.
