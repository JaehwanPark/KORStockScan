# 트레일링·제출 지연 정책 생성 구조 상세 보완계획 — 2026-10-10

상태: **P1–P5 코드 구현·반복 리뷰·승인된 운영 장후 재생성·배포와 10/12 준비 완료. 자연 PID 소비·새 경제 성과는 별도 확인 필요.** 대상은 사용자가 지정한 **현재 PASS·정책 해시 연결 → holding-AI 원천 연결 → classifier 순환 조건 제거 → 결손 행 격리·대용량 후보 연결 → 과도한 수용 조건 정리**의 다섯 단계다. [구조 재점검 TG1–TG4/DG1–DG4](../audits/main-trailing-delay-policy-generation-structural-review-2026-10-10.md)를 수정 위치·계약·반례·완료 조건으로 구체화하고, [실제 구현·검증 근거](../audits/main-trailing-delay-structural-implementation-review-2026-10-10.md)로 닫는다.

## 1. 목표와 범위

목표는 **현재 정상 producer로 새 자료를 수집하면 유효 자료가 후보 계산·기존 selector·준비 lookup까지 도달할 수 있게 하는 것**이다. 구현이 끝났다는 이유로 양수 지연이나 변경된 트레일링 값을 반드시 발행하지 않는다. 성과가 없어서 부모/0초를 유지하는 결과와 원천 연결·논리 오류 때문에 계산조차 못 하는 결과를 구분한다.

이 문서는 최초 수량·손절 퇴역·의미적 감시기 개선을 포함하지 않는다. 다른 계획의 완료를 이번 다섯 단계의 선행 조건으로 추가하지 않는다. 현재 entry/holding 정책, 원 deadline, 주문·수량·자금·freshness·수탁·hard/protect/emergency guard와 퇴역 경계를 유지한다. 보조 AI 프롬프트·모델·호출 예산의 튜닝도 포함하지 않는다.

코드 기준은 `main-trailing-delay-residual-20261010-v6` / `78f2c1d784fd5043d5b5bc0fedd7b963f8fe42d4`다. 구현 착수 때 작업트리·선택 릴리스와 원천 세대를 다시 고정한다. 60→240건 재현은 구조적 실패의 기존 근거이며 실제 수익성·새 코드 통과 근거가 아니다.

구현 owner는 기존 `MainAllScopeTrailingReplay`, `PreSubmitDelaySituationImplementation1010`를 재사용한다. [현재 checklist](../checklists/2026-10-10-stage2-todo-checklist.md)의 완료 이력을 보존하고 동일 ID를 이번 구조 결함 범위로 재개했다. P1–P5는 내부 단계이며 별도 backlog ID가 아니다. 원 봉인 10/12 checklist는 스냅샷으로 보존하고, 후속 운영 승인에 따라 native summary의 정식 successor로 인계했다. 최초 코드 수리·격리 시험 종료 후 별도 승인으로 운영 산출물 재생성·정식 발행·배포·PREOPEN 검증을 완료했다. Main은 중지 상태이며 10/12 자연 기동 owner를 유지한다. 기존 승인 이력과 당시 릴리스 증거는 보존한다.

| 순서 | 대상 결함 | 주 변경 위치 | 단계 산출물 |
| --- | --- | --- | --- |
| P1 | DG1/DG2 | entry compose·Main provenance·delay 두 anchor | 원 요청에 결속한 effective PASS·기계/보조 부모가 있는 관측 |
| P2 | TG1 | holding path-vote·quote projection·source assembler·공통 replay | 원 투표/원 정책을 사용하는 causal AI 포함 재생 |
| P3 | TG2 | resident/partitioned 상황 학습·pin/typed schema | 원 pin과 연구 분류가 분리된 frozen classifier·typed 후보 |
| P4 | TG3/DG3 | 적격 모집단·대용량 report·기존 selector | 결손 행을 격리한 전역 cohort와 실제 전달되는 후보 |
| P5 | TG4/DG4 | 일반 악화/손실 악화·horizon 비교·consumer | 과도한 전수 veto/교집합 차단을 제거한 선정 계약과 전체 연결 검증 |

각 단계는 구현→리뷰→보완→영향 검증으로 닫는다. P1·P2는 새로운 정상 자료가 계속 결손으로 저장되는 문제를 먼저 해결한다. P3·P4·P5는 그 자료가 쌓여도 계산·선정을 막는 조건을 제거한다. 완료 여부는 아래 시험표로 판정한다.

### 1.1 이번 재리뷰에서 보완한 계획 결함

| 항목 | 재확인한 문제 | 수정 계약·종료 검사 |
| --- | --- | --- |
| R1 | coverage 최대 그룹을 먼저 고르면 30초 241건/180초 240건에서 180초는 성과와 관계없이 비교에서 탈락 | P5를 후보별 동일 기회 P0–Pd 비교로 교체. 한 건 많은 짧은 후보가 긴 후보의 연구 진입을 독점하지 않음 |
| R2 | trailing의 `common_ids`도 모든 후보의 비검열 교집합. 미지원 후보 하나가 정상 후보를 전부 제거 | P4에서 후보–부모별 적격 ID를 보존. 전역 split은 공유하고 후보 추가가 기존 정상 pair를 지우지 않음 |
| R3 | 최근 48개라는 설명은 legacy vote 기준. 현재 path-vote는 반환 192개/파일 append 방식이며 16MiB 초과 reader는 실패 | P2에서 실제 보관·크기 한도·원문 참조·부분 쓰기/재개·coverage 증명을 명시 |
| R4 | `path_decision_input_sha256`는 중복 투표 억제용으로 모델이 본 일부 시각/age와 requested-path 집합을 제외 | P2의 원 AI 재사용에 실제 전체 요청 projection 검증 추가. 같은 dedup hash를 AI 입력 동등성 증거로 단독 사용하지 않음 |
| R5 | 새 필드를 producer에 추가해도 축약 JSON/feature spool/cache/독립 verifier에서 버릴 수 있음 | P1–P4 전달 표와 cold/warm/증분·구/신 reader 회귀를 같은 변경 단위로 고정 |
| R6 | 현재 손실 악화 guard까지 제거됐다는 오해, 부모/0초 유지와 구조 결함의 구별 부족 | P5에서 보존할 predicate·표본/경제 조건을 명시하고 §8에서 자료 증가의 효과를 조건별로 구별 |

R1의 산술 반례는 30초 평균 개선 +10bp(241건), 180초 +40bp(240건)에서도 구 계획이 30초만 비교한다는 것이다. [계획 산술 점검](../../tmp/trailing-delay-generability-20261010/plan-rereview-arithmetic.json)은 선정 절차의 반례이며 실제 수익·새 코드 구현 검증이 아니다. R2의 실제 수정 위치는 §5.2에 명시한다.

