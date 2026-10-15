# 최신 Main 재기동 이후 제출병목 점검 — 2026-10-15

**판정: 제출병목 미해소.** 현재 PID의 정책 소비·WS 수신·평가 결과 전달은 확인했지만, 유효 PASS가 실제 broker 제출까지 도달하지 못했다. HPSP 요청 원문/참조정보 결손 1건도 확인했다. `Intraday Control State: RED`는 이 실제 source-chain 결손을 포함한 판정이며, 프로세스 정지나 broker 주문 거절을 뜻하지 않는다.

분석 창은 **09:49:20.600~10:00:27.405 KST**다. 후속 감시·탐지기 소비는 10:00:40 보고서와 10:04:56 health까지 확인했다. 일일 누적·이전 PID·서로 다른 평가/submit-call 분모를 합치지 않았다. 이번 작업은 점검과 원 증빙에 근거한 분석 projection 보완이며, 매매 코드·정책·operator lock·provider·주문·배포·재기동은 변경하지 않았다.

## 1. 실행 신원과 증거 범위

- 선택 release: `/home/ubuntu/KORStockScan-runtime-releases/observer-publication-integrated-20261015-27e1b5bdf`.
- commit `27e1b5bdfe4156491ad275e88034980153f5bc62`, 실제 PID `1614174`, start ticks `8930260`, 실제 cwd `release/src`를 `/proc`와 대사했다. ordered transition은 09:50:33.562 complete/pass다.
- target 10/15 bootstrap verifier는 같은 PID에 `pid_passed=true`, missing/mismatch 0이다. manifest seal은 `73a9a4f20bc146ea40c2f74966e107a3cb7773ef623dd1b9df0750a838adebad`.
- 자연 machine capture에서 소비한 bundle은 `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`; source/publication 10/14, effective 10/15다. 준비·selector만으로 실제 소비를 추정하지 않았다.
- 10:00:04~05 자연 inventory receipt는 KRX/NXT complete, open-orders verified다. 042660·475150은 기존 수동관리로 남았고 Main 보유 복구 수는 0이다. 추가 계좌/API 조회는 실행하지 않았다.

[원본 snapshot manifest](../../tmp/submission-bottleneck-review-20261015-0958/snapshot-1001/manifest.json), [정확한 평가·제출 연결](../../tmp/submission-bottleneck-review-20261015-0958/snapshot-1001/analysis.json), [비고정 전수 표](../../tmp/submission-bottleneck-review-20261015-0958/snapshot-1001/nonfixed-all-code-route.csv), [해시 검증](../../tmp/submission-bottleneck-review-20261015-0958/snapshot-1001/hash-validation.json)을 보존했다. 591MB까지 증가한 pipeline raw는 전체 검색하지 않았다. 기존 compact index의 현재 PID 창과 최대16MiB raw/trace tail을 사용했다. index의 3,215개 header/payload 해시·내용과 native observation 19개 해시를 검증했다.

원 raw tail은 09:57:56부터, index는 10:00:05까지다. 겹치는 구간을 확보했고 raw/요약 행 수를 거래 수로 합산하지 않았다. trace tail의 첫 완전 행은 09:19:58이어서 이번 PID 창을 포함한다. 시간으로만 PID를 추정하지 않고 아래 23개 모두 원 `evaluation_attempt_id`의 async PID/start-ticks receipt와 연결했다. 분석 중 canonical 원본을 수정하거나 이전 payload를 재구성하지 않았다.

## 2. 고정 5종목 및 비고정 전수

10:00:26 동일 PID/commit의 shared WS는 connection available, writer loss/projection error 각각0이다. 아래 수신 age는 그 snapshot 시점 값이다. 0건은 포착된 attempt 부재이며, 해당 종목의 native FSM이 실행되지 않았다는 뜻이 아니다.

| 종목 | 0B / 0D age(ms) | 평가 trace | provider 호출 | raw PASS / 응답 후 실행 유효 PASS | broker 제출 |
|---|---:|---:|---:|---:|---:|
| 삼성전자 005930 | 20 / 19 | 0 | 0 | 0 / 0 | 0 |
| 두산에너빌리티 034020 | 420 / 18 | 0 | 0 | 0 / 0 | 0 |
| HPSP 403870 | 822 / 8 | 8 | 5 | 4 / 1 | 0 |
| 알테오젠 196170 | 1,521 / 617 | 0 | 0 | 0 / 0 | 0 |
| 주성엔지니어링 036930 | 221 / 16 | 15 | 6 | 5 / 3 | 0 |

