# 보조 AI PASS/VETO 원천·선택 결함 보완: 2026-10-02 장후 적용 계획

## 결정과 시간 경계

- **2026-10-02 장중에는 10월 1일 장후에 최종 선정된 현행 보조 AI 프롬프트·소프트 정책을 그대로 사용한다.** 장중 AI 응답, provider, 주문·가격·수량, 기계 `BLOCK/RECHECK/ENTER_NOW` 및 안전 차단을 새 후보로 바꾸지 않는다.
- 원천 결속에 필요한 **기록 전용 생산자**는 기존 [10월 1일 compact 직접 원천 수리 항목](../checklists/2026-10-01-stage2-todo-checklist.md)의 소유 범위에서 리뷰·표적 시험 후 10월 2일 장전 선택 릴리스에 포함되어야 10월 2일 자연 원천을 얻을 수 있다. 이 수리는 판정·제출·주문 수량·제공자·안전 경로의 before/after 불변을 확인하고 장중 재기동을 요구하지 않는다. 장전 반영이 불가능하면 원천을 사후 생성하지 않고 10월 2일 표본을 `source_gap`으로 처리한다.
- 후보 선택·발행 **새 계산 버전**은 10월 2일 장후 시작 전 격리된 작업본에서 리뷰·샘플 시험을 마친다. 장중 프로세스 종료 뒤 선택 릴리스와 장후 생산자 경로를 대조해 **10월 2일 원천의 장후 평가부터** 소비한다. 조건을 모두 통과한 정책만 다음 실제 거래일자로 발행하며, 그렇지 않으면 현 정책을 승계한다. 정책 파일 생성, 장전 준비, 실제 PID 소비와 자연 비용 후 성과는 각각 별도 영수증이다.
- 범위는 기계 `ENTER_NOW` 뒤의 compact 보조 AI다. 2026-09-29 이후 정확한 원천만 누적한다. 6~8월과 9월 28일까지의 자료는 새 후보 학습·승계에 사용하지 않는다. 과거 결손을 임의 손절·0원 비용·실제 체결로 복원하지 않는다.

## 재현된 문제

9월 30일 원본 6건은 `PASS` 5건, 전송 미평가 1건, `VETO` 0건이었다. 정확한 주 경제성 비교는 **0/6건**으로, 5건은 손절 거리 결손, 1건은 응답 전송 결손이었다. 현재 원천 투영의 writer plan hash, trace plan hash, exact owner join은 각각 0/6건이다. 따라서 기존 정책보다 비용 후 우수한 후보라는 결론이 없다.

별도의 고정 10분 반사실 진단은 9월 29~30일 누적 44건 중 10건이 적격했다. 모두 `PASS`이며 기록된 비용을 뺀 경로가 양수 4건·음수 6건이다. 보고서의 **23개 trial 기록은 부모·중복·미응답 프롬프트 fallback을 포함**한다. 정책/프롬프트 조합은 22개이며 8개 trial은 정확한 변형 응답이 없다. 모든 표시 전이는 `PASS→PASS`였으나 23개 후보 모두 AI 비교를 완료했다는 뜻이 아니다. 적격 10건의 `LIQUIDITY_FRAGILE`·`ADVERSE_TAPE` 강도는 모두 0, `REWARD_RISK_WEAK`은 결손이다. 전자의 0은 검증된 변환식의 정상 값으로, 후자의 결손과 다르다. 프롬프트 변형은 `prompt_DuplicateAttemptError` 후 정확한 후보 응답이 없어 끝나지 않았다. 이 10분 경로는 실제 주문·정확 손절·왕복 총비용·포트폴리오 수익을 증명하지 않는다.

## 변경 설계

