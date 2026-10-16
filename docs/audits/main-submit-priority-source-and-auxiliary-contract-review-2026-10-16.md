# 2026-10-16 제출 병목 우선순위 원천·보조 계약 보완

## 판정과 범위

- 사용자 `보완 우선순위 진행`에 따라 비상시 원천, 삼성전자 전송 시간 초과, HPSP CAUTION을 순서대로 검토했다.
- 기준은 selected `c94c669738d9b2c1d9bec78af9967a80ed6c02a3`, Main PID `3083694` / start ticks `17636435`, 관찰창 `2026-10-16T10:00:21.350000+09:00`~`10:35:05`다. 원 [점검 영수증](/home/ubuntu/KORStockScan/tmp/postrestart-submit-review-20261016-1035/verification.json)과 원 trace/probe bytes는 보존한다.
- 기존 `src/engine/scalping`의 producer/진단/trace와 대응 `src/tests`를 수정한다. 새 모듈이나 별도 실행 owner는 만들지 않는다. 원 작업 트리의 동시 변경은 보존하며 selected release는 수정하지 않는다.
- 세 가지 기록·분류 결함을 보완한다. 기계 신호, AI 원문·prompt·입력·membership·risk binding·PASS 조건, 원 5초 deadline, 원천 freshness, 수량·계좌·주문·custody 안전 조건은 바꾸지 않는다. 자연 제출·체결·비용 후 성과를 완료로 주장하지 않는다.

## 1. 비상시 원천·관측

- exact PID/start가 일치하는 probe는 36종목 36건이다. 패턴 불일치 18, `native_source_stale_or_absent` 14, `native_observation_source_censored` 3, `feature_window_incomplete` 1이며 Main 평가에 도달한 probe는 0이다.
- stale 14건의 원 terminal 0B age는 4,212.132~31,667.579ms다. 0D 수신이나 최초 WS ready가 이후의 fresh 0B를 증명하지 않는다. 기존 freshness 차단을 유지한다. 이 표본으로 REG 실패나 VI를 원인으로 단정하지 않는다.
- source-censored 3건의 마지막 연속 관측은 약 34~35초이며 선택 branch의 60초 history를 충족하지 못했다. 과거 결손 구간을 이어 붙이거나 residence/슬롯/TTL을 늘리지 않는다.
- 셀트리온 `068270`은 약 149.81초 관측·rolling feature complete와 native detector UNKNOWN이 함께 기록됐다. 원 receipt에는 당시 native quote tuple이 없으므로 이 사례의 UNKNOWN 원인을 호가로 확정하지 않는다.
- 별도 회귀에서 호가 누락·역전·native quote age 5,001ms에도 readiness가 실행 호가의 부적격을 표시하지 않는 결함을 재현했다. `branch_readiness`에 기존 `K.good_quote(last)` 결과와 `executable_quote` 결손을 연결했다. detector truth/ready/pending는 불변이며 UNKNOWN을 FALSE/성공으로 바꾸지 않는다.
- 운영 수용 owner는 기존 `NonfixedDispatchReadinessReview1012`다. 적용 후 같은 item/epoch/sequence의 native quote usability·missing inputs·detector truth와 자연 Main 편입 여부를 확인한다. 이번 코드 검증으로 위 36건을 소급 복구하지 않는다.

## 2. 삼성전자 시간 초과

