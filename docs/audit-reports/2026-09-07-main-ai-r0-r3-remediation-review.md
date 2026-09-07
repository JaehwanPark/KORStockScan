# Main AI R0–R3 보완·최종 리뷰

현행 판정은 아래 **현행 Entry AI 연결 3차 보완**을 우선한다. 1·2차 구현·검증과 미등록 판정은 당시 기록이며 이후 구현·권한 상태와 구분한다.

후속 사용자 승인·성능 검증·배포 지시의 현재 상태는 [별도 실행 판정](2026-09-07-main-ai-current-axis-approval-performance-deployment.md)을 따른다. 새 source 합성 preflight는 PASS이며 exact 후보/승인 artifact·active chain 종료·clean 배포는 별도 gate다.

대상: 장후 목록 #77과 직접 연결된 source-quality, R2/R3 검증, legacy #81 예약 호출 및 사용자 후속 지시로 확정된 현행 Entry AI 연결 구현. 사용자 지시: 권고 다음 액션 구현 후 review → fix → re-review → validation. #79/#80 전체 상세검토나 실제 실런타임 프롬프트 활성화는 이번 완료 범위가 아니다.

## 구현 판정

- 기존 A/B/C prompt/input 축을 보완했다. 새 매매 튜닝축은 만들지 않았다. 정확한 비용·동일 lifecycle 비교, 누적 EV·p10/tail·source gate를 유지한다.
- `observer_source_quality.py`는 기존 `src/engine/scalping/micro_reversion`의 오프라인 입력품질 검증 소유다. 기계 microstructure와 Main AI가 동일한 격리 검증을 사용한다. engine root 신규 모듈·중복 검증 구현은 없다. 고정 benchmark 소유 `canary_monitor.py`는 원본 그대로 보존했다.
- 종료·대사가 완료된 collector에서 timestamp 역행 사유만 존재하고, 수량 대사·저장 무손실·권한·행 소비금지 계약이 모두 유효한 경우 `pass_with_row_quarantine`다. 해당 행은 기존 bridge의 `market_path_consumer_ineligible`로 계속 제외한다. 큐/저장 손실, 사전 timestamp 거절, 결손 계수, 혼합 사유, 잘못된 권한은 Provider/R3 차단을 유지한다.
- custody blocker 숫자는 실제 pipeline 결손 건수다. `real_submitted_lifecycle_count`와 `broker_execution_unique_count`는 분모/관측 수치로 별도 보존한다. 1건 결손·3개 submitted·2개 broker execution을 `gap:3`으로 쓰던 문제를 `gap:1`로 수정했다.
- 5일/10일/20일 표본 하한은 각각 parent·symbol `5/3`, `10/5`, `20/10`이다. 기존 20일 표본 밀도를 비례 적용한 단기 바닥이며 통계적 유의성 보장은 아니다. Provider의 5일/20 parent/10 symbol 입장 조건, 비용·호출 cap은 변경하지 않았다.
- R2 각 partition은 `source_quality_blocked`, `hold_no_edge`, `hold_sample`, `research_candidate`, `runtime_review_ready`를 판별한다. 연구 후보는 5일의 source/경제성/표본 조건을 통과해야 하며 다른 창의 측정된 경제성 악화와 계약 손상도 확인한다. 10/20일 미누적·명목비교 결손은 full-gate blocker로 보존한다.
- R3는 `research_candidates`와 기존 full-gate `candidates`를 별도로 기록한다. `runtime_review_ready`는 누적 연구 증거 충족만 뜻하며 실적용 권한이 아니다. exact R2 hash와 재계산된 상태/목록 검증으로 연구 후보를 기존 승격 목록에 넣거나 권한 필드를 바꾸는 경우 거부한다. cycle summary에도 연구 후보 수와 상태별 수를 노출한다.
- 동일 lifecycle의 최초 결정차이 대표행에서 양쪽 명목 손익을 함께 비교한다. 한쪽이 probe/경제성 결손이면 비교값은 null이며 partial 공통표본 수를 명시한다. 검증된 no-entry/노출0만 실제 배분 없음의 0원으로 해석한다. 누락 비용/결과를 0으로 대체하지 않는다.
- 20일 full gate는 모든 대표행의 paired notional 비교 완결과 candidate−control 순이익 증가를 요구하며, 현행 A/B/C 설계는 candidate−baseline 증가도 요구한다. 양수 percentage EV만으로 원화 순이익 감소 후보가 통과하지 못한다. 수량·포지션 크기를 바꾸는 축은 없다.
- 신호 수·기준 session-hour당 신호·기준 capital-hour당 순이익을 양쪽에서 비교한다. 분모는 실제 관측 lifecycle의 공통 기준이며 독립 A/B/C 보유시간 재현을 주장하지 않는다. 빈도는 경제성 tradeoff 진단으로 공개하며 추가 독립 veto를 만들지 않는다. 값의 basis는 비용 결속된 counterfactual 증분값이고 실현 손익/실체결 품질이 아니다.
- postclose/PREOPEN wrapper는 disabled legacy runtime family를 호출하지 않고 `SKIP status=retired_disabled`를 남긴다. 과거 env flag로 호출을 되살릴 수 없다. R0–R3/#82/#78/holding manifest/consumer 순서는 유지하고 별도 `entry_setup_live_policy`는 그대로 둔다.

