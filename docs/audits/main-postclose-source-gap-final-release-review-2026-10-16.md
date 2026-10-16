# 최종 릴리스 source gap 통합·익절 전이 수리 — 2026-10-16

## 범위와 승인

사용자는 최종 선택 릴리스 기준 재통합, 익절 최초 전이 결손 5건 및 12:25:19 탐지 알림의 보완을 지시했고, 통합·리뷰·검증 후 배포·재기동도 명시적으로 승인했다. 정책·threshold·수량·provider·수동/retired custody·hard safety 변경은 포함하지 않는다.

- 기준 commit: `4c65523b20469ca6d195f22293b21fb2f253f7ee`.
- 착수 시 실제 PID: `3377997`, start ticks `18399636`, cwd `/home/ubuntu/KORStockScan-runtime-releases/sor-krx-pipeline-consumer-final-20261016-4c65523b2/src`.
- 격리 작업트리: `/home/ubuntu/KORStockScan-worktrees/postclose-source-gap-final-release-20261016`, branch `codex/postclose-source-gap-final-release-20261016`.
- 기존 수리 `e9cfb9bcaf4f84491d4593587bc48c2bdde4ae85`를 no-commit cherry-pick으로 통합했다. 최신 SOR KRX 귀속·체결 시각·pipeline 참조 검증·transport 계측 변경을 보존했다. 자동 병합된 trade-review/trace 테스트의 실제 결합 결과도 검토했다. 이전 [구현 기록](main-postclose-source-gap-repair-review-and-deployment-handoff-2026-10-16.md)은 과거 3c 기준 검증이며 현재 코드 검증과 구분한다.
- 정규 workspace의 동시 수정과 원 evidence는 그대로 두었다. 정책/PREOPEN/원 journal·trace·DB의 소급 정정은 실행하지 않는다.

## 익절 결손 5건의 확정 원인

12:25:19 full detector의 `holding_profit_exit/source_gap`은 검증 기록의 recovered report SHA `e9efa1c85dd240acd2f9e94c4cf7060be93d90193c6922f5a60f011c6f69a338`와 같다. 정책 결속/PID 소비 gap은 이미 비어 있고, 아래 원천 결손이 남은 동일 세대 알림이다. 이를 새 정책 실패나 실제 SELL 누락으로 확대하지 않는다.

원 생산자의 sampled grid 상한은 position당 256행이다. 관측 종료 표시 257번 행 이후 `scalp_trailing_observation_coverage_exhausted=true`이면 이후 transition은 조기 return한다. 최초 TP crossing은 그 이후에도 실제 판단 경로에서 발생하고 signal snapshot은 발급되므로, 필수 인과 증거만 빠지는 생산자 결함이다.

| record | 마지막 상세 전이 | 최초 충족 signal 시각 KST | 원천 상태 |
| --- | --- | --- | --- |
| 49328 | 08:17:24.699582 | 08:18:23.977830 | 상세 cap 소진 후 신호 |
| 49267 | 08:17:37.578886 | 08:22:37.169000 | 상세 cap 소진 후 신호 |
| 49300 | 08:17:56.011988 | 08:18:30.774000 | 재시작 뒤 해당 신호는 결손; 08:00의 다른 최초 신호는 기존 전이 36건과 연결됨 |
| 49340 | 09:03:42.773918 | 09:05:36.334011 | 상세 cap 소진 후 신호 |
| 49343 | 10:38:28.167157 | 11:23:13.585000 | 상세 cap 소진 후 신호 |

캐시는 한 번만 읽어 원 generation을 고정했다: 199,644,718 bytes, SHA `56df80b3c7b3dbdcd15dfcb1a31397ff75e424396c02603978307bc9b3f8c1db`. 19,808,881-byte의 대상 position 추출본과 더 작은 10개 원 event projection으로 재검증했다. 838MiB 이상의 당일 raw pipeline을 재전수 읽지 않았다. private evidence는 작업트리 `tmp/source-gap-final-release-20261016/{first-crossing-diagnosis,cap-exhaustion-diagnosis,frozen-five-gap-recheck}.json`에 보존한다.

## 수정과 리뷰 경계

