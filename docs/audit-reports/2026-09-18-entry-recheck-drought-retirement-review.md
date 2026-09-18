# Entry recheck drought 전용 경로 폐기 검증 — 2026-09-18

사용자 최종 지시 `관련 런타임, 장후작업, 산출물 모두 삭제하라`에 따라 `entry_recheck_drought_controller`와 전용 `entry_opportunity_recheck_runtime`을 작업본에서 폐기했다. 이전 파일선택 수리·9/17 보고서 갱신 지시는 더 이상 현행 목표가 아니다. 폐기한 family의 유효 no-edge나 source gap 해소를 기다리지 않는다.

## 변경과 유지 경계

- 삭제: 전용 actor/config/state/attempt mint, score 69–74.999 WAIT 복구, pending 재평가/WS handoff, 독립 submit budget, controller/policy/maintenance 모듈과 전용 테스트.
- 삭제: 장후 wrapper의 실행 flag·CLI·artifact wait·DONE 필드, DONE 자동 복구, workorder 생산·fingerprint, summary/checklist source binding, PREOPEN 전용 loader/validator·deterministic AI 예외·dependency carry·family env mapping.
- 차단: 과거 ON env·operator lock·후보·`order_entry_recheck_*` workorder는 기존 retirement owner가 제거/거부한다. 복원된 armed/pending intent는 첫 BUY 제출 전에 거부한다. 전용 stage/명시 family는 threshold backfill partition을 다시 생성할 수 없다.
- 보존: 정상 machine RECHECK·보조 AI·normal BUY, 공통 source-only 제출병목 진단의 6개 workorder ID와 final handoff, broker/account/sizing/quantity/cooldown/stop 및 custody. 일반 AI gate backtest는 기존 on-demand 진단으로 남고 runtime 후보를 만들지 않는다.
- 보존: 이미 접수된 실제 주문의 체결·정산·완료 손익. actor의 immutable attribution 복사만 기존 receipt-only `scalping/entry_recheck_economics.py`로 옮겼다. 신규 config/state/evaluate/mint/order 권한은 없다. 과거 원장의 field 이름은 정산 결속을 위해 남긴다.
- 공통 helper 소유권: 정상 scope 정규화는 기존 `entry_setup_scalping_rollout`, 정상 funnel 숫자 검증은 기존 `automation/submit_drought_contract`가 소유한다. 신규 Python 모듈·호환 wrapper·정책 그리드·성능 점검 체계는 추가하지 않았다.

## 리뷰와 보완

정상 AI setup 계약이 삭제한 recheck env와 100회 독립 budget에 의존하던 연결을 제거했다. 정확한 scope는 기존 정상 canary의 명시 ON 또는 검증된 rollout/auto-promotion으로 확인한다. 정책 날짜·prompt owner·probe-first/post-probe execution 계약과 signed exploration limit/실제 접수 누적 cap은 계속 검증한다. process-level 명시 OFF는 파일의 ON보다 우선하도록 보완하고 회귀 검증했다. 통합 애프터마켓은 이 폐기한 경로의 observe-only 구분으로 제한하지 않으며, 현행 정상 machine/AI의 기존 exact-scope 승인 계약을 따른다.

정상 exploration의 신규 상태는 기존 `entry_setup_bounded_exploration_probe_only`를 사용하도록 분리했다. 현재 cap guard/접수 누적 commit은 이 공통 flag와 과거 custody flag를 모두 인식하여, 전용 actor 삭제가 정상 경로의 누적 cap을 우회시키지 않도록 검증했다.

과거 family의 actual fill/SELL receipt가 남아 있어도 전용 partition을 재생성할 수 있는 stage registry 잔여 연결을 재리뷰에서 발견해 제거했다. 원 pipeline/custody 이벤트는 보존한다. 과거 workorder 반복은 신규 구현 업무로 승격되지 않는다.

## 산출물 삭제 증거

`tmp/entry-recheck-retirement-20260918/deleted-products.json`에 경로·파일 크기·삭제 목록을 기록했다. workspace와 private worktree/release의 전용 보고서·sidecar/lock·threshold family 파생 partition·전용 budget·전용 override lock 및 이번 수리의 전용 보고서 사본을 삭제했다. 삭제 전 관련 producer/wrapper process와 열린 FD, advisory lock을 확인했다.

- 삭제 파일: 최초659개 + 검증 후 전용 fixture 사본6개 + 최종 review pycache/과거 lock7개 = 총672개, 547,696,994 bytes (약 522MiB).
- 보호: 공통 pipeline 원천·broker/custody/owner ledger·DB·실제 완료 손익 원천, mixed env/PREOPEN/verification 과거 receipt.
- 보호: immutable release source와 runtime selector. 생성물 정리는 실제 source release 교체가 아니다.

## 검증과 실행 경계

검증 로그는 `tmp/entry-recheck-retirement-20260918/`에 기록한다. 영향 범위는 actor 폐기 계약·PREOPEN·wrapper/자동 복구·정상 machine/AI·BUY/SELL 안전과 receipt 정산이며, 실제 주문·provider 호출·전체 장후 재실행·성능 benchmark는 실행하지 않았다.

