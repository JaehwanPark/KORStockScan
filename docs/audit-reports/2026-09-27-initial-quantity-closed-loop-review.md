# 최초 수량 정책 폐루프 재리뷰 — 2026-09-27

## 결정 범위

최초 v2/갱신 정책의 변경 형상·유형별 cap 소비·순차 BUY 시간표·정확 terminal·정규 장후 stage→strict→CAS→PREOPEN 연결을 구현했다. 최초 코드 릴리스 `58dbddd6`와 v2 정책 CAS 이후, 타임아웃 소유권 수리 릴리스 `96c67f30532c51c86a7cfb10461d7aa55f64b387`을 메인 selector에 다시 선택했다. 실제 PID 소비·자연 주문·실현 EV는 별도 영수증으로 판정한다.

## 결함 재리뷰와 수리

- 변경 형상을 고른 초기 후보를 롤백용 부모 기본정책 생성기가 거부하던 경로를 수리했다. 부모 기본정책은 부모 형상을 보존하고 v2가 후보 형상을 봉인한다.
- 첫 BUY 직전 CAS `SUBMIT_INTENT`와 대상 index, 결정 attempt·policy SHA·probe 포함 순차 시간표를 기록한다. 브로커 호출 예외/불확실 응답/저장 실패는 재제출 없이 broker·owner 조회로 남긴다. 후속 leg는 이전 leg의 정확 terminal, 현재 수량·현금·route/epoch·P1 가격·buy/exit/operator 안전을 다시 확인한다.
- 실제 동적 가격 leg의 broker terminal bridge가 journal에 필수인 owner client intent ID를 빠뜨리는 결함을 재리뷰에서 찾았다. terminal state에 원래 intent ID와 제출 가격을 보존하도록 수리하고, 실제 bridge 출력→영속 전이→다음 leg 허용을 잇는 회귀를 추가했다.
- 후속 리뷰에서 순차 묶음 첫 leg에 구 profile TTL을 다시 붙이고 `entry_cancel_wait_submission`의 `actual_timeout_sec`에 신규 묶음 T를 넣던 중복 소유 경로를 제거했다. 실행 계획의 시간 소유자는 새 순차 시간표로 표시하고, 첫 주문 시작·정책·attempt는 `order_leg_sent`와 영속 journal에 따로 기록한다. `entry_cancel_wait`의 주문 시작 판정은 유지한다.
- v2/갱신 allocator의 유형 행 영수증 누락과 갱신 부모의 `initial_policy_refresh_loaded` 상태 불일치를 수리했다. 수량 cap 10/15/20%는 부모 5단계와 25% 절대 상한 안에서만 소비한다. ratio의 데이터 기반 선택 생산자는 여전히 부모 carry다.
- 영속 첫 BUY 시작 시각을 정확 주문번호·attempt·계획 SHA·수량 정책 SHA에 결속해 장후 경로가 구 request-to-sent 추정 시각보다 우선 읽는다. T 후보는 같은 유형 30건 이상, 모델 coverage 80%, 정확 시작 시각 전수, 검증 가격 교차, 3개 독립 날짜, 보수적 비용 후 EV·원화 순익 우위가 있을 때만 고른다. 현 데이터는 정확 시작 원천 0건이므로 기존 프로필 시간을 유지한다.
- 갱신 stage 적격 후보만 최종 strict 이후 선택 코드 릴리스 root 대사와 release-set 잠금 아래 current CAS로 적용한다. 부모 archive를 재귀 검증하고 재실행/부모 충돌을 거부한다. `carry_parent`는 pointer를 바꾸지 않는다.
- 재기동 시 journal에 이미 `OPEN`인 주문이 있지만 로컬 주문 행이 없는 경우, 브로커 snapshot 생산자는 읽기 전용이어서 로컬 행을 자동 복원하지 않는다. 이 경로는 후속 BUY를 열지 않고 재조회·보류한다. 자동 취소/다음 leg 진행을 완료 상태로 주장하지 않는다. 변경 분할 정책의 자연 주문 전에는 정확 owner·broker 행 복원과 기한 내 취소 회귀가 추가로 필요하다.

## 데이터 기반 결과와 성능

