# Main AI 현행축 최초 승인·성능 검증·배포 판정

후속 상태(22시): 사용자가 전체 소스 commit/push/main 통합을 선택했다. [전체 통합·재생성 handoff](2026-09-07-source-integration-review.md)가 최신 통합 owner다. 21:44 main 종료 뒤 새 측정 source 48개를 재대조해 동일 한도의 baseline 참조를 게시했고 frozen 회귀27 PASS다. 아래 20:49 당시 미게시·범위 확인 대기는 역사적 상태이며, 최초 정책 승인/기동·자연 경제성 OPEN은 그대로다. 당일 R0-R3는21:39 생성된 source-only blocked/deferred로 확인했다.

요청: 사용자의 `최초 승인·새 소스 세대 성능 검증·배포` 지시. 앞선 구현 전용 범위와 달리 이번에는 승인 조건 확인·현재 source 성능 측정·조건을 통과한 배포까지 요청받았다. 재시작/승인 artifact를 이미 발행한 것으로 기록하지 않는다.

## 판정

- 합성 성능 preflight와 현재 소스 48개 hash 재검증은 PASS다. 기존 callback p95 1ms/p99 2ms 한도와 canary stop 규칙은 그대로다. 새 측정 결과와 prospective baseline/guard를 별도 보존했다.
- 최초 승인 지시는 접수했으나 승인 artifact에 결속할 유효 exact R3 후보가 없다. 최신 완료 source-date 9/4의 candidate0, cycle source-quality/custody BLOCK을 확인했다. 9/7 R0/R2/R3는 점검 시 아직 장후 선행 작업 실행 중으로 미생성(`not_yet_produced`)이며 실패나 최종0으로 단정하지 않는다. unknown 후보를 승인하거나 source/economic gate를 면제하지 않는다.
- 20:10 시작 장후 wrapper PID895257이 봇을 `POSTCLOSE_BOT_ACTION=stop`으로 정지한 채 실행 중이다. 이 세대를 중단·변경하거나 봇을 먼저 시작하지 않았다. 운영 guard/config·runtime enable·등록·승인·activation 파일도 바꾸지 않았다.
- 배포 대상 외 daily-threshold/WAIT6579/EV/PREOPEN 변경이 함께 미커밋 상태다. `src/run_bot.sh`는 `src/deploy` 변경이 남으면 `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=true`로 기록하므로 Main AI 일부 commit만으로 현재 workspace의 clean deployment를 주장할 수 없다. 전체 통합 검증·commit 또는 Main AI 분리 배포의 범위를 사용자에게 확인 중이다. 미검토 변경을 포함한 재기동은 수행하지 않았다.

## 성능 증거

기존 `run_callback_latency_preflight(iterations=5000,warmup=500,repeats=5)`를 재사용했다. `MAIN_AI_CURRENT_AXIS_ENABLED` OFF/ON은 **폐기되는 검사 child process 안에서만** 설정했으며 운영 env를 수정하지 않았다. CPU0 affinity/nice15, 장후 chain 동시 실행 환경을 명시했다. 시장 주문·Provider·실시간 구독을 만들지 않고 임시 디렉터리의 합성 collector를 정상 close했다.

| 측정 | 결과 | 해석 |
| --- | --- | --- |
| 0B callback, 기능 OFF | internal p95 최대0.025672ms / p99 최대0.037266ms | 기존1ms/2ms 이하 |
| 0B callback, 기능 ON | internal p95 최대0.023219ms / p99 최대0.035517ms | 기존1ms/2ms 이하; 미세한 차이를 성능 개선율로 주장하지 않음 |
| 0B 손실/오류 | 각 모드5,000×5, queue drop0/worker error0 | 합성 ingress 무손실 |
| canonical causal input 준비 | warmup5 뒤50회, p99 3.540855ms / max3.561761ms | 고정 fixture의 입력 준비만 측정; 실제 R2/R3 파일 I/O·Provider 지연은 별도 |
| normalized source copy | 24,001행×20회, p99 86.573561ms / max90.416301ms | copying과 callback mutex 분리 검증 보조; 실제 장중 부하 acceptance 아님 |
| scope eviction | 300개 신규 scope 뒤256 scopes/768 rows | 256scope/60,000row 상한 검증 |
| 0D callback, 기능 ON | 5,000회, internal p95 0.034630ms / p99 0.059456ms | depth는 진단값이며 신규 latency veto를 만들지 않음 |
| 0D 무손실 | OFF/ON 각 enqueue=processed=persisted=5,000, queue/worker/writer error0 | read-only buffer의 depth worker 연결 포함 |