영향 회귀 검증은 `final-pytest.log`의 **2,895 passed / 7 deselected**다. 이후 마지막 공통 cap/handoff 보완은 `final-cap-handoff.log`의 **187 passed**, 신규 정상 flag를 사용하는 실제 접수 누적 cap과 과거 opaque workorder 차단을 포함한다. `final-ai-retry.log`는 정상 AI retry의 상태 전파 **1 passed**다. 중복되는 검증을 합산해 독립 표본 수로 보고하지 않는다. compile/bash/parser/diff 결과와 검증 집계는 같은 디렉터리의 `validation.json`을 따른다. 별도의 비관련 기존 실패는 변경 전 source를 subprocess 메모리에 로드하여 재현했고 `preexisting-failures.log`에 남긴다. 기존 실패를 이번 폐기의 성공으로 감추거나 전체 작업본 GREEN으로 선언하지 않는다.

최초 삭제 요청은 source-only로 완료했다. 이후 사용자가 반복 리뷰·수정보완·commit/push·배포를 명시 승인했다. 다른 세션의 변경을 제외하고 현재 main `2fe8ccf17`에 폐기 delta만 3-way 적용한 clean managed release `/home/ubuntu/KORStockScan-runtime-releases/entry-recheck-retired-reviewed-20260918`에서 재검증했다. 삭제 대상 controller strict 계약의 3개 merge 충돌은 폐기 후 정상 공통 계약을 남기도록 해소했다.

clean release 핵심 계약은 `clean-pytest-core.log`의 **563 passed**다. 정상 BUY/AI/PREOPEN/체결 회귀는 `clean-pytest-runtime.log`의 **1,970 passed / 3 failed**다. 실패 3개는 `release-preexisting-failures.log`에서 변경 전 main source로 모두 동일하게 재현했다: quote age float 정확 일치(49.999999999954525 vs 50), 기존 ADM feature projection 기대값, NXT 18:00 실제 receipt의 `nxt_aftermarket` vs 과거 `nxt_entry_window` 기대값. 자동화 소비/반복 workorder 회귀는 `clean-pytest-automation-final.log`의 **454 passed**이며 분리 과정에서 빠졌던 폐기 테스트를 포함해 재검증했다. 새로운 미해결 폐기 회귀는 없으며 전체 repository GREEN은 주장하지 않는다. clean source compile/bash/diff 및 print-only 문서 parser도 통과했다. workspace 기존 7개 실패와 clean baseline 3개는 입력 baseline이 달라 합산하지 않는다.

commit/push·selector CAS·실제 PID 및 경로 검증 결과는 `tmp/entry-recheck-retirement-20260918/deployment.json`과 `release-validation.json`을 따른다. 이 승인에 따라 source release를 선택하되 기존 dated env·policy·hard safety를 보존한다. 실제 PID 소비·자연 행동·경제성은 source publication과 구분한다. 이번 요청의 다음 장후 단위 분석은 [microstructure 분석](2026-09-18-microstructure-reaction-context-result-review.md)에서 기록한다.

## 승인 배포 receipt

source commit **`d7b2d380761ab835c78acbf3180f8979d92f9a29`**을 main과 `review/entry-recheck-retirement-20260918`에 atomic push하고 remote SHA를 대사했다. 2026-09-18T11:34:53.634584+09:00에 clean managed root `entry-recheck-retired-reviewed-20260918`를 selector lock/CAS로 선택하고 readback의 root/HEAD/clean source/공유 경로 계약을 확인했다. 이전 selector는 `selection-before-retirement.json`에 hash-bound 보존했다. deploy JSON 및 routing-postclose/preopen JSON은 선택 source만 증명한다.

현재 Main PID 없음, `actual_pid_consumed=false`. 새 source의 **readonly** PREOPEN verify는 기존 `runtime_env_handoff_missing`이며 integrated-axis unconfigured/policy-date/shared-policy-hash/bundle-hash4개 결손이다. 정책/env/lock·operator override·provider·주문·기동/재시작·전체 장후 재실행을 수행하지 않았다.

전체9개 cron-target verifier는 `cron_target_missing_or_duplicate`를 반환했다. current checklist에 보존 대상으로 명시된 정지 장후 cron 때문이다. 현재 설치된 start/preopen/eod3개는 각각 단일 selector routing으로 대사했다. postclose/controller/finalization/replay/archive 등 누락 schedule을 복원하거나 배포했다고 주장하지 않는다. 현행 선택 source의 next-unit 분석은 상기 microstructure 문서를 따른다.

최종 리뷰에서 추가 전용 pycache/과거 lock7개를 발견해 active producer/FD/lock 확인 후 삭제했다. `deleted-products-review.json`과 cumulative `deleted-products.json`에 반영했다. 공통 정산 원천·source/PID 증거와 다른 세션 작업본은 보존했다.