## 원천 재검증 정정

이전 점검에서 9/4를 역행 5건만의 문제처럼 설명한 부분은 불완전했다. 9/4 보존 snapshot에는 `invalid_exchange_timestamp_count=667422`, `stale_exchange_timestamp_block_count=667422`, `invalid_depth_timestamp_count=923052`도 있다. 각 계수는 중복 가능하여 합산한 고유 결손 수로 해석하지 않는다. 이 사전 enqueue 거절은 정확한 격리 증명이 없어 새 코드에서도 Provider/R3를 차단한다. 과거 날짜를 정상화하거나 이 보완으로 표본/수익이 생겼다고 주장하지 않는다.

관측 owner는 기존 `Intraday1120SourceAcceptance0907`, custody 결손은 `MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0907`이다. 정상 수집 여부와 자연 A/B/C 생성은 기존 `AIDecisionActionOutcomeNaturalEvidence0908`의 후속 검증으로 연결한다. 운영 보고서 재발행·Provider 호출·봇 재기동·env/주문 변경은 수행하지 않았다.

## 리뷰·검증

최종 11개 test module 확대 검증은 **782 PASS / 1 FAIL**이다. 실패는 아래 작업 전 고정 benchmark hash 정합성 1건이며 이번 변경 회귀는 발견되지 않았다. 새 테스트는 5일 연구/20일 심사 분리, 연구 목록·권한 위조 거부, 단기 symbol floor, 낮아진 원화 순이익 거부, 결손값 null 보존, 격리 대사·mixed loss·malformed contract 거부, 정확한 custody gap 표시를 확인했다. 연결된 machine microstructure, materialization, optimizer/consumer, standing authorization와 wrapper/verifier도 함께 검사했다.

Ruff, Black 7개 Python 파일, compileall, wrapper 2개 bash syntax, git diff --check와 print-only backlog parser(49개 OPEN 출력)는 PASS다. 9/4 snapshot의 읽기 전용 판정은 역행 격리 증명 PASS/사전 timestamp 거절 3개 counter 조건 BLOCK을 동시에 확인했고 원본 SHA-256은 불변이다. 구현→리뷰→보완→재리뷰에서 연구 목록 권한 위조, 누적 창 계약 손상, 고정 benchmark 모듈 변경의 파급과 비정상 테스트 census를 추가 검증했다. 검토한 변경 범위의 미해결 코드 finding은 0이며 전체 저장소/성능 source 검증이 모두 GREEN이라는 판정은 아니다.