1. 상세 grid cap/heartbeat/dedup과 별도로 `scalp_trailing_first_crossing_transition`을 기록한다. `scalp_trailing_first_crossing_source_v1`은 8KiB 이하의 원 position·BUY generation·PID·첫 시각·정책/분류기·typed pin·threshold·evaluator만 보존하며 전체 quote/context를 복사하지 않는다.
2. native latch가 새로 생성한 PID와 BUY identity만 허용한다. 과거에 적재된 latch나 다른 PID/BUY generation으로 원 증빙을 합성하지 않는다. source는 한 번 freeze하고, 기록 실패 시 1초 이상 간격·최대 3회만 재시도한다. 명시적 queue 수락만 emitted로 기록하며 예외/false는 SELL 결과나 재시도를 바꾸지 않는다.
3. 필수 receipt는 grid cap과 무관하게 소비한다. strict reader는 source SHA·identity·시계·현재 signal·PID·policy를 검증하고 기존 sampled transition과 함께 인과를 확인한다. 서로 다른 signal을 합치지 않으며, 변조/교차 BUY·PID·symbol/미래 시각/과대 body는 거부한다. sampled quote coverage나 실제 체결·경제성으로 승격하지 않는다.
4. cap 이후에도 collector checked clock이 실제 호출 순서를 유지하도록 coverage 갱신을 cap return 전으로 이동했다. native birth/ADD/restart 계약과 frozen/live 시계 역행 방지는 보존한다.
5. 원 5건의 `tp_first_crossing_transition_missing`은 유지한다. 보고서의 `source_gap_details`에 `sampled_grid_exhausted_before_signal`, 마지막 원 전이·sample limit·`historical_recovery_proven=false`를 추가한다. 과거 경고를 숨기거나 source-gap을 PASS/0원으로 바꾸지 않는다.
6. 자동 인계는 exact PREOPEN-origin/candidate source pair와 각 family의 fresh network-denied fixture에만 결속한다. 현재 선택본의 source generation도 별도 exact pair로 보존한다. 새 source adapter/consumer를 holding capability 구성에 포함하며 기존 policy/report와 source hash·선정·수량·timeout·provider 권한을 바꾸지 않는다.

## 검증과 배포 수용

초기 관련 184개, 필수 전이 producer→consumer 및 tamper/실패 회귀 193개, 최종 통합 **4,882개**가 통과했다(88.88초). 변경 Python 28개 compile, print-only parser와 diff 검사도 통과했다. 현재 checklist OPEN은 고유11개이며 stable ID/원 Acceptance를 유지했다. 리뷰 범위의 미해결 코드 finding은 없다. 배포는 fresh capability fixture와 native 동일 workload parity, 원 정책/PREOPEN hash 보존을 확인한 뒤 `ordered_intraday_deploy`로 실행한다. old PID graceful drain→selector→동일 정책 준비→새 PID 독립 검증의 원 영수증을 보존한다.

실제 실행 결과와 commit/PID는 배포 terminal 및 이 기록의 후속 항목에 추가한다. source code PASS, 배포/PID, 새 자연 crossing, 과거 5건 및 실제 비용 후 성과를 각각 구분한다. 과거 5건의 정확한 전이 원문은 이번 진단으로 생기지 않으므로 후속 detector가 같은 역사적 gap을 보고할 수 있다. 신규 자연 전이에 receipt가 생성되는지는 배포 뒤 별도 확인한다.

기존 실행 owner는 `HoldingProfitExitSourceContractRepair`, `DirectFamilyPreopenPolicyHandoff` 및 각 source-repair family다. 새 stable ID나 별도 경제성 gate는 추가하지 않는다. 실제 비용 분해, 원문 미발견 request, native forward path·모델/holdout의 기존 OPEN은 이전 인계 기록대로 보존한다.

## 실제 배포와 기동 후 보고서 검증