## 2. P1 — 현재 PASS와 정책 해시를 두 anchor에 연결

### 2.1 변경 위치와 실제 흐름

[continuous-reversal compose](../../src/engine/scalping/continuous_reversal_policy.py)와 [AI caller](../../src/engine/ai_engine_openai.py) → [Main provenance/제출 직전 기록](../../src/engine/sniper_state_handlers.py)의 `_machine_primary_entry_provenance_fields` 및 0초/양수 `price_ready` commit → [signal-ready adapter](../../src/engine/scalping/pre_submit_delay_observation.py)의 `register_pass_result` → [초기 정책](../../src/engine/scalping/pre_submit_delay_initial_policy.py) / [분할 계산](../../src/engine/automation/pre_submit_delay_partitioned_research.py) → `PreparedPolicy.lookup`을 한 계약으로 맞춘다.

### 2.2 보조정책 identity와 PASS 정규화

1. **보조정책의 원천을 요청 작성 시점에 고정한다.** [auxiliary registry](../../src/engine/scalping/reversal_auxiliary_registry.py)의 definition과 [intraday overlay](../../src/engine/scalping/reversal_auxiliary_intraday.py)의 `selected_definition`/`at_confirmation`을 대조한다. overlay가 없는 base 경로·등록된 v4 호환 경로도 실제 사용한 prompt/입력 projector/validator/response schema/model/요청 옵션의 원 정의를 식별해야 한다. 새 결과가 도착한 시점의 최신 overlay로 원 요청을 재결속하지 않는다.
2. **의미 identity와 artifact identity를 구분한다.** 제안 계약 `entry_auxiliary_policy_identity_v1`은 실제 모델 판단에 영향을 주는 위 정의와 정규화 규칙의 hash다. 관측 시각·종목·request ID·입력 가격·보고일·파일 경로·연구 설명 문구는 정책 의미 hash에 넣지 않는다. 원 registry SHA·overlay SHA·bundle SHA·원 request/response SHA는 별도 provenance로 보존한다. 의미가 같은 날짜별 발행은 학습 셀을 쪼개지 않고 실제 prompt/model/schema 의미 변경은 분리한다. 새 필드 이름/스키마는 구현 제안이며 현재 설치된 계약으로 표시하지 않는다.
3. 해당 identity를 기존 소비 필드 `entry_ai_soft_policy_sha256`에 연결하되 schema version을 동반한다. 기계 부모 `entry_mechanistic_policy_sha256`는 실제 assessment가 소비한 값을 유지한다. 외형이 64자리라는 사실만으로 유효 부모로 인정하지 않는다. 원 definition·요청 영수증에서 재계산·검증할 수 있어야 한다.
4. **유효 PASS는 현재 compose의 최종 판단에서 산출한다.** machine `ENTER_NOW`, 검증 오류 없음, 현행 screen PASS가 모두 성립한 경우에만 `entry_ai_effective_assessment.effective_verdict=PASS`를 제공한다. raw `risk_verdict=PASS`만 있고 claim/정책/응답이 무효인 경우 PASS로 정규화하지 않는다. 현재 normalizer와 겹치는 곳은 공통 함수로 정리해 두 의미가 생기지 않게 한다.
5. Main provenance와 비동기 완료 객체가 원 request/native attempt·원 completed/deadline·원 해시를 보존하도록 한다. `signal_ready`는 원 완료 시각, `price_ready`는 실제 가격·수량 계산 완료 시각을 계속 사용한다. 두 anchor를 한 기회로 결속하되 서로의 P0·후행 가격을 섞지 않는다.
6. 0초 경로에서도 같은 원천을 기록한다. 양수 정책이 먼저 존재해야 관측이 시작되는 구조를 만들지 않는다. 부모 해시 결손은 해당 행의 연구 자격 결손이며 새로운 실주문 차단 규칙이나 원 PASS TTL 연장을 만들지 않는다. due 재평가와 새 successor의 기존 guard는 유지한다.

구 부모 hash와 새 의미 identity가 혼재하는 이행기간에는 버전을 명시해 읽는다. 과거 정상 부모를 새 identity로 연결하려면 당시 원 정의의 일대일 의미 동등성을 검증한 migration receipt가 필요하다. 증명되지 않은 alias·`legacy` wildcard는 허용하지 않는다. 구 정책/구 lookup과 새 정책/새 lookup을 같은 전환 세트로 검증하고 불일치를 조용히 호환 처리하지 않는다. identity 도입 자체가 새 AI 판정·프롬프트·기계정책 채택을 뜻하지 않는다.

**필드 전달은 끝까지 닫는다.** effective PASS·identity version·원 definition 참조·원 request/response 참조를 compose/완료 객체에만 추가하지 않는다. Main commit → observer → projection → resident/분할 셀 키 → policy/committed → `PreparedPolicy.lookup`의 reader와 검증 함수를 함께 바꾼다. 구 schema를 읽으면 구 계약을 적용하고, 새 schema의 필수 identity가 누락되면 그 행/세대의 source gap으로 드러낸다. 신필드를 버린 뒤 구 부모나 현재 overlay로 조용히 채우지 않는다. 의미 identity 계산은 검증된 definition별로 재사용하고 이벤트별 원 request 결속은 각각 남긴다.

### 2.3 과거 자료와 종료 조건

- 과거 행은 원 request/response·당시 bundle/registry·native ID로 유일하게 확인되는 경우만 별도 source-bound projection에 복원한다. 원 JSONL은 수정하지 않는다. 현재 해시를 과거 `legacy` 행에 대입하거나 machine 해시를 AI 해시로 복사하지 않는다.
- 원 정의가 없는 행은 그대로 진단에 보존하고 P4에서 적격 cohort와 분리한다. 새 원천이 정상화되면 앞으로의 동일 부모 자료가 계산을 시작할 수 있어야 한다.
- **종료:** 실제 compose→Main 저장→두 anchor→정규화→단일/분할 계산→lookup을 거친 정상 자료가 양수 후보를 만들 수 있고, 오류 응답·만료·부모 교체 반례는 기존 의미대로 제외/거부된다. 내부 정상화를 mock해서 양수 결과를 만든 시험으로 대체하지 않는다. provider/broker 경계만 동결 응답으로 격리한다.

## 3. P2 — holding-AI의 실제 원천과 재생 계약 연결

### 3.1 실제 runtime에 맞춰 바로잡을 부분

현 runtime의 [_collect_holding_path_votes / _holding_path_signal_decision / _holding_path_exit_proceeds](../../src/engine/sniper_state_handlers.py)는 **신호 전에 수집·영속된 경로별 투표**를 사용한다. [path_signal_snapshot](../../src/engine/ai/holding_exit_vote.py)은 `requested_at <= received_at <= persisted_at < signal_at`인 투표로 시퀀스를 만들고, [공통 유예 판단](../../src/engine/scalping/trailing_exit_decision.py)은 성숙한 VETO만 유예한다. `INSUFFICIENT`는 runtime에서 VETO가 아니다.

