# 9/10 v10 격리 평가·재평가 지연 후속 실행 리뷰

## 범위와 판정

사용자의 “지금 수행해야 하는 다음액션 실행하고 코드리뷰”에 따라 [직전 리뷰](2026-09-10-entry-micro-recovery-automation-review.md)의 우선 작업인 v10 후보 준비와 재평가 지연 경로를 수행한다. micro-only 일반 수량 승격·NXT 장전/정규장 확장은 이 기록으로 완료 처리하지 않는다. 운영 중인 v9 산출물, 당일 activation, PID375167 및 다른 세션의 위젯/에피소드 변경은 보존한다.

현재 소스의 코드 리뷰와 격리 평가, 실제 적용, 자연 체결/비용후 이익은 각각 독립 판정이다. 새 후보를 준비했다는 사실로 기존 승인 파일을 덮어쓰거나 프로세스를 재기동하지 않는다.

## 수정과 재리뷰

| 지점 | 수정 / 검증 |
| --- | --- |
| 재평가 hot path에서 첫 예산 조회가 전체 당일 pipeline을 동기 bootstrap | `entry_recheck_submit_budget.observe_nonblocking` 추가. 기존 atomic ledger는 잠금 대기 없이 advisory read하고, 없으면 단일 background worker가 원 계약으로 복구한다. 최종 locked reservation은 그대로다. |
| 잠금/복구 지연 중 과거 quote가 낡음 | 예산 조회를 quote refresh 앞으로 이동하고 budget/refresh/features/micro-and-cap 경과시간을 분리 계측한다. 최종 freshness는 실제 결정 시점에서 계속 재검사한다. |
| 비동기 복구 대기가 곧바로 180초 AI-WAIT cooldown으로 전이할 수 있음 | `bootstrap_pending`을 손상과 분리한다. 선택된 scope·유효 WAIT/probe·probe-first·freshness·DANGER/source safety를 통과한 경우에만 기존 finite pending window에서 재관측하며 submit 권한은 없다. pending TTL은 늘리지 않았다. |
| 결손 예산을 in-memory 0처럼 표시할 위험 | 관측 count는 null로 남기고 pending/failed/invalid 상태를 구분한다. 실패한 같은 bootstrap을 매 tick 재시도하거나 손상 ledger를 초기화하지 않는다. |

`reserved`/unknown broker outcome은 계속 quota를 차지하며 definitive rejection만 기존 계약으로 해제한다. 동시 reservation cap, 실제 수량, broker API, provider route, hard/protect/emergency guard와 operator lock은 변경하지 않았다.

09:15 강동씨앤엘 refresh25.368ms→결정53,932ms/heavy64.072초의 실제 내부 구간별 원인은 당시 계측이 없어 확정하지 않는다. 이번에는 전체 로그 scan/lock wait가 live thread에 놓인 재현 가능한 구조를 제거했다. 당시 53.9초 전부가 bootstrap 때문이라고 주장하거나, 아직 재기동하지 않은 PID에서 지연 개선이 검증됐다고 표시하지 않는다.

## 비용후 label 0의 직접 근거

source9/9 bridge는 trace277, paired eligible24, mature eligible47, net-economic eligible0, current exact source0이다. 관련 93행의 liquidity-capacity blocker는 다음과 같다. 이 수는 중복 제거된 독립 거래 수가 아니다.

- `same_epoch_past_depth_missing`: 33행
- `depth_row_stale`: 33행
- `market_depth_bbo_conflict_capacity_unavailable`: 27행

이 때문에 반사실 수량과 snapshot execution basis도 없으며 action-neutral materialization0 → label artifact 없음으로 이어진다. 이미 mature인 mark-price 결과만으로 executable depth와 비용을 합성하지 않는다. 이 원천은 현재 자료만 반복 재생해서 복구할 수 없다. 새로운 exact quote/depth/route/epoch와 비용/master가 있는 표본을 기존 producer가 소비해야 한다. 원본 bridge와 과거 hash는 변경하지 않았다.

## 격리 v10 실행

- staging: `/tmp/kss-entry-v10-stage-4m6XWX`; 기존 batch/control/detailed/candidate 생산자만 사용한다. output path를 staging 안으로 제한하며 운영 report/candidate/activation 경로 쓰기를 거부한다.
- source date9/9, 현재 as-of, predecessor gate 유지, 두 등록 cohort 각각 최대30 신규 평가·worker2·timeout45초, batch1회다. 상한 증액과 무한 retry는 없다.
- forward market은 보존된 pipeline과 기존 same-date/same-trace outcome recovery만 사용한다. 새 Kiwoom 조회/주문 없이 exact payload를 원천에서 구성하며 v9 판단을 v10 결과로 재라벨하지 않는다.
- KRX 완료 시점: evidencev10/composerv11, prepared58 중 신규30 평가, provider failure0/none0, WAIT26/DROP4/BUY0, probe intent21건/18종목. full-cost verified0, net EV null이며 일반 수량 승격 근거가 아니다.
- staging 산출물은 설치된 정책이나 현재 PID 소비 receipt가 아니다.