- 2026-06-05 클린 기준 이후 9/23까지 완료 첫 거래 387건·익절 244건. 수량 replay validator와 타임아웃 연구 validator PASS, replay 내용 SHA `5ea85f0fc068d46b39ad6900747ae74ed68160df3500a4c612989479f50c67dd`. 6유형 모두 부모 형상이며, `KRX_PARENT`의 900초는 1건 수준의 **모델 연구 최고 후보**일 뿐 실행 정책 T가 아니다. 영속 시작 시각 지원 거래 0건이다.
- 한 번의 원천 스캔을 공유한 격리 재생: 수량 replay 378.223초, 타임아웃 후보 34,056건 0.580초, 추가 pipeline 스캔 0회. 프로세스 전체 wall 381.27초, CPU user/system 354.03/2.69초, peak RSS 151,960KB, swap 0. 동일 전수 원모수·형상 선택은 직전 봉인 실행과 같다. 외부 `ka10080` 193그룹 전체 수집은 앞선 별도 실측에서 193/193 응답, wall 124.98초·peak RSS 약 432MB였다. 이 측정은 정규 threshold postclose 전체 체인 시간이 아니다.
- 9/27 효력 이후 완료 거래 0건의 격리 갱신 stage는 validator PASS, `carry_parent`, 후보 파일 없음, wall 0.79초·peak RSS 134,108KB였다. 새 적용 세대 자연 경제성은 관측되지 않았다.

## 검증·남은 판정

격리 helper/실제 pipeline 원천 결속 및 기존 주문 회귀를 포함한 광역 pytest 1,176건 PASS와 terminal 수정 영향 회귀 50건 PASS, wrapper `bash -n`, Python compile, 변경 신설 모듈 Ruff, `git diff --check`, print-only 문서 parser를 수행한다. 최종 릴리스 commit/selector/PREOPEN 결과는 실제 완료 후 별도 기록한다. Kiwoom 주문 wire/parser는 변경하지 않았다. 공식 `Kiwoom-Securities/Kiwoom-REST-API` commit `953e5dbff123f437ab4d11a78a95191a685eb51f`의 `kiwoom/_data/kiwoom_api_spec.json` `kt10000/kt10003`, `postman/kiwoom-openapi.postman_collection.json`, `kiwoom/specs.py`를 2026-09-27 14:33 KST에 확인했다. KRX/NXT/SOR route, 지정가/시장가 코드, 수량 단위와 7자리 주문번호는 기존 local 계약을 유지한다.

## 코드·정책 배포 및 다음 소비

- 최종 선택 릴리스: `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-closed-loop-20260927-final`, commit `96c67f30532c51c86a7cfb10461d7aa55f64b387`. 직전 selector 원본은 `tmp/runtime-release-selection-before-initial-timeout-owner-20260927.json`에 봉인했다. release-set PASS, cron 필수 8경로 PASS, 9/28 PREOPEN print-plan은 새 commit을 가리킨다. Main PID는 9/27 15:40 KST `0/inactive`였고 실제 소비를 주장하지 않는다. 타임아웃 소유권 수정 후 영향 105건·entry_cancel_wait 52건 PASS이며, 이전 광역 1,176건도 PASS다.
- 활성 `current.json`은 `initial_entry_quantity_current_v2`, 내용 SHA `91d195d1de7215360e7ee625dc7636e41bb642f1c709b74666e470490052ebf3`, 파일 SHA `a34d980f13be8c4929012557f23958871c832edb118058f498420ab078b83585`이다. 9/28 로더는 최초 v2 파일 SHA `ba72d720a4c11dbcfd18a667d2f47a648c0e7b792fe9a3edbb7193f674870cca`를 검증했다. 모든 유형은 데이터 선정대로 부모 5단계 수량·부모 주문 형상·기존 프로필 타임아웃이다. 실데이터에서 달라진 수량·분할·T는 없다.
- 새 선택 릴리스에서 9/27 갱신 장후 생산자를 다시 실행했다. 0건 `carry_parent`, stage validator PASS, candidate 없음, wall 0.80초·peak RSS 134,292KB다. 이를 일반적인 정규 장후 전체 체인 측정으로 확대 해석하지 않는다.
- 9/28 기존 bootstrap 파일은 9/26에 생성되어 새 current를 담지 않는다. 읽기 전용 검증은 `initial_quantity_policy_env_mismatch`, `owner_mismatch`, `receipt_mismatch`로 실패했다. 선택 릴리스에서 9/28 `build_manifest`를 읽기 전용 재구성하면 정확한 새 파일 SHA가 env와 receipt에 들어간다. 정규 9/28 PREOPEN이 동시 family 생산과 bootstrap을 새로 발행·검증한 후 Main PID가 파일 SHA를 소비해야 적용 수용이 닫힌다. 미래 날짜 bootstrap만 조기 발행해 정상 장전 절차를 대체하지 않는다.
- 유형별 cap의 데이터 기반 선정은 현재 생산자가 부모 carry이므로 정책 자동 갱신 범위에 남아 있다. 자연 적용 후 T 갱신은 적격 새 거래의 정확 시작 시각과 terminal/economics가 생길 때만 가능하다.