따라서 [현재 공통 재생](../../src/engine/scalping/universal_trailing_replay.py)의 “후보 crossing 이후 알려진 원 PASS/VETO receipt 필수” 가정을 실제 pre-signal 투표 모델로 교체한다. `operating_ai_required=False`로 일괄 우회하거나 holding-AI를 추가 호출하는 방식으로 해결하지 않는다.

### 3.2 수집·결합 계약

1. 기존 `holding_path_votes` 원장·`holding_path_signal_snapshot`·`holding_path_exit_veto_deferred`/resolution·quote transition·실제 position/buy generation의 참조를 결합한다. 제안된 replay용 투표 요약은 원 ledger 경로/offset/byte SHA·정책 정의·원 입력/응답 SHA를 가리킨다. 전체 prompt/response를 매 quote에 복제하지 않는다.
2. position·buy-fill identity·path=`EXIT_TRAILING_TP`·시장·session·route/transport epoch·정책/model/prompt·원 request/received/persisted 시계를 검증한다. ADD 이후 buy generation, restart, 익일·세션 전환은 별도 결속한다. 현재 path-vote의 `append_path_events_file`은 파일에 append하고 반환 목록은 `PATH_MAX_EVENTS=192`로 제한한다. `load_path_events_file`은 전체 파일을 읽고 `PATH_MAX_STORE_BYTES=16MiB` 초과 시 실패한다. legacy의 `MAX_VOTES=48`과 구분하며 반환 목록을 전체 과거 coverage로 간주하지 않는다. 재생은 봉인된 해당 창의 원 event를 bounded stream으로 읽는다.
3. 원 holding 정책의 요구 여부·해시를 명시적으로 기록한다. 누락 필드의 기본 True를 모든 과거 거래에 씌운 뒤 없는 응답을 요구하지 않는다. 그렇다고 누락을 False로 바꾸지도 않는다. 당시 적용 모드/정책이 확인되지 않으면 기계 재생과 AI 포함 재생의 지원 여부를 나눠 해당 후자를 미확정으로 둔다.
4. collection coverage·알려진 gap·실제 provider 실패/INSUFFICIENT도 기록한다. **충분히 관측된 빈/미성숙 투표와 원장 유실을 구분한다.** 해당 position/세션의 수집 시작·마지막 확정 event/offset·요청 없음/기존 cadence skip·저장 실패·재기동/절단 경계를 source receipt로 입증한다. 기존 수집기의 상태 전환에 기록하고 매 tick heartbeat 원장을 추가하지 않는다. 정상적으로 입증된 빈 창은 실제 runtime의 INSUFFICIENT→기존 청산 진행을 재현할 수 있다. ledger 파일이 없거나 비었다는 사실만으로 빈 창을 인증하지 않는다. coverage 불명은 AI 포함 재생에서 검열한다.
5. source assembler의 실제 completed/CF adapter, 최소 JSON field whitelist, 분할 입력/tree와 독립 verifier까지 필드를 전달한다. 실제 비용·terminal을 갖춘 완료 거래와 CF 모델 결과의 evidence kind는 유지한다. 상세 원장은 한 번 저장하고 후속 후보는 참조를 공유한다.

원 AI 입력은 hash만 보관해서는 후보 입력과의 동등성을 재구성할 수 없다. 이미 보존한 요청 원문에 불변 참조를 연결하고, 원문이 없는 신규 요청은 모델이 실제 본 최소 payload projection을 기존 evidence writer에 한 번 저장한다. 원 request/prompt/schema와 projection의 대응을 검증한다. 동일 내용을 별도 비교 원장으로 반복 복제하지 않는다. 과거에 hash만 남고 원 내용이나 재구성 가능한 원천이 없으면 해당 AI 포함 후보는 미확정으로 남긴다.

이 최소 projection은 **모델에 보내기 전 후보 payload가 아니라 실제 `ai_engine_openai.evaluate_scalping_holding_path_votes`가 보낸 요청**에 결속한다. 원 system prompt·전체 user payload·requested paths·응답 schema·model/옵션의 재구성 가능한 내용과 원 byte hash를 보존한다. `source`/age처럼 모델에 전달된 필드를 dedup 규칙에 따라 지운 projection은 완전 입력 증거가 아니다. token/인증정보는 요청 evidence에 포함하지 않는다.

새 원문은 16MiB vote 파일의 각 path event에 중복 삽입하지 않고 공유 evidence의 불변 참조로 연결한다. 해당 파일의 한도 도달도 수집 중단으로 방치하지 않도록 기존 저장 패키지의 봉인 segment/index를 활용하는 bounded 승계를 구현한다. active vote window·중복 claim·원 persisted 시각은 유지하고, archive 참조 검증이 끝나기 전에 원 파일을 절단하지 않는다. 과거 archive를 매 live 요청에서 전수 읽지 않는다. 요청 원문/투표를 별도 저장하는 경우 durable source → 참조 publish 순서와 원 request ID 기반 중복 방지·crash 재개를 검증한다. 저장 실패는 coverage gap으로 드러내며 새 청산 차단·AI 재호출을 만들지 않는다. 장후 읽기 cutoff 뒤 append는 다음 source 세대이고, cutoff 이전 hash/offset은 불변이어야 한다.

### 3.3 후보마다 원 AI를 재사용할 수 있는 범위

- 후보의 첫 crossing 시각 `t`에서, `t` 전에 영속된 원 투표만 `path_signal_snapshot(..., signal_at=t)`에 넣는다. 원 신호보다 이르거나 늦은 후보라도 그 시각에 사용 가능한 투표창을 공통 함수로 재구성한다. 미래 응답을 당겨 쓰지 않는다.
- 원 투표를 재사용할 때는 **투표 요청 당시** 후보의 position 상태·AI 입력을 원 요청 builder로 재구성한다. `path_vote_input_hashes`의 dedup hash는 일부 시각/age와 requested-path 집합을 제외하므로 단독 동등성 검사가 아니다. 실제 전체 payload와 prompt/schema/model/옵션의 canonical projection이 원 요청과 같은지 검증하고 원 byte hash와 함께 결속한다. 원 source clock은 그 요청 때의 값을 보존하며 후보 crossing 시각으로 바꾸지 않는다. 후보 숫자·연구 classifier의 감사용 ID가 원 모델 입력에 없으면 ID 차이만으로 거절하지 않는다. 모델이 본 입력이 달라지거나 원 입력을 재구성할 수 없으면 해당 AI 포함 pair는 미확정이다.
- 현재 `holding_ai_context_digest`가 quote·numeric·상황 pin을 하나로 묶어 원 AI 응답 자체의 identity처럼 쓰는 부분을 분리한다. 원 request/response의 identity와 후보 실행 context의 identity를 각각 보존하고 검증 가능한 관계를 report에 남긴다.
- 후보가 원 관측으로 지원되는 position 기간을 벗어나거나 AI 입력을 바꾸면 기계 재생은 모델 결과로 남기고 AI 포함 결과는 `candidate_holding_ai_input_unobserved` 등 현행 결손 사유로 분리한다. 해당 후보/행을 제외하고 다른 적격 후보를 진행한다. 새로운 AI 호출·프롬프트 연구는 이 다섯 단계의 기본 실행 조건이 아니다.
- 실제 AI 요청의 cadence·투표 window·VETO 유예·최대 악화 해제·시장/수탁/hard safety를 재생에서도 유지한다. 알려진 AI 저장 실패 때문에 runtime이 기존 청산을 진행한 경우도 원 사건이 입증될 때만 재현한다. 로그가 없다는 이유로 저장 실패를 가정하지 않는다.

