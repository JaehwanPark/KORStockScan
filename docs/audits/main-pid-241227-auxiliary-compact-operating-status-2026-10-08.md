# Main PID 241227 기동 후 가동 점검 — 2026-10-08

판정: **RED — 프로세스는 가동 중이나 상시감시 3종목의 시장 전환 원천과 현행 장중 인계 계약에 결손이 있다.** 이번 점검은 16:36~16:52 KST의 일회성 관찰이다. 봇·정책·환경·주문 경로를 변경하거나 재기동하지 않았다.

근거는 [20KB 상태 요약](../../data/report/auxiliary_compact_adoption/2026-10-08/pid-241227-operating-status-1652.json)에 보존했다. 대형 원장의 복제본이나 신규 AI 비교 원장을 만들지 않았다. 현재 owner는 당일 체크리스트의 `DirectFamilySourceRepairMainMechanisticEntry`이며, [compact 구현 기록](main-auxiliary-compact-intraday-adoption-review-2026-10-08.md)과 [후속 성능 개선 계획](../proposals/main-post-warmup-latency-rest-ws-bottleneck-remediation-implementation-plan-2026-10-08.md)을 구분한다.

## 1. 실행·정책 소비

- Main PID `241227`, start ticks `2483072`, 기동 `15:42:24 KST`. 중복 Main PID는 없으며 실제 cwd는 `/home/ubuntu/KORStockScan-runtime-releases/main-aux-compact-20261008-v3/src`다.
- 선택 release와 실제 PID의 commit은 `dc769a09c052df06b265c7d9ce196428caae20ec`로 일치한다. data/logs는 작업공간의 공통 anchor다. 웹은 16:49:46의 로컬 HTTP 확인에서 200이었다.
- 기계 bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`: PID 영수증의 128 경로가 신규 소비 상태이고 legacy carry는 0이다.
- 보조 overlay `b8e97475121038c21d1608f99530f1c740f696f4ba084d0cfd2f9b48c4961626`: 현재 PID의 소비 영수증이 같은 overlay를 가리키며 `actual_pid_consumed=true`다. 발행 파일의 불변 `actual_pid_consumed=false`를 PID 미소비로 오인하지 않는다.
- 전환 범위는 비상시 종목 AFTER의 2개 가격대, 비상시 종목 PRE의 1개 가격대, 삼성 AFTER다. 위 영수증은 로드 증거이며 아래의 현재 인계 실패와 자연 요청 미관측을 대체하지 않는다.

## 2. 상시감시 — 등록 5, 최근 상세평가 2

16:00:20~16:51:23의 current-PID machine capture 16MiB suffix에서 상시감시 35행을 확인했다. 이는 반복 관측이며 독립 진입 기회 35건이라는 뜻이 아니다.

| 종목 | DB 감시 상태 | 현재 도달 단계 | 직접 사유 |
| --- | --- | --- | --- |
| 삼성전자 005930 | AFTER / WATCHING, ID 49157 | 기계 상세평가 18행 | 모두 BLOCK / `no_current_operating_signal` |
| 두산에너빌리티 034020 | AFTER / WATCHING, ID 49158 | 기계 상세평가 17행 | 모두 BLOCK / `no_current_operating_signal` |
| HPSP 403870 | REGULAR / WATCHING, ID 49159 | 기계 이전 대기 | `fixed_watch_nxt_eligibility_unproven` → `session_generation_mismatch` |
| 알테오젠 196170 | REGULAR / WATCHING, ID 49160 | 기계 이전 대기 | 같은 원인 |
| 주성엔지니어링 036930 | REGULAR / WATCHING, ID 49161 | 기계 이전 대기 | 같은 원인 |

DB를 read-only transaction으로 조회한 결과, 5종목 모두 10/8 exact-date `security_market_eligibility_daily`와 `daily_stock_quotes` fallback 행이 없다. 현재 reader는 HPSP·알테오젠·주성의 PRE/AFTER 편입에 당일 NXT 적격성 원천을 요구한다. 이 검사가 실패하여 reconcile이 시장 세대를 바꾸기 전에 반환하고, 정규장 감시 행은 메모리/DB에 남는다. 이후 `observation_ready`는 현재 AFTER 세대와의 불일치로 상세평가를 중단한다. 16:47:41의 Main 로그와 16:45:22까지의 pipeline 대기 기록이 같은 경로를 확인한다.

원천 부재는 실제 NXT 비대상 판정과 구별한다. 기존 heartbeat의 감시 5는 등록 상태이고 5종목의 현재 시장 상세평가 완료 증거가 아니다. 당시 eligible/raw 패킷 없이 API 장애나 놓친 승리 건수를 확정하지 않는다.

최초 owner는 `main_fixed_watch._new_symbol_session_eligible`의 source consumer와 기존 당일 eligibility producer다. `update_kospi._collect_and_store_market_eligibility`의 정규 EOD 일정은 20:05 이후이며 지금 앞당겨 전체 EOD를 실행하지 않았다. 다음 조치는 승인된 기존 제한 원천 경로로 세 종목의 정확 날짜·종목·출처 적격성을 보강한 뒤 AFTER admission/generation → exact 0B/0D → machine capture를 대조하는 것이다. 과거 자료의 날짜를 바꾸거나 eligibility guard를 완화하지 않는다.

## 3. 보조 AI·제출과 자연 경로의 한계

- 현재 PID performance의 provider response, preparation queue/service, Main commit 관측은 모두 0이다. 요청 원장의 마지막 수정은 14:41:41로 현재 PID 기동 전이다. 새 compact 정책의 자연 요청·해독·Main commit 효과는 아직 확인할 수 없다.
- 같은 machine suffix의 비상시 `zero_base_probe_machine_only_v1` 59행 중 ENTER_NOW는 2행이다. 000250과 473980의 원천 관측용 판정이며 live AI 요청 또는 주문 intent로 집계하지 않는다.
- native ingress ready 236 / fixed-watch claim 0은 별도 진단값이다. ready에는 실행 편입·현재 선택 정책·후단 적격성 검증이 포함되지 않으므로 236건의 미진입 또는 승리로 해석하지 않는다.
- Main heartbeat 보유는 0이고 위 5개 감시 행의 buy quantity는 0이다. 이 증거를 전체 증권계좌 flat이나 수동·퇴역 원장 잔여분의 소멸로 확장하지 않는다. 퇴역 owner의 자동 실행 누출은 현재 health에서 관측되지 않았다.

## 4. 점검 중 바뀐 인계 세대

장중 handoff를 처음 read-only 검증했을 때는 PASS였다. 그러나 점검 중 16:48:08 KST에 현행 체크리스트 바이트가 변경됐다. 이번 점검은 체크리스트를 수정하지 않았다.

- handoff가 봉인한 체크리스트: `ca53931ef8e47bfab9d387460a17b1993a00355f24e91b9b6a4f3ccc3afadaf2`
- 변경 후 체크리스트: `b60000ae0c9998eaa6bea68c00224515db86d3301daa76fb0927ef09f6aee085`
- 재검증: **FAIL / `intraday_preserved_generation_changed`**

기동 당시 소비 영수증을 현재 인계 PASS로 전용하지 않는다. 이 실패만으로 변경 후 모든 기계 호출이 실제로 중단됐다고 확정하지도 않는다. 기존 배포 owner가 최종 체크리스트와 현행 source를 검증하여 다음 승인된 배포의 호환 인계를 준비해야 한다. 동시 작업의 문서를 원래 바이트로 덮거나 기존 불변 handoff를 수정하는 복구는 하지 않았다.

현재 cron health에는 과거 `strict_checklist_generation_stale` 실패가 없다. 10/7 최종화의 historical observer는 보존된 소비 세대로 검증되고, 남은 cron 경고는 10/8 06:50 cutoff 이후 07:26에 완료된 두 작업의 `recovered_late`다. 과거 최종화 관찰의 PASS와 현재 실행 인계 FAIL은 별개다.

## 5. 성능·운영 건전성·작업본 반영

16:49:02 performance snapshot 기준 첫 루프 제외 2,997회에서 p95 0.900초 / p99 2.156초, 5초 초과 2회, 최대 44.843초다. AI 호출이 없는 AFTER 관측 창이므로 이전 정규장과의 전체 개선율이나 B3~B6 완료를 주장하지 않는다. 이 두 긴 지연의 직접 stack owner는 이번 관측에서 확정되지 않았다.

WS lock의 최신 retained 4,096 표본은 wait p95 21.52ms / p99 62.03ms, hold p95 4.62ms / p99 8.78ms다. 누적 전체 표본의 percentile로 전용하지 않는다. HTTP physical attempt는 1,148 시작 = 1,147 response + 1 inflight이며 timeout/exception은 0이다. response는 증권사 business success와 다르다. 분봉 logical demand 102건은 모두 REST retained로, WS 대체 효과는 이 창에서 확인되지 않았다.

16:50:38 health의 프로세스/스레드·resource·인증·log scanner·lock은 PASS이고 Main loop heartbeat는 최신이다. 루트 디스크는 약 71%, 여유 약 44GB다.

작업본과 실제 release의 관련 source 15개 중 14개가 다르다. Main/AI caller, journal projection, WS snapshot, REST controller/telemetry, 시장 국면/Telegram 변경 등이 포함된다. 로컬 구현 존재를 현재 PID 반영으로 표시하지 않는다. 현재 release의 B1/B2·compact 인계와 후속 작업본은 기존 구현 owner가 최종 diff/review/호환 handoff를 통해 구분해야 한다.

## 6. OPEN 확인·검증·종료

- `DirectFamilySourceRepairMainMechanisticEntry`: 당일 기계·보조 PID 로드는 확인했으나 현재 인계 실패, 3종목 source gap, 자연 async/AI 경로 미관측이 남는다. 이번 점검으로 완료 처리하지 않는다.
- `DirectFamilyPreopenPolicyHandoff`: 15:42:26 current-PID bootstrap 영수증은 PASS다. 변경 후 인계 문제를 이 과거 bootstrap으로 덮지 않는다.
- entry_cancel_wait / entry_split 장후 owner: 지정 자연 postclose 일정의 후속 검증 대상이다. 이번 장중 점검에서 heavy producer를 실행하지 않았다.
- 자동 생성된 low_price_two_leg OPEN: Main-only 퇴역 계약에 따라 active 복구/연구 대상으로 삼지 않는다.
- `MainMarketWeaknessPostcloseObservation1008`: 현재는 계획/후속 구현 인계이며 연구는 21:40 이후 허용 창이다. 이번 점검에서 추가 장중 hook·수집·API 호출을 만들지 않았다.

검증은 실제 PID/selector/cwd/start ticks, 정책·소비 영수증, read-only DB, bounded source/capture/trace, handoff 재검증과 로컬 HTTP 확인으로 수행했다. source-only probe와 live 요청의 분모를 재리뷰하여 구분했다. 로컬 링크 3개, print-only parser 22항목·현재 Main owner 1개, `git diff --check`와 문서 공백 검사를 통과했다. 코드 수정이 없어 pytest/compile·provider replay·장후 재생성·외부 sync·재기동은 실행하지 않았다. 임시 raw tail 복제본은 작은 요약 보존 후 삭제했다. 이번 일회성 가동 점검은 종료하며 위 결손의 구현/배포 closure와 자연 정책 효과는 미완료로 인계한다.