비고정 queue는 **415 code×route 행 / 406개 고유 종목**이다. 재기동 이후 claim한 9행은 terminal7 + observing2이며, 나머지406행은 이번 PID에서 아직 claim하지 않았다. 이를 전체 시장 평가 완료 또는 전체 무신호로 표현하지 않는다.

| 새 claim 종목 | 결과 |
|---|---|
| 동양고속 084670, 디케이락 105740, KT 030200, 대한제강 084010 | exact native no-match 4건 |
| KoAct 미국치매&뇌질환치료제액티브 490330 | `0B_age_exceeded` |
| 고려신용정보 049720 | `native_source_stale_or_absent` |
| 엘컴텍 037950 | `route_snapshot_missing` |
| 레메디 387690, TIME 글로벌바이오액티브 485810 | 관측 중2; cutoff에서 terminal 아님 |

비고정 Main 편입·보조 AI·제출의 새 성공은 이 창에서 확인되지 않았다. 원천 결손3건을 정상 BLOCK/no-match로 바꾸지 않았다. independently measured market-wide recall이나 415행의 전체 평가 완료도 입증되지 않았다.

## 3. 기계 → AI → Main → 제출 보존식

서로 다른 단계의 분모를 아래처럼 유지했다.

```text
평가 trace 23 = native capture 19 + capture 전 contract-invalid 4
native capture 19 = ENTER_NOW 17 + source_invalid 2
ENTER_NOW 17 = 실제 provider 호출 11 + 호출 전 local 종료 6
provider 호출 11 = raw PASS 9 + CAUTION 1 + timeout 1
raw PASS 9 = 응답 후 원 신호 경로 무효 5 + 실행 유효 PASS 4
실행 유효 PASS 4 = Main 수용 3 + Main 소비 시 deadline 만료 1
Main 수용 PASS 3 = budget 통과 평가 3 → submit 함수 호출 6 → broker 제출 0
```

호출 전 local 종료6은 원 신호 경로 변경4·AI lock contention2다. capture 전 contract-invalid4의 원 사유 역시 `reversal_signal_path_changed`다. source_invalid2는 `krx_integrated_event_venue_unproven` 및 candle timing/source/age 결손을 보존한다. 이들을 AI VETO, 새 정상 RECHECK, 주문 실패로 바꾸지 않는다.

23개 평가 모두 `worker_completed → rejected 또는 accepted_to_entry_path`에 연결됐다. 수용5개는 PASS3·CAUTION1·source-invalid DROP1로, 수용/`ai_confirmed`라는 stage명 자체를 BUY/PASS로 세지 않았다. 모든 budget 통과 submit-call6개에는 정확한 최초 blocker와 `returned_false / broker_accepted=false` terminal이 있다. 확인한 분모 내에서 원인 없는 submit 반환 누락은0이다.

## 4. 유효 PASS가 실제로 막힌 지점

| 평가 / 종목 | 실제 흐름 | 최초 차단 |
|---|---|---|
| 09:56:47 주성 `aims-c20439dea8aba53eebdb` | PASS→budget→CAUTION 허용; 재방문에서 budget→SAFE→sizing | 첫 call: `real_weak_pullback_entry_block`; 두 번째: `pre_submit_weak_context_late_entry_guard_block` |
| 09:58:24 HPSP `aims-05085a127d27bf82a455` | 응답 검증은 유효; worker completion 후 Main 수용 전 만료 | `result_deadline_expired` |
| 09:58:34 주성 `aims-24ff7f93147a07cb882e` | PASS→budget→CAUTION 허용 | `real_weak_pullback_entry_block` |
| 09:58:48 주성 `aims-f47ec14a8c5a7e43eed9` | PASS→budget, 같은 평가의 call3개 | `latency_block`: DANGER / `ws_jitter_above_caution` |

주성의 약한 pullback 차단2건은 fresh micro 입력에서 positive1 / 요구2, spread1tick / 요구5tick, `below_strength_base`였다. SAFE 뒤 추가 weak-context 차단은 최근 차단 이력과 `below_strength_base|tick_accel_below_min`에 의한 것이며, 당시 tick acceleration0.500·매수비중78.51%·drift context false였다. 관련 운영 flag 두 개는 실제 bootstrap에서 ON이다. `SCALP_REAL_WEAK_PULLBACK_ENTRY_BLOCK_ENABLED`는 기존 operator owner이며 임의 해제하지 않았다.