**종료:** 실제 원 ledger와 quote adapter에서 나온 AI-required 정상 거래가 후보 재생에 도달한다. PASS/VETO/INSUFFICIENT·원장 결손·늦은 영속·ADD/시장 전환·유예 해제 반례가 runtime과 같다. AI 없는 기계 모델 결과를 AI 포함 경제 후보로 승격하지 않는다.

## 4. P3 — classifier 학습 세대와 과거 pin의 순환 제거

대상은 [resident 상황 연구](../../src/engine/scalping/trailing_situation_policy.py)의 `research_registered_grid`, [분할 상황 집계](../../src/engine/automation/main_trailing_situation_aggregation.py), 공통 재생 context와 typed selector/loader다.

1. **세 identity를 분리한다.** `original_pin`은 실제 당시 classifier·feature·entry/as-of를 가진 불변 증거다. 제안 `classifier_semantic_sha256`는 schema/feature/window/threshold/분류 우선순위의 의미다. `classifier_generation_sha256`는 의미 hash에 train ID/split/source/code와 실제 `trained_through`를 결속한 학습 세대다. 구 `classifier_sha256`는 구 reader의 역사적 의미를 보존한다.
2. train의 원 entry feature를 등록된 hypothesis로 재분류하되 `research_assignment`로 저장한다. **연구 재분류를 실제 원 진입 때 사용한 pin이라고 주장하지 않는다.** `original_pin.classifier_sha256 == new_frozen_sha`를 train/holdout 적격 요건에서 제거한다. 원 pin의 무결성·원 feature known-at 검사는 계속 수행한다.
3. 기존 전역 시간순 split과 train-only hypothesis/숫자 후보 선택을 유지한다. train의 결과 관측 종료까지 포함한 학습 cutoff를 고정하고, holdout entry가 그 cutoff 뒤에 있는지 검증한다. 겹치는 긴 보유 행은 purge하거나 해당 split에서 제외하며 holdout 수익을 보고 경계를 이동하지 않는다.
4. holdout에는 frozen hypothesis와 숫자 후보를 그대로 적용한다. 호환성은 원 AI에 실제 입력한 내용과 P2의 재구성 결과로 판단한다. 새 classifier가 과거에 설치됐어야 한다는 조건을 새 이름으로 다시 만들지 않는다. 연구 라벨만 달라지고 AI 입력은 같으면 원 pre-signal 투표를 사용할 수 있다.
5. 새 typed bundle은 선택된 generation을 보존한다. 적용 후 **새 진입**은 새 classifier로 pin하고 기존 보유의 pin은 그대로 둔다. 기존 pin이 새 bundle의 의미와 호환되지 않으면 기존 계약의 검증된 시장 부모로 처리한다. `PreparedPin`·lookup·restart/ADD 승계·정책 교체까지 같은 규칙을 적용한다.
6. replay/report/cache/schema를 함께 versioning한다. 기존 봉인 산출물을 새 의미로 재해석하지 않는다. hypothesis 결과 cache는 feature/의미 hash로 재사용할 수 있지만 split·train cutoff·선정·발행 증거는 새로운 generation으로 결속한다.

split은 P4의 원천 적격 전역 모집단에서 한 번 정하고 후보/hypothesis별로 다시 70/30 분할하지 않는다. 경계 이후에야 결과를 알 수 있는 train 행을 purge한 뒤 남은 train의 관측 종료를 `trained_through`로 고정한다. trailing은 기존 evidence-kind 전역 split을 시장/상황 cell이 상속한다. 다른 증거 kind의 cutoff로 실제 완료 거래를 인증하지 않는다. candidate별 AI 지원 여부는 P4의 pair mask로 교차 적용한다. 긴 보유 한 건 때문에 cutoff를 계속 미래로 밀거나 holdout까지 학습 세대 hash의 train source로 포함하지 않는다.

**종료:** causal original pin을 보존한 AI-required 60/240건에서 P2로 증빙이 연결되면 typed 후보 검토에 도달한다. 신규 학습이 과거 pin 수정 없이 가능해야 하며, 미래 feature·holdout 재선정·잘못된 old/new schema는 거절된다. 통과 시험에 `operating_ai_required=False`를 사용하지 않는다.

## 5. P4 — 결손 행 격리와 대용량 후보의 실제 전달

### 5.1 모집단 격리

1. 원천/부모/native/quote/비용/AI의 자격 검사를 필요한 평가 층별로 수행한다. raw census는 원 행·중복 alias·충돌·제외·적격 ID의 보존식을 가진다. source 부족을 손익 0·승패·무기회로 바꾸지 않는다.
2. 지연은 정상 부모/native/P0를 가진 행만 해당 anchor의 학습 모집단에 넣는다. 미검증 native 1건 때문에 같은 부모의 전체 셀을 0초로 덮는 `any(native=0)` 분기를 제거한다. 부모를 모르는 행은 `legacy` 진단에 남기며 정상 부모 셀에 합치지 않는다. 특정 horizon 결손은 P5의 해당 비교 범위에서만 다룬다.
3. trailing은 실제 비용·terminal·quote·AI가 지원되는 완료 거래를 경제 cohort로 만든다. 누적창의 snapshot missing/source-gap/unverified 1/5/1을 전체 정상 cohort의 incomplete로 단순 전달하지 않는다. 누락 파일의 날짜·범위와 영향을 식별·격리할 수 있으면 그 범위를 제외하고 정상 날짜를 평가한다. 손실 범위조차 식별할 수 없는 global manifest/census 손상은 계속 전역 차단한다.
4. `raw_census_complete`와 `eligible_evaluation_complete`의 의미를 분리한다. 전체 미복구 자료가 있음을 공개하면서도 격리된 적격 모집단은 완전하게 평가할 수 있어야 한다. 단순히 기존 `complete`를 True로 고치는 방식은 금지한다. 제외 ID/count/source hash와 격리 검증 영수증을 consumer가 확인한다.
5. 격리 후 지연은 동일 parent/anchor/market, trailing은 기존 evidence-kind 전역 순서를 확정하고 shared split/purge를 계산한다. 상황 cell은 부모 split을 상속한다. shard 경계나 읽는 순서가 제외/학습/검증 결과를 바꾸지 않아야 한다. 뒤늦은 ID 충돌은 해당 ID의 이전 결과도 무효화한다.