### 최종 실행 결과 (10:30:34~10:34:16 KST)

| cohort | 신규 평가 / 실제 Provider attempts | 유효 판단 | probe intent | 후보 판정 |
| --- | --- | --- | --- | --- |
| KRX/KRX_REGULAR | 30 / 30 | WAIT26·DROP4·BUY0 | 21건 / 18종목 | `bounded_exploration_apply_ready`, 1주 탐색만, 유효일9/11 |
| NXT/NXT_AFTERMARKET | 30 / 33 | WAIT21·DROP8·BUY0, 의미 검증 탈락1 | 12건 / 8종목 | `blocked`, `detailed_promotion_integrity_not_passed` |

transport failure/`provider=none`는 양쪽0이다. 기존 내부 retry를 포함한 실제 Provider attempts는63이며 신규 평가 parent는60이다. 이를 60회 호출 또는 60개 독립 거래로 혼동하지 않는다. batch 추가 재실행 없음.

NXT 탈락 trace=`analyze_target:484870:1788937984803:4b124ba3`, 오류=`entry_risk_unfounded_insufficient`: 사용 가능한 ledger에 모델이 `INSUFFICIENT/SOURCE_QUALITY_GAP`을 반환했다. parser가 올바르게 거부했으며 임의 CAUTION/BUY 변환, 오류행 삭제 후 전체 PASS 또는 반복 호출로 성공 결과만 선택하지 않았다. 이는 남은 Provider 판단/의미 계약 실패이며 정상 생성/적용 완료라고 표시하지 않는다.

KRX candidate artifact hash=`315550104afd19f7ef34864067b7d7bb52491fd4a1efb81e26f2c3dc3b495d0e`. 새 결과만으로 초기10 arms/3종목 floor를 통과했고 이전 v9 누적 성과를 섞지 않았다. 두 cohort 모두 full-cost verified0, 실제 노출/체결0이다. 일반 수량 승격 또는 순이익 개선 근거는 없다.

### Activation 사전 검증 / 운영 보존

`activation-preflight.json`은 staging에만 기록했다. 9/11 KRX candidate 자체의 runtime contract 오류0이다. 하지만 9/10에는 effective-date candidate가 없고, 9/11 PREOPEN env는 아직 생성 전이므로 실제 env 기반 activation은 둘 다 inactive다. 다음 날짜 파일 미생성은 현재 시각의 `not_yet_due`이며 기존 recheck/scope/date 검증을 제거할 이유가 아니다.

현재 staging은 자동 PREOPEN 검색 경로가 아니다. 오늘 운영 중인 source9/9 v9 report/candidate를 덮어쓰면 기존 승인 lineage가 깨질 수 있어, 새 후보를 canonical 경로에 설치하지 않았다. 오늘21:05 자연 source9/10 평가와 다음 유효 PREOPEN에서 새 정식 후보·scope·activation을 별도로 확인해야 한다. 오늘 장중 적용을 요구하는 경우에는 exact 당일 예외 적용 artifact와 안전한 deployment handoff가 추가로 필요하며, 유효일을 소급하거나 재기동만 실행해서는 안 된다.

실행 전후 canonical v9 detailed2개·batch·candidate·9/10 activation의 SHA256 5개 모두 동일하다. 10:39:31 PID375167(08:45:53 시작) 유지. 격리 산출물 크기3.1MiB이며 복구 근거로 보존한다. 운영 Provider route/env/정책/서비스/주문 변경 없음.

## 검증

`korstockscan-review-gate`에 따라 bootstrap 생산자→호가 준비→재평가 guard→finite pending→최종 reserve/settle과 BUY Funnel reason 소비를 재검토했다. 부정 반례는 손상 ledger, 중복 worker, 날짜 전환, writer lock, 동시 cap, pending 중 stale/DANGER/다른 scope/DROP/비정상 probe, 기존 pending TTL을 포함한다.

관련 7개 test module 최종 **1,616 PASS / 40.11초**. 두 기존 multiprocessing fork 경고가 있으며 테스트 실패는 없다. compile·Black·변경 보조 Python/test Ruff·`git diff --check`를 확인했다. 테스트 추가 중 import 누락은 수정 후 통합 실행으로 재검증했다. 후속 리뷰에서 unavailable ledger의 basis도 in-memory가 아닌 `unavailable_ledger`로 수정했고 실제 background bootstrap이 과거 주문을 보존한 뒤 ready가 되는 회귀 테스트를 추가했다. 이전 중간 실행 수는 합산하지 않는다.

수정한 예산/재평가 코드 범위의 미해결 review finding0이다. 이것은 NXT 의미 검증 탈락1, 원천 depth/cost 결손, 배포 및 실제 매매 경제성 acceptance까지 닫았다는 뜻이 아니다.

## 다음 acceptance owner

