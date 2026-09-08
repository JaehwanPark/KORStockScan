# 9/7 장후 우선순위 보완·재생성 검토

대상 거래일: `2026-09-07`. 재생성·검증은 `2026-09-08 KST`에 수행했고 최종 관찰은 `00:28 KST`다. 자정 이후에도 source date를 바꾸지 않았다.

판정: **YELLOW — 요청한 코드/계약 보완은 닫았으나 자연 source 및 수익개선 acceptance는 남아 있다.** `korstockscan-review-gate`에 따라 구현 → 리뷰 → 보충 수정 → 재검증을 반복했다. 코드 완료를 실전 적용·수익 향상으로 해석하지 않는다.

## 우선순위별 결과

| 우선순위 | 직접 원인 | 보완 및 실제 재생성 결과 | 남은 경계 |
| --- | --- | --- | --- |
| 1. 최종 요약·체크리스트 | 후행 workorder/AI 산출물이 바뀌어도 앞서 만든 tower/checklist의 세대를 최종 verifier가 대사하지 않음 | `postclose_summary_sources_v1`의 exact source SHA-256 도입. tower → checklist → strict verifier 순서로 마감. 선택 **16→15건**, 구현 검토 **10→9건**이 최신 workorder와 일치. 실제 handoff `pass`, source-generation/필수/후행 결손 0 | verifier/controller 자체 hash는 순환 방지를 위해 제외. 요약 직전의 운영 검증과 마지막 strict 검증은 분리; 다음 자연 wrapper 실행은 별도 acceptance |
| 2. exact 주문·체결·손익 | `avg_down_route_arbitration_observed`의 CF route 관찰을 실제 scale-in 결정으로 오인해 정상 NXT lifecycle을 격리. 서로 다른 거래 집합의 snapshot PnL을 당일 headline에 표시 | v2 schema·exact identity·source-only authority를 확인한 관찰 **3행**을 실제 ADD/NO_ADD와 분리. instrumentation gap **5→2**, eligible 실제 lifecycle **0→2**. 잘못 표시되던 headline `0원`은 `null/unresolved_trade_review_count_mismatch`로 정정 | 원본 결손 2행과 미체결 KRX lifecycle을 정상화했다고 주장하지 않음. snapshot 건수 일치만으로도 비용 검증을 승인하지 않음 |
| 3. AI·machine source 준비 | Main AI custody 결손과 과거 micro 입력 유실, machine ingress receipt 유실이 혼재 | 추가 Provider 호출 없이 R0–R3와 `calibration → frozen optimizer → batch metadata rebind → holding manifest → consumer` 재생성. custody workorder 1건 제거. consumer terminal 연결 유지 | micro 과거 market row **18행**, Entry exact control **KRX/NXT 각 0**, holding provider checkpoint 미충족. machine 9/7 anchor **8개 eligible 0**과 다음 날짜 source acceptance 유지; 같은 날짜 machine 재실행하지 않음 |

## 복원된 실제 경제 근거

[main lifecycle 산출물](../../data/report/main_scalping_lifecycle_paired/main_scalping_lifecycle_paired_2026-09-07.json)의 동일 attempt/order/owner 연결을 검토했다.

| Record / 종목 | Attempt | 체결·terminal | 비용 / 순손익 |
| --- | --- | --- | --- |
| `40904 / 304100` | `SCANPROM-304100-1788766259214` | NXT, 최초 1주+추가 1주→청산 2주, `full_only`, `FINAL_EXIT_RECONCILED` | fees/taxes **75원**, 순손익 **+395원** |
| `40942 / 249420` | `SCANPROM-249420-1788766498453` | NXT, 최초 1주+추가 1주→청산 2주, `full_only`, `FINAL_EXIT_RECONCILED` | fees/taxes **72원**, 순손익 **+58원** |

두 행 모두 cost profile verified, row-source gate pass, broker provenance/conflict gap 0이다. 합계 **+453원은 기존 실거래 결과의 귀속 복원**이지 이번 코드가 새로 만든 수익이나 튜닝의 인과적 개선량이 아니다. partial fill을 full fill에 합치지 않았다. 다른 집합인 trade-review snapshot과 숫자를 맞추려고 이 값을 EV headline에 덮어쓰지 않았다.

남은 legacy identity 결손은 record `159 / 016360`의 2행이며, 실제 identity를 추정하지 않는다. KRX record `40581 / 387690`의 미완료·미체결도 실현손익으로 세지 않는다. 실제 경제 근거 2건이 개선 후보 연구의 입력 가능성을 높이지만 Main AI prompt/input 후보의 수익성 또는 실전 승격을 입증하지는 않는다.

## 재리뷰에서 추가로 닫은 결함

- Summary-only recovery가 이전 자기 자신의 handoff 오류를 새 tower에 다시 담지 않도록 **요약 직전 일반 verifier → tower/checklist → strict verifier**로 분리했다. 마지막 허용 recovery attempt에서도 strict 검증을 수행한다.
- Strict verifier 명령 실패 뒤 남아 있는 과거 `pass/warning` artifact를 controller DONE으로 인정하지 않는다. recovery action 실패도 기존 성공 상태에 가려지지 않는다.
- CF 관찰의 order authority가 `true`이거나 알 수 없는 값이면 관찰-only 경로로 빼지 않는다. 위조 ID·잘못된 schema/authority는 계속 결손으로 남긴다.
- 기존 controller 회귀 fixture가 필수 artifact census 없이 내부 reconciliation 실패를 숨기던 것을 발견했다. 실제 성공 조건을 갖춘 fixture로 정정하고 실패 재사용 방지 테스트를 추가했다.