**유효 PASS+자금 통과 후 정상 제출 경로가 추가 문맥 검사에 막힌다는 가설의 실제 분모가 생겼다.** 다만 차단 뒤 executable 비용 후 성과를 아직 대사하지 않았으므로 과도한 차단이라는 경제적 결론은 미확정이다. `order_bundle_failed`와 `probe_broker_submit_failed`는 이 사례에서 앞선 로컬 guard 실패의 후속 기록이며, broker에 전송했다가 거절된 증거가 아니다.

DANGER의 WS jitter는 674/675/738ms였다. quote age454/121/357ms와 구분한다. 확인된 DANGER/stale·broker/account/order/quantity/cooldown guard는 유지 대상이다.

## 5. 시간초과와 신호 전달

HPSP 09:58:31의 timeout은 물리 호출1회, HTTP budget1,379ms였다. 같은 trace의 provider 진입 전 준비2.026초, adapter 호출1.673초가 관측됐다. `provider_total_ms=823`은 내부 구간이며 총 벽시계 예산 또는 provider 서버 처리시간으로 대신 쓰지 않는다. 이번 창의 provider 호출11개 중 timeout1개이며, 이전 PID의 timeout 비율과 같은 조건의 성능 비교는 아니다.

성공 응답에서도 local 비용이 남는다. 09:55:53 HPSP의 응답 후 처리1.462초, 09:58:24 HPSP의 응답 후 처리0.661초가 기록됐다. 후자는 worker completion09:58:25.616, 원 deadline25.826, Main 판정25.933으로 **Main 소비가 기한보다 약106ms 늦었다**. 응답 검증 이후 소비·기록·Main 방문 지연을 함께 다뤄야 하며 timeout 숫자만 늘려서는 닫히지 않는다.

[현재 PID 성능 원본](../../tmp/submission-bottleneck-review-20261015-0958/snapshot-1001/performance-last.json)의 loop work423회 p95 1.255초 / p99 2.755초 / max4.927초, confirmed→claim23회 max0.926초다. 이 수치는 수면을 포함한 종단간 기회 지연이 아니다. 회로는 CLOSED·연속실패0·unsettled future0으로 회복했지만 timeout/제출병목 해결의 증명은 아니다.

selected native signal56개는 claim23 + **claim 전 무효화33**이다. 상세 lifecycle의 `observed_valid_until_deadline_unclaimed=0`, unobservable0을 확인했다. 상위 집계의 `expired_before_claim=33` 이름만 읽고 모두 scheduler가 놓친 유효 신호라고 판정하면 잘못이다. ready ingress117도 distinct signal56과 다른 분모다.

## 6. 요청 원천 결손과 감시 소비

09:58:22 `jsonl_generation_lock_busy`로 `ai_decision_trace.capture_request`가 빈 metadata를 반환했다. 같은 HPSP 평가 `aims-05085a127d27bf82a455`는 provider 응답 PASS·실행 유효였지만 `request_capture_status=partial`, `payload_replay_exact=false`, `prompt_replay_exact=false`, 직접 async PID/request metadata가 null이다. 원 machine capture와 별도의 async disposition은 남아 있어 이번 분석에서는 그 동일 attempt로 PID를 연결했다. 이 보완은 원 request payload를 저장했다거나 정확히 재생할 수 있다는 뜻이 아니다.

[10:00 후속 monitor](../../tmp/submission-bottleneck-review-20261015-0958/snapshot-1001/monitor-1000-followup.json)는 해당 동일 attempt를 `auxiliary_call:route_or_reference_missing=1`, `auxiliary_pending:route_or_reference_missing=1`로 검출했다. 이는 결손 평가1건의 두 downstream 표현이다. [10:04:56 detector](../../tmp/submission-bottleneck-review-20261015-0958/snapshot-1001/health-followup.json)는 같은 run `6bacc639e9b54598bbefc3558434960d`의 health projection match=true와 artifact fail을 소비했다. process/resource/lock 검사는 PASS였다. source warning이 실제로 보고·탐지기에 전파되므로 이 사례를 경보 없는 실패로 판정하지 않는다.

