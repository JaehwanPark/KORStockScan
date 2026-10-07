# 2026-10-08 보조 튜닝·장중 적용 구현 검토

Owner: `DirectFamilySourceRepairMainMechanisticEntry`. 사용자 승인 범위는 구현·반복 리뷰/보완·배포·재기동이다. 기계 초기 목록 재선발과 원천일 quota reset은 포함하지 않는다.

## 구현과 검토

- 불변 prompt registry, 공유 원장 기반 현행/후보 표본·누적 쌍 비교, 원천일 100 attempt, cache/실패/미완료 분리, 누적 PASS 승률 채택을 구현했다. 새로운 문구는 검토 후 수동 등록하며 장후는 등록 후보만 평가한다.
- 보조 적용 기록은 기존 v5 기계 bundle 밖에서 발행한다. 확인 시각별 binding·TTL·CAS·rollback revocation·제출 직전 검증, PID 소비·다음 장후 승계를 연결했다. 기계 FSM/scope 실행 hash와 주문 중복 방지는 유지한다.
- 검토에서 발견한 보완: 원천일 변경으로 옛 예산 재설정 방지, 기본 기계 pin을 바꾸지 않는 최초 reader 이관, rollback 후 늦은 PASS 제출 차단, 독립 평가 PRE/AFTER 승계 보존, 자동 생성 checklist의 strict 원본 보존.
- 초기 목록과 미완료 보조비교를 분리했다. 표본 응답이 미완료여도 128 route의 초기 목록이 유지되는 회귀를 포함한다. 이 계약은 후속 보조 개선의 당일 교체를 금지하지 않는다.

## 검증과 실행 증거

- 1차 공유 원장/운용 계약/튜닝 회귀 51 PASS, 후속 튜닝·release handoff 74 PASS, 통합 117 PASS. 추가 소비자 회귀와 최종 배포 검증은 아래 실행 receipt로 남긴다.
- 비교 통계는 확인점 가격 경로의 WIN/FAIL_STOP/FAIL_TIMEOUT이며, 실제 주문/체결/PnL과 분리한다. 테스트 transport는 외부 AI 호출 증거가 아니다.
- 원 strict가 결속한 checklist SHA256: `48e77497685fc5f132cc435bf85d79dfad2814b4923943b0cc89d8e2e84ef828`. 수정 전에 `data/runtime/policy_bootstrap/historical_checklists/<sha>.md`로 검증·보존했다.
- 실행 receipt 저장 위치: `data/report/auxiliary-paired-intraday/2026-10-08/`. 배포/재기동/PID와 실제 후보 적용 상태는 해당 receipt로 구분한다.

- 추가 튜닝/제출/의미 감시 소비자 회귀 **375 PASS**. Python compile·`git diff --check`·print-only parser 통과, 현재 stable owner 1건.
- 실제 공유 원장에 현행/후보 50쌍을 사전 봉인했다. 신규 호출 **0**, 10/7 기존 attempt **15,228**로 새 100회 한도를 이미 초과했으므로 잔여 0을 보존했다. 후보 응답이 없어 유효 공통 쌍 0, 개선 scope 0, 후보 적용 없음이다. 비교 계약/reader 구현 완료와 후보 성과 입증을 구분한다.
- 새 후보 registry `dd44e565c10205a806554abe0b44051d22f6e4422e1176cea07d565b726833f0`는 위험 인용 ID의 존재와 실제 현재 실패 증거를 구분하는 가설이다. REGULAR scope를 결과와 무관하게 순환 추출하며 신규 실제 원천의 예산 내 평가 대상으로 등록했다.

- 최종 재리뷰: 설정된 새 비교의 캠페인 결손 시 옛 전수 큐로 fallback하지 않도록 차단했다. 최종 통합 **118 PASS**, 기계 고정 module **18/18 bytes 동일**, 검토 범위 미해결 코드 결함 0. 실제 성능 우월성은 미입증이며 현행 보조 유지다.