기존 `RuntimeEnvIntradayObserve0910`가 새 코드/정책/date/scope/PID와 자연 recheck→submit→fill→terminal/net을, `MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0910`가 새로운 exact depth/cost 교집합과 v10 후보를 계속 소유한다. 별도 OPEN ID를 중복 생성하지 않는다. Project/Calendar sync, commit/push, 서비스 재기동, 운영 env/activation 변경은 이번 실행 범위에 포함하지 않는다.

## 후속 커밋 리뷰와 조건부 재기동 판정

후속 사용자 요청은 코드리뷰·수정보완·커밋/푸시/main 반영 및 **코드·정책 일치 검증 후 필요한 우아한 재기동**이다. 위 절의 미실행 기록은 이전 실행에 해당한다. 이번 변경 범위는 예산/재평가 Python 5개 파일과 이 리뷰·기존 체크리스트의 해당 후속 기록이다. 병행 위젯/에피소드/WS/체결 ACK·경제성 변경은 이 커밋과 전체 배포 승인에 섞지 않는다.

재리뷰에서 예산 bootstrap 대기의 TTL 만료가 `recovery_micro_pending_expired`로 잘못 귀속되는 결함을 발견했다. 실제 blocking reason으로 pending/expired 상태를 선택하는 공통 helper를 사용해 즉시 평가와 다음 WATCHING tick의 두 만료 경로를 모두 보완한다. `submit_budget_bootstrap_pending_expired`도 최초 만료 로그에 포함한다. 기존 finite TTL, 종료 후 cooldown, source/freshness/수량 및 최종 locked reservation은 유지한다. 이 수정은 기다림의 원인 계측이지 대기 연장이나 주문 허용이 아니다.

11:19:10 KST 읽기 전용 실계약 검증은 PID375167의 KORSTOCKSCAN env만 새 코드 resolver에 전달했다. KRX/KRX_REGULAR/SCANNER 결과는 `enabled=false`, `status=fallback_activation_contract_invalid`, `selected_prompt_version=decision_quality_v2_13_recovery_confirmation_probe`, `runtime_effect=false`다. 현재 activation은 evidence v9/composer v8, 새 코드는 evidence v10/composer v11이므로 요청된 코드·정책 일치 조건을 통과하지 못했다. 9/11 격리 후보를 9/10으로 소급하거나 운영 hash를 덮어쓰지 않는다.

따라서 재기동은 **불필요 판정이 아니라 사전조건 실패로 보류**한다. 현재 PID와 당일 activation을 유지하며 restart flag, 서비스/PID, 정책/env 및 broker 주문을 변경하지 않는다. 첫 코드·정책 gate에서 중단하므로 broker 계좌/미체결의 재기동용 신규 대사는 수행하지 않았고 custody preflight PASS를 주장하지 않는다. 다음 허용된 배포는 정식 exact-date 후보/activation, 검토된 고정 코드 세대, owner별 최신 broker 대사 후 진행해야 한다. 조건부 재기동 승인은 유지되지만 초기 탐색에 일반 수량 승격/양수 EV의 추가 floor를 요구하는 것은 아니다.

최종 검증은 HEAD에 이번 7개 파일만 반영한 index tree를 격리 추출해 수행했다. 관련 7개 모듈 **1,621 PASS / 27.13초**, 기존 multiprocessing fork 경고2건이다. 초기 새 테스트의 formatter 줄바꿈 의존 단언을 수정한 뒤 전체 격리 검증을 다시 통과했다. compile·Black 포맷·보조 Python/test 4개 Ruff·index/working-tree `git diff --check` PASS, print-only parser28건/기존 두 owner 각각1회다. 1,616 및 중간 실행 횟수와 합산하지 않는다. 직접 producer/consumer 재리뷰의 미해결 in-scope finding0이며, 병행 변경이나 실제 경제성·배포까지 승인한 결과는 아니다.

커밋 범위는 Python5+본 리뷰+체크리스트의 이 세션 후속3행, 총7파일이다. 체크리스트의 다른 세션 이력은 index에 섞지 않고 working tree에 보존했다. 시작 branch는 main, fetch 후 HEAD/origin/main 차이0/0이므로 별도 가짜 merge commit 대신 현재 main에 직접 반영한다. commit/push 실행 결과의 SHA와 원격 일치는 최종 응답에서 보고한다. 신규 Provider 평가·비싼 report 재생·외부 Project/Calendar 동기화는 실행하지 않는다.

최종 사전 확인에서도 PID375167(08:45:53 시작)은 유지됐다. 운영 activation 파일 SHA256=`ec54cd12996886c258b34d09336e22bc7fa971ee34d34a0212cfd1e810201922`, source9/9 운영 candidate 파일 SHA256=`ed8193ee5cd0a07875d07c8d5fcbbd9a998facde82d415991773032d67eb093a`로 이전 실행과 같다. 재기동 및 새 코드의 장중 지연/체결 개선은 미적용·미검증이다.
