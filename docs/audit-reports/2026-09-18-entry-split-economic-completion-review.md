# Entry split 경제성 구현 완결 리뷰

2026-09-18 KST. 사용자 승인: 미완료 구현·반복 리뷰/보완·영향 검증·관련 commit/push·immutable successor 선택 배포·source9/17 결과의 prepared-effective9/21 정책 준비. 봇 재시작·주문·조기 PREOPEN 확정은 제외한다.

## 구현 판정

| 항목 | 코드 완료 및 검증 계약 |
|---|---|
| ES0 | bounded 원자 계획·native journal·완료 SELL receipt census; invalid/conflict 분모 보존. historical invalid3 상세는 미확정이며 유효0으로 바꾸지 않는다. |
| ES1 | 코드/청산/비용/scope 버전, 실측 calibration 최대 오차 고정, chronological model holdout20건·coverage80% 및 이후 별도 candidate holdout. |
| ES2 | frozen 운영 context/TTL/budget/cost/보유 상태, 자연 depth의 기존 관측 입력, compact→durable BUY/SELL→완료 receipt 보존. |
| ES3 | 실제 운영 holding interpreter로 독립 CF 청산; 당시 비용 owner 순익, reserve·holding capital 계산. actual SELL을 CF에 붙이지 않는다. |
| ES4 | 동일 총수량/예산 guarded weights·원래 가격4군, paired 순익/EV/tail/노출/참여율. 스트레스와 양쪽 모델 오차를 차감한 보수 하한 및 후보30건·coverage80%·독립 holdout. |
| ES5 | 한 predecessor state의 compact witness와 late completion/cost revision; hash 결속·충돌 격리·holdout 재사용 금지·동일 revision cheap reuse. |
| ES6 | signed 후보/정책 generation→Daily→PREOPEN reader/audit→장중 loader; supported quantity/scope/hash 검증 및 keep-original fallback. |
| ES7 | 실제 적용 policy/PID/version별 episode 중복 제거·rolling20 completed source days/cumulative 비용 차감 순익/EV/tail/노출/모델 오차 경로 구현. 미래 자연 적용과 완료 손익은 OPEN. |

지원 범위는 Main real의 초기 총수량 완전체결, 정확 frozen 운영 정책·같은 venue/session·관측 market inputs·독립 full SELL까지의 보유 경로다. partial/no-fill CF의 cancel ack/late fill, 후속 ADD/partial SELL, 누락 AI/시장 입력은 현재 재현 근거가 없어 구체 unsupported/pending/null로 반환한다. 모든 입력을 차단하지 않는다. 합성 지원 입력은 실제 경제성 계산→모델 검증→후보 선정→활성 정책→Daily/PREOPEN/장중 적용까지 통과한다.

비용 provenance는 당시 loaded trade profit configuration이며 broker settlement 확정과 분리한다. 허용 오차는 선행 calibration에서 고정한 경험적 envelope이며 holdout을 보고 확대하지 않는다. ΔEV 하한은 stress와 양쪽 모델 오차를 차감한 관측 최솟값으로, 통계적 신뢰구간으로 표현하지 않는다. actual model error 미지원이어도 유효 실제 완료 손익은 평가하며 causal uplift를 주장하지 않는다.

## 리뷰 및 검증 증거

1. 초기 가격-arm 실패로 운영 재생까지 유실되는 경로 분리, frozen qty/budget/provenance/hash/TTL 검증 보완.
2. baseline seed가 비활성 정책 상태에서 사라지는 문제, durable BUY/SELL snapshot allowlist 유실, naive KST 완료 날짜 및 UTF8 hash 차이 수정.
3. partial holding frame·ADD guard 우회 차단, 최초 model/calibration 날짜 및 late 완료 availability leakage, 모델 버전 변경으로 동일 candidate holdout 재시험하는 경로 수정.
4. source gap/null/unsupported/insufficient/valid-no-edge 분리, predecessor hash/current source quality binding, 자연 관측 입력 frozen metadata와 compact witness 크기 보완.

영향 회귀535건 및 소비 계약19건 통과. Python compile·git diff check와 문서 print-only parser 증거 및 병행 변경 병합 후 재검증은 아래 evidence directory가 소유한다. 합성 활성 정책 검증은 자연 표본이나 경제적 성과가 아니다. 새 Python module·서비스·DB·collector·장후 stage를 만들지 않았다. 기존 quantity/budget/custody/guard/operator override/holdout을 보존했다.

## 배포·재생성 및 자연 OPEN

선택 배포와 제한 재생성의 최종 commit/root/router·artifact hash·준비 정책 상태는 `/home/ubuntu/KORStockScan/tmp/entry-split-economic-completion-20260918/validation.json`, `deployment.json`, `regeneration.json` 및 각 command log에 기록한다. source9/17의 기존 결손은 소급 생성할 수 없으며 candidate0이면 blocker에 따라 inactive keep-original 정책을 준비한다. 양수 정책·실제 EV 개선은 보장하지 않는다.

다음9/21 OPEN은 정상 PREOPEN 정책 소비→자연 Main 주문/관측 원천→model calibration/holdout→별도 candidate holdout→실제 적용 버전별 mature completed cost 성과다. owner는 기존 entry split report/policy generation 및 KiwoomCommonHealthOpportunityCostAcceptance0917 체크리스트이며 새 중복 스케줄을 만들지 않는다. closure는 exact version/hash/PID 및 비용 완료 receipt 연결, source-quality/coverage/model error/독립 holdout 통과다. 휴장·미적재 ETA는 null이다. 전체 postclose의 다른 작업 blocker와 본 작업 코드 완료는 구분한다.

광범위 raw 재스캔·성능 검사·provider 호출·실제 주문·봇 재시작·full PREOPEN·외부 sync는 실행하지 않는다.