별도 기존 실패: `test_repository_guard_matches_frozen_baseline_artifact`에서 forward_collector/path_journal/kiwoom_websocket의 고정 benchmark hash가 현재 HEAD와 불일치한다. 세 파일의 작업 전 HEAD hash와 작업 후 hash는 같아 이번 변경의 회귀가 아니다. 과거 측정 artifact의 hash만 갱신하여 검증을 우회하지 않는다. 고정 수치와 측정 세대 정합성 재확인은 기존 source acceptance에 남긴다.

현재 실행 코드의 경제적 효과나 자동 live 적용은 입증되지 않았다. #81은 disabled이고 현재 ask-depletion 조건부 축의 runtime consumer는 미등록 상태다. 이번 구현 완료는 source-only 연구 계약 보완의 완료이며 실적용 승인·수익 acceptance가 아니다.

## 목적 부합성 2차 보완

사용자의 재점검·보완 지시에 따라 1차 회귀검증이 다루지 못한 목적 부합성 반례를 재현했다. 정상 무신호가 누적 연구를 지우는 문제, WAIT/HOLD 횟수 veto, A→B 악화가 A→C/B→C 개선까지 거부하는 문제, 5일 연구에 10/20일 경제성 실패가 전파되는 문제, probe 혼합 때문에 원화 비교가 전부 막히는 문제를 이번 보완 범위로 고정했다.

- 정상 `no_micro_reversion_eligible_requests`는 R2의 `current_run_observation_states`로 분리하고 기존 정상 누적 증거를 보존한다. cycle은 다른 결함이 없을 때 `source_only_no_new_sample`/exit0으로 종료한다. source/hash/계측/실행 실패는 여전히 blocker이며 빈 신호를 이용해 우회할 수 없다.
- WAIT/HOLD는 terminal 미해결이 아닌 action 진단값이다. 실제 lifecycle custody·성숙도·비용·invalid transition 검증은 유지한다. A→B feature-only EV는 진단으로 바꾸고 최종 C의 C−A/C−B EV·원화 증분손익·p10/severe-tail 조건을 유지한다. R3 evidence contract도 같은 의미로 보완했다.
- 연구 상태 v2는 5일 표본/경제성으로 추가 평가 가치를 판단한다. 연구에는 상대개선 1%를 요구하지 않고 10/20일 경제성은 진단으로 노출한다. 모든 기간의 source 계약 손상과 severe-tail 악화는 계속 차단한다. 5/10/20일 full-gate 심사와 runtime 적용 권한은 별도다.
- 원본 arm의 검증된 `ev_basis`로 `full_or_zero_exposure`와 `standardized_probe_research_only`를 결과 수익과 무관하게 사전 구분한다. R2 partition과 R3 연구 identity에 포함한다. probe는 연구에 남지만 full 후보가 되지 않으며 full 집단 내 100% 원화 비교 완결성은 유지한다. 결측을 0원으로 채우거나 full 집단 성과를 probe 포함 전체 정책 성과로 일반화하지 않는다.
- Provider 입장 하한은 floor target date `2026-09-07`부터 5거래일·5 parent·3종목이다. 이전 날짜의 5/20/10 계약과 immutable hash는 그대로다. 생산자와 Provider 직전 검증기가 같은 effective-dated 함수를 사용하며 four-companion/full-window census·가격/비용·checkpoint 검증 및 130 parent/390 attempt/USD1 상한은 유지한다. 이 변경은 연구 평가 입장이며 실매매 승인 하한이 아니다.
- 기존 #80 consumer가 exact-date R2/R3를 검증하여 `r3_research_handoff`에 연구 ID·source hash·경제성 상태를 수용한다. 정상 연구는 기존 bounded 평가로, full 경제성 증거는 `runtime_contract_implementation_required`와 owner/acceptance로 분리하며 추가 Provider 큐를 만들지 않는다. 미등록 consumer/승인 계약을 표본 누적으로 자동 해결했다고 표시하지 않는다.