1. **원천 생성과 결속:** 기존 `entry_execution_sizing_plan.py`의 계획 해시 생산자, `sniper_state_handlers.py`의 writer 영수증, `ai_decision_trace.py`의 AI 호출 영수증, `ai_decision_quality.py`의 후행 라벨을 `evaluation_attempt_id + plan_sha256 + venue/session/route + 결정시각`으로 연결한다. AI 호출 전 사용 가능한 기준가·비용 종류·명시적 손절 원천은 source-only 영수증으로 고정하고, PASS 뒤의 실제 제출 계획과 VETO/미제출의 반사실 계획을 다른 유형으로 보존한다. 실제 주문이 없으면 `actual_order_submitted=false`이며 체결 손익을 만들지 않는다. 손절·왕복비용·owner seed가 없으면 이유를 남기고 그 값을 요구하는 비교에서 해당 행만 제외한다. producer에 값이 없던 9월 30일 기록은 복원했다고 표시하지 않는다.
2. **결과 경로와 비용 의미:** 현재 고정 10분 경로의 비용이 체결 마찰만인지 왕복 수수료·세금까지 포함한 값인지 contract 종류·구성요소로 검증한다. 이름의 `net`만으로 full-cost로 인정하지 않는다. 고정 경계 CF의 진단은 정확 stop/portfolio 결손 때문에 전부 막지 않는다. 별도 owner 운영 비교는 실제/반사실 실행계획·명시적 손절·full-cost·노출·검증된 모델의 원래 요건을 적용한다. 고정 10분 경계를 실제 손절로 대체하지 않고, 같은 봉의 target/adverse 선후 불명·관측 간격·세션 종료 결손은 제외한다. 검증된 고정 기간 비용 모델을 향후 정책 평가에 쓰려면 metric/authority를 명시한 버전으로 발행 소비자와 함께 검증하며, 현재 마찰비용 진단을 몰래 그 모델로 승격하지 않는다.
3. **잘못된 PASS와 VETO를 함께 계수:** 같은 고유 기회에서 `PASS→PASS`, `PASS→CAUTION/VETO`, `VETO→VETO`, `VETO→PASS`, transport/INSUFFICIENT를 나눠, 비용 후 음수 PASS 차단, 양수 PASS 보존, 양수 VETO 회복, 음수 VETO 보존 및 꼬리 손실을 보고한다. 현재 VETO 자연 표본 0건은 개선 0건이 아니라 `not_observed`다. 기계 미진입을 보조 AI가 진입으로 바꾸지 않는다.
4. **후보 생성 보완:** 기존 증거 수/강도 trial을 비교 기준으로 보존하되 정책+프롬프트 hash로 중복을 제거한다. 현재 소프트 로직은 근거 부족 PASS를 CAUTION으로, 제한된 soft VETO를 PASS로 바꿀 수 있다. PASS→VETO는 검증된 후보 프롬프트 응답의 위험 사실·인용 근거가 필요하며 소프트 threshold만으로 만들어졌다고 표시하지 않는다. 신규 후보의 특징·경계는 학습일 사전 사실에서만 생성하고 무근거 VETO를 만들지 않는다. 유형 leaf는 현행 학습 고유 기회 5개 하한을 유지하며 희소/UNKNOWN은 부모 설정으로 되돌린다. 유형별 같은 값만 있는 축은 탐색에서 제외하고 이를 source missing과 구별한다. 내부 프롬프트·schema는 English ASCII 계약을 유지한다.
5. **정확 프롬프트 후보와 재시도:** `prompt_DuplicateAttemptError`는 이전 예산 예약·응답의 동일 identity와 원천/프롬프트 해시를 조회해 완전한 성공 응답만 재사용한다. 응답이 없거나 identity가 다르면 `prompt_variant_source_gap`으로 격리하고 그 변형은 승계 대상에서 제외한다. 새 identity를 발급해 중복 예약을 우회하거나 provider를 무한 재호출하지 않는다. 비교할 후보 응답이 없으면 프롬프트 개선을 주장하지 않는다.
6. **학습 선택과 검증의 분리:** 현재 `evaluate_auxiliary_stage`는 모든 trial의 holdout 결과를 필터에 넣은 뒤 train 순위로 고른다. 이를 실제 코드 수정 대상으로 명시한다. 학습 적격성·학습 순위만으로 후보 1개와 계약 hash를 먼저 봉인하고 그 후보의 holdout만 통과/거절에 사용한다. 학습 1위가 실패하고 2위가 통과하는 fixture의 결론은 부모 승계다. 검증 성적·검증 응답 결손·검증 전체 양음 분포를 보고 후보를 교체하지 않는다. 같은 날짜도 기회 단위 70/30 분할과 관측구간 purge로 독립성이 있으면 평가한다.
7. **승계·발행 계약:** 기존 보조 단계의 학습 5·검증 3개 고유 기회, 학습 변경 2·검증 변경 1개, 성공 PASS 손실 0, 학습 쌍 차이 양수·검증 차이 비음수, 원래의 split별 양수/음수 경로 및 PASS 지원 조건을 명시적으로 보존한다. 비용·원천·후보 응답은 승계 비교에 포함된 모든 행에 정확히 결속되어야 한다. 대상 scope 전체에서 몇 행이 제외됐는지도 별도 기록해 100% 응답을 선택적 표본의 통계로 숨기지 않는다. 실제 VETO→PASS를 바꾸는 후보는 그 방향의 train/holdout 지원을 요구한다. VETO 원본이 없더라도 VETO 동작을 바꾸지 않는 PASS 개선의 연구·검증은 계속하며 '오류 VETO 개선' 주장은 하지 않는다. 비용 후 쌍 EV와 꼬리 위험이 목적이고 `q`나 단순 승률이 이를 대신하지 않는다.

