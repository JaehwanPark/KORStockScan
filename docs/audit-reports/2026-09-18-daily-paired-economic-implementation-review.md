# Daily paired 경제성 구현·소비·배포 리뷰

2026-09-18 KST. 사용자 승인 범위는 D0–D6 구현·review/fix/re-review·검증·commit/push·immutable 선택 배포 및 제한 장후 결과/다음 거래일 정책 발행이다. 주문·bot restart·수동 PREOPEN/env/provider/guard 변경은 수행하지 않는다. 실행/정책 최종 receipt는 `tmp/daily-paired-economic-20260918/closure.json`이며 source commit·selected root·적용일·각 소비자 SHA와 실제 PID 미소비를 분리한다.

## 구현과 리뷰

- D0/D1: 현재 calibration projection에서 퇴역 family를 제거하고 historical source와 기존 applied manifest는 보존한다. 각 row의 방향/calibration state, economic status, runtime authority는 별도다. 결손/비대상/미성숙/소표본/동일 정책에 null·owner/closure를 전달한다. OFF/observe 상태의 sample 증가가 적용 권한을 만들지 않는다.
- D2/D3: 가격은 기존 exact price selection proof의 동일 opportunity union·shared budget·cost·tail·stress·chronological holdout을 재사용한다. 거래일별 cash delta와 전체 union cash delta conservation도 검사한다. Scale-in은 기존 actual-fill-conditioned runtime refresh proof를 소비한다. 원 owner proof가 없는 수량/holding 등은 causal 값 null이며 새로운 grid나 threshold를 만들지 않는다.
- D4: source metrics/current/recommended/source date와 Daily·가격 replay·scale-in code SHA로 평가 fingerprint를 만든다. 동일 revision은 평가 시각/SHA 재사용, late cost/terminal revision은 family 증거를 무효화한다. 기존 CLI의 bounded refresh는 producer CAS·Daily CAS·byte SHA predecessor를 보존한다.
- D5: Calibration/EV/runtime summary/PREOPEN/strict 검증과 post-apply attribution에 section을 전달한다. 계약 누락/변조·stale input·positive EV이나 cash 부재는 fail closed다. 기존 별도 승인 baseline/operator/negative disable은 기존 guard를 유지한다. Strict parse warning이 AI pass로 가려지는 결함도 수정했다.
- D6: 관련 기존 테스트를 확장하고 실제 가격 producer→replay→selection fixture의 ΔEV와 거래일별 순익을 검증했다. 이는 모델 계약 회귀 증거이며 자연 거래 개선 실적이 아니다. Release와 정책 결과는 아래 receipt로 닫고 미래 실제 소비/경제성은 기존 checklist OPEN이다.

## 운영 원천과 경제성 경계

9/17 scale-in actual fill5·applicable0은 시장가 계열/qty<2 등 지원 범위 밖 체결 census이며 기다려서 같은 과거 fill이 평가 대상이 되지 않는다. 현재 entry split 실행 모델 source gap은 원 operating execution/model owner의 원천 closure가 필요하다. 다른 family의 outcome maturity와 원천 손실·unsupported 비교를 동일 waiting으로 합치지 않는다. Compact의 원천 제외21건과 dated incumbent carry는 독립 consumer owner가 표시한다. 기존 policy loader가 다음 거래일 정책을 읽는 것과 PREOPEN 실행/PID/actual 비용 후 신규 개선은 별도다.

## 검증

최종 targeted pytest·compile·diff·print-only parser 및 immutable release/routing·bounded regeneration·strict consumer 증거는 `tmp/daily-paired-economic-20260918/`에 저장한다. 원천 비교 불가를 개선0이나 valid-no-edge로 바꾸지 않는다. 전체 native expensive chain/주문/provider 호출·외부 Project/Calendar sync는 수행하지 않는다.
