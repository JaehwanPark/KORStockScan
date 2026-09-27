# 최초 수량 정책 폐루프 재리뷰 — 2026-09-27

## 결정 범위

최초 v2/갱신 정책의 변경 형상·유형별 cap 소비·순차 BUY 시간표·정확 terminal·정규 장후 stage→strict→CAS→PREOPEN 연결을 구현했다. 불변 코드 릴리스 `58dbddd642205129d73c495be98c5b37e4c75ed9`를 메인 selector에 선택하고, 이어 최초 v2 정책을 `current.json`에 CAS 적용했다. 실제 PID 소비·자연 주문·실현 EV는 별도 영수증으로 판정한다.

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

- 선택 릴리스: `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-closed-loop-20260927-review`, commit `58dbddd642205129d73c495be98c5b37e4c75ed9`. 직전 selector 원본은 `tmp/runtime-release-selection-before-initial-closed-loop-20260927.json`에 봉인했다. release-set PASS, cron 필수 8경로 PASS, 9/28 PREOPEN print-plan은 새 commit을 가리킨다. Main PID는 9/27 15:40 KST `0/inactive`였고 실제 소비를 주장하지 않는다.
- 활성 `current.json`은 `initial_entry_quantity_current_v2`, 내용 SHA `91d195d1de7215360e7ee625dc7636e41bb642f1c709b74666e470490052ebf3`, 파일 SHA `a34d980f13be8c4929012557f23958871c832edb118058f498420ab078b83585`이다. 9/28 로더는 최초 v2 파일 SHA `ba72d720a4c11dbcfd18a667d2f47a648c0e7b792fe9a3edbb7193f674870cca`를 검증했다. 모든 유형은 데이터 선정대로 부모 5단계 수량·부모 주문 형상·기존 프로필 타임아웃이다. 실데이터에서 달라진 수량·분할·T는 없다.
- 새 선택 릴리스에서 9/27 갱신 장후 생산자를 다시 실행했다. 0건 `carry_parent`, stage validator PASS, candidate 없음, wall 0.80초·peak RSS 134,292KB다. 이를 일반적인 정규 장후 전체 체인 측정으로 확대 해석하지 않는다.
- 9/28 기존 bootstrap 파일은 9/26에 생성되어 새 current를 담지 않는다. 읽기 전용 검증은 `initial_quantity_policy_env_mismatch`, `owner_mismatch`, `receipt_mismatch`로 실패했다. 선택 릴리스에서 9/28 `build_manifest`를 읽기 전용 재구성하면 정확한 새 파일 SHA가 env와 receipt에 들어간다. 정규 9/28 PREOPEN이 동시 family 생산과 bootstrap을 새로 발행·검증한 후 Main PID가 파일 SHA를 소비해야 적용 수용이 닫힌다. 미래 날짜 bootstrap만 조기 발행해 정상 장전 절차를 대체하지 않는다.
- 유형별 cap의 데이터 기반 선정은 현재 생산자가 부모 carry이므로 정책 자동 갱신 범위에 남아 있다. 자연 적용 후 T 갱신은 적격 새 거래의 정확 시작 시각과 terminal/economics가 생길 때만 가능하다.