- 배포 commit은 `63b758ac8e98ace56e62419b677f374449fd724f`, immutable root는 `/home/ubuntu/KORStockScan-runtime-releases/source-gap-crossing-final-20261016-63b758ac8`다. 사용자 승인 범위에서 정규 `ordered_intraday_deploy`를 실행했다. 원 PID drain 12:42:42.203624 → selector 게시 12:42:42.222175 → 시작 12:43:03.894902 → 새 PID attestation 12:43:31.898090 → 독립 검증 완료 12:43:43.140264 순서로 terminal PASS다.
- 새 Main PID `3474098`, start ticks `18613546`, 실제 cwd는 위 release의 `src`다. 정책 소비 검증은 12:43:18 PASS이며 원 bootstrap JSON/env·prepared pointer의 바이트는 보존했다. 기존 Main 수량과 수동 제외 custody도 유지했다. 선택, PID, 계좌 조회는 실제 새 매매·체결·경제성의 증명이 아니다.
- 12:45 경보가 인용한 `d5c505c91c81ccc3c17dc8a183b7865debf6d653301f29b039af923af1669772` 보고서는 **기동 전 12:35:08 기준**이다. 이것을 기동 후 보고서 수용 근거로 사용한 것은 잘못이었다. 12:45 정규 holding 작업도 이전 완료 시각 기준 cooldown으로 skip됐다. 시작 순서 PASS만으로 보고서 수용을 닫지 않는다.
- 현재 selected release의 정규 wrapper를 12:48:10 실행해 12:53:49 완료했다. 새 보고서 기준 시각은 `2026-10-16T12:48:12.927626+09:00`, SHA는 `61d71cc17641a7a20708f429ad50fe806d68d3d66547c9a7c4759b7f07374d1e`, 원천 generation은 `47c6e9a107a609420a57d487ad6b349aceca1ffe7d19bd4c7538b3c5f12f5d0a`다. body/semantic 시각·generation 일치, 소비 PID 목록의 `3474098`, policy/runtime gap 빈 배열을 확인했다.
- 12:54:22 후속 full detector가 **위 새 보고서의 정확한 SHA/generation**을 native 검증했다. `native_validated=true`, `observation_complete=true`, 새 native finding은 0이다. 역사적 전이 결손 5건에는 새 `source_gap_details`가 붙었으며 원문 복구를 주장하지 않는다. 새 독립 crossing stage의 자연 event는 0이므로 새 자연 crossing 생산까지 확인됐다고 주장하지 않는다.
- 영수증은 정규 workspace의 `tmp/source-gap-final-release-deploy-20261016/{ordered-deploy-result,postrestart-identity-and-policy,postrestart-holding-native,postrestart-holding-full-detector,final-verification}.json`에 보존한다. 코드 검증의 network/provider 0은 테스트/fixture 범위의 주장이다. 정규 Main 기동 뒤 기존 운영 조회와 구분한다.

## BUY partial의 실제 검증 실패 수리

13:00 이전 BUY 보고서의 `entry_split_verification_invalid:manifest_contract`는 전일 보고서 검증 영수증의 native code hash가 `ed738295a7de91c3972c8360b655d222b26f69e4d1976b2ef27c2c0f0e660c5c`에 묶인 데서 발생했다. 현재 native hash는 `bf3c8b69f4c92270f8084bbb44373aa213af1dc94da22d91cf4cbd23e300d37f`다. source-gap 수리로 native 모듈이 바뀌었는데 배포 뒤 관측 소비자의 검증 영수증을 갱신하는 단계가 빠졌다. 기동 성공 또는 과거 PASS를 현재 소비 수용으로 대체할 수 없다.

기존 migration/변조/세대 계약 회귀 **56개 PASS** 뒤, selected release의 bounded `entry_split_monitor_projection` worker로 report alias와 immutable 원본을 모두 native 재검증했다. 원 보고서 SHA `7944f30f4717fe379a254896f434f7f97cf800a66a1f5dad5fad701d2e1ab4e5`와 generation `b659cce09505f73353d17a4fe609739db30bf656e13fbe8c24d42857cfe5470e`는 그대로다. 보고서 재계산·정책 승격·Main 재기동 없이 관측용 검증 영수증만 발급했다. 후속 reader는 `observed/verified`, issues `{}`, full report read **0 bytes**, metadata **18,606 bytes**다.