발행 검사에서 **현재 코드가 독립 `auxiliary_stage`를 통해 owner 운영 비교와 별도로 선정할 수 있다는 사실**을 보존해 검토한다. 앞선 계획의 모든 보조 후보에 full portfolio/정확 stop을 일괄 요구하는 표현은 수정했다. stop 경로에는 exact stop, owner 운영 경제성에는 owner 모델·노출 조건, 고정 기간 CF에는 명시된 경계·완료 가격·비용/metric 계약을 각각 적용한다. source-only 수리와 단순 진단에 수익 하한을 새로 붙이지 않는다. 반대로 마찰비용만 있는 현재 10분 진단이 full-cost 주 경제성의 발행 근거로 오인되는 경로는 승인된 metric 계약에 맞춰 막는다. 기존 발행물은 원래 버전으로 읽고 신규 결과의 metric/authority 버전만 올린다. 고정된 날짜 수 대기는 도입하지 않는다.

| 평가 계약 | 표본·비용 조건 | 발행에서 확인할 것 |
| --- | --- | --- |
| 독립 AI 단계 | 현행 5개 학습/3개 검증과 변경 2/1 조건, 정확 응답·고정 경계·명시된 비용 | 현재 코드는 이 경로로 soft/prompt 발행이 가능하다. 새 버전은 비용 종류와 승인된 단계 metric의 일치를 소비자에서도 재검증한다. 현 10분 마찰비용 진단을 완전한 운영 순이익으로 표기하지 않는다. 비용 계약을 보완하지 못한 신규 후보는 research/carry이고 과거 발행의 계약은 소급 변경하지 않는다. |
| owner 운영 쌍 비교 v8 | 기존 학습/검증 각 20개 episode, 모델의 독립 검증이 prompt 학습보다 앞섬, full-cost·동일 노출·추론비용, 양수 paired/portfolio delta·스트레스 하한 및 꼬리 비악화 | 기존 20/20은 episode 수이며 20일 대기가 아니다. 이 경로에 속한 후보를 5/3 단계 검사만으로 우회 발행하지 않는다. 실제 체결과 CF 모델 이익은 구분한다. |

## 재점검에서 추가한 원천·의미·재실행 계약

