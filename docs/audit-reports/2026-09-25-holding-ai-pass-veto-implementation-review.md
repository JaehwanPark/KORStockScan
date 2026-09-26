# 보유 AI PASS/VETO 선행 투표 구현·코드리뷰 (2026-09-25)

## 결정

계획의 선행 관측 계층을 구현했다. `PASS`는 모든 신규 투표에서 기존 청산 신호의 진행 허용만 뜻한다. 새 투표에는 매도·추가매수·임계치·provider 변경 권한이 없다. `KORSTOCKSCAN_HOLDING_EXIT_VOTE_OBSERVE_ENABLED`의 기본값은 `false`이며, 현재 live 점수 소비·신호 시점 `holding_flow`와 실주문 결정은 이 변경으로 전환되지 않는다. 따라서 전체 PASS/VETO 전환 완료나 자연 성과 개선을 선언하지 않는다.

## 구현과 리뷰 수리

| 범위 | 구현·수리 | 검증 경계 |
| --- | --- | --- |
| 생산자 | English ASCII PASS/VETO·FIRM/TENTATIVE 프롬프트, 구조화 응답 schema, `gpt-5.4-nano` 기본 후보 endpoint, 입력 스냅샷 hash 및 AI trace 연결 | 기존 점수·HOLD/TRIM/EXIT 답변을 새 표로 변환하지 않음 |
| 원장 | 실제 포지션 key·3시장·세션·모델·프롬프트·quote route/epoch/source generation별 표, 같은 호가 중복·늦은 요청·캐시·파싱/원천 결손 제외 | 포지션별 JSONL은 0600으로 보존하고 손상 행을 source gap으로 처리 |
| 호출 | 주기적 보유 AI 입력이 있는 경우 관측 호출을 별도 symbol budget과 bounded worker로 예약 | feature flag가 꺼져 있으면 추가 provider 호출 없음. 켜져도 투표는 주문에 미반영 |
| 신호 | 일반·fast 청산 신호의 첫 시점에서 이미 완료된 표만 고정. fast 주문 경로는 dispatch 뒤 관측해 안전 지연을 추가하지 않음 | 집계는 관측 전용. hard/protect/emergency에 VETO 적용 없음 |
| 기존 회귀 | 제거된 MFE 보호 임계치의 미정의 env 변수 여섯 개를 `constants.py` 조건식에서 제거 | 기존 작업 트리의 MFE 삭제를 완결하는 import 오류 수리 |

리뷰 중 최초 문제로 `constants.py`의 `env_mfe_protect_enabled` 등 미정의 참조 때문에 모든 pytest fixture가 부팅 전에 실패했다. 잔여 참조를 제거하고 재실행했다. 이어서 quote receipt 구조를 잘못 중첩해 읽던 문제, 동일 호가의 복수 표, out-of-order 응답, 재시작 원장 소실, 손상 원장 행의 무저항 통과를 수정했다.

## 남은 전환 조건

1. 추가매수·AVG_DOWN이 현재 holding score와 재호출을 실제로 소비한다. 이 경로의 별도 소유자와 결손 기본값이 검증되기 전에는 구 점수 생산자를 제거할 수 없다. 신규 `EXIT_PERMISSION` 표는 ADD 판단에 절대 전달하지 않는다.
2. 현재 `holding_flow`는 일부 손절 신호에서 동기식으로 호출되고, trailing 및 fast exit는 별도 경로다. 시장별 표의 정족수·강도·최신성·최대 보류를 독립 검증으로 선택한 뒤에야 모든 신호 소비자를 한 계약으로 전환할 수 있다. 지금은 그 정책 산출물이 없다.
3. 9/23 보존 `holding_score` request 600건은 확인했으나 canonical context capture는 모두 `canonical_context_missing`이다. 과거 점수 답변을 PASS/VETO 표로 소급 전환할 수 없고 신규 자연 표도 아직 없다. 요청 자료는 별도 provenance 검증 후 실험 입력으로만 사용할 수 있다.
4. 정확한 BUY 체결·완료 SELL·비용·청산 후 관측을 결속한 paired EV와 독립 holdout은 아직 이 신규 투표 정책에 대해 산출되지 않았다. 이 결과 없이 선택 정책·실거래 전환·PID 소비를 선언하지 않는다.
5. 9/25 KST 체크리스트 파일이 없어 현행 실행 owner를 확인할 수 없다. 9/28 파일을 오늘 owner로 소급 사용하지 않는다.

## 검증

- 신규 원장·endpoint·호출·신호 관측 10건 PASS.
- 기존 holding fast signature·flow override 44건 PASS, fast exit dispatch 대표 1건 PASS.
- Python compile 및 `git diff --check` PASS.
- 인접 범위의 더 넓은 테스트에서 3건 실패했다. NXT 장간 세션 route와 M1 mechanical replay의 2건은 기존 작업 트리의 세션·기계 강약 변경 경로이며, entry `analyze_target` feature audit 1건은 신규 holding vote 경로 밖이다. 이 결과를 신규 투표 구현의 PASS로 합산하지 않는다.

코드 리뷰의 완료 범위는 **관측용 생산자·원장·신호 스냅샷**이다. 배포·provider 호출 기동·live 청산 소비자 전환·자연 경제성은 별개다.