원 요청 저장 실패는 과거 입력을 합성해서 복구할 수 없다. exact replay 입력에서 결손을 그대로 제외하고, 이후 수리는 deadline을 소모하지 않는 원문 저장·실패 receipt/필수 identity 보존을 함께 검증해야 한다. 이번 분석 projection은 손실된 원문·시각·actor를 원 파일에 덧씌우지 않았다.

## 7. 기존 owner의 다음 액션과 종료 조건

| 기존 owner | 이번 판단 / 다음 액션 | 종료 조건 |
|---|---|---|
| `DirectFamilyPreopenPolicyHandoff` | 현재 PID/정책 소비 확인; 자연 거래·성과는 별도 | 동일 PID/target/hash 유지와 자연 downstream 별도 수용 |
| `AuxiliaryCircuitRecoveryRepair1012` | 요청 capture 결손1과 PASS 소비 만료1을 보완 대상으로 유지. 후단 약세 gate의 역할을 현재 기계/보조 owner와 대사 | 원5초·응답 의미·원 신호/보호 guard를 보존하며 새 정상 요청 원문→trace→Main terminal 완전 결속; 유효 PASS의 정상 제출 또는 직접 guard 사유 |
| `NonfixedDispatchReadinessReview1012` | 415 code×route 전수 상태 확인; source 결손3·관측 중2·이번 PID 미claim406을 유지 | 기존 cadence/lease 내 새 exact-route 원천→native 판정→편입, 연속 슬롯과 누락 없는 coverage 확인 |
| `HoldingProfitExitSourceContractRepair` | 기존 비용/원천 수용 OPEN; 이번 창 Main 보유0 | 기존 policy/source/실제 terminal·비용 계약; 표본0을 수리 완료로 닫지 않음 |

우선순위는 요청 원문/identity 보존과 응답→Main 소비 지연 보완, 이어서 **machine ENTER_NOW+유효 PASS 뒤의 추가 약세 문맥 veto**가 현재 승인 owner와 중복되는지 검토하는 것이다. 새 병목 분류 체계를 늘리지 않는다. 같은 quote·가격·수량·hard safety를 보존한 정상 submit 경로 비교가 필요하며, 관측된 blocker만을 이유로 operator lock이나 DANGER를 해제하지 않는다. 변경 자체가 필요하면 그 정확한 runtime/정책 owner 범위에서 별도로 구현·검증한다.

현재 checklist OPEN9개를 분류했다. 장후5개(`DirectFamilySourceRepairEntryCancelWait`, `DirectFamilySourceRepairEntrySplit`, `MainStopLossRetirementRuntimeTuning1010`, `PostcloseStructuralPolicyCompletion1011`, `MainMarketWeaknessPostcloseObservation1008`)는 해당 실행창 전 `not_yet_due`다. 위 due4개 중 장전 소비는 확인, 보조회로는 source 결손으로 `blocked_missing_evidence`, 비고정은 기존 연속 관측 수용 `waiting`, holding source 수용은 기존 증거 결손 `blocked_missing_evidence`로 유지한다. 미분류0이다. runtime에 결속된 checklist의 원 bytes와 stable ID를 수정하지 않았다.

실주문·체결·완료 비용 결과가 없으므로 비용 후 EV/순이익 개선은 미판정이다. 이 짧은 창으로 후행10/20/30/60분 성숙·scanner recall·전체 시장 기회 또는 필터의 적정성을 완료 처리하지 않는다.

## 8. 리뷰와 검증

분모와 용어를 재검토해 raw PASS/실행 유효 PASS/Main 수용, evaluation/재방문 submit-call, pre-claim 무효화/미방문 만료, 로컬 guard/broker 거절, symbol/code×route를 분리했다. source-only 분석은 원 index 해시·exact attempt PID 연결·call terminal 검증으로 확인했다. 현재 배포 코드의 guard와 capture 실패 경로를 직접 읽었으며 실행 코드를 수정하지 않았다.

문서 로컬 링크7개 오류0, 진단 스크립트2개 compile·분모 보존식·whitespace·`git diff --check`·print-only checklist parser가 통과했다. 당일 OPEN9개 중복0, selector와 실제 PID/start ticks 및 checklist의 원 봉인 해시 불변도 확인했다. 운영 코드 변경이 없어 pytest·provider replay·주문 시험·장후 보고서 재생성은 실행하지 않았다. 외부 Project/Calendar 동기화도 실행하지 않았다. 검증 receipt는 같은 증거 디렉터리의 `validation.json`에 보존했다.