### 5.2 후보 하나의 결손이 다른 후보를 제거하는 교집합 제거

[공통 replay](../../src/engine/scalping/universal_trailing_replay.py)의 `common_ids`, [전수 연구의 비용 정정](../../src/engine/automation/main_trailing_all_scope_research.py)의 `_cost_revision_result`, [분할 모집단 집계](../../src/engine/automation/main_trailing_population_aggregation.py)는 현재 **모든 후보 결과가 non-null인 행만** 공통 모집단으로 삼는다. P2에서 후보 B의 AI 입력을 재구성하지 못하면 후보 A와 부모가 모두 정상인 240건도 제거될 수 있다. 행 격리만 고쳐서는 해결되지 않으므로 이 교집합도 같은 범위에서 수정한다.

1. 후보와 독립인 source/native/position/cost/clock 자격을 먼저 확정하고, 공통 전역 train/holdout/purge를 그 모집단에 한 번 부여한다. 후보를 추가했다고 기존 행의 split이 달라지지 않아야 한다.
2. 각 후보 `c`에 대해 `pair_eligible(c) = 기본 적격 ID ∩ 부모 재생 지원 ID ∩ 후보 c 재생 지원 ID`를 계산한다. 실제 완료/CF 등 증거 종류를 분리하고, 각 pair의 양쪽은 같은 거래·원가·가격 원천을 사용한다. 후보 B 결손을 A의 pair mask에 전파하지 않는다. 모든 후보 교집합은 필요하면 진단용으로 남기며 필수 수용 분모가 아니다.
3. 기존 train 점수식·표본/경제 조건을 해당 후보의 pair에 적용해 시장·scope·hypothesis·숫자 후보를 train에서 고정한다. 이후 그 후보의 holdout pair로만 검증한다. 다른 후보를 holdout으로 다시 고르지 않는다. 서로 다른 support에서 계산한 점수는 탐색 순위이며 동일 전체 모집단에서의 후보 간 우월성을 증명한다고 표시하지 않는다. 후보별 적격/결손/일수/종목·원 ID 참조와 공통 교차 진단을 공개한다.
4. 제외는 source/causal/AI 재현 지원 여부에 의해서만 정한다. 손익이 불리하다는 이유로 pair를 빼거나 미관측을 0으로 넣지 않는다. 실제 손실 악화·stress 검사는 선정된 pair 전체에 적용한다. 표본 gate의 `n`/일수도 그 pair에서 재계산해 다른 후보의 수를 빌리지 않는다.
5. resident·partitioned·typed 연구·market bridge·cost-only 정정·cache 재개·독립 verifier·selector의 ID/count/digest를 함께 바꾼다. 구 `common_ids_ref`에 새 분모를 넣고 같은 schema라고 주장하지 않는다. 새 contract version은 후보별 ID 참조와 공유 split 참조를 가지며 구 reader는 구 계약을 유지한다.

**반례:** 부모/A가 240건 정상이고 B만 240건 검열되면 A–부모 240건은 계속 평가한다. A 자체의 AI/원가 결손은 A pair에서 제외하고, 원가 공통 세대가 무효이면 해당 거래의 모든 actual pair를 제외한다. 후보 순서·shard 수·새 무지원 후보 추가가 기존 A pair·split·metric을 바꾸지 않아야 한다.

### 5.3 대용량 bridge

[source assembler](../../src/engine/automation/main_trailing_source_assembler.py)·[전수 연구](../../src/engine/automation/main_trailing_all_scope_research.py)·[holding report](../../src/engine/holding_exit_observation_report.py)의 `_partitioned_holding_report` → [mechanical apply](../../src/engine/automation/scalp_trailing_mechanical_policy_apply.py) → [정책 validator](../../src/engine/scalping/trailing_mechanical_policy.py)를 연결한다.

- `research_candidate=None` 고정 반환을 제거하고 분할 결과의 적격 actual 후보·숫자 vector·부모·M1/classifier·train/holdout·비용/source 세대·slippage/손실 지표를 기존 selector의 검증 가능한 view로 전달한다. 큰 ID 집합은 봉인 tree 참조로 유지한다.
- 시장 공통 후보와 상황 후보의 scope를 후보 등록 때 고정한다. 같은 stage에서 각각 독립 apply하지 않는다. train에서 선택한 시장·후보 scope/숫자를 고정하고 기존 one-market canary/rollback으로 한 번만 적용한다. typed holdout 실패 뒤 시장 공통 후보로 갈아타는 재선정은 금지한다.
- source byte verifier·구 report reader·reference report reader를 같이 보완한다. referenced ID/count/digest가 정확해야 하며 검증을 mock한 selector 단위시험만으로 연결 완료를 선언하지 않는다.
- 유효 후보 없음은 `hold_sample`/`hold_no_edge` 계열의 현행 상태, 실제 source 문제는 `hold_source_gap`으로 전달한다. 자료가 정상인데 연결 코드가 빠진 상태를 표본 부족으로 숨기지 않는다.

`population_complete`를 단순히 True로 바꾸는 수리는 허용하지 않는다. 새 report에서 전체 원천 census의 상태와 선정된 후보 pair의 평가 완료를 분리하고, selector는 새 schema의 제외 receipt·pair ID·공유 split·metric을 검증한다. 구 report의 `population_complete` 의미는 그대로 둔다.

**종료:** 결손 1건 + 정상 60/240건에서 결손은 census에 남고 정상 cohort는 연구/selector까지 도달한다. 단일·대용량·중단 재개 결과의 논리 ID/split/후보가 같다. global 손상은 그대로 차단된다. 실제 EOD 원장을 다시 생성하거나 주문을 만들어 이 시험을 통과시키지 않는다.

## 6. P5 — 과도한 수용 조건과 horizon 교집합 정리

### 6.1 일반 악화와 기존 손실 악화 guard 구분

현재 분할 상황 집계의 `worsened_ids_ref.count == 0`과 `_type_view`의 `sealed_adverse_population` 대입을 수정한다. **일반 악화 0건을 요구하는 조건만 제거**하고 기존 selector의 손실 제한을 정확하게 계산한다.