측정 receipt:

- [0B·입력·buffer 성능 및 source hashes](2026-09-07-main-ai-current-axis-performance-preflight.json.txt), content SHA `a51177f821f2534443736eac0a2126b6cbb3d86c8bed28e5acfb731bc5ac2770`.
- [0D depth 성능](2026-09-07-main-ai-current-axis-depth-preflight.json.txt), content SHA `1d602514f1e622d5051b842662786f51f41212f5eff0b91a4050d3a0d2c4a2ba`.
- [새 측정 baseline](2026-09-07-scalp-micro-reversion-callback-latency-baseline-current-axis.json.txt)과 [prospective guard](2026-09-07-main-ai-current-axis-prospective-canary-guard.toml.txt). 현재 `configs/scalp_micro_reversion_canary_guard.toml`은 변경하지 않았다. 측정 당시 active guard hash와 향후 게시할 동일 한도의 guard hash를 구분한다.

## 리뷰·검증 및 남은 순서

관련 Main AI/current collector/canary 회귀는 123 PASS다. active config가 아직 참조하는 8/13 frozen source hash 검증1건은 명시 제외했으며 해결했다고 표시하지 않는다. prospective guard의 schema/ID/한도·새 측정 source hash·receipt 자기해시와 연결은 별도 검사했다. JSON 숫자 표현이 바뀌어 자기해시가 달라지는 보존 결함을 재검토에서 발견하여, 수치를 재계산하지 않고 원 Python JSON 직렬화 byte 표현을 보존한 뒤 재검증했다. 과거8/13 baseline 측정값·hash를 덮어쓰지 않는다.

20:49 최종 재검증: 측정 receipt 자기해시2개·현재 source hash48개·depth fixture hash·prospective frozen 계약/한도·baseline 연결 PASS, git diff --check 및 checklist print-only parser PASS(51 OPEN). 운영 current-axis 디렉터리는 여전히 없고 장후 wrapper PID895257은 실행 중이다. 검토한 새 증거 보존·연결 범위의 미해결 finding은 0이며 active frozen 연결·정책 승인·배포 gate를 완료로 바꾸지 않는다.

다음 실행 owner는 기존 `MainAICurrentAxisActivationReadiness0908`다.

1. 실행 중 장후 chain의 마지막 consumer/terminal 완료를 확인한다. 그 전 source/config 교체·재기동을 하지 않는다.
2. 확정된 배포 범위의 변경을 함께 리뷰/검증하고 local commit을 만든다. 실제 기동 전 `src/deploy` clean generation을 확인한다. 다른 사용자의 미커밋 변경을 폐기·되돌려 clean 상태를 만들지 않는다.
3. 게시 직전 측정48개 source hash를 재확인한다. 변경됐으면 해당 성능 검증을 다시 하고, 동일하면 prospective guard를 한도 불변으로 게시·frozen hash 회귀를 다시 닫는다. 새 측정 artifact 자체는 live approval이 아니다.
4. 유효 full R3 후보·실제 prompt/parser/cost scope가 식별될 때만 사용자 지시와 exact hash를 결속한 최초 승인/등록을 작성한다. 아직 정해지지 않은 prompt·cohort·유효기간·renewal을 임의 승인하지 않는다. 최초 승인 없이 family flag만 켜지 않는다.
5. 승인된 기동 창/운영 정지 owner, current broker/custody 및 clean commit을 확인한 뒤 표준 launcher/graceful 경로로 배포한다. 현재 postclose가 제거한 supervisor를 `restart.flag`만으로 재기동했다고 주장하지 않는다. 새 PID의 env/hash/WS/source barrier와 자연 요청 receipt, #76/#82 경제성은 각각 확인한다.

이번 턴의 성능 PASS는 합성 소스 preflight이며 최초 정책 승인, 운영 guard 게시, runtime 배포, 자연 주문·실수익 acceptance는 완료 판정이 아니다.