- `10:18:22`, `10:34:48`의 두 요청은 원 budget 내 시간 초과이며 AI VETO가 아니다. 첫 요청의 provider 예약→executor enqueue는 약 877ms, 실제 SDK 구간은 약 1,471ms다. 두 번째는 input freeze 전 잔여 약 1,430ms, 준비 후 약 1,313ms였고 실제 SDK 구간 약 530ms 뒤 원 deadline이 소진됐다. 시간 초과를 전부 외부 응답 지연으로 귀속하지 않는다.
- producer가 이미 계산하는 `request_built_before_capture`, `capture_started`, `capture_finished`, `http_prepare_completed`, 단계별 잔여 ms와 `provider_deadline_budget`를 trace writer가 버리고 있었다. 고정 allowlist와 finite numeric 검증으로 보존하도록 수리했다. 원 deadline이나 timeout을 연장하지 않는다.
- cache hit의 과거 monotonic/budget를 현재 전송으로 재사용하지 않는다. token/임의 key/NaN/bool/음수 잔여값은 저장하지 않으며, 만료 근거인 음수 `timeout_override_ms`는 원 값 그대로 보존한다. 늦은 SDK terminal이나 응답을 합성하지 않는다.
- 기존 `AuxiliaryCircuitRecoveryRepair1012`가 다음 자연 요청의 capture 전후·executor/SDK·원 budget 소진을 확인한다. 이번 수리는 지연 계측 결손의 수리이며 실제 전송 속도 개선을 주장하지 않는다.

## 3. HPSP CAUTION

- 4건은 모두 response contract와 post-response execution validity가 유효한 CAUTION이다. spread 근거 3건의 원 spread는 약 0.1866~0.1880%, 거래량 근거 1건의 60초 volume ratio는 약 0.4783이다. 원 supplied fact ID와 risk binding이 일치한다.
- `continuous_reversal_policy.compose`는 이 CAUTION을 별도 `entry_ai_effective_assessment.effective_verdict`에 INSUFFICIENT로 잘못 투영했다. 유효 CAUTION을 그대로 보존하도록 수리하고 WAIT·screen pass false와 invalid-response 처리는 유지했다. prompt/원 응답/기존 보조 연구를 수정하거나 CAUTION을 PASS로 승격하지 않는다.
- 현재 결속된 outcome label은 pending이다. spread/거래량 우려가 과차단이었는지는 기존 action-neutral outcome과 비용 계약으로 검토한다. source pending을 손익 0/no-edge로 바꾸지 않는다. 원 자동 AI 승인 범위를 넓히는 overlay는 이번 변경에 포함하지 않는다.

## 리뷰·검증과 운영 인계

- 기존 함수를 원 커밋에서 읽어 동일 새 회귀에 실행했을 때 6개 실패를 재현했다. 수정 후 핵심 250개가 통과했고 probe/정책 소비/제출 observer/공유 deadline을 포함한 관련 1,253개가 모두 통과했다. 첫 전체 실행의 1,252개 통과/1개 실패 중 실패는 격리 작업본 `.venv` 부재였다. 기존 프로젝트 환경을 연결한 후 해당 별도-process native parent 검사 1개도 통과했다. compile·diff·print-only parser도 통과했으며 현재 checklist에서 기존 두 stable ID가 각각 하나임을 확인했다. [검증 영수증](/home/ubuntu/KORStockScan/tmp/submit-priority-remediation-20261016-1040/verification.json)에 원 실행과 재검사 결과를 분리한다.
- producer→trace/준비 상태→기존 consumer를 재리뷰한다. CAUTION/VETO/invalid는 진입 권한이 없고, PASS와 현재 policy/claim/주문 보호 검증은 기존 경로를 유지한다. 진단 read가 native ready나 pending을 소비하지 않는 회귀를 포함한다.
- 재리뷰 범위의 미해결 구현 finding은 0이다. 음수 timeout override의 원 만료 증거는 보존하도록 보충 수정했다. 원 셀트리온 native quote 결손·자연 원천 복구·차단 후 경제성은 구현 finding과 분리한 미확인 수용 조건이다. 실주문 경로 전체 재생, 실제 Provider/Broker 호출, 비싼 보고서 재생성과 운영 배포·재기동은 수행하지 않았다.
- 코드 검증과 배포/PID 소비는 별도다. 현재 PID를 변경하거나 원 정책/PREOPEN을 재작성하지 않았다. 운영 반영 시 기존 same-date code handoff와 native full validation, 실제 PID·다음 자연 receipt를 기존 owner로 확인한다. 새 임계치·provider·재시도·원천 freshness 완화는 없다.