권한/완료 경계: 새 live consumer의 실제 입력 연결, exact approval, same-stage conflict, PREOPEN apply/rollback와 post-apply attribution은 아직 구현 완료가 아니다. 이 경로의 범위는 사용자 확인 대상으로 분리했고 #81 재활성화·실매매 활성화·env 수정·보고서 재생성·Provider 호출·재기동은 실행하지 않았다. 자연 생성은 기존 `AIDecisionActionOutcomeNaturalEvidence0908`에서 확인한다. 이번 source-only 구현과 실런타임 연결 전체 완료를 구분한다.

최종 검증: 14개 모듈 재실행 **1113 PASS / 기존 benchmark hash 1 FAIL**. 최초 확대 1112 PASS/같은 기존 실패 뒤 CLI 정상 무신호·consumer 표시 보완을 추가하고 재실행한 결과다. 실패 파일 forward_collector/path_journal/kiwoom_websocket은 `git diff --exit-code HEAD`로 작업 전 HEAD와 동일함을 재확인했다. 기존 source acceptance에서 측정 세대 정합성을 확인하며 과거 artifact hash만 교체하지 않는다.

Ruff, Black8, compile4, wrapper bash syntax2, git diff --check와 print-only parser를 통과했다. producer→Provider 직전 검증기→R2/R3 projection→#80 handoff 재리뷰에서 evidence contract의 옛 feature/deferred 문구, 정상 무신호 CLI exit2, 소비자 표시 누락을 추가 수정했다. 20일 정상 이력 보존/실제 결손 차단, 경제성 개선에도 WAIT/HOLD 증가 허용, C 개선/B 단독 악화 구분, 장기 경제성 진단/심각 tail 차단, full/probe 분리, Provider 새 하한의 canonical-window/위조 하한 거부, consumer source/hash/권한 위조 거부를 검증했다. 검토한 source-only 변경 범위의 미해결 코드 finding은 0이며 실런타임 연결 미구현과 실제 수익 acceptance는 이 코드 종결에 포함하지 않는다.

## 현행 Entry AI 연결 3차 보완

사용자가 범위 확인 요청에 `이어서 진행`으로 응답하여 현행 ask-depletion 축의 소비·승인 검증·PREOPEN·rollback·attribution을 구현했다. 이는 코드 구현 범위의 확정이며 실제 활성화 승인이 아니다. 별도 family `main_ai_ask_depletion_prompt_input_v1`는 기존 R3 축 `prompt_contract_effect_on_ask_depletion_context`의 연결이며 새 alpha 튜닝축이나 #81 재활성화가 아니다.

### 연결과 승인 경계

| 경로 | 구현 계약 | 실제 권한/상태 |
| --- | --- | --- |
| R2/R3 → postclose | exact full candidate, 최신 terminal cycle의 R2/R3 hash, 등록된 prompt contract 및 verified cost/master로 다음 거래일 후보 생성 | 등록 없음은 `registration_missing_disabled`; 연구 후보는 live 후보가 아님 |
| 승인 → PREOPEN | 첫 candidate exact hash·계약·명시 지시 참조·최대31일 유효기간; 다음 거래일 06:00~08:50, Entry Setup 선택 이후 비충돌 확인 | `MAIN_AI_CURRENT_AXIS_ENABLED=true`와 외부 승인 모두 필요; 자동으로 동의/환경변수를 만들지 않음 |
| PREOPEN → Entry AI | immutable apply receipt와 activation commit, exact-date 09:00~15:30; 본문 hash·만료·철회·후발 source 실패 매번 확인 | KRX 정규장 SCANNER의 기존 `entry_v1` 또는 `decision_quality_v2_7_entry`, 동일 provider/model/transport/schema/parser/호출 budget만 지원 |
| 입력 → 실제 요청 | 기존 collector의 처리 완료 barrier와 symbol/venue/session/epoch 범위, fresh snapshot·preflight·canonical tactical/ask builders·비용 일치 | 기존 provider 호출의 prompt/input만 교체; 추가 Provider 호출·수량·주문/안전장치 변경 없음 |
| rollback → 후속 기록 | env OFF/rollback 파일/만료/source drift 시 baseline; 진행 중 철회·transport 변경 응답은 판단에서 제외 | sticky AI cache 재사용 없음; exact-request 전달 census는 실제 체결·EV acceptance가 아님 |