## 9/27 재기동 주문 복구 재리뷰

- 선택 릴리스 `96c67f30`의 `OPEN/PARTIAL/CANCEL_REQUESTED` journal에서 로컬 주문 행이 유실되면 진행이 멈추는 결함을 확인했다. 격리 수리 릴리스 `3ccd0b89ae90223a7d4d166e7da0974f61a72de1`은 정확한 원주문 번호·날짜·종목·route·수량·가격·Main owner intent와 완전한 `ka10075` 미체결 목록으로 살아 있는 주문 행만 복원한다. 브로커에서 이미 체결 또는 취소되어 미체결 행이 없으면 `kt00007`의 원주문과 단 하나의 확인된 취소 자식, `ka10075` 부재, Main owner·계좌 수량을 재대사해 terminal을 CAS 저장한다. 로컬 주문이 남은 `CANCEL_REQUESTED`도 같은 terminal 증거를 요구한다. 응답 불명 취소를 재전송하거나 증거 없이 후속 BUY를 제출하지 않는다.
- Kiwoom 공식 commit `953e5dbff123f437ab4d11a78a95191a685eb51f`의 `kiwoom/_data/kiwoom_api_spec.json` `ka10075`, Postman collection, 기존 `src/utils/kiwoom_utils.py` 정규화 계약을 9/27 16:00 KST에 대조했다. 신규 REST wire/parser는 만들지 않고 기존 조회 함수를 사용한다.
- 격리 릴리스에서 terminal/bundle/timeout 회귀 56건과 기존 sniper의 초기 bundle 회귀 7건 PASS, Python compile 및 `git diff --check` PASS. 전체 sniper 광역 실행의 SELL 21건 실패는 직전 선택 릴리스 `96c67f30`에서도 같은 `pending_submit_integrated_venue_context_invalid`로 재현되어 이번 BUY 복구 변경의 회귀가 아니다. 후행 API 193그룹과 387건 역사 재생 결과는 위 봉인 실행을 재사용한다. 정규 threshold 장후 전체 체인 시간은 아직 실측하지 않았으며 정책 수치 갱신은 현재 데이터에서 선택되지 않았다.
- 최종 코드 포인터를 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-open-recovery-20260927-final`의 `3ccd0b89ae90223a7d4d166e7da0974f61a72de1`로 교체하고 직전 JSON을 `tmp/runtime-release-selection-before-initial-open-recovery-20260927.json`에 봉인했다. 공유 `logs/docs/restart.flag`를 정합 경로에 연결한 뒤 release-set PASS, cron 필수 8경로 PASS, 9/28 PREOPEN print-plan은 새 commit을 가리켰다. `current.json` 파일 SHA `a34d980f…`, 정책 파일 SHA `ba72d720…`은 그대로다. Main PID 수용과 9/28 정상 PREOPEN 발행은 미래 자연 절차다.
- 선택 릴리스 경로에서 수량 결정·bundle/terminal/timeout·정책 생산/검증·bootstrap·장후 wrapper 영향 테스트 **232건 PASS**(110.42초). 9/28 `build_manifest` 읽기 전용 재구성은 current 파일 SHA `a34d980f…`와 최초 정책 파일 SHA `ba72d720…`을 동일 receipt에 담았다. 기존 9/28 bootstrap 파일은 아직 재발행되지 않았으며 정상 PREOPEN을 기다린다.
- 유형별 ratio 근거 재점검: 9/23까지의 봉인 replay 387건은 `KRX_PARENT` 32건/순손익 +13,582원, `KRX_THIN_HIGH_TICK` 5건/-1,801원, `SAFE_UNKNOWN` 350건/-581,502원이다. 전체 순손익 -569,721원과 일치한다. `SAFE_UNKNOWN`은 현 계약상 부모 비율 고정이며, 얇은 호가 5건은 갱신 최소 표본에 못 미친다. replay 거래 행에는 실제 체결 수량을 달리했을 때의 broker 체결·정확 비용 반사실이 없으므로 10/15/20% cap의 우월성을 이 숫자만으로 주장하지 않는다. 현재 정책의 부모 비율 유지와 자동 ratio 후보 생산 코드의 미완료를 구분한다.
- 추가 가격 결속 리뷰: 공식 `kt00007`의 `ord_uv`는 원주문 단가(원)다. 종전 terminal proof가 원주문 번호·수량·route만 대사해 잘못된 주문가가 같은 leg로 종결될 수 있었다. `submitted_price`를 exact broker terminal/discovery와 재시작 취소 복구에 결속하고 시장가 probe의 0원, 다른 지정가, 잘못된 local 가격을 회귀로 확인했다. 불변 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-price-proof-20260927-final` commit `ffe86509efaf1b20c8476cdd1ac5e1f84ca3aa73`를 메인 selector에 선택했으며 직전 JSON은 `tmp/runtime-release-selection-before-initial-price-proof-20260927.json`에 봉인했다. terminal·bundle·timeout 56건과 기존 초기 bundle 7건 PASS, compile·diff PASS, release-set·cron 8경로·9/28 PREOPEN print-plan PASS. 정책 current 및 파일 SHA는 변함없다.
- 9/28 Main `start --print-plan`도 동일 `ffe86509` 릴리스의 `src/run_bot.sh`를 가리킨다. 이는 실행 경유 검사이며 실제 시작·PID 파일 SHA 소비는 아직 발생하지 않았다.
- 정규 장후 전체 체인 시간 영수증은 9/27(일) 자연 `postclose_stage_terminal`이 없어 생성되지 않았다. 9/23 동결 전수 재생은 활성 v2 정책의 효력일(9/24) 전이라 후속 갱신 wrapper의 전체 체인 실측을 대체하지 않는다. 9/28 원천일 정상 postclose의 stage→summary/strict→정책 carry/CAS와 총 wall/CPU/RSS를 한 영수증으로 대사해야 한다.