- 일반 악화: 동일 비교 기준에서 `paired_delta < 0`. 건수·금액·ID는 진단으로 유지한다.
- 기존 손실 악화: [기존 mechanical replay의 `_metric`](../../src/engine/scalping/trailing_mechanical_replay.py)이 사용하는 `paired_delta_pnl_krw < 0 AND modeled_or_observed_pnl_krw < 0`. 이 집합만 실제 ID/tree로 `large_loss_worsened_ids`에 연결한다. 현재 명칭이 large loss라고 해서 임의의 새 손실률 기준을 도입하지 않는다.
- 실제 완료 cohort·원가·paired 비교 기준·최소 유효일/train/holdout·독립 검증·slippage와 일별 stress·one-market/rollback 조건은 유지한다. 그 조건의 결과는 항목별로 보고하여 전체 “후보 없음” 하나로 숨기지 않는다. 이번 수정에서 새로운 최소 우월성·종목별 최소 표본·모든 거래 승리 조건을 추가하지 않는다.
- **정상 반례:** 부모 이익 10원→후보 이익 9원인 일반 악화 1건과 충분한 개선 거래를 함께 넣는다. 전체 기존 경제·stress 조건을 통과하면 그 1건 때문에 자동 탈락하지 않아야 한다.
- **보호 반례:** 부모 0원→후보 -1원은 현재 손실 악화 predicate에 해당하므로 계속 제한한다. 앞선 감사의 -1원 예시는 “악화 0건” 조건이 표본 증가로 없어지지 않는다는 증거이며, 그 거래를 반드시 수용해야 한다는 근거로 사용하지 않는다.

### 6.2 희소 horizon 하나가 전체 비교를 소거하지 않게 함

resident `_selection`과 분할 `_select`의 후보 전체 교집합을 **후보별 동일 기회 P0–Pd pair**로 대체한다. 앞선 계획의 “공통 train 수 최대 그룹 우선”은 폐기한다. 한 horizon의 coverage가 한 건 더 많다는 이유로 다른 horizon이 계속 탈락하기 때문이다. 0/30/60/120/180초 grid와 기존 가격 개선 계산·짧은 지연 동률 우선은 그대로다.

1. P4의 부모/anchor/market별 전역 split을 고정한 뒤, 각 `d`에 대해 동일 기회의 유효 P0와 Pd가 있는 train pair `T_d`를 만든다. 원 route·epoch·freshness·관측시각 계약을 유지하며 다른 horizon의 존재 여부는 `T_d` 자격에 넣지 않는다. 하나의 기회/지연에는 중복 alias를 제거한 한 표본만 허용한다.
2. 각 후보의 `mean_d = sum(기존 가격 개선 bp) / |T_d|`를 구하고 `|T_d| > 0`인 후보 중 평균 최대·동률 짧은 지연으로 train 승자를 정한다. 후보별 n/coverage·분위/부호·ID와 day/symbol support를 함께 기록한다. coverage는 진단이며 최대 coverage 그룹·추가 임의 표본율·새 최소 n으로 후보를 먼저 버리지 않는다. 4개 후보가 모두 같은 행을 지원하면 기존 평균 비교와 같은 결과여야 한다.
3. 승자를 고정한 후 그 지연의 validation pair만 기존 독립 검증에 사용한다. 기존 계약대로 train/validation 평균이 모두 양수이면 양수 초기 후보이며, 양수가 아니거나 validation이 없으면 기존 0초/부모/unsupported 처리를 구분한다. holdout이 없는 180초를 승자로 고른 뒤 holdout을 보고 30초를 대신 채택하지 않는다.
4. 서로 다른 `T_d`의 평균은 **각 후보가 관측된 기회에서 P0보다 개선됐는지의 탐색 점수**다. 후보 간 모든 기회에서의 우월성 증거라고 과장하지 않는다. 공통 교차 ID 비교는 진단으로 남기고, 결손은 null과 이유로 보존한다. 검증을 통과해도 기존 `estimated_provisional` 의미를 유지한다. 실제 fill·청산·EV를 지연 가격 연구의 새로운 필수 gate로 추가하지 않는다.
5. 30초 train 6 / validation 4에 180초만 있는 train 1건이 추가돼도 30초 `T_30`의 6건과 metric은 그대로다. 다만 그 신규 후보가 train에서 실제로 우세하면 선택은 달라질 수 있고 holdout 실패 시 재선정하지 않는다. “기존 자료가 사라지지 않음”을 “기존 정책이 반드시 계속 채택됨”으로 혼동하지 않는다.
6. 30초 241건 +10bp, 180초 240건 +40bp의 반례에서 180초가 연구 순위에서 사라지지 않아야 한다. 고정 split의 train에 30초만 지원하는 행을 추가해도 180초 pair/metric은 불변이다. 새 날짜/source 세대에서 정식 전역 split을 다시 계산해 표본이 이동한 경우는 이 불변 시험과 구별한다. 모든 horizon 완비·동률·전부 음수·정상 부모별 분리·holdout 결손과 성과 악화도 검증한다. 단일/분할 구현의 합산·정렬·tie-break가 같아야 한다.

기존 정책 v2의 역사적 selection/validator 의미는 고정하고 새 알고리즘 계약 버전을 report/policy/committed reader에 함께 기록한다. 구 세대의 선정 규칙을 새 함수로 재검증해 과거 준비를 무효화하지 않는다. 새 generation의 publisher·validator·prepared lookup은 같은 규칙을 사용해야 한다.

## 7. 필수 통합 시험과 마지막 소비 확인

| 시험 | 반드시 확인할 결과 |
| --- | --- |
| 원 compose의 PASS·오류·만료·base/overlay·fixed/scanner 경로 | 정상 원 보조 identity만 두 anchor에 도달. raw PASS·미래 overlay로 승격 0 |
| 같은 의미/다른 발행일, 다른 의미/같은 발행일 | 전자는 같은 학습 부모, 후자는 다른 부모. 원 request/response bytes는 별도 결속 |
| 정상 path-vote ledger·quote·원 비용·완료 adapter | AI-required 재생이 모델 결과를 생성. internal adapter나 verifier를 mock하지 않음 |
| PASS/VETO/관측된 INSUFFICIENT/원장 결손 | 실제 runtime 유예 의미와 동일, 미관측을 PASS·실현 0으로 합성하지 않음 |
| 원 투표 뒤 후보 crossing 이동·늦은 응답·ADD·세션 전환 | 후보시점까지 사용 가능한 동일 입력만 재사용, 원 position/정책 혼합 없음 |
| dedup hash 같음/전체 AI 입력 다름, 요청 원문만 저장 후 crash | 원 AI 재사용 거절 또는 원 request 기반 재개. dangling 참조를 정상 투표로 인증하지 않음 |
| 192개 초과/16MiB 경계·봉인 segment·저장 실패·restart | active vote 의미/기존 청산 동작 보존, 연구 coverage를 입증하고 유실 창만 격리 |
| 10일/60건→40일/240건, 기존 pin 유지 | healthy AI-required cohort가 새 classifier/typed 후보에 도달. future hash 요구 없음 |
| 결손 1건과 정상 증가·다른 부모·global 손상 | 국소 결손만 격리, 정상 cohort 평가, 전역 손상은 차단 |
| 정상 부모/A 240건 + 전부 미지원 B | A pair/split/metric 불변, B만 검열. B의 비용 정정·재개가 A 원천에 영향 없으면 A를 지우지 않음 |
| 대용량·여러 shard·순서 변경·중단 재개 | 기존 단일 계산과 logical cohort/split/후보 의미 동일, 후보 None 고정 없음 |
| 이익 감소 1건 vs 손실 악화 1건 | 전자는 진단, 후자는 기존 손실 guard. 총 성과가 음수인 후보는 계속 탈락 |
| 희소 horizon 추가·30초 241/180초 240·모든 horizon 완비 | 각 P0–Pd pair 보존, coverage 한 건 차이로 긴 지연 탈락 없음, 완비 시 기존 비교와 동등, holdout 재선정 없음 |
| 구/신 schema·source/cost/정책 수정·손상 leaf | 구 준비는 구 규칙으로 검증, 새 증거는 새 generation. stale cache/pointer 거절 |
| 후보→독립 verifier→selector→prepared lookup | 정상 양수 delay/typed/시장 후보의 마지막 소비 도달. 원천·경제 실패는 정확한 부모 유지 |

