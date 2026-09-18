# 삼성 owner 승인 수량 기준 native 경제성 timing 구현 리뷰

Source target: 2026-09-18. As-of: 2026-09-19 KST. [owning plan](../proposals/samsung-owner-quantity-native-economic-timing-plan-2026-09-18.md). 사용자가 승인한 비교는 owner별 native 승인 수량 독립 비교이며 shared Samsung cash allocation은 없다.

## 원천 결손과 수리

| 경계 | 수리 | 회귀 증거 |
|---|---|---|
| 실제 체결 leg만 anchor | confirmation 전 parent opportunity 및 차단/거절/미체결 분모 | native runtime 기존 fixture의 frozen root/quantity source assertions |
| arbitrary first-hit/horizon 청산 | native limit/market BUY·weighted tick/pooled target·reserve/보유 노출 | native source→canonical projection→replay tests |
| 활성 exit pin이면 일괄 unsupported | 선택 pin 인계 + 기존 quote/pressure/stagnation arithmetic + 측정 action clocks | active pin target-path 및 programme action tests |
| 공통 guard 통과 전 CF 제출 | 원 native guard admission barrier·후속 veto 분리 | early CF BUY 금지/공통 block 회귀 |
| ADD guard의 다른 leg 재사용 | stage별 receipt 및 마지막 weakness check 뒤 허용 | original widget 3-leg 및 cross-stage 차단 회귀 |
| SOR prearm plan/source 누락 | deferred opening-price resolver의 최초 실행 시점 CAP·raw bar identity 보존 | 원 morning producer/reload 회귀 |
| 날짜별 native policy SHA로 모델 분열 | semantic native rule + quantity/cost/route/code/programme scope | dated receipt 동일 scope/target 변화 다른 scope 회귀 |
| target-only 최초 모델에 영구 고정 | 새 action의 chronological calibration/holdout에 model prefix 갱신 | 실행 가능한 fit/clock source 계약 |
| 늦게 완료한 carry의 actual 연결 | 원 checkpoint exact root/as-of actual refresh, date-reset terminal 보존 및 기존 보고서 sealed completion history | before/after as-of·중복·다른 계약 차단 회귀 |
| 과도한 observability 누적 | programme unchanged interval 압축·bounded path·terminal lookup reuse | 100 owner ticks→1 interval·cadence 보존 회귀 |

원 Kiwoom request/response parser/API/WS registration은 수정하지 않았다. native guard·수량·quantity authority·budget/custody·operator veto·기존 stop/target/override·holdout은 유지한다. src/engine root Python module/새 producer/서비스/DB/collector를 추가하지 않았다.

## 계산과 선정의 증거 구분

S0–S6의 지원 full-fill 입력 계산·model/candidate holdout·native policy 소비 및 fallback은 통제 source writer/canonical projection과 기존 runtime fixture로 검증한다. active programme pin을 유지한 동일 native scope에서도 계산→모델 holdout→별도 후보 holdout→dated reader/loader가 동작한다. 이러한 fixture는 자연 표본·실제 이익·인과적 EV 개선 증거가 아니다.

지원 범위 밖 partial BUY/취소 race/remainder/overnight CF replay는 구체 blocker/null이다. 측정한 action clock이 없으면 그 action을 실제 요청하는 경로만 차단된다. 구현된 action source writer와 양쪽 chronological 검증 계약의 표본 부족은 자연 검증 OPEN이다. 구현되지 않은 generic 청산/새 queue 모델을 이미 지원한다고 보고하지 않는다.

## 검증 및 배포

최종 영향 범위 회귀 **872 PASS**, 마지막 admission 재확인 및 own-registry identity 보완 회귀 **231 PASS**. carry/date-reset 누적 연결 보완 회귀 **257 PASS**가 추가로 통과했다. 이 suite들은 중복이 있으므로 합산 표본 수가 아니다. owned 16 Python compile, Ruff F821/F823/F811, diff whitespace, local links 및 print-only parser(기존 stable ID의 current OPEN owner 1개)가 통과했다. 통제 source writer→canonical→모델 검증→별도 후보 검증→dated loader의 활성/거절/fallback 상태를 포함한다. 자연 경제적 성과를 주장하지 않는다.

정규장 원 leg에 없는 route는 실제 native owner policy로 **사본에만** 결속한다. 위젯 KRX 판단 호가와 SOR execution depth를 분리하고, SOR 경로 부재를 KRX 호가로 대체하지 않는 회귀를 추가했다. 차단 후 real BUY가 허용된 recheck는 최초 허용 시각부터 admission을 갱신한다. 원 checkpoint identity 충돌은 실제 손익 평가에서 제외한다.

Commit/push/immutable deployment와 제한 재생성의 기계 검증 receipt는 아래 evidence directory에 기록한다. 최종 receipt 전에는 selected release·PID 소비·새 정책 후보가 생성됐다고 주장하지 않는다.

Evidence owner: `tmp/samsung-owner-economic-timing-20260918/`. 실행 중 배포본 수정·수동 bot restart·주문·조기 PREOPEN 확정·Project/Calendar sync는 수행하지 않는다. 현재 9/19 checklist 부재를 보고하며 다음 자연 acceptance는 기존 stable ID를 [9/21 checklist](../checklists/2026-09-21-stage2-todo-checklist.md)에 인계한다.

## 자연 OPEN 및 closure test

1. 다음 영업일 최초 eligible 신호와 차단/recheck마다 frozen root·quantity receipt·cost/code/exit pin·admission·stage guard가 실제 checkpoint에 존재하는지 확인.
2. 자연 full-fill native terminal의 own registry/clock/price/provenance가 projection에 연결되는지 확인. selected pin 자체의 unsupported 전수 제외가 재발하면 implementation defect로 재개.
3. 독립 model/calibration/candidate holdout의 chronological coverage/floors를 충족한 뒤에만 신규 후보를 평가. valid no-edge와 source gap/unsupported/pending/insufficient sample을 구분.
4. 실제 다음 적용일 policy hash와 native scope/code/quantity/cost/programme pin을 PID/cwd/source provenance 및 실제 행동에 대사. selector·unit 설정 변경만으로 PID 소비를 주장하지 않음.
5. 실제 완료 root를 버전별로 중복 제거하고 rolling/cumulative 비용 모델 순익·노출·tail·모델 오차를 확인. broker settlement 비용을 별도로 확보하기 전 frozen fee 순익을 settled cash net이라고 부르지 않음. 인과적 개선은 적합한 비교가 확보될 때까지 null.

배포 후 추가 재리뷰 finding: date reset으로 늦게 완료한 원 root가 유실되는 경로를 발견하여 보완했다. original `_roll_date`의 native state는 그대로 초기화하되 research terminal history만 128개로 보존한다. 기존 timing 보고서의 sealed actual completion history를 한 번 bounded 읽어 checkpoint 교체 뒤에도 누적 평가에 연결한다. 새 ledger/DB/producer·raw rescan은 없다. exact cSHA/as-of/own terminal economic identity를 대사하고 충돌 tombstone은 이후에도 제외된다.