## 9/27 16:46 KST 갱신 자연 영수증 연결 재리뷰

- **발견·수리:** 정규 장후 wrapper는 `--pid-receipt`와 `--terminal-receipt`를 전달하지 않았고, 생산자 CLI도 이를 자동 생성하지 않아 후속 적격 거래가 생겨도 갱신 평가가 항상 `parent_pid_consumption_missing`·`post_apply_terminal_cost_binding_missing`으로 `carry_parent`에 머물렀다. 선택 릴리스 `363d170cfdffd733332707ae72e65389b6fe58fa`는 완료 비용 거래 census의 원천 manifest와 보고서 SHA를 terminal 영수증에 결속한다. 거래별 `entry_execution_sizing_plan`의 실제 PID를 첫 체결 주문·attempt·계획 SHA·정책 파일 SHA에 이어 붙이고, 각 진입일의 정상 PREOPEN manifest/env와 `pid_passed` 영수증의 같은 PID를 확인해 PID 소비 영수증을 자동 구성한다. 누락·날짜/정책/파일 해시/PID 불일치는 carry하며 명시 인수로 이 검증을 우회할 수 없다. stage 검증기는 영수증 원천 파일을 재검증한다.
- **데이터·성능:** 변경 코드로 2026-06-05 이후 9/23까지 완료 387건·익절 244건·실현 순손익 -569,721원을 전수 재생했다. 유형 건수 `KRX_PARENT=32`, `KRX_THIN_HIGH_TICK=5`, `SAFE_UNKNOWN=350`, 6유형 모두 `parent` 형상으로 기존 결과와 같다. replay·초기 후보·stage validator PASS, wall 372.228초, CPU user/system 353.620/2.237초, peak RSS 151,184KiB, swap 0, 거래 평가 p95/p99 0.107/0.133ms. 새 PID 필드는 과거 거래 387건 모두 `null`이며 과거 데이터에 PID 소비를 소급 주장하지 않는다. 선택 릴리스의 9/27 적용 후 완료 0건 격리 실행은 `carry_parent`, validator PASS, 전체 wall 0.78초, peak RSS 134,148KiB였다. 정규 전체 장후 체인 성능 영수증으로 해석하지 않는다.
- **검증·배포:** PID/비용 영수증 경계와 주변 영향 테스트 495건 PASS(112.83초), 불변 릴리스 내 69건 PASS, Python compile·Ruff·`git diff --check` PASS. 이전 릴리스의 기존 SELL fixture 21건 실패와 이번 BUY 갱신 변경을 혼동하지 않는다. 메인 선택 포인터는 위 불변 commit으로 CAS 전환했고 선택 release-set PASS, 필수 cron 8경로 PASS, 9/28 PREOPEN·start `--print-plan`이 같은 root/commit을 가리킨다. 초기 v2 정책 `current.json` 파일 SHA `a34d980f…`와 정책 파일 SHA `ba72d720…`은 유지했다. 9/27 Main PID는 0/inactive이며 새 코드·정책의 실제 PID 소비, 자연 주문·terminal, 적용 후 비용 성과는 아직 관측되지 않았다.
- **계속 OPEN:** 유형별 10/15/20% ratio의 근거 있는 자동 후보 선정, 정상 9/28 장후 wrapper→summary/strict→정책 carry/CAS 전체 시간·메모리, 구 TTL/중복 소비자 퇴역의 caller-0 대사, 9/28 정상 PREOPEN·PID 실소비. 대체 수량 broker 체결 자료가 없어 ratio를 임의의 비례 수익으로 승격하지 않는다. 최초 기본정책은 배포됐고 이 항목들은 후속 변경 폐루프의 완료 조건이다.