변경 위치: `src/engine/automation/postclose_summary_handoff.py`(automation package 소유), controller/tower, checklist builder, final verifier, main lifecycle paired, EV report, main wrapper 및 직접 테스트. `src/engine` root에 새 Python 모듈을 추가하지 않았다. 동시에 진행 중인 위젯·저가주 runtime/profile 수정은 이번 변경·완료 주장에서 제외했다.

## 재생성·운영 확인

- 원본·source hash·로그: `tmp/postclose_priority_20260907.onRRk7/`. 이전 정상 산출물을 보존한 후 영향 범위만 재생성했다.
- AI source 재생성은 `source_only_blocked_or_deferred` / exit 2이며 **6단계 실행은 모두 성공**했다. 이 exit는 남아 있는 canary source block이지 새로운 실행 장애가 아니다. `provider_call_performed=false`.
- 재생성 범위: lifecycle/R0–R3 source → calibration/optimizer → batch metadata-only/holding manifest/consumer → EV → workorder → runtime **summary** → tower → checklist → strict verifier/controller. runtime summary는 보고서이며 runtime env 적용이 아니다.
- CLI 점검에서 EV 전용이 아닌 `--producer-gap-disabled` 옵션 오류를 발견해 실행 전 중단됐고, 지원하는 `--disabled-source` 옵션으로 재실행해 성공했다. 원본 또는 운영 설정 변경 없음.
- strict verifier: `warning` terminal, summary handoff `pass`, missing required/downstream/stale/source-generation 모두 0. 남은 warning은 `limit_down_watch_ordered_path_not_observed`, `microstructure_diagnostic:warning`이다.
- controller: `00:27:44 DONE`, strict verifier `00:27:43 warning` / summary handoff `pass`, full wrapper 재실행 없음. 후행 AI는 앞선 metadata-only 재결속으로 검증했으므로 이 수동 controller run에서는 replay follower와 Codex runner를 OFF해 중복 호출하지 않았다. 보충 코드 수정 후 마지막 controller 실행에서도 추가 recovery action 없이 완료했다.
- finalization의 원본 predecessor 검사 코드를 읽기 전용으로 재실행해 **7개 검사 모두 done / ready**를 확인했다. cleanup/final detector의 대상일 최신 성공은 **9/7 23:23:29 / 23:23:30**이다.
- final detector는 현재 날짜 컨텍스트를 사용하므로 자정 이후 과거일을 강제 실행해 새로운 9/7 성공이라고 기록하지 않았다. 이번 요약 복구와 무관한 cleanup도 다시 실행하지 않았다. 과거 detector receipt와 새 verifier/controller 결과를 구분한다.
- 매매 process, PREOPEN/live env, operator lock, provider route/model, 주문·수량·가격·cap·threshold·safety 변경 없음. main wrapper 전체 재실행, package 설치, commit/push 및 외부 Project/Calendar sync 없음.

## 추천 대사와 fixed-point

[이번 frozen ledger](./2026-09-08-postclose-priority-repair-ledger.json)는 이전 66행에서 custody gap 1건이 제거된 **65행**을 보존한다. JSON/Markdown native ID 및 **11개 source hash**를 대사했고, 두 번의 재-intake에서 source/decision 변경과 미분류 0이다.

- 전체 65 = 구현 검토 9 + 비구현 56.
- eligible 9 = `blocked_missing_evidence` 9 + actionable open 0. NXT receipt 2건의 복원만으로 각각 다른 Telegram/taxonomy/post-submit 계약까지 모두 닫았다고 간주하지 않는다.
- 비구현 56 = observed 25 + deferred 2 + rejected 1 + external source dependency 2 + native ID/authority 결손 26.
- 제거된 `main-ai-gap-aa95ee8a62abfc8036cd4876`은 과거 generation의 보완 이력이며 현재 분모에 중복 계상하지 않는다. Main AI micro canary 및 machine ingress-loss source workorder는 유지한다.
- 이 frozen generation의 신규/변경 eligible actionable 0이다. **근거 대기·권한 결손은 구현 완료가 아니므로 전체 GREEN을 선언하지 않는다.** 별도 세션의 widget/episode 추천 구현과 그 이후 산출물은 이 frozen 검토를 자동 승계하지 않는다.

## 검증 및 다음 owner

최종 단일 실행에서 **955 tests passed (18.12초)**. main lifecycle/receipt, handoff, controller/tower/checklist/verifier/EV, wrapper, AI quality cycle, finalization의 11개 파일이며 반복 실행 건수를 합산하지 않았다. Python compile·Ruff, `bash -n`, `git diff --check`, 문서 print-only parser PASS. 수정한 코드와 직접 producer/consumer 검토 범위의 미해결 P0~P2 finding은 0이다. Provider 재평가나 실주문 테스트는 수행하지 않았고 자연 source/경제성 acceptance가 완료됐다는 뜻은 아니다.

다음 자연 확인은 [9/8 checklist](../checklists/2026-09-08-stage2-todo-checklist.md)의 기존 `PostcloseRecoverySourceAcceptance0908`, `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908`, `MachineLifecycleTurnoverObjectiveFollowup0908`을 재사용한다. 향후 exact source가 회복돼야 prompt/input 후보와 machine timing의 비용 차감 EV 비교가 가능하다. 이미 유실된 9/7 원본을 같은 재실행으로 복원할 수 있다는 기대는 두지 않는다.