AI·broker·계좌 호출은 동결 응답/격리 adapter로 대체하고 실제 내부 producer·normalizer·source verifier·selector는 실행한다. 기존 실패 재현은 red test로 남기고 P1–P5 수리 뒤 green을 확인한다. 좋은 표본을 추가해도 실패하는 기존 반례와, 성과가 실제로 나빠 계속 부모를 유지해야 하는 반례를 함께 둔다.

### 7.1 전달·세대 변경 대사표

| 계약 | 생산·변환 경로 | 최종 소비·무효화 검사 |
| --- | --- | --- |
| P1 effective PASS/보조 identity version | compose/AI 완료 → Main commit → delay observer/projection → resident/분할 셀 | 새 policy/committed/Prepared lookup, 구 버전 보존·위조/누락 receipt 거절 |
| P2 원 요청·투표·coverage | 실제 AI caller/evidence writer → vote ledger/segment → quote/완료 adapter → `research_json_stream.completed_rows` | replay context·feature spool·CF adapter·독립 source verifier, 모델 입력 동일성·완료/CF 분리 |
| P3 원 pin/연구 assignment/학습 generation | 상황 feature → 공유 split → frozen hypothesis/typed report | typed selector/schema/PreparedPin/lookup, 기존 보유 pin 유지·새 진입 causal pin |
| P4 후보 pair/제외/공유 split | replay minimal result → resident/`main_trailing_population_aggregation` → 상황 집계/holding report | source byte verifier/selector, 후보별 n/ID/digest·부모/actual 비용 기준 일치 |
| P5 선정 알고리즘/손실 predicate | resident/분할 train 선정 → fixed holdout → policy report | 코드/source 계약·committed/prepared reader, 과거 규칙으로 과거 봉인 검증 |

`research_json_stream`의 field whitelist, compact/tree 출력, replay source/context field, feature spool, cache key, `code_contract` 경로 목록을 모두 대사한다. vote/schema/정규화 구현을 새로 참조한다면 그 코드도 source contract에 넣는다. 원 vote·원가·부모·정의·분류·split·알고리즘의 변경은 관련 캐시와 파생 후보를 무효화하되 무관한 가격 원문을 다시 복제하지 않는다. cold 결과와 warm/증분/비용 정정/중단 재개의 논리 결과를 비교한다. 내부 연결을 mock한 양수 결과로 이 표를 완료 처리하지 않는다.

성능은 기존 공유 writer·feature/cache·streaming/tree·heavy admission 예산 안에서 검증한다. 장중에는 원 요청당 identity 계산/기록을 한 번 수행하고 매 tick 파일/원문 AI 전체를 읽거나 새 provider call을 하지 않는다. 장후는 원장/투표/feature를 한 번 읽어 후보가 공유하며 P5의 최대 4개 pair 집계와 P4 후보 mask는 streaming/index로 계산한다. 후보별로 전체 원장을 복사하거나 별도 train/holdout 파일을 만들지 않는다. 정상/burst/slow-writer 및 cold/warm/delta를 같은 입력으로 비교하고 장중 tail·보호 간격·queue·합산 CPU/RSS/disk의 기존 예산을 유지한다. 거대 원장을 회차마다 복제하지 않는다.

기존 0건 검열·후보 미전달의 짧은 실행 시간을 신규 정상 연구의 성능 기준으로 삼지 않는다. 지원되는 동일 성공 작업과 독립적인 순차 기준 계산을 사용하고 실제 처리한 행·후보·AI 증빙 수, wall/CPU·RSS·I/O·중복 decode·출력량을 함께 대사한다. 새 파일이 필요하면 기존 scalping/ai/automation/lifecycle 역할 패키지의 소유 경계를 먼저 정하며 engine root에 새 구현을 추가하지 않는다.

영향 pytest·compile·`git diff --check`·문서 parser와 연결 시험의 코드 검증 후 발행 인계는 별도 단계로 구분한다. source date/publication date/effective date를 구분하고 source→report→policy→committed→기존 summary/strict/controller/finalization→PREOPEN을 새 generation으로 결속한다. 중간 실패 시 새 policy pointer와 구 loader가 섞이지 않도록 기존 전환 journal/CAS/복구 계약을 사용한다. 변경 없는 EOD·원 기계/보조 정책을 재생성하지 않는다. 이번 코드 구현에서는 이 운영 절차를 실행하지 않았다.

## 8. 완료 기준과 계획 검증

완료 보고는 **① 원천 연결 정상화 ② 적격 자료의 후보 생성 가능 ③ 기존 선정 조건 통과 여부 ④ 정식 발행/준비 ⑤ 자연 PID·경제 결과**로 구분한다. 코드 완료에는 ①②의 정상·실패 통합 증거가 필수다. ③의 정당한 성과 부족은 구현 결함이 아니며 부모/0초가 유효하다. 반대로 정상 자료가 구조적으로 계속 검열되거나 후보가 consumer에 전달되지 않으면 구현 완료가 아니다.