## 9/27 17시 재기동 PID 영수증 보존 수리

- 일별 `runtime_policy_bootstrap_verify_YYYY-MM-DD.json`은 동일 날짜의 bot 재기동 때 덮어써진다. 갱신 평가기가 이 최신 파일의 단일 PID만 받아들이면 이전 PID로 체결한 거래가 영구 검열되는 결함을 확인했다. 성공한 실제 PID/env 검증을 `data/runtime/policy_bootstrap/verified_initial_quantity_pid/<date>/`에 내용 해시가 포함된 불변 파일로 추가 보존한다. 장후 생산자는 같은 날짜의 복수 PID를 읽고 거래별 `entry_execution_sizing_plan`의 PID와 검증 시각이 수량 판정보다 빠른지 확인한다. 새 archive가 있으면 덮어쓴 최신 단일 파일에 의존하지 않으며, 기존 carry stage의 이후 재검증은 봉인 당시 PID 근거가 현재 유효한 불변 파일의 부분집합인지 확인한다. 실패/누락 PID는 여전히 carry다.
- 영향 테스트 **496건 PASS**(112.36초), 보존·다중 PID·늦은 검증 시각 격리 3건 PASS, compile·Ruff·diff PASS. 이전 387건 전수 재생의 입력·후행 평가 로직은 바꾸지 않았으므로 위 동결 데이터 결과를 재사용하고, 9/28 실제 다중 PID 자연 사례는 사후 관측한다. 불변 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-pid-archive-20260927` commit `db34188a64a38518afedf31d577c4e59e176a1de`를 메인 selector에 선택했다. release-set·cron 8경로·9/28 PREOPEN/start print-plan PASS, 초기 v2 정책 SHA 불변, Main PID 0/inactive. 실제 PID 소비·자연 주문/경제성과 유형별 ratio 자동 선정·정규 장후 전체 성능은 별도 OPEN이다.

## 9/27 17시 KST cap 후보 원천·전수 재생·선택 릴리스

- 실제 초기 수량 판정의 최종 allocator 예산·가격·cap·실제 ratio/수량을 `entry_execution_sizing_plan`에 source-only로 기록하고, 장후에는 체결 주문→attempt→계획 SHA가 맞는 거래 행에만 투영한다. 이 릴리스는 정책값과 주문 동작을 변경하지 않는다.
- 영향 테스트 496건 PASS(114.17초), 새 원천·결속 표적 2건 PASS. 9/23까지 완료 387건·익절 244건 재생의 보고서 내용 SHA는 직전과 동일한 `f8c24e61e89cc0ef62721affd6414e7fa0d41a1b50cf26410751e896711aed11`; replay/초기 후보/stage validator PASS. wall 373.741초·CPU 353.637/2.763초·peak RSS 151,016KiB·swap 0. 광역 sniper SELL fixture 실패 21건은 이전 선택 릴리스에서도 같은 원인으로 재현되며 BUY 변경의 신규 실패가 아니다.
- 불변 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-cap-source-20260927` commit `37223b467c5af5576dbe64a2b4a449e93d76e1c5`를 메인 selector에 CAS 선택했다. 이전 JSON은 `tmp/runtime-release-selection-before-initial-cap-source-20260927.json`. release-set PASS, cron 8경로 PASS, 9/28 PREOPEN/start print-plan이 같은 commit을 가리킨다. 초기 v2 current 파일 SHA `a34d980f…`, 정책 파일 SHA `ba72d720…`은 유지된다. Main PID 0/inactive이므로 실제 소비·자연 주문/경제성과 전체 정규 장후 체인 성능은 수용하지 않았다.
- 10/15/20% cap의 자동 선정은 대체 수량의 실제 broker 체결·비용 반사실이 없어 미완료다. 축소 체결 가정을 연구에 허용할지 사용자 답변을 기다리며, 현 부모 cap을 유지한다. 9/28 자연 PREOPEN·PID와 정상 postclose stage→summary/strict→CAS 및 총 자원 영수증이 배포 후 수용 대상이다.

