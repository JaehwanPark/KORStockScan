# Entry AI exact 입력·판단 전달 및 작은 수익 기회 진단 보완

작성 기준: 2026-09-08 KST. 대상은 #119/#23에 연결되는 Entry AI #76/#77/#78/#80/#82이며 장후 전체 실행 지시가 아니다.

## 1. 판정과 범위

목적은 비용 차감 후 작은 수익을 빈번하게 확보할 수 있도록 기존 Entry AI의 입력·판단·사후평가 연결을 복구하는 것이다. 이번 변경은 저장, 판단 계층의 출처, 비용 결손 격리와 진단 전달을 보완한다. 새로운 alpha 튜닝축이나 주문 허용 경로를 만들지 않는다.

코드 수리, 배포, 자연 입력/후속 소비, PREOPEN/PID, 실제 제출·체결·순이익은 별도 상태다. 이 작업에서는 provider 호출, 운영 산출물 덮어쓰기, 장후 전체 재실행, 봇 재기동, 수동 env/lock/TTL/진입조건 변경을 하지 않았다. 다른 세션의 scanner/census/workorder 및 운영 산출물 변경은 보존한다.

## 2. 원인과 수정

| 항목 | 확인한 결함 | 보완 및 경계 |
| --- | --- | --- |
| exact 입력 저장 | 12:30:03까지 KRX analyze_target 고유 요청39건 모두 replay_exact=false. 집중 확인한 정상 응답5건의 redaction은 폐기된 ADM/LDM cache 식별자3곳 | 실제 producer의 공개 `RETIREMENT_ID`를 정확히 일치하는3개 cache_token 경로에서만 보존. 다른 경로·다른 값·실제 credential 마스킹은 유지. 예전 redacted 파일은 복원하거나 exact로 재라벨링하지 않음 |
| 판단 계층 | 052690의 모델 WAIT가 보정 후 DROP인데 control이 최종 action/reason과 원모델 evidence를 혼합 | 원모델 필드를 보존하고 검증·보정 후 response, runtime action mapping, 최종 response를 분리. `ai_entry_decision_layers_v1` 최종 response hash와 trace/action/score/reason/probe 연결을 producer→prepared control→엄격 source 재검증→captured control까지 공유 |
| 과거 control | 보정 전 근거만으로 보정 후 decision을 재구성할 수 없음 | adapter/model 필드가 있으나 최종 snapshot이 없는 과거 행은 `natural_control_final_response_missing`. 없는 근거를 합성하지 않음. adapter 없는 과거 단순 control은 유지 |
| 작은 기회 누락 | gross1% false-drop 진단과 기존 gross0.30% target-first 진단이 분리되어 작은 비용 차감 기회가 핵심 taxonomy에서 보이지 않음 | 기존 target-first에 유한·비음수 execution proxy를 연결하여 `false_drop/false_wait_small_profit_execution_proxy` 진단을 생성. #82 cohort 요약과 #78의 기존 offline 개선목표에 전달. 기존1% 진단·false-drop10% review ceiling 및 live gate는 변경하지 않음 |
| 비용 결손 | 노출이 선택됐는데 execution cost가 없으면 `or 0.0` 계산으로 gross 값이 primary value에 남을 수 있음 | 생산자에서 결손 pair를 이유/ID와 함께 격리. #82도 과거 report를 포함하여 control/candidate 실제 exposure의 비용을 재검사. 정상 pair는 남기고 retained+excluded 보존식 유지. 결손 원본 report의 전체 promotion 성공은 허용하지 않음 |
| 재검증 시간·입력 | expired handoff는 입력을 재생성하지만 거부된 원 trace와 준비시간이 부족 | 만료/거부된 handoff의 관찰용 trace/snapshot/TTL을 보존하되 authoritative parent/consumed로 표시하지 않음. 재입력 준비시간, analyze 소요시간, 입력 재사용/재생성, 원모델 action·보정·trusted tape 관측을 기록 |

수정 owner: `ai_decision_trace.py`, `ai_engine_openai.py`, `ai_decision_quality.py`, `ai_action_outcome_calibration.py`, `micro_reversion/main_ai_prompt_optimizer.py`, `sniper_state_handlers.py`와 직접 회귀 테스트. 신규 Python 모듈·wrapper·cron은 만들지 않았다.

## 3. 경제성과 조건 달성 가능성