| 수리 후 남을 수 있는 상태 | 자료 증가만으로 달라질 가능성 | 보고·다음 조치 |
| --- | --- | --- |
| 새 정상 PASS/AI 증빙이 적고 아직 표본·독립 기간 부족 | 있음. 실제 같은 의미 부모/관측 가능한 후보의 자료가 쌓여야 함 | 적격 n/일수와 유지 중인 부모/0초를 보고. 새 정상 자료의 경로가 열렸는지 별도 확인 |
| 과거 요청 원문·투표 coverage·원가 복구 불가 | 해당 과거 행은 시간 경과로 회복되지 않음 | 제외 근거 보존. 신규 정상 행과 분리하고 같은 실패 연구를 반복하지 않음 |
| 후보가 실제 보유 관측창 밖이거나 원 AI 입력을 변경 | 단순 건수 증가로 해결된다고 보장할 수 없음 | 그 후보의 지원 비율을 보고. 지원되는 원 입력/관측창의 자료가 없다면 별도 원천 연구 과제로 남김 |
| train/holdout 개선 음수 또는 기존 손실/stress guard 실패 | 건수 자체가 해법이 아님. 평가창·후보의 실제 성과에 따라 결정 | 미채택 항목을 그대로 보고. 손익 0 합성·guard 우회·holdout 재선정 금지 |
| 정상 원천인데 구 해시 equality/전역 교집합/None bridge로 계속 차단 | 없음. 코드 수리가 필요 | 구현 미완료로 표시하고 해당 P1–P5 producer/consumer 재점검 |

특히 기존 `paired_delta < 0 AND 후보 순손익 < 0`이 1건이라도 있으면 제한하는 계약은 유지된다. 같은 평가 cohort에서 그 행을 그대로 보존하면 좋은 행을 추가하는 것만으로 그 실패가 없어지지는 않는다. 이를 일반 악화 veto 제거와 혼동하거나 “데이터가 쌓이면 반드시 채택”으로 보고하지 않는다. 손실 guard 자체의 변경은 이번 계획에서 결정하지 않는다.

계획 리뷰에서 원 holding-AI가 pre-signal 투표를 사용한다는 점, 관측된 INSUFFICIENT와 원장 유실의 차이, 원 pin·연구 분류·배포 세대의 분리, 기존 손실 악화 predicate, sparse horizon의 선정 절차를 구체화했다. 기능 없는 schema/영수증만 추가하거나 새로운 불가능 조건으로 차단 위치를 옮기지 않는다.

계획 리뷰 당시 문서 수용은 변경 링크·권한/owner·공백·print-only parser로 확인했으며 구현·provider 호출·장후 실행·성능 측정·배포/기동은 수행하지 않았다. 아래 구현 검증은 그 이후 요청으로 수행한 별도 증거다. 기존 관련 계획의 완료/배포 기록은 당시 근거로 보존한다.

최초 계획 검증 기록: 당시 변경 3문서의 로컬 링크/anchor 65개 결손 0, fence·공백 검사 PASS, print-only parser OPEN 23개·stderr 0이었다. 이 기록을 이번 수정본 검증으로 재사용하지 않는다. 이번 재리뷰는 R1–R6·후보별 pair·원 AI 전체 입력·실제 보관 한도·전달/세대 표·자료 증가의 한계를 보완했고 아래 별도 검증 근거에 결과를 기록한다.

계획 재리뷰 당시 검증: 본문과 직접 연결된 3문서의 로컬 링크 70개 결손 0, fence·공백·`git diff --check` PASS, print-only parser OPEN 23개·stderr 0, 10/12 `DirectFamilyPreopenPolicyHandoff` 한 개다. [문서 검증 근거](../../tmp/trailing-delay-generability-20261010/plan-rereview-validation.json)에 당시 보호 대상 17개의 hash 불변을 기록했다. 당시 수정은 본 계획 한 문서와 소형 검토 근거뿐이며 pytest·AI/계좌 호출·장후 재생·배포는 실행하지 않았다.

## 9. 실제 구현과 남은 운영 확인

- P1: 실제 요청의 보조 의미 identity·effective PASS를 원 기계 부모와 함께 전달한다. 새 anchor는 `anchor_contract_version=3`이며 문자열 로그·중첩 고정 객체에서도 동일 digest를 보존한다. 지연 선정은 `candidate_paired_chronological_split_v3`, 구 알고리즘 검증은 구 규칙으로 유지한다.
- P2: [AI 소유 원천 adapter](../../src/engine/ai/holding_vote_replay_source.py)가 기존 원 요청 파일의 byte 참조와 pre-signal path vote를 연결한다. 새 provider 호출·복제 원장은 없다. 투표 segment rollover, 현재 PID/체결 세대 coverage, 원문·route·epoch·시간 검증과 공유 메모리 한도를 적용한다.
- P3: 원 holding pin을 보존하고 연구 assignment를 분리했다. 의미 hash와 train 원천/점수만 결속하는 `classifier_generation_sha256`를 별도로 기록한다. holdout으로 hypothesis·시장·후보를 다시 고르지 않는다.
- P4: 후보별 pair/적격 ID와 raw census를 분리하고 대용량 typed 후보를 기존 selector에 연결했다. 집계는 `candidate_parent_pairs_v2` 의미를 명시하며 독립 검증기는 봉인된 minimal checkpoint에서 집계를 재계산한다.
- P5: 일반 이익 감소는 진단에 남기고 기존 손실 악화 predicate를 실제 ID로 유지한다. 각 지연 horizon은 자신의 P0–Pd pair로 train을 비교하고 고정 승자만 holdout에서 확인한다.

실제 시험 수·수정 이력·성능 측정 범위는 [구현 리뷰](../audits/main-trailing-delay-structural-implementation-review-2026-10-10.md)에 기록한다. 이번 시험은 신규 정상 자료가 후보/기존 소비 함수에 도달하는 구조를 검증한다. 운영 누적 자료의 새 경제 후보 채택, 장후 전체 성능, 정식 successor 발행/PREOPEN와 자연 PID 소비는 아직 이번 코드의 완료 증거가 아니다. 기존 owner를 OPEN으로 유지하고 이전 v6 발행·준비 증거와 구분한다.

## 후속 운영 완료 기록

사용자의 운영 장후 재생성·배포 승인 후 `main-trailing-delay-structural-20261010-v1`을 선택했다. source 10/8·publication 10/10·effective 10/12로 정식 지연 v3/trailing 부모 계승을 발행하고 summary/strict/controller·native finalization DONE·PREOPEN 전체 계약을 검증했다. EOD·원 기계/보조 policy bytes는 유지하며, 새 채택 후보가 없어 trailing 12 cell 부모·지연 0초다. [운영 실행·한계](../audits/main-trailing-delay-structural-implementation-review-2026-10-10.md), [최종 준비](../../data/report/main_trailing_delay_deployment/2026-10-10/final-structural-readiness.json)를 확인한다. 새 provider/AI/주문 호출은 없으며 웹은 새 릴리스에서 HTTP 200을 확인했다. Main의 10/12 07:35/07:55 실제 기동은 future_due이고 자연 PID/성과·전체 장중 성능 관측은 아직 미수용이다.
