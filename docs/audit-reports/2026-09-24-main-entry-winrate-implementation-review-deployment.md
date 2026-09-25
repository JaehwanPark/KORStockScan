# Main 진입 승률 정책 구현·검토·배포 영수증 — 2026-09-24

## 판정과 권한

- 9/28 목표의 `winrate_initial_v1`을 코드에 구현하고 9/23 유효 원천으로 날짜별 **대기** 정책을 발행했다. `KRX|KRX_REGULAR`에서 parent가 `ENTER_NOW`이며 동일 raw capture의 유효·신선 micro VWAP 대비 가격이 68.75bp 이상인 시도만 `BLOCK`한다. 결손·비유한·scope 충돌은 별도 `VWAP_UNKNOWN`/오류로 처리하며 다른 시장·exact scope, hard safety, 주문·수량 owner는 그대로 둔다.
- 1차 검토 release는 `/home/ubuntu/KORStockScan-runtime-releases/main-winrate-reviewed-v2-20260924`의 `fd8f14aeb87b61360eb1ba6f097ff73de2c5e356`이었다. 9/24 15:42 KST 전환 영수증은 `/home/ubuntu/KORStockScan/tmp/runtime-release-selection-before-main-winrate-v2-20260924-154218.json`에 보존했다. 추가 코드리뷰 후 현재 선택 release는 아래 재검토 영수증을 따른다.
- 9/28 대기 bundle hash는 `4d08df81a491cf4aae594ad38b702132b07ef42b1eddca53dd32f2ec1ae456a8`; 그 안의 machine hash는 `d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a`. 9/24 현재 활성 parent `99cb0e3af2a3e17e52b5edc4d2ba4ed018fd60fd4e8eca3a3386f91efa622de0`과 `current.json`은 변경하지 않았다. 9/28 장전의 날짜·parent CAS 검증과 활성화, 실제 PID 소비는 미실행이다.

## 산출·분모·비용 검증

승률 점수는 비용 계약을 통과한 `net_target_first`/`exact_stop_first`의 이진 승패를 고유 기회 단위로 계산한다. 수익률 크기나 EV는 선택 점수에 넣지 않는다. 9/23 frozen machine capture 평가의 시장별 분모는 다음과 같다.

| exact scope | 입력 | 유효 | source contract 제외 | 로컬 구조·경로·비용 제외 |
| --- | ---: | ---: | ---: | ---: |
| `KRX|KRX_REGULAR` | 1,485 | 351 | 60 | 1,074 |
| `PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE` | 116 | 19 | 6 | 91 |
| `KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET` | 484 | 84 | 8 | 392 |

세 scope 모두 입력 = 유효 + source contract 제외 + 로컬 제외가 성립한다. KRX 유효 351건은 `VWAP_NOT_EXTENDED` 291건과 `VWAP_EXTENDED` 60건이다. 비용 결속 승패와 gross 경로 승패가 다른 KRX 행은 9건이다. 기존 **전체 평가** 보고서의 476 유효행(KRX 351, PRE 25, AFTER 100)은 별도 frozen reference hash `10b29ced3cf6e61bee35e84de5e456db3dd78b562378cd0aef9db605fdc85564`로 결속했다. 476과 새 machine capture lane의 시장별 19/84를 같은 분모로 합치지 않는다.

초기 후보는 9/22 학습에서 선택 11기회·10승, 날짜순 9/23 진단에서 4기회·3승으로 원안의 값을 재현했다. 이후 장후 검색은 등록된 VWAP 값의 train-only 분위 후보로 제한하고, 3개 학습일·30기회와 나중의 미사용 2개 holdout일·10기회, parent 대비 원승률 및 표본 보정 승률 개선·5%p 차·50% coverage·80% 승자 보존을 모두 만족해야 갱신한다. 미달이면 마지막 활성 machine payload/hash를 유지한다. holdout 소비일은 별도 영수증으로 기록한다.

## 코드 검토와 재검증

1. 첫 검토에서 VWAP 유효성 flag가 raw top level이 아닌 `features` 아래 있음을 확인하고 consumer를 수정했다.
2. 실제 보고서의 KRX source contract 제외 60건이 상위 분모에 빠지는 결함을 찾아 evaluator·stage 검사·의미 감시를 고쳤다. 재생성 후 `main_machine_policy`의 stage semantic issues는 0건이다.
3. 장전 활성화를 같은 날짜에 반복하면 CAS 실패하는 경로와, 발행기가 veto 이외의 threshold 변경을 허용할 수 있는 경로를 막고 회귀 검사를 추가했다.
4. 전체 strict 검증에서 새 `pre_submit_delay` 직접 owner가 checklist 계약에 없고, 오래된 자동 `DirectFamily` 작업이 현재 투영과 중복되는 결함을 찾아 검증기·생성기를 고쳤다. 기존 수동 작업은 유지한다.

