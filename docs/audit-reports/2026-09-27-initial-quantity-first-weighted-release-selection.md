# 최초 수량 형상 선택 허들 수리 릴리스 — 2026-09-27

## 결정과 범위

초기 수량 정책 생성의 형상 선택에서 후속 갱신용 기존 정책 대비 우월성·검증된 가격 교차 허들을 제거했다. 최초 생성은 클린 기준 이후 완료 거래 전수를 모수로 두고, 익절 거래의 실현 순이익 원화를 가중치로 한 보수적 후보 수익률 중 관측된 형상을 선택한다. 비교 가능한 익절 거래가 없는 형상, 동률, `SAFE_UNKNOWN`은 `parent`를 유지한다. 후속 갱신 허들은 유지한다.

불변 코드 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-first-weighted-20260927`의 commit `c0d88893f816fbf2c86810728ee5a435e3092321`을 메인 selector에 선택했다. 이 릴리스는 최초 생산자와 테스트만 이전 선택 릴리스 `538bad38`에 추가한다. 활성 초기 정책 파일 SHA `dcd937b4015eb0869a38ce4ff3d2ffc62baf2933b9a63668ba2c993e90c52e39`와 수량·주문 형상·프로필 타임아웃은 바뀌지 않는다. 선택 영수증은 `data/runtime/runtime_release_selection.json`, 이전 선택 백업은 `tmp/runtime-release-selection-before-initial-weighted-20260927.json`이다.

## 데이터·코드 검증

- 2026-09-23까지 클린 기준 이후 완료 거래 387건·익절 244건을 다시 읽었다. 입력 manifest와 유형 모수 `SAFE_UNKNOWN=350`, `KRX_PARENT=32`, `KRX_THIN_HIGH_TICK=5`가 기존 재생과 같고, 6개 유형 모두 `parent`를 다시 선택했다. replay 및 후보 validator PASS. 측정 368.187초, 최대 RSS 154,752KB, swap 0. 상세 내부 영수증은 `tmp/initial_quantity_first_weighted_selection_rereplay_20260927.json`이다.
- 릴리스 내부의 수량 정책·타임아웃·장후 wrapper·실행 수량 테스트 160건 PASS. Python compile, 변경 파일 Ruff, `git diff --check`, 기존 초기 정책의 9/28 파일/SHA 로더 검증 PASS. 선택 후 release-set PASS, cron 필수 8경로 PASS, 9/28 PREOPEN `--print-plan`이 이 commit을 가리킨다. 읽기 전용 장전 manifest의 초기 정책 SHA도 동일하다.
- 작업공간의 별도 실주문 안전 bridge에서는 취소 intent 영속 실패 시 broker 호출 차단, 불확실한 취소 재전송 차단, 계획 수량·가격·경로 일치, 전량 체결 시 `FILLED` 상태 보존을 수리했다. 새 bundle이 붙은 상태에서 구 병렬 BUY loop로 진입하면 broker 호출 전에 차단한다. 격리 테스트 14건과 기존 주문 회귀 897건은 각각 PASS. 이 bridge는 본 릴리스에 포함하지 않았고 아직 최초 BUY intent·후속 순차 leg 호출 및 재시작 복구가 없다.

## 적용·수용 경계

릴리스 선택은 코드 배포이며 선택 시 Main PID 영수증은 `not_attested`다. 실제 PID의 정책 소비·자연 주문·체결과 비용 성과는 9/28 정상 기동 이후 별도로 확인한다. 유형별 수량×분할×총시간 변경 정책에는 단일 publisher/current CAS·PREOPEN 로더와 순차 실주문·terminal·복구가 아직 필요하다. 자연 소비의 부재를 해당 코드 미완료의 이유로 삼지 않는다.