## 9/27 수량·분할·타임아웃 의미 감시 보강

- `artifact_freshness.initial_quantity_semantics`가 원천일에 실제 적용된 current/부모 정책의 파일 SHA·유형별 ratio/형상/시간 모드를 검증한다. 정규 장후 갱신 stage는 정확 날짜 terminal validator와 완료 거래 분모를 확인하고 `valid_empty`, carry, 후보, 과거 날짜 stage 결손, 변조를 구분한다.
- Main PID/env 불변 archive는 날짜·정책 파일/내용 SHA·원본 검증 상태와 해시를 대사한다. 순차 bundle journal은 해시·수량 합·정책 형상·leg 수·선정 총시간·기한 내 terminal을 검사한다. deadline 전 미종결은 보류, deadline 후 미종결과 늦은 terminal은 경고한다. journal의 수량 보존과 PID 파일 검증은 실제 broker 체결 및 실현 손익 증거로 승격하지 않는다. 감시기는 읽기 전용이다.
- 표적 5건 및 감지기·cron·수량/타임아웃 영향 180건 PASS(4.22초), compile·Ruff·diff PASS. 9/28 정책 읽기 전용 점검 168.47ms에서 부모 ratio/형상/시간 6유형, 정책 파일 SHA `ba72d720…`, PID/stage/bundle `not_observed`를 확인했다. 불변 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-semantic-monitor-20260927` commit `964ed6d116f1afd3be39f1ebf11153da62c75308`을 메인 selector에 CAS 선택했다. 직전 포인터 백업은 `tmp/runtime-release-selection-before-initial-semantic-monitor-20260927.json`. release-set·cron 8경로·9/28 PREOPEN/start print-plan PASS, v2 current/정책 SHA 불변, Main PID 0/inactive. 첫 자연 detector report·PID/주문/terminal·정규 장후 전체 체인은 9/28 사후 확인한다.
- **재리뷰 수정·최종 선택:** 날짜 불명 손상 journal이 오래된 파일이어도 모든 원천일의 경고로 섞이는 문제를 수정했다. 영속 내용의 시작일이 해당 날짜이거나 날짜를 읽을 수 없는 파일의 KST 수정일이 해당 날짜일 때만 귀속한다. 대상일/다른 날짜 손상 fixture 포함 표적 6건·영향 181건 PASS(4.21초), compile·Ruff·diff PASS. 최종 불변 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-semantic-monitor-datefix-20260927` commit `bee25b178da48aaf849a65bdb9c4772af1ec5a00`를 메인 selector에 CAS 선택했다. 이전 JSON은 `tmp/runtime-release-selection-before-initial-semantic-datefix-20260927.json`. 9/28 읽기 전용 사전 검사 168.43ms에서 `policy_selected`·결함 0, release-set·cron 8경로·9/28 PREOPEN/start print-plan PASS, 정책 SHA 불변·Main PID 0/inactive다. `964ed6d1`은 중간 선택 이력이다.