최종 release에서 관련 테스트 375개 PASS(핵심 313, checklist 62), Python compile, PREOPEN wrapper `bash -n`, `git diff --check` PASS. 더 넓은 evaluator 묶음의 16개 실패는 `test_entry_setup_paired_replay_batch.py`의 동일 fixture가 `validation['model_scopes'][0]`에서 실패하는 기존 결함으로, 변경 전 선택 release에서 같은 첫 실패를 재현했다. 이 묶음을 전체 PASS라고 주장하지 않는다.

9/23 원천의 승률 계산은 1분 44.71초 wall, 사용자 CPU 104.16초, 최대 RSS 1,037,756KB, swap 0이었다. 검토 release에서 `main_machine_policy`를 다시 실행해 최신 stage 영수증을 만들고, `summary_handoff`를 갱신했다. 15개 활성 stage의 입력·출력 영수증에 이슈가 없으며 전체 strict `--require-summary-handoff`는 issue 0으로 PASS했다. 범위별 strict Main 검증도 PASS했다. 의미 감시의 새 `winrate_*` 오류는 0건이다.

## 남은 실행 경계

- 기존 의미 감시는 `compact_operating_rows_all_excluded`, `machine_current_structure_empty`, `machine_operating_economics_incomplete`, `machine_operating_paired_unbound`, `machine_source_contract_exclusions`를 계속 경고한다. 새 승률 정책의 성공이나 비용 조정 수익 실현 증거로 해석하지 않는다. 각 원천·운영경제성 owner의 후속 수리는 별도로 필요하다.
- 선택 release는 향후 scheduled main 작업의 코드 경로다. 현재 main PID는 실행 중이지 않아 새 코드·9/28 정책의 PID 소비 영수증은 없다. 9/28 PREOPEN activation, loader/bootstrap, 실제 PID의 exact-scope hash 대조 및 그날의 새 자연 원천 장후 전체 성능·최종화·의미 감시 수용은 9/28 checklist의 OPEN owner에 남는다. frozen 9/23의 1분 45초를 9/28 자연 실행의 성능 증거로 전이하지 않는다.

## 추가 코드리뷰·수정보완 — 18:12 KST

- 후속 정책 후보가 두 holdout 원천일 중 하루만 선택하고도 승격되던 결함을 재현해, **선택 기회가 두 날짜 모두 존재**해야 하도록 수정했다. 고유값이 9개 이하일 때 탐색 grid에서 최고값이 빠지는 결함도 수정했다. 후속 veto는 현재 veto보다 느슨해지지 않도록 제한했다.
- 발행기는 후속 train/holdout 날짜·선택 기회 수·원승률/표본 보정 승률·5%p 개선·coverage·승자 보존·선택 holdout manifest와 정책/원천 hash를 다시 검사한다. malformed 지표 객체 및 기회 수보다 적은 시도 수도 거부한다. 장전 재실행이 동일 승률 세대의 AI 보조 정책 자식을 만날 때는 검증된 한 단계 상속만 `already_active`로 인정한다.
- 시장별 PREMARKET/REGULAR/AFTERMARKET 분모와 제외 사유의 합·상위 KRX 결속을 stage/의미 감시가 함께 검사한다. 원천 행이 없는 시장은 `no_rows`로 드러내고, 잘못된 승률 sidecar schema 또는 후속 허들 위반은 의미 감시 finding으로 보고한다.
- 새 격리 release `/home/ubuntu/KORStockScan-runtime-releases/main-winrate-rereview-20260924`의 commit은 `bd001179757149ac412ae9ad9932147eebe1c377`이다. 관련 회귀 검사 **317 PASS**, Python compile, wrapper `bash -n`, `git diff --check` PASS. 이 릴리스의 공유 9/23 원천으로 `main_machine_policy` stage 이슈 0, 전체 strict `--require-summary-handoff` PASS, 새 `winrate_*` 의미 finding 0을 다시 확인했다. 기존 의미 finding 5종은 위 경계대로 남는다. 재검토 과정에서 전체 장후 계산을 다시 실행하지 않았다.
- 18:12:39 KST에 selector를 이 release로 원자적으로 전환했다. 이전 selector는 `/home/ubuntu/KORStockScan/tmp/runtime-release-selection-before-main-winrate-rereview-20260924-181239.json`에 보존했다. `--check-release-set` PASS이고 9/28 PREOPEN `--print-plan`이 `bd001179`를 가리킨다. 9/28 대기 bundle `4d08df81`·machine `d94fecaf`와 9/24 활성 parent `99cb0e3a`는 변경되지 않았다. 실제 PID 소비·장전 activation·9/28 새 자연일 장후 성능/결과는 여전히 미검증이다.
