# Main 손절 연구 실행·원천 계약 수리 검토 — 2026-10-18

## 범위와 실행 신원

사용자 `연구실행` 지시에 따라 [실행안 §12](../proposals/main-stop-loss-retirement-runtime-policy-and-postclose-tuning-plan-2026-10-10.md#12-2026-10-18-상세-연구-실행안과-원천-계약)의 첫 유한 연구와 실행에 필요한 격리 코드 수리를 수행했다. **R1 역사 연구·이번 변경의 검증은 완료, 전체 정책화/원천 수리와 운영 적용은 미완료**다. 현재 실행 owner는 [MainStopResearchExecution1018](../checklists/2026-10-18-stage2-todo-checklist.md)이며 아래 잔여 계약을 OPEN으로 유지한다.

- 연구 원천일 `2026-10-16`, 기존 준비 대상 `2026-10-19`; 과거 관측은 실제 등록 시각을 유지하는 `historical_report_only`다.
- 구현 격리본: `/home/ubuntu/KORStockScan-worktrees/main-stop-research-20261018`, branch `codex/main-stop-research-20261018`, 출발 commit `7c241ea21619ce3153f1a338f1b846b0313a894f`.
- 선택 릴리스: `quantity-broker-cost-monitor-20261018-900234d79` / `900234d791b0bf31797cd4e823d0ae40296f790b`. selector의 `actual_pid_consumed=false`는 연구 결과와 별개다.
- 원 보고서: [10/16 Main stop research](../../data/report/main_stop_confirmation/main_stop_research_2026-10-16.json), semantic SHA `9fae4881ce24567043b410209539769c4d031c0241da79d5f685ce57527cd3b5`, source inventory SHA `51de140c4b7dbd3777d7c5c4cbb1274526afdedc7e841a92f102f49be0365510`.
- 정책·bootstrap·selector·원본 원장/관측/비용을 변경하는 실행은 하지 않는다. 증거와 캐시는 [전용 실행 디렉터리](../../tmp/main-stop-research-20261018)에 둔다. 외부 API·구독·주문·배포·Main 재기동·외부 동기화는 실행하지 않는다.

## 원천 전수 처리와 식별 가능한 범위 격리

원 보고서가 사용한 실제 14개 물리 파일, 총 `12,094,426,218`바이트를 동일 SHA로 검증했다. 원래 행 단위 2MiB resident 제한은 유지한다. 큰 행은 128MiB 디스크 예약 안에서 spool하고 완전한 JSON 구조·중복 key·문자 escape·수치·전체 종료를 검증한다. 문서 안 stage 문자열만 보고 제외하지 않는다. stop 입력 필드가 섞인 행이나 미식별/불량 행은 계속 결손이다.

| 실제 실행 | 큰 행 / 검증된 무관 행 / 미식별 | wall / CPU / peak RSS | 판정 |
| --- | --- | --- | --- |
| attempt-01 | 2,521 / 1,603 / 918 | 371.645초 / 334.180초 / 45,464KiB | 정상 entry snapshot의 455~497개 필드가 공용 256-key 제한에 걸림. 이 실행과 코드 원문을 보존 |
| attempt-02 | 2,521 / 2,521 / 0 | 378.226초 / 340.949초 / 45,192KiB | 공유 active key 64KiB·object 1,024-key·깊이 제한 안에서 전수 재검증 |

최종 무관 행은 `entry_ai_economic_plan_observed` 1,603개, `scalp_entry_action_decision_snapshot` 918개다. 총 `8,547,677,964`바이트를 검증해 범위에서 분리했고 실제 stop 입력 `56,980`개를 보존했다. unbound handoff 1개와 release 4개도 별도 census로 남겼다. 퇴역 기능의 새 생산/튜닝을 복구한 것이 아니라 혼합 역사 로그의 읽기 범위를 검증한 것이다.

[attempt-01 receipt](../../tmp/main-stop-research-20261018/attempt-01/cold_index_measurement.json), [attempt-02 receipt](../../tmp/main-stop-research-20261018/attempt-02/cold_index_measurement.json)는 각 실행 전후 동일한 decoder 3개 hash를 결속한다. 각 `decoder_evidence/`에 실제 실행 코드와 명령 스크립트를 보존했다. 원문 로그를 삭제하거나 불량 stop 자료를 정상으로 바꾸지 않았다.

### 첫 재생 중단과 세대 재고정

첫 실제 재생 PID1083988의 시작 뒤 최종 리뷰에서 체결 시각의 whole-second 표현 허용을 subsecond 원시 시각에도 적용하는 결함을 보완했다. 실행 중 `main_stop_replay.py` 세대가 바뀐 시도는 수용하지 않았다. SIGINT와 exit130·PID 소멸을 확인하고 [interruption receipt](../../tmp/main-stop-research-20261018/attempt-02/interruption_receipt.json), 원 input receipt·부분 shard/캐시·로그·원 progress bytes를 보존했다. 성공 report와 정책은 발행하지 않았다. 이때의 589 PASS 회귀도 최종 동일 코드 세대 수용과 분리한다.

같은 리뷰에서 preset 상한가의 이른 dispatch와 일반 상한가의 `is_sell_signal`이 trailing 관측을 건너뛰는 producer 결손을 추가 확인했다. 현재 평가의 기존 검증 quote를 공통 context builder에 연결하되 새 시세 요청/파일 I/O 없이 기존 sink를 사용하도록 보완했다. 원천 관측 실패는 기존 안전 청산을 차단하지 않는다. runner도 KeyboardInterrupt를 봉인 실패·incomplete progress로 남긴 뒤 재발생시키도록 수정하고 중단→자원 반환→같은 의존성 캐시 재개를 시험했다.

첫 성공 attempt-03은 [복사 검증 영수증](../../tmp/main-stop-research-20261018/attempt-03/cache_reuse_receipt.json)에 따라 동일 decoder의 source index110파일/19,562,349바이트만 재사용했다. 중단 시도의 가격 재생 결과는 복사하지 않았다. 새 input/code generation으로 다시 검증했으며 성공/실패 세대와 성능 분모를 섞지 않았다. 최종04도 같은 검증된 source index를 재사용하고 가격 재생을 다시 수행했다.

## 구현·독립 리뷰에서 확인한 계약

수정의 소유 경계는 순수 판단/재생 `scalping`, 비용/보존 `lifecycle`, 장후 실행/manifest `automation`, 기존 runtime adapter `sniper_state_handlers.py`, 시험 `src/tests`다. `src/engine` root 신규 Python 모듈을 만들지 않는다.

1. **실험 등록과 원천 봉인:** 관측 전 가설·cell·부모·코드·후보 grid·split/embargo를 등록하고 cutoff 뒤 실제 원천을 별도로 봉인한다. 과거 연구의 등록 시각을 소급하지 않으며 역사 모드는 실제 정책 선정 consumer가 거부한다. 등록된 grid·cell·실제 관측 범위를 정상 publisher가 다시 검증한다.
2. **상태와 재생 도달성:** preset 안전선 미발화 시 일반 손절 평가로 진행한다. 표본/검열/오차 조건 미충족은 `hold_sample`이며 `hold_no_edge`로 바꾸지 않는다. ADD 비용 `known_at`의 aware ISO/epoch를 실제 생산 형식에 맞추고 미래/naive/비유한 시각을 거부한다.
3. **비용:** 원본 완료 snapshot과 후행 공식 비용을 독립 세대로 검증한다. per-fill exact, whole-position exact total, broker total allocated를 나누고 manual·잔량·중복/충돌 원천을 별도 상태로 남긴다. canonical PnL과 runtime 정책 권한은 없다. 새 공식 비용만 도착한 경우도 원본 snapshot 재생성 없이 재대사하도록 리뷰에서 보완했다.
4. **정상 청산 결과:** 정상 trailing/상한가 결정의 원본 quote·pin·position을 기존 source capture owner에 연결한다. 결정 자체와 실제 주문/체결/완료는 별도 증명이다. 완료 뒤 flat의 automatic-management flag를 과거 결정시점의 권한으로 오인하지 않는다. 실제 원본 결정행이 있을 때만 해당 prefix를 사용하며 뒤쪽 주문/체결 대기 행은 제외 census로 보존한다. 시각/가격 보간이나 가상 체결은 없다.
5. **성능과 재개:** index·가격 재생과 후행 비용 overlay의 무효화 경계를 나눈다. position 증거는 bounded tree로 쓰고 report 예시는 최대16개다. 4시간 stage·durable2GiB/temporary2GiB·공유 resident64MiB admission, 실패 영수증·동시 실행 lock·완료 결과 덮어쓰기 금지를 유지한다. 실제 cold/warm·가격 재생·비용·순수 판단을 측정한다.

실제 완료 census9건의 엄격 비용 재검증은 broker total allocated4건(49351/49347/49343/49340), 수동49345 검열1건, 원본 중복 매도 체결 및 exact-cost 결손4건(49267/49294/49300/49328)이다. exact execution/whole-position 적격은0건이다. 이전 수량 연구의 비용 receipt8건 수용을 이번 손절 연구8건 적격으로 옮기지 않는다. 공유 resident admission2,109,752바이트와 종료 후 반환·원천 불변을 확인했다. 네 비용 적격의 역사 연구 net932/435/174/1410원은 신규 손절 정책의 수익 또는 paired uplift가 아니다.

원본 완료·가격 원천이 손상되었거나 확보 불가한 구간은 새 계약을 만들었다는 이유로 재라벨하지 않는다. 공식 Kiwoom upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`와 상세 원천 mapping은 실행안 §12의 확인 근거를 재사용한다. 이번 수리는 REST/WS 요청·FID·인증·continuation·주문 프로토콜을 바꾸지 않는다.

### 순수 판단 비교의 실제 범위

[순수 판단 비교](../../tmp/main-stop-research-20261018/pure-decision-comparison.json)는 같은 CPU3에서 각 arm5회×20,000회의 soft/protect 호출을 순차 측정했다. 측정 함수 원문과 판단 결과 hash가 같았다. trial median의 p95는 기존11,193ns/후보11,127ns, p99는16,358ns/15,814ns였다. max는45,776ns/87,696ns로 잡음과 극단 지연 차이를 보존한다. 함수가 같은 이 작은 비교를 알고리즘 성능 개선이나 full Main/capture의 비악화 승인으로 해석하지 않는다.

첫 동시·비고정 CPU 측정과 CPU metadata 변수를 타이머 변수로 덮어쓴 초기 측정은 원 bytes를 보존하고 비교 receipt의 제외 사유에 기록했다. 수정한 v2 arm만 위 수치에 사용했다. 실제 장후 성능은 별도 성공 실행 receipt로 측정한다.

## 잔여 수용의 경계

### R1에서 확인한 도달성과 evaluator 결손

실제15개는 모두 `SCALP_PRESET_TP`이며 REGULAR9개·INTEGRATED_AFTERMARKET6개다. 기록된 각 포지션의 최소 decision profit은 -1.89~-0.42%였고 부모 soft -3%의 **관측 교차는0**이다. 관측하지 못한 구간까지 교차 부재를 증명하거나 유예 효과를0으로 추정하지 않는다. native preset handoff는4개(49347/49350/49328/49267)이며3개 등록·49347은 이후 해제다. SELL4건이나 손절 완료15건으로 세지 않는다.

공통 유예를 이 모집단에서 계속 탐색하는 데는 두 가지 구조적 한계가 있다.

- 현재 normal·nonlegacy preset -1.4%/비상-2.4%·동일 가격/평가시점이 유지되면 soft 후보 최대-2.5% 및 부모-3% 전에 preset 분기가 종료된다. 그 조건의 grace0/15/30/45/60 축은 비도달이며 손절 표본 증가로 해결되지 않는다. preset 기준선은 공통 hard-5%와 다르고 현 `TUNABLE`에 없다. 별도 정책 소유권·producer/consumer·우선순위/승계 계약 없이 임의 완화하지 않는다.
- 공유 `main_stop_source_at` 1초 throttle은 fast_prearm/fast/normal을 구분하지 않는다. 일반 evaluator/실제 판단 owner·평가세대 필드는 source row와 index 식별자에 없고 preset nested receipt에만 evaluator가 있다. fast_prearm의 `enabled=False`와 별도 normal의 활성 preset handoff는 동시에 가능하다. `effective_preset`은 마지막 관측 receipt이며 전체 포지션의 normal 정책 상태가 아니다. 미래 적격 표본이 생겨도 fast 관측 시각을 normal soft 판단 시각으로 간주해 선정하지 않도록 공통 원천·지원 scope 계약을 먼저 닫아야 한다.

`HoldingProfitExitSourceContractRepair`는 기존 공유 호가에 실제 판단 시점의 작은 receipt를 결속하고 owner/시각/가격/수량·정책 세대를 생산해야 한다. fast→normal 호출 순서를 바꿔도 normal 원천이 누락되지 않고 가상 soft 평가가 생기지 않는 반례가 종료 시험이다. 원시 호가를 evaluator별로 무제한 복제하는 설계는 피한다. `MainStopResearchExecution1018`는 실험 전 cell/후보별 `표본 부족 / 원천 미지원 / 선행 경로로 비도달`을 분리하고 실제 soft owner가 입증되는 cell부터 다음 연구를 진행한다. 이는 이번 R1로 발굴한 잔여 구조 결손이며 완료나 자연 표본 대기로 처리하지 않는다.

`entry_partial_fill_deferred_notice`는 알림 상태이며 완전한 BUY/cancel terminal 증명이 아니다. 기존 역사 source의 `partial_fill=bool(notice)`를 임의 False로 바꾸지 않는다. 앞으로의 일반적인 부분체결/취소/재기동 자료를 경제 비교에 넣으려면 현재 position 수량 세대와 전체 BUY leg terminal을 봉인하는 공통 원천 수리가 필요하다. 종료되지 않은 주문 map의 900초 소멸이나 `FULL_FILL` 표시만으로 이를 증명하지 않는다.

보호 가격선은 현재 Main 활성 generator가 확인되지 않았다. 기존 DB 숫자/퇴역 PYRAMID/수동 보호선을 신규 정책 표본으로 채택하지 않는다. 신규 generator·arm/monotonicity·승계 계약이 없는 상태에서 보호 확인 파라미터의 경제 개선을 주장하지 않는다. 전체 Main/capture 경로의 지연 비악화도 순수 판단 microbenchmark만으로 PASS 처리하지 않는다.

새 비용 adapter의 allocated/whole-position 등급은 offline 연구에서 분리 소비한다. 정상 `post.publish`의 기존 exact 비용 기반 선정 계약을 그 자료로 교체하지 않았다. allocated 등급을 정규 선정에 연결할 grade별 통계/승인 계약과 `runtime_and_postclose` full Main/capture 성능 PASS의 실측 생산자는 잔여 구현이다. prospective manifest 생산자 연결이나 gate fixture의 PASS를 이 두 결손의 해결로 세지 않는다.

공통 보유·ADD/수량·manual/preset 원천 및 자연 수용은 [10/19 HoldingProfitExitSourceContractRepair](../checklists/2026-10-19-stage2-todo-checklist.md), 실제 PREOPEN/PID 소비는 같은 날 `DirectFamilyPreopenPolicyHandoff`가 계속 소유한다. stop 고유 실험·비용 소비·성능 생산/인계의 잔여 구현은 현재 `MainStopResearchExecution1018`에 유지한다. 단순한 손절 건수 축적 대기로 이관하지 않는다.

## 최종 실행·검증

최종 코드 commit은 격리 branch의 `ad7cb200e0915f917326a644fe112d4ca5fe2120`다. 최초 수리 `bf4117c07`와 성능 후속을 Git에 보존했다. [코드 검토 종결](../../tmp/main-stop-research-20261018/code-review-closure.json)은 Python16개·독립 교차 리뷰·596 PASS 로그 SHA·원본 보존을 결속한다. 공유 workspace 실행 소스16경로는 출발 상태 그대로이며 코드 overlay/merge와 운영 배포는 수행하지 않았다. 다른 보유·로딩 연구의 코드/문서도 덮어쓰지 않았다. 이 작업본의 검토된 코드와 현재 선택900은 서로 다른 세대다.

실행한 명령은 아래와 같다. 원 output은 봉인되어 같은 경로의 재실행을 거부한다. 반복 연구는 새 attempt와 명시적 의존성 검증을 사용한다.

```bash
cd /home/ubuntu/KORStockScan-worktrees/main-stop-research-20261018
PYTHONPATH=. /home/ubuntu/KORStockScan/.venv/bin/python -m src.engine.automation.main_stop_research_execution \
  --data-root /home/ubuntu/KORStockScan/data \
  --output-root /home/ubuntu/KORStockScan/tmp/main-stop-research-20261018/attempt-04 \
  --date 2026-10-16 --target 2026-10-19 \
  --input-report /home/ubuntu/KORStockScan/data/report/main_stop_confirmation/main_stop_research_2026-10-16.json \
  --cost-data-root /home/ubuntu/KORStockScan-worktrees/quantity-broker-cost-closure-20261017/tmp/quantity-broker-cost-actual-20261017/repaired-temp-data
```

[최종 보고서](../../tmp/main-stop-research-20261018/attempt-04/report.json)는 `completed_report_only`, semantic SHA `8883ec469e1198775db55aa7b749b08f16ce33986816bd0c6c6af0d27e1afe60`, 연구 코드 SHA `91ea566bcb325eb1ceeffe788e6d5ee3b0f50e55db76f6f888338b05d36d63a9`다. 실제 현재 시각의 역사 등록·사후 source seal을 생성했으며 prospective 실험으로 소급하지 않았다.

| 실제 모집단 | 포지션 | quote/position source gap | 생애주기 검열 | 비용 적격 / manual / 비용 결손 | paired 경제 적격 |
| --- | --- | --- | --- | --- | --- |
| SCALP_PRESET_TP / REGULAR | 9 | 2 | 7 | 4 / 1 / 4 | 0 |
| SCALP_PRESET_TP / INTEGRATED_AFTERMARKET | 6 | 3 | 3 | 0 / 0 / 6 | 0 |
| 합계 | 15 | 5 | 10 | 4 / 1 / 10 | 0 |

가격 재생 결손과 비용 적격성은 서로 다른 열이다. 비용 결손10은 원본 완료 census에 없는6개와 중복 매도/비용 결손4개를 포함한다. 56,980관측은10/15의25,773개와10/16의31,207개이며15번 실제 손절이라는 의미가 아니다. 후보별 delta/표준오차는 적격 분모가 없어 null이다. selected policy는 없고 기존60초/보호 확인 수치·준비 정책을 변경하지 않았다.

### 생산·소비 마지막 단계까지 측정한 성능

attempt-03은 정상 완료했지만 원천 hash session을 조기에 닫아 finalization에서 같은 원천을 다시 해시했다. [범위 검토](../../tmp/main-stop-research-20261018/attempt-03-performance-scope-review/review.json)에 원 report/performance SHA와 수정 전 코드 bytes를 보존했다. 당시 내부 phase 측정121.997초와 보고서 시작~종료218.455초 사이 약96.458초가 측정 범위 밖이었다. 그 차이를 모두 순수 해시시간이라고 단정하지 않는다.

수리 후 동일한 invocation session을 finalization/report commit까지 유지한다. 동일 stat/ancestry와 기존 TTL 안에서만 hash를 재사용하며 변조·TTL 갱신은 그대로 검증한다. 전체 측정은 순환 참조를 만들지 않는 [최종 terminal](../../tmp/main-stop-research-20261018/attempt-04/execution_terminal_1a1418e8c30d51631ef6363d13328cfb15348145deb4770c853ae8b7d5322bc4.json)이 report byte/semantic SHA와 결속한다. 자신의 receipt 쓰기·마지막 lock 해제는 측정 밖이다.

| 실제 측정 | 최종 값 |
| --- | --- |
| 전체 연구: 입력 검증→재생/비용→실험/보고서 봉인→자원 반환 | wall113.511초 / CPU62.335초 / peak RSS130,420KiB |
| invocation digest | full15회/12,362,299,544바이트; 재사용26회/24,196,849,128바이트; 종료된 세션 stats |
| index 초기 재사용 / warm 재확인 | 0.0100초 / 0.00127초; 둘 다 raw decode0회 |
| position 재생·비용 overlay | wall44.495초 / CPU18.294초 |
| process I/O | rchar13,658,869,639 / physical read11,222,548,480 / physical write235,233,280바이트 |

[동일 의미·성능 비교](../../tmp/main-stop-research-20261018/semantic-performance-comparison.json)는 source SHA·census·15포지션·cell별 결과·비용 상태·paired 적격 분모·미선정 결과가 attempt-03과 같은지 검증했다. 이번 한 쌍에서218.455→113.511초로48.0% 감소를 관측했다. 기존 단계의 측정 범위가 달랐으므로121.997초와113.511초만 비교하지 않는다. 전체 Main/capture의 반복 부하·p95/p99 승인이나 자연 성과는 아니다. source/cost 전량 검증과 원본 quote 해석을 생략한 개선도 아니다.

최종 영향14개 시험 모듈 **596 PASS(39.72초)**, 변경 Python16개 compile, commit diff 공백 검사를 통과했다. 실제 >1MiB 원천의 동일 session full-read1회·finalization 직전 append 변조 거부, 정상/fast·early/generic 상한가 실패 경로, interruption/예산 해제·재개, native manifest→reader→publisher→loader/pin 양성/음성을 포함한다. 반복 실행 수는 합산하지 않는다.

원 선택 selector·기존 보고서·10/19 stop 정책3개 hash와 공유 실행 소스16경로의 출발 상태 불변을 확인했다. 전체 Main/거래 suite, full Main/capture 부하, 운영 strict/controller·장후 정책 재발행·배포·자연 PREOPEN/PID·외부 provider/주문은 이번 offline 범위에서 실행하지 않았다. 자료 적격성·evaluator·조건부 비도달·preset/보호선/비용 선정·성능 생산의 잔여는 위 owner/종료 시험을 유지한다. 로컬 링크/anchor113개·현재 OPEN owner1개·print-only parser25개와 diff 검사를 확인했다. 문서 교차 리뷰의 실질 finding은0이며 완료 시제와 최종 attempt 표기를 보완했다.
