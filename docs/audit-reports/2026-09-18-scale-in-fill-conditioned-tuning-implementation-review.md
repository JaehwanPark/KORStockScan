# Scale-in 체결 실적 조건부 튜닝 구현·반복 리뷰 — 2026-09-18

실제 AVG_DOWN 체결과 새 평가 가능 outcome가 있을 때만 평가하도록 구현했다. 기존 원천·실제 incumbent·독립 holdout·모델 검증 계약의 구조 결손을 보완했다. **실제 EV 개선/신규 split 활성화는 입증되지 않았다.** 제한 결과 재생성과 immutable release receipt는 `tmp/scale-in-fill-conditioned-20260918/`에 기록한다.

## 구현·리뷰·보완

기존 fact-sync scan에서 actual record ID의 execution/quote/terminal projection을 signed receipt에 함께 보존한다. 장후 순서는 fact-sync→조건부 scale-in→Daily/EV다. 최근20 report date·clean baseline·Main/default custody 실제 receipt-confirmed AVG_DOWN census를 read-only 조회하며 source missing과 체결0을 분리한다. 날짜/mtime 변경이나 오래된 표본 제외만으로 재평가하지 않는다. 후행 terminal/revision은 원 fill date에 결합한다. 새 collector/module/service/provider/order는 없다.

v4는 현재 incumbent primary control과 canonical price/quantity plan을 비교하고 자기 비교를 보존 판단으로 분리한다. 실제 체결량/가격과 관측 marketable BBO/depth·기존 WS epoch/sequence/clock을 대사하며 동일 quote depth를 중복 사용하지 않는다. 모델 원천/lot 결손은 null이다. 공통 cohort·한 tick 불리한 스트레스·일별 ΔKRW/weighted ΔEV와 비용모델 표시를 추가한다. 음수 표본을 제거하지 않는다.

Calibration과 최신 미사용 독립2일 holdout을 outcome 확인 전에 분리하고 episode/늦은 outcome를 purge한다. 기존 grid/수량/예산/TTL/gates를 유지하며 calibration 후보1개만 holdout 검증한다. 실패 후 차순위를 찾지 않는다. v3/동일표본/불충분 holdout는 runtime refresh 근거가 아니다. 실제 적용 버전의 경제성·carry age·operator/하드 safety는 기존 계약을 유지한다.

실제 첫 재생성에서 기본 태그 전용 필터가 Main `SCANNER` 실제4건을 체결0으로 누락한 결함을 발견했다. 해당 결과를 superseded로 기록하고 기존 Main SCANNER/default custody를 포함하며 widget/episode/manual을 제외하도록 수리했다. 실제 inventory custody 회귀를 추가하고 수정 release에서 재생성한다. 최근20 report date DB census는5건(8/21 qty1 추가)이며9월 기존4건과 분모를 분리한다. 현재 DB의 COMPLETED2건은 sell_time가 결손이므로 HOLDING/시간대기로 바꾸지 않고 terminal-clock source gap으로 표시한다.

재리뷰에서 음수 스트레스 표본 누락, 동일 포지션의 과거 시장가로 후속 지정가 재시도를 제외할 가능성, projection target-date 덮어쓰기, cursor의 source-gap 은폐, 날짜별 정책 적용일/영수증/hash 검증을 보완했다. 정상 conditional skip에서 불필요한 코드 workorder를 만들지 않고 구조적 source gap은 남긴다. Report/policy 원자적 기록·source lock·immutable evaluation snapshot을 사용한다.

## 검증·배포 경계

최종 영향 producer/consumer/wrapper pytest860 PASS, 기존 snapshot emitter5 PASS를 확인했다. 최종 hash handoff 회귀·compile/bash syntax/diff/print-only parser receipt를 기록한다. 검토 범위 finding0은 실제 경제성의 수락이 아니다. 전체 거래/provider suite·5.7GB pipeline/537MB threshold 재스캔·전체 장후 chain·Main/active worker restart·주문·수동 env/guard/calendar 변경·외부 sync는 수행하지 않는다.

## 실제 결과·다음 조치

Read-only history census의 실제 AVG_DOWN EXECUTED/receipt_confirmed4건은 frozen anchor의 주문번호로 확인된 market-like이고3건은 요청량1이다. 현재 applicable/paired0이며 EV·일별 Δ순익은 null이다. 보유 미성숙과 시장가/qty1·가격/모델 원천의 구조 결손을 구분한다. 표본 확보 주문/수량 증대는 하지 않는다.

다음 사용자 예정9/21 정책은 원 source9/17의 incumbent unsplit base-order 보존 정책으로 준비한다. Available 날짜별 정책은 신규 split 활성화/positive edge/전체 PREOPEN 허용이 아니다. 전체 integrated-entry handoff·native resource guard 중단·Main PID/자연 소비는 별도 owner이며 과거 PASS로 최신 실패를 덮지 않는다. Executable owner는 `KiwoomCommonHealthOpportunityCostAcceptance0917` 하나를 유지한다. 유효 지정가 full-fill·기존 가격/lot/비용 원천과 미사용 독립 날짜가 확보될 때 평가한다. 경제성 ETA=null이다.
