# 최초 수량 정책 폐루프 재리뷰 — 2026-09-27

## 결정 범위

작업공간에서 최초 v2/갱신 정책의 변경 형상·유형별 cap·순차 BUY 시간표·정확 terminal·정규 장후 stage→strict→CAS→PREOPEN 연결을 구현했다. 현재 운영 selector `c0d88893`와 기본정책 `current.json`은 이 문서 작성 시점에 그대로다. 실제 PID 소비·자연 주문·실현 EV는 별도 영수증으로 판정한다.

## 결함 재리뷰와 수리

- 변경 형상을 고른 초기 후보를 롤백용 부모 기본정책 생성기가 거부하던 경로를 수리했다. 부모 기본정책은 부모 형상을 보존하고 v2가 후보 형상을 봉인한다.
- 첫 BUY 직전 CAS `SUBMIT_INTENT`와 대상 index, 결정 attempt·policy SHA·probe 포함 순차 시간표를 기록한다. 브로커 호출 예외/불확실 응답/저장 실패는 재제출 없이 broker·owner 조회로 남긴다. 후속 leg는 이전 leg의 정확 terminal, 현재 수량·현금·route/epoch·P1 가격·buy/exit/operator 안전을 다시 확인한다.
- 실제 동적 가격 leg의 broker terminal bridge가 journal에 필수인 owner client intent ID를 빠뜨리는 결함을 재리뷰에서 찾았다. terminal state에 원래 intent ID와 제출 가격을 보존하도록 수리하고, 실제 bridge 출력→영속 전이→다음 leg 허용을 잇는 회귀를 추가했다.
- v2/갱신 allocator의 유형 행 영수증 누락과 갱신 부모의 `initial_policy_refresh_loaded` 상태 불일치를 수리했다. 수량 cap 10/15/20%는 부모 5단계와 25% 절대 상한 안에서만 소비한다. ratio의 데이터 기반 선택 생산자는 여전히 부모 carry다.
- 영속 첫 BUY 시작 시각을 정확 주문번호·attempt·계획 SHA·수량 정책 SHA에 결속해 장후 경로가 구 request-to-sent 추정 시각보다 우선 읽는다. T 후보는 같은 유형 30건 이상, 모델 coverage 80%, 정확 시작 시각 전수, 검증 가격 교차, 3개 독립 날짜, 보수적 비용 후 EV·원화 순익 우위가 있을 때만 고른다. 현 데이터는 정확 시작 원천 0건이므로 기존 프로필 시간을 유지한다.
- 갱신 stage 적격 후보만 최종 strict 이후 선택 코드 릴리스 root 대사와 release-set 잠금 아래 current CAS로 적용한다. 부모 archive를 재귀 검증하고 재실행/부모 충돌을 거부한다. `carry_parent`는 pointer를 바꾸지 않는다.

## 데이터 기반 결과와 성능

- 2026-06-05 클린 기준 이후 9/23까지 완료 첫 거래 387건·익절 244건. 수량 replay validator와 타임아웃 연구 validator PASS, replay 내용 SHA `5ea85f0fc068d46b39ad6900747ae74ed68160df3500a4c612989479f50c67dd`. 6유형 모두 부모 형상이며, `KRX_PARENT`의 900초는 1건 수준의 **모델 연구 최고 후보**일 뿐 실행 정책 T가 아니다. 영속 시작 시각 지원 거래 0건이다.
- 한 번의 원천 스캔을 공유한 격리 재생: 수량 replay 378.223초, 타임아웃 후보 34,056건 0.580초, 추가 pipeline 스캔 0회. 프로세스 전체 wall 381.27초, CPU user/system 354.03/2.69초, peak RSS 151,960KB, swap 0. 동일 전수 원모수·형상 선택은 직전 봉인 실행과 같다. 외부 `ka10080` 193그룹 전체 수집은 앞선 별도 실측에서 193/193 응답, wall 124.98초·peak RSS 약 432MB였다. 이 측정은 정규 threshold postclose 전체 체인 시간이 아니다.
- 9/27 효력 이후 완료 거래 0건의 격리 갱신 stage는 validator PASS, `carry_parent`, 후보 파일 없음, wall 0.79초·peak RSS 134,108KB였다. 새 적용 세대 자연 경제성은 관측되지 않았다.

## 검증·남은 판정

격리 helper/실제 pipeline 원천 결속 및 기존 주문 회귀를 포함한 광역 pytest 1,176건 PASS와 terminal 수정 영향 회귀 50건 PASS, wrapper `bash -n`, Python compile, 변경 신설 모듈 Ruff, `git diff --check`, print-only 문서 parser를 수행한다. 최종 릴리스 commit/selector/PREOPEN 결과는 실제 완료 후 별도 기록한다. Kiwoom 주문 wire/parser는 변경하지 않았다. 공식 `Kiwoom-Securities/Kiwoom-REST-API` commit `953e5dbff123f437ab4d11a78a95191a685eb51f`의 `kiwoom/_data/kiwoom_api_spec.json` `kt10000/kt10003`, `postman/kiwoom-openapi.postman_collection.json`, `kiwoom/specs.py`를 2026-09-27 14:33 KST에 확인했다. KRX/NXT/SOR route, 지정가/시장가 코드, 수량 단위와 7자리 주문번호는 기존 local 계약을 유지한다.

실행용 코드 릴리스 선택·다음 PREOPEN 파일 SHA, 실제 Main PID 소비, 자연 주문/terminal, 비용 후 결과는 각각 별도로 기록한다. 유형별 cap의 데이터 기반 선정과 자연 적용 후 T 갱신은 적격 새 거래가 없으면 부모 carry로 남긴다.