등록 파일 `data/runtime/main_ai_current_axis/registration.json`의 schema는 `main_ai_current_axis_registration_v1`이며 `contract_sha256`, exact `control`/`recommended`와 자기해시를 요구한다. 동일 prompt 계약의 비용 cohort가 여러 개면 선택을 추정하지 않고 중단하며, 안정적인 `scope.selected_cost_profile_id`로 1개 cohort를 등록할 수 있다. 다음 source date의 cost/master는 R3의 최신 master source date에서 자동 재구성하므로 매일 수동으로 등록 파일을 갱신하지 않는다.

외부 `operator_authorization.json`의 schema는 `main_ai_current_axis_operator_authorization_v1`이며 최초 `first_candidate_sha256`, `operator_instruction_ref`, `reviewed_at_kst`, `expires_at_kst`, `enabled=true`와 계약/자기해시를 요구한다. 명시 승인에 `allow_same_contract_renewal=true`가 포함된 경우에만 첫 적용의 commit/동일 prompt 계약을 증명한 다음 날짜 후보를 승인 유효기간 안에서 자동 갱신한다. 최초 승인 누락·새 prompt/parser/provider 계약·승인 만료는 일수나 표본 누적으로 자동 해제하지 않는다. 실제 등록·승인 파일은 이번에 만들지 않았다.

### 재리뷰에서 보완한 결함

- collector hot path에 AI 모듈 의존성이 유입되지 않게 read-only source buffer를 micro-reversion package로 분리했다. 신규 orchestration은 `src/engine/automation`, 정책/입력/소비자는 `src/engine/scalping` 소유이며 engine root 신규 모듈은 없다. 별도 구독/프로토콜 파싱을 만들지 않는다.
- producer callback의 오류 처리는 bulk copy lock을 기다리지 않고 invalidation 세대만 표시한다. 종목/venue가 식별되는 timestamp 불량은 해당 scope만 격리하고, 재수집·coverage 회복을 허용한다. 미처리 sequence·동시 변경·epoch 경계·출처 불명 손실은 후보 입력에 쓰지 않는다. 메모리는 256 scopes/60,000 rows 전체/stream당12,000 rows로 제한하며 eviction 경계를 숨기지 않는다.
- PREOPEN은 receipt를 먼저 기록하고 activation을 commit marker로 쓴다. 중단 후 exact 최초 승인 재시도는 복구 가능하며, 미완결 첫 적용으로 다음 날짜 renewal을 열 수 없다. 이미 적용된 날짜의 다른 세대를 덮어쓰지 않는다.
- live 검증 cache는 immutable 내용에만 사용한다. 승인/rollback/경쟁 owner/최신 postclose·cycle terminal은 매번 확인하므로 늦은 실패를 낡은 성공 artifact로 우회하지 못한다. 경쟁 Entry Setup의 `runtime_effect=false`만 믿지 않고 자체 schema/hash·exact date·inactive status도 확인한다.
- 실제 provider 요청 저장이 실패하거나 선택 입력/프롬프트 hash가 일치하지 않으면, 보내지 않은 준비 요청과 새 baseline 요청 ID를 분리해 baseline으로 복귀한다. 추가 호출이나 신규 entry veto를 만들지 않는다. provider 응답 대기 중 철회·만료·transport 변경은 candidate 판단을 사용하지 않는다.
- 다음 세션 후보 생성이 실패해도 당일의 전달/철회 census는 별도로 실행한다. 미확인 전송·정상 전송·진행 중 철회·미적용을 나누고, 누락 trace·identity/hash 불일치는 source-quality 실패다. #76/#82의 기존 경제성 평가를 전달 성공 횟수로 대체하지 않는다.

