# 비삼성 최초 신호와 현행 청산 분리 연구

## 1. 범위와 고정 입력

- 사용자 다음액션 실행. 기존 관측 생성기의 비삼성6,550건·`pullback_p60_v0` 교체형·부모 정책을 고정한다. 삼성/보조 AI는 제외한다.
- 학습9/29·9/30, 비교10/2는 이미 사용한 날짜다. 새 임계치·평가 단위·가설의 후단 최적화를 하지 않는다.
- 산출물은 `tmp/non-samsung-first-signal-exit-20261005`. 소유 코드는 `src/engine/scalping/entry_first_signal_exit_research.py`, 회귀는 `src/tests`다. 기존 봉인 모듈·원천·정책 파일은 수정하지 않는다.

## 2. 최초 신호

- 같은 날짜/종목/venue/session/request code/원 bundle에서 parent 또는 candidate ENTER가 연속 관측되는 구간을 하나의 **관측 신호 사건**으로 묶는다. 두 판정 모두 비진입이면 구간을 닫는다.
- 사건의 시작/종료는 당시 행동과 시각만 사용한다. 미래 가격·승패는 사용하지 않는다. 사건별 각 정책의 첫 ENTER를 고정하고 기존 선택 관측과 비교한다.
- 첫 관측 이전 상태와 관측 사이 상태는 추정하지 않는다. 첫 행에서 시작한 사건은 좌측 검열, 관측 공백은 길이를 기록한다. 물리적으로 연속된 시장 사건 또는 독립 native 기회라고 주장하지 않는다.
- 같은 원천의600초 축소가 성공 신호를 없애는지, 최초 신호를 선택해도 개선이 유지되는지 분리한다. 두 정책이 모두 진입하는 동일 사건에서는 진입 시각 차이를 비교한다.

## 3. 현행 청산

- 현재 선택 release 및10/6 prepared bootstrap의 실제 trailing receipt를 hash로 고정한다. 현재 값은 start0.4%, weak0.4%, strong0.8%, classifier `mechanical_strength_v2`다.
- 기본 Main SCALP의 준비된 초기 stop은 순수익-1.4%, emergency-2.4%다. SCANNER/기존 보유의 별도 stop/state에는 이 값을 덮어쓰지 않는다. 기본 SCALP를 가정한 가격 CF와 전체 운영 재현을 구분한다.
- 원 진입 ask와 원 전비용을 사용한다. peak는 진입 후 실제 체결 가격에서만 올리고, 청산은 보관 bid와 shared trailing 함수로 평가한다. 가능한 경우 기존 M1 classifier의 원 입력을 재생한다.
- archive의 epoch/sequence는 archive 자체 영역이다. Main epoch로 바꾸지 않는다. exact item/시각·fresh quote·순서·gap을 검사하며 연속성 결손 이후 첫 청산을 확정하지 않는다.
- 현행 가격 판단 재생에도 계좌·주문·fill/cancel·AI holding·기존 보유 stop/plan 전체 상태가 없으면 전체 운영 성과는 미입증으로 표시한다. 실제 fill/손익을 만들지 않는다.
- 보관 연속 원천이 불충분한 경우에는 완성봉으로 동일 shared trailing 수식의 weak/strong 두 폭을 **조건부 가격 시나리오**로 비교한다. 두 폭은 이미 운영 중인 값이며 후보를 새로 고르지 않는다. 첫 부분봉·같은 봉 내 순서·가격 gap과 종료 미도달을 보존한다.
- 기존 +0.1% 목표/-0.7% gross stop과 동일 진입·동일 평가 가능 분모로 비교한다. 60분은 연구 관측기간이며 운영 강제 시간종료로 해석하지 않는다.

## 4. 완료 기준

사건 및 고정 진입 manifest → 원천/정책 계약·구현 → 리뷰/수정·표적 회귀 → 격리 재생 → 날짜별 최초/반복 영향·청산·결손 대사 → 재리뷰·문서 parser. 정책 배포·프로세스 기동·API/provider·새 원천 수집은 실행하지 않는다.