정규 13:00:52 BUY 보고서가 새 영수증을 소비했고 `execution_or_bootstrap_not_verified`와 `split_projection_not_verified`가 사라졌다. 13:01:57 full detector는 **FAIL 0건**, 프로세스/인증/크론/자원/잠금 6개 PASS, artifact WARNING이다. 근거는 `entry-split-{prior-verification,reverification}.json`, `entry-execution-reverified.json`, `post-buy-repair-full-detector.json`이다. 이전 FAIL 보고서도 삭제하지 않았다.

BUY의 `semantic_status=partial`, `warning_pending/bounded_source_quality_observation`은 여전히 실제 입력 조건을 표현한다. 12:55 기준 현재 PID의 probe 13개 중 10개가 residence 종료 시 `native_source_stale_or_absent`, 1개는 `required_branch_feature_missing`, 1개는 `route_snapshot_missing`, 1개는 검증된 native no-match다. 예를 들어 062970은 초기에 exact 0B/0D를 받았지만 종료 시 0B age 5.064초, 0D age 4.865초이며 native source current=false였다. 초기 수신 성공은 종료 시 fresh 입력의 증명이 아니다. 새 scanner 기계 평가 분모도 0이어서 전체 Main 평가 0으로 확대하지 않는다. 원천 만료/입력 부족·과거 미확정·실제 기계/보조/제출 결과는 PASS로 바꾸지 않는다. 기존 `AuxiliaryCircuitRecoveryRepair1012`, `NonfixedDispatchReadinessReview1012`의 자연 원천 수용을 유지한다.

다음 배포 수용은 코드·정책·PID와 별도로 **변경된 native verifier의 report/projection 영수증 재검증 → 기동 이후 새 보고서 → 그 SHA를 소비한 detector**까지 확인해야 한다. 이번 기록은 이 단계를 자동화했다고 주장하지 않는다.

### 13:06 최종 현재 세대 재점검

정규 13:05:45.854058 BUY 보고서에서 `unmet_conditions=[]`, `reason=recorded_guard_or_cohort_pending`, 원천 커버리지 incident=`recovered`를 확인했다. 현재 10분 probe 13개 중 9개가 검증된 native 원천 커버리지이며 current machine/source issues는 모두 `{}`다. `partial/warning_pending`은 식별된 scanner 기계 평가가 아직 없는 대기 상태로 보존하고 기계 PASS·주문·전체 자연 관측 완료를 주장하지 않는다. 이전 10개의 만료 표본은 마지막 원천이 3.029~27.998초 전인 반면 실제 packet→native 반영은 0.754~8.202ms였다. 이 표본은 수신 뒤 수초의 로컬 정체를 뒷받침하지 않는다. 원 표본/결손은 보존하며 현재 회복과 구분한다.

정규 후속 holding도 13:06:06 완료됐다. 새 기준 시각 `2026-10-16T13:00:05.562981+09:00`, SHA `04045bd4957565e6dd2504ed0d6cbdb08d39e3827200bda6af45788e331fe7e3`, generation `c55c7bd09de83eabde317e399bcc92c84089200b5a39660bcf50307ba57bcd52`를 확인한다. 현재 PID 소비와 policy/runtime gap 빈 배열을 다시 대조했다. 13:06:37 full detector가 이 holding 원문과 13:05 BUY 원문의 정확한 SHA를 소비했고 **FAIL 0건/일반 health 6개 PASS**다. 과거 holding 원천 결손 5개 및 전일 entry_cancel_wait/rising_missed policy-generation warning은 유지한다. `final-verification.json`, `holding-native-current-1300.json`, `buy-observer-current-1305.json`, `current-buy-health-full-detector.json`, `buy-native-expiry-clock-diagnosis.json`을 최종 근거로 사용한다.

## Holding 5분 39초 지연의 측정과 개선 순서

운영 보고서는 339초 걸렸다. 실행 중 단일 Python thread가 약 99% CPU를 사용했고, 두 표본 사이 `rchar=951,327,309`, `read_bytes=692,842,496`이 변하지 않은 채 CPU 시간이 증가했다. 모든 stage의 wall time을 계측한 것은 아니지만, source wait/정지 대신 반복 계산의 영향이 크다는 실행 증거다. 전체 보고서를 다시 생성하지 않고 frozen scope projection과 제한된 순수 함수 profile로 확인했다.