### 목적 부합성·조건 달성 가능성·완료 경계

목적은 검증된 기존 prompt/input 개선을 실제 동일 경로로 전달하여 비용 차감 EV·순이익 개선을 시험할 수 있게 하는 것이다. 2차에서 완화한 연구 하한/무신호 처리와 full/probe 분리, full 후보의 5/10/20일 C−A/C−B 경제성·원화 비교·tail/source 조건은 유지했다. 실체결이나 모든 horizon의 미래 결과를 **live 입력 구성**의 추가 조건으로 요구하지 않는다. 범위 밖·불충분 source는 baseline으로 돌아가므로 보조 입력 실패 자체가 새 매수 차단축이 되지 않는다.

자동화 연결은 구현했지만 **현재 자동 실적용은 OFF**다. 첫 등록/정확한 승인, fresh collector를 가진 별도 허용된 PID, full-gate 자연 증거가 필요하다. `entry_v1`/V2.7과 다른 응답·ledger·probe/수량 adapter는 현재 지원 범위가 아니며 V2.14/V2.15 owner로 alias하지 않는다. 표본 누적만으로 계약/최초 동의/배포 결손이 해결되지는 않는다. 현재의 자연 full 후보·등록·승인이 없으므로 다음 장전 적용 가능이나 수익 발생을 확정하지 않는다.

**성능 증거 정정:** 1·2차의 forward_collector가 HEAD와 같았다는 기록은 당시 사실이다. 3차에서는 normalized read-only handoff를 위해 그 파일도 수정했다. frozen benchmark 불일치는 작업 전부터 있었으나 이번 변경에 대해 과거 성능 승인을 재사용할 수 없다. `canary_monitor.py`/과거 benchmark artifact는 수정하지 않았으며 새 소스 세대 성능 측정·source acceptance는 `Intraday1120SourceAcceptance0907`에 남긴다. hash만 바꿔 PASS를 만들지 않는다.

최종 20-module 확대 회귀는 **1,410 PASS / frozen benchmark hash 1 FAIL**다. 기능 범위에서는 최초 등록→source-bound 후보→PREOPEN crash/retry→live 읽기→늦은 source 실패→rollback, exact canonical 입력의 정상/불량 사례, 실제 호출 위치의 선택 byte/capture 실패 baseline 복귀/진행 중 철회, owner hash, 요청 census, 장후·장전 wrapper 조건 및 기존 trace/location gate를 확인했다. 실패는 위에 분리한 성능 증거 세대 불일치이며 전체 검증 GREEN이라고 표시하지 않는다. 새 모듈·테스트 Ruff6, 관련 Python Black11/compile10, wrapper 2개 syntax, git diff --check 및 print-only checklist parser(51개 OPEN 출력)는 PASS다. 운영 current-axis 디렉터리가 생성되지 않았음도 읽기 전용으로 확인했다.

변경된 producer→consumer→요청 저장/응답→전달 census와 문서를 재리뷰한 기능 범위의 미해결 코드 finding은 0이다. 자연 wrapper/현재 PID/실수익 acceptance는 기존 `AIDecisionActionOutcomeNaturalEvidence0908`, 최초 활성화 준비는 `MainAICurrentAxisActivationReadiness0908`가 소유한다. 운영 보고서 재생성, Provider/broker 호출, 등록·승인·활성화 파일 작성, env 변경, 재기동, 커밋·푸시는 수행하지 않았다.