- **위험 강도 0의 포화:** 현재 `LIQUIDITY_FRAGILE=max(0, spread_bp−40)`, `ADVERSE_TAPE=max(0, 1−2×buy_pressure/100)`이다. 강한 체결 압력 구간에서 0만 나온다고 producer가 고장났다고 단정하지 않는다. 원시값·변환값·단위·as-of·원천 hash·risk_fact_binding을 대조하고, 단위 오류/전파 누락/정상 포화를 구분한다. 정상 포화에는 같은 0을 반복하는 후보 대신 현재 등록 축의 유효 변화 범위와 사실 결속을 검토한다. 원시 압력·완료 상승률 추가 학습은 오프라인 가설이며 미래 label로 새로운 위험 사실을 만들거나 기계 판단을 중복 우회하지 않는다.
- **위험 억제 프롬프트 누락:** `entry_machine_auxiliary_compact_risk_v2`는 등록되어 있고 owner 후보 방향 선택에서도 쓰이지만, 현재 독립 단계의 prompt 목록은 compact/opportunity/contract여서 risk 변형이 빠져 있다. 잘못된 PASS를 줄이는 방향이 탐색에 실제 들어가도록 현재 contract 부모 기준 risk와 opportunity 두 변형을 학습에서 대칭 비교한다. 다른 부모일 때도 등록된 같은 목적의 최대 2개 변형을 명시적으로 선택한다. 생산·cache identity·완료 검사·재생·발행은 하나의 봉인된 변형 목록을 소비하며 서로 다른 하드코딩 목록을 없앤다. 모든 PASS를 차단하는 후보는 성공 PASS 보존과 EV 조건에서 탈락해야 한다. 프롬프트 문구 변경 시 hash/버전·사실 인용·schema 시험을 함께 갱신한다.
- **예외 경로 기록:** PASS/VETO뿐 아니라 timeout/schema reject도 같은 사전 관측 영수증을 보존한다. 다만 broker capacity가 없거나 기존 guard가 차단한 경우의 plan 부재는 정상적인 source_gap일 수 있다. 분석을 위해 broker 조회·가상 수량·가짜 stop을 강제하지 않는다. pre-AI source-only plan과 post-AI 실제 sizing plan이 다르면 각 hash와 전이 이유를 보존한다. 로깅 실패가 매매를 새로 승인하거나 원래 거부를 해제해서는 안 된다.
- **CAUTION의 시간 의미:** 현재 코드의 `new != PASS`는 즉시 노출을 안 했다는 비교다. CAUTION 후 재진입·지연·가격 악화를 무조건 0원으로 처리해 VETO와 같은 영구 손실 회피로 계산하지 않는다. 고정 checkpoint CF에는 '이 시점 미진입'으로만 표시하고, 실제 운영 EV를 주장할 때는 같은 episode의 recheck→결정→실행 후행 owner 경로를 연결한다. 연결이 없으면 운영 비교는 source_gap이다.
- **관측 flag와 실주문:** 관측 보고서·pending label의 `actual_order_submitted=false`는 해당 artifact가 주문을 실행하지 않는다는 authority 값일 수 있다. 그 값만으로 실제 제출 0건을 확정하지 않는다. 실제 주문 여부는 native intent·broker order·fill·terminal ledger와 attempt/owner로 대조하며 `BUY` action도 실제 제출 건수로 세지 않는다. AI PASS 이후의 guard 차단 손실을 AI의 실현 손익으로 귀속하지 않는다.
- **프롬프트 결손과 cache:** 완전한 응답 없이 부모 fallback을 쓴 trial은 `not_evaluated_prompt`이며 평가 완료 후보 수에 넣지 않는다. 성공 ledger settlement만 있고 checkpoint 응답이 없는 상태는 정확 response hash의 영속 원본을 검증해 복구하거나 해당 변형을 미완료로 끝낸다. 예약/전송 여부 불명 상태를 timeout=VETO로 바꾸지 않는다. 하나의 결손은 다른 독립 소프트 후보의 학습을 전부 막지 않으며, 전역 예산/인증 장애는 provider 작업의 terminal에 남긴다.
- **호출·탐색 상한:** scope당 고유 정책/프롬프트 후보 최대 32개, 기존 parent 외 프롬프트 변형 최대 2개를 기본 상한으로 고정한다. 학습에서 공통 응답 cache를 만들고 holdout은 선택된 한 prompt만 추가 평가한다. 기존 ledger의 일일 390회·1 USD와 CLI `max_new`·기존 stage timeout 중 더 작은 한도를 적용하고 검증된 비용표를 사용한다. 예산 초과 후보는 불완전이며 저렴한 차순위 후보를 같은 holdout 성적으로 재선택하지 않는다. provider/model은 바꾸지 않는다.
- **같은 기회·부모·원천:** 날짜·종목·venue/session·scanner promotion을 포함한 검증된 lineage로 중복을 묶는다. promotion ID 결손끼리 한 기회로 합치거나 trace마다 새 기회로 세지 않는다. 반복 시도 대표 선택은 결과를 보기 전 시각 기준으로 정한다. 현행 최대 4개 과거 projection+당일은 제한된 rolling 창이며 장기 누적과 다르다. 사용자 의도에 맞춰 9/29 이후 적격 날짜의 봉인된 compact projection manifest를 누적하고, 학습은 이 manifest의 검증일 이전 적격 기회를 제한 메모리로 순회한다. raw 전체 재로딩은 하지 않는다. 정확 입력·계약·부모 hash가 일치하는 projection/cache만 재사용하며 변경된 날짜만 재구축한다. 최근 창과 누적 결과를 별도 보고하고, 읽지 않은 과거 날짜를 포함한 누적 성과를 주장하지 않는다. 5일을 넘는 fixture에서 초기 적격 날짜 보존, 검증일 격리, 중복 제거, bounded RSS를 검사한다.