- `entry_small_profit_opportunity_v1`은 기존 target-first 진단의 보완이며 새 승인 gate가 아니다. 예를 들어 target0.30%에서 execution proxy0.20%를 뺀0.10% 여유는 진단에 남는다. 이는 모델의 예상 상승률이나 실제 실현 순익이 아니다.
- execution proxy는 spread/age 추정치다. 수수료·세금·실체결이 결속되지 않은 곳의 `net_profit_opportunity`는 null, 이유는 `fee_tax_and_actual_fill_not_bound`로 남긴다. 이를 full net EV로 부르거나 검증된 #77 경제성/실체결 원장을 대체하지 않는다.
- focused latency 통과 후 정상 응답5건의 결과 age는0.108~0.399초였으므로90초 결과 TTL을 늘릴 근거가 없다. Entry-price handoff2초는6건 중4건에서 만료됐지만, 만료 입력을 그대로 재사용하는 대신 재생성 시간을 관측한다. 과거 trusted tape를 현재 fresh source로 간주하지 않는다.
- offline 연구와 live 승격은 별개다. 기존 one-sample learning/thin-positive 경로를 유지한다. #77 연구5일/부모5/종목3과 full-gate5/10/20일, #82 review/승격 floor를 이번 진단 수리 완료조건으로 요구하지 않는다. 등록·승인되지 않은 runtime을 표본만으로 자동 활성화하지 않는다.
- 정상 WAIT/DROP·bounded probe arm·실제 submit/fill을 혼합하지 않는다. 작은 기회 진단이 positive여도 stale/tape/구조/broker guard를 우회하지 않는다.

## 4. 리뷰·검증

`korstockscan-review-gate`에 따라 producer/consumer, silent-fail, exact identity·hash, secret redaction, historical compatibility, 비용 결손 및 runtime authority를 반복 리뷰했다. 검토 범위 내 미해결 finding은0이다.

1차 trace/quality/AI adapter408 tests PASS. 확장 검증에서는1730 PASS/11 FAIL이었으며, 실패11건은 기존 call-local `entry_submit_attempt_finished` 추가를 반영하지 않은 테스트였다. 차단 원인·deposit/broker 미호출·주문 금지 검증을 유지하고 마지막 observation-only 종료 이벤트까지 검증하도록 보완했다. 비용 결손 consumer 테스트도 결손 행 제외와 정상 행의 thin-positive 학습 유지로 수정했다.

추가 리뷰에서 malformed final edge 자료가 보고서 예외로 번지지 않도록 행 단위 finding으로 격리했고, 비용 결손 pair와 정상 pair의 혼합 report가 #82까지 정상 학습을 유지하는 종단 테스트를 추가했다. 포맷 도중 실행한 source-inspection 테스트7건은 파일 위치와 로드된 코드의 줄 번호가 달라 실패했으며, 포맷 완료 후 새 process에서 재실행해 닫았다. 코드나 안전조건을 완화하여 테스트를 통과시키지 않았다.

최종 검증:

- 8개 모듈1746 tests PASS: `test_ai_decision_trace`, `test_ai_decision_quality`, `test_ai_engine_openai_transport`, `test_ai_action_outcome_calibration`, `test_main_ai_prompt_optimizer`, `test_main_ai_prompt_consumer`, `test_state_handler_fast_signatures`, `test_sniper_scale_in` (49.72초).
- malformed final/부분 성공·비용 격리/strict verifier calibration 계약9 tests PASS. 위1746건과 중복되는6건을 별도 합산하지 않는다.
- 변경 Python 및 테스트 `py_compile` PASS, `git diff --check` PASS.
- print-only 문서 parser PASS, 현재 checklist에서 기존 Entry/AI acceptance ID 각각1건 확인. 다른 세션의 backlog 추가는 보존했다. Project/Calendar sync는 실행하지 않음.

이 코드 수리 완료는 배포·자연/경제성 acceptance 완료를 뜻하지 않는다.

## 5. 자동화 및 자연 acceptance

현재 설치된 기존 예약 경로인20:10 materialization→R0–R3→calibration→optimizer→consumer와21:05 follower를 유지한다. 다음 정상 producer가 새 코드를 읽으면 변경된 저장/검사/진단 계약을 소비한다. 이미 실행 중인 PID의 새 trace snapshot 생성 여부는 별도 배포 receipt로 확인해야 한다.

실행 owner는 [오늘 checklist](../checklists/2026-09-08-stage2-todo-checklist.md)의 기존 `AIDecisionActionOutcomeNaturalEvidence0908` 및 `EntryRecheckNaturalAttribution0907`이다. 중복 OPEN을 만들지 않는다.

확인할 근거는 새 generation의 exact 입력/최종 response hash, control 포함·제외 사유, 작은 target-first 진단의 #82/#78 전달, 비용 결손 pair 제외 보존식, handoff 재생성 소요시간/거부 이유, 마지막 consumer hash다. 실전 prompt 적용은 기존 별도 registration/authorization/PREOPEN/receipt owner를 따르며 #81은 계속 DISABLED다. 실제 submit drought 해소 및 수수료·세금 차감 순이익은 이후 자연 terminal/fill 근거가 필요하다.
