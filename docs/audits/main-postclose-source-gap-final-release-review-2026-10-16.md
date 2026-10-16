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