기계/보조 부모 충돌, 검증 관측기간 겹침, 전체 해시와 학습 seed 분리, 부분 발행·중복 실행·rollback 및 NXT 종료 이후의 실제 배포 경계는 [기계 계획의 공통 계약](main-machine-missed-entry-priority-postclose-plan-2026-10-01.md#두-계획의-공통-적용검증-계약)을 따른다. 보조 A1은 기계 M0에서 통과했다고 기계 M1의 신규 ENTER_NOW 표본에 자동 적용하지 않는다.

## 완료된 작은 시험과 내일의 성능 게이트

| 시험 | 결과 또는 합격 조건 |
| --- | --- |
| **현재 평가 재현** | 읽기 전용 44행·23 trial 보조 단계 재생 10회 중앙값 **73.9ms**, 한 프로세스 최대 RSS **48,532KiB ≈47.4MiB**. 프롬프트 호출·파일 쓰기 없이 같은 10개 적격 기회와 표시 전이를 재현했다. 8개 prompt trial은 응답 결손이며 전체 장후 실행/완전한 23후보 비교가 아니다. |
| **일반화 실패 반례** | 사전 특징 3개(`buy_pressure_10t`, 완료 상승률, 순공격 체결량)의 단일 경계만 9/29 학습 5건으로 탐색했다. 최선의 `완료 상승률 > 0.75615%` 차단은 학습 손실 PASS 2건을 걸러 쌍 차이 **+0.09409%p**였지만, 9/30 검증 5건에서는 성공 PASS 1건을 막고 손실 PASS 0건을 걸러 **−0.04544%p**였다. 이는 표본의 일반화 실패를 보이는 승계 거절 회귀이며 이 시험 자체가 데이터 누수를 입증한 것은 아니다. 경계 탐색 10,000회 반복의 순수 계산은 약 **76μs/10행**이었다. |
| **원천 fixture** | 자연 PASS, VETO, timeout, schema 거절, 미제출·부분체결·완료체결, stop/비용/owner seed 결손, 동일 attempt 재시도, route/session/plan hash 충돌을 검사한다. 유효 행만 채택하고 결손을 0으로 채우지 않으며, 실제/반사실·시도/기회가 합쳐지지 않아야 한다. |
| **판정 fixture** | 근거 있는 나쁜 PASS의 `PASS→CAUTION/VETO`, 근거 있는 놓친 VETO의 `VETO→PASS`, 성공 PASS 보존, 하드 위험 VETO 보존, 무근거 PASS 및 자료 결손 fail closed를 검사한다. 정확 프롬프트 응답이 없거나 후보가 한 건도 바뀌지 않으면 승계하지 않는다. |
| **선택·계약 fixture** | 학습 1위가 holdout 실패하고 2위가 통과해도 carry여야 한다. 검증 label/종목/응답 결손 변경은 학습 1위를 바꾸지 못한다. 같은 날 독립 5/3 지원이 있으면 날짜 하한으로 막히지 않는다. risk/opportunity 두 변형의 생산·완료·재생 목록 일치, owner v8의 20/20 요건 우회 방지, 관측기간 겹침, VETO 0건의 PASS-only 개선, CAUTION 후 손실 재진입, 비용 종류 혼동, 기계 부모 교체, prompt settlement 뒤 checkpoint 소실을 검사한다. |
| **같은 입력 성능 비교** | 9/29~30 동결 원천과 10/2 새 자연 원천을 각각 구/신 버전의 동일 상한으로 재생해 wall·CPU·RSS·읽은 바이트·후보 수·provider 예약/실호출 수를 기록한다. 새 버전은 정해진 호출·메모리 가드를 넘지 않고 중단/재개 후 동일 해시·선택을 재현해야 한다. 초과나 영수증 누락 시 장후 투입을 중단한다. |
| **10/2 장후 최종** | 선행 원천 감사→라벨→보조 단계·해당 비용/owner 비교→발행→summary·strict verifier·controller·finalization 순으로 영수증을 확인한다. 새 자연 원천이나 해당 후보가 바꾸는 방향의 지원·비용·독립 검증이 부족하면 그 scope를 carry한다. VETO 원본 0건 자체가 PASS-only 연구/승계를 일괄 막는 조건은 아니다. 다음 거래일 로더·PID·자연 손익은 이후 별도 수용한다. |

수정 후에는 producer→라벨→후보→발행기·기존 발행물 readback을 리뷰하고 보완·재리뷰한다. 표적 pytest/compile, 선택 릴리스 검증 및 `git diff --check`를 통과시키기 전 장후 경로를 바꾸지 않는다. 계획의 구현 상태와 검증 결과는 아래 구현 절 및 별도 근거 문서가 소유한다. 릴리스 전환·정책 재발행은 10/2 수용 항목이다.

성능 비교는 동일 source/parent/prompt hash·표본·후보 상한에서 각 3회 별도 프로세스의 중앙 wall/CPU **구 버전×1.20 이하**, peak RSS **구 버전×1.10+64MiB 이하**, 원래의 절대 메모리/시간/비용 가드 이내를 구현 전 합격선으로 고정한다. provider 대기시간과 순수 재생 시간을 분리하고, cache hit/miss·실호출·비용·후보당 판정 변경 수를 측정한다. 44행과 결정적인 결손/중복 fixture, 수백 행의 결정적 부하 표본으로 자원 확장성을 검증하되 합성 반복 행은 경제성 지원 수에 넣지 않는다. 실원천 전체 비교는 충분한 신규 자료가 있을 때 같은 입력으로 한 번씩 시행한다. 명령·코드·원천/split/부모 hash와 지표를 별도 evidence로 보존한다. 기존 진단의 73.9ms를 새 경제성 로직의 검증 완료나 수익 개선으로 표기하지 않는다.

경제 성능은 부모 대비 기회별 동일 가중 paired EV, 정상 PASS·VETO 보존, 위험 PASS 차단, 놓친 수익 VETO 회복, 선택/제외 coverage 및 최악 손실을 함께 본다. 0에 가까운 손익과 단위 오차를 구분하고 인위적인 손익 epsilon을 결과를 본 뒤 정하지 않는다. provider 추론비용과 현재 owner의 검증된 비용 스트레스 조건도 반영한다. 종목·시간대에 성과가 집중되면 그 사실과 지원 수를 공개하며 작은 5/3 표본 통과를 통계적 우월성이나 다음 날 순이익 보장으로 표현하지 않는다. 표본의 실제 수익 개선이 없으면 정책 carry가 올바른 결과다.

## 참조

- [Main 정책 원칙](../plan-korStockScanPerformanceOptimization.rebase.md)
- [9/30 보조판정 평가](../../data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-30.json)
- [9/30 후행 라벨](../../data/report/ai_decision_outcome_labels/ai_decision_outcome_labels_2026-09-30.json)
- [보조판정 장후 생산자](../../src/engine/scalping/compact_auxiliary_paired_replay.py)
- [보조판정 소프트 정책](../../src/engine/scalping/entry_setup_evidence.py)
- [날짜별 정책 발행기](../../src/engine/scalping/mechanistic_entry_runtime_policy.py)

## 구현·리뷰 상태 (2026-10-01)

- 새 독립 단계는 `train_top1_frozen_paired_net_ev_holdout_gate_v4`다. source date 10/2부터 적용하고 이전 날짜 재생/발행의 v3 의미는 유지한다. 학습 상위 한 후보만 승계 검증하고 차순위 교체를 금지한다. 다른 trial의 후행 통계는 `diagnostic_unselected_no_promotion_authority`로 분리했다.
- 원천 결과를 보기 전 정확 기회와 시간순 경계를 정하고 관측기간이 겹친 기회 전체를 purge한다. 부모 기계/프롬프트/soft 정책은 label 결손 이전의 원천에서 고정한다. 일자/scope별 학습 선택을 별도 봉인 파일에 영속화하여 재시도 중 부모·학습 원천·split 변경은 carry로 끝낸다.
- risk/opportunity 등 최대 2개 변형 목록을 생산·완료·재생에서 공유하고 후보는 parent 외 최대 32개다. 학습 응답을 먼저 모으고 후행 추가 호출은 동결된 한 prompt만 한다. 기존 일일 390회/1 USD 및 max_new/provider guard는 유지한다.
- 검증된 정확일자 broker fee·tax·product catalog와 기록된 마찰비용으로 full-cost 계약을 결속한다. 결손 행은 진단 census에 남기고 유효 full-cost 행의 승계를 막지 않는다. full-cost 입력이 전무하면 독립 후보는 진단만 수행하며 승계하지 않는다. 주 owner 비교의 exact stop·seed·20/20 및 포트폴리오 조건은 그대로다.
- 관측되지 않은 VETO 축은 PASS-only 튜닝에서 부모 값을 유지한다. VETO→PASS 후보는 그 방향의 후행 지원을 요구한다. CAUTION은 checkpoint 미진입 반사실로 표시하고 후속 owner 결속 없이 영구 손실 회피/운영 EV를 주장하지 않는다.
- settlement 뒤 응답 파일을 영속화하여 checkpoint 소실 시 정확 identity/provenance/schema의 응답만 복구한다. 응답 없는 중복 예약은 미완료로 남기며 독립 soft 연구를 전부 중단하지 않는다. M1이 먼저 발행됐으면 M0에서 검증한 A1은 보류하고 M1/A0를 보존한다.
- 9/29 이후 봉인 projection manifest를 누적하고 projection 행을 디스크에 순회 보관한다. policy 완전 일치에 대한 SHA 재사용으로 직렬화 병목을 줄였으며 원천/후보 hash 검증을 생략하지 않는다. 재생 eligible 행/기회 인덱스는 여전히 모집단에 비례하므로 전체 RSS는 자연 장후에서 별도로 확인한다.
- 기존 source-only pre-AI economic recorder와 trace 생산자는 이미 구현된 것을 재사용하고 sizing/trace 회귀로 검증했다. 이번 작업은 관측 plan을 실제 주문이나 과거 결손 복구로 간주하지 않는다.
- [구현·시험 근거](../audits/entry-postclose-remediation-implementation-review-2026-10-01.md)에 최종 수정·회귀·성능 및 원천 한계를 남긴다. 10/2 장중 정책/프롬프트·PID 변경과 실제 자연 성과 수용은 이 구현 완료와 구분한다.