| 입력 | 캐시 크기 | 전체 event | 동일 시각 집계 적격 | 기존 scope 분류의 후보 거리 평가 |
| --- | ---: | ---: | ---: | ---: |
| 10/16 | 206,004,078 bytes | 35,411 | 35,375 | 103,930,542 |
| 10/15 | 478,787,144 bytes | 102,240 | 0 | 732,575,710 |

원 raw는 증분 처리됐으며 두 캐시 모두 `rebuilt=false`다. 그러나 holding reader는 `compact_index_enabled=false`, `cache_body_rescanned=true`여서 두 일자의 약 685MB를 매번 전량 decode·materialize한다. 전일 보존 event의 시각은 13:33:25~20:24:28뿐이라 12:48 동일 시각 집계는 0인데, `_partition_events_by_venue_session`에는 전일 전체가 다시 전달된다. 이것은 전일 오전 활동/완전성이 0이라는 증명이 아니다.

가장 큰 계산 결함은 위 함수의 implicit event마다 동일 record의 모든 explicit 후보에 대해 `min(abs(delta))`를 구하고 동률 후보를 찾으려고 다시 전수 순회하는 구조다. 이번 입력의 두 번 거리 계산 합계는 **836,506,252회**다. 전일 worst record 49267만 explicit 20,880 × implicit 7,485 구조다. 제한 profile에서도 `min`, generator, `timedelta.total_seconds`, `abs`가 비용의 대부분이다.

시간별 후보 인덱스·이분 검색 prototype은 같은 시각의 상충 scope와 좌우 동률을 보존한다. 10/16 worst record의 2,045개 표본은 0.249→0.013초, 전일 2,027개 표본은 0.383→0.017초였고 각 기존 함수 결과가 완전히 일치했다. 전체 scope projection의 prototype 처리 시간은 당일 0.209초/전일 0.760초다. 당일 전체 quality counts도 새 native report와 정확히 일치했다. **이것은 제한된 검색 prototype의 측정이며 운영 전체 보고서 개선율이나 배포 완료가 아니다.**

구체적인 우선순위는 다음과 같다.

1. 동일 attempt의 scope 후보를 시각별로 한 번 정렬·인덱싱해 nearest 검색을 `O(log n)`으로 바꾼다. 동률 conflict, missing, 같은 timestamp 다중 scope와 event 순서는 보존한다. 직접적인 8.37억 회 반복 제거가 최우선이다.
2. 전일 native cache의 고정 generation에 대해 verified 시간 인덱스/집계 receipt를 만들고 동일 cutoff에 필요한 범위만 재사용한다. same-time 원천 없음과 검증된 valid-empty를 구분하며 `None`/빈 집계의 기존 의미를 유지한다. 전체 native 검증을 hash 확인만으로 대체하지 않는다.
3. 현재 `event_generation(events)`를 caller와 auditor가 각각 수행한다. 동일 호출 입력의 중복 직렬화·hash를 제거하되 reader가 최종 filtered 원천 generation을 한 번 검증하도록 책임을 유지한다.
4. session·5/10/30분·각 scope 집계에서 stage별 전수 순회를 반복한다. stage/attempt 집합을 한 번 집계하고 시간창별로 재사용한다. real/probe/수동 custody와 scope 분모는 보존한다.
5. 8개 signal snapshot마다 vote ledger를 읽는 구조는 6개 position별 불변 snapshot으로 호출 내 재사용할 수 있다. 이 입력에서는 2개 position이 2번 읽혔다. 정책 ancestry 6단계의 source도 각 hash/read_text 두 번을 같은 고정 bytes 한 번으로 합칠 수 있으나, 단독 원천은 약 13.8MB여서 scope 검색보다 우선순위가 낮다.

분석 증거는 `holding-performance-analysis.json`과 두 `holding-scope-perf-projection-YYYY-MM-DD.jsonl`에 보존한다. 원 raw 재전수·추가 API·주문은 실행하지 않았다. prototype의 첫 시도에서 mixed timezone 정규화를 누락해 실패했으며, native parser와 같은 KST 정규화로 수정하고 위 일치 검증을 통과했다. 성능 개선 운영 코드는 이번 분석에서 아직 변경하지 않았다.
