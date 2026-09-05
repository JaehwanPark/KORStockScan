# 장후작업 상세검토 진행 목록

작성 기준: `2026-09-05 KST`

목적: 설치된 장후 자동화의 각 실행 단위를 순서대로 검토하면서 목적·목표·기대효과·운영상태·상세검토 상태·연결 lock을 한 표에서 추적한다. 실행 원칙과 owner는 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1~§8과 [2026-09-07 체크리스트](../checklists/2026-09-07-stage2-todo-checklist.md)가 우선한다.

## 1. 이번 갱신 판정

- `Bot stop`부터 `AVG_DOWN recovery calibration`까지 13개 실행 단위의 코드·계약 점검과 허용된 보완을 완료했다.
- 1~9번은 기존 동작과 격리·재현·source-only 권한 계약을 확인했다. 별도 전략 또는 runtime 변경은 없었다.
- 10~12번 PYRAMID/source-quality 구간은 exact event·BBO/resolver·terminal·비용·candidate identity를 보완했다. 2026-09-04 구형 원천은 exact-ready 0건이므로 경제성 실패가 아니라 과거 source contract 결손으로 유지한다.
- 13번 AVG_DOWN은 production cadence capture, frozen full-policy snapshot, 독립 A/B/C 상태 재현, 격리된 기존 holding/exit policy adapter, source audit, postclose report, AI/PREOPEN/verifier 연결을 구현했다.
- 구현 종결은 실적용·수익개선 종결이 아니다. 2026-09-05는 토요일이므로 새 자연 runtime frame, paired exit, 당일 장후 AI, 다음 PREOPEN 선택, PID 소비 및 post-apply EV는 아직 관찰되지 않았다. 이 확인은 OPEN `AvgDownPairedExitRuntimeEvidence0907`과 `PyramidEconomicFeasibilityHandoff0907`이 소유한다.
- 이번 재검증은 관련 AVG_DOWN/PYRAMID/holding/scale-in/source-quality/daily-AI/PREOPEN/verifier 테스트 `1,964 passed`, 기존 외부 pandas-ta 경고 1건이다.

## 2. 상태와 lock 표기

| 표기 | 의미 |
| --- | --- |
| `구현·점검 종결` | 요청한 코드·계약 보완과 targeted validation 완료 |
| `자연증거 대기` | 구현은 닫혔지만 다음 자연 거래일 산출물·runtime 소비·EV는 미확인 |
| `상세검토 대기` | 현재 자동실행 상태만 식별했고 이번 순차 상세검토는 아직 시작하지 않음 |
| `OFF` | 현재 wrapper/cron 정책상 비실행 |
| `RETIRED` | 자동실행 경로 폐기 |
| `E1` | owned-log writer/rotation lock; 전체 wrapper 실행 mutex는 아님 |
| `E2` | threshold resource guard와 artifact generation lock |
| `E3` | 개별 intraday `tmp/run_*.lock` |
| `E4` | rising-missed/PYRAMID 공용 `tmp/intraday_heavy_analysis.lock` |
| `E5` | tuning-monitoring 단일실행 lock |
| `E6` | 날짜별 AI entry replay lock |
| `E7` | systemd oneshot 단일 인스턴스 |
| `E8` | system metric writer lock |
| `E9` | log/storage maintenance lock |
| `P14/P18` | 기존 PYRAMID quality/operator lock |
| `P15` | 기존 rising-missed normal BUY bridge lock |
| `P16/P17` | scalp-sim AI budget/candidate-window lock |

## 3. 상위 장후 실행 목록

아래 표는 20:10 main wrapper 내부 단계만 나열했을 때 빠지는 병렬·후행 작업을 포함한 상위 스케줄이다. 15:10 sim preclose는 장후 체인의 선행 작업으로만 병기한다.

| 시각 | 작업/owner | 목적·목표 | 기대효과 | 운영상태 | 이번 상세검토 상태 | 연결 lock |
| --- | --- | --- | --- | --- | --- | --- |
| `15:10` | Scalp-sim overnight preclose | 미결 sim position의 당일 가상청산·overnight carry 판정 | postclose sim label 완결 | ON, sim-only | 이번 구간 외; 상세검토 대기 | E2, P16/P17 |
| `20:05` | EOD KOSPI update | NXT 종료 뒤 일봉 DB·추천 원천 갱신 | 장후 producer의 최신 시장자료 확보 | ON | 상세검토 대기 | 없음 |
| `20:10` | Main threshold-cycle wrapper | bot stop 뒤 tuning/source-quality/AI/approval/verifier 체인 실행 | 다음 PREOPEN 후보와 결손 workorder 생성 | ON, stop-only | **내부 1~13 구현·점검 종결**; 14~118 순차 검토 대기 | E1, E2, E3/E4/E6, P14~P18 |
| `20:10` | Widget evaluation systemd | advisory·auto-trade calibration과 다음-session widget policy 생성 | widget 독립 정책의 당일 source-date 일치 | ON | 상세검토 대기 | E7 |
| `20:10` | Postclose DONE controller | main wrapper terminal 대기·복구·최종 verifier 조정 | 부분 실패 은폐 방지 | ON, bounded wait | 상세검토 대기 | E1, follower E6 |
| `20:10` | Tuning monitoring | main postclose DONE 뒤 Parquet/DuckDB late-pass 갱신 | 분석 조회속도와 데이터 재사용 개선 | ON, bounded wait | 상세검토 대기 | E5 |
| `20:15` | Swing live dry-run | swing 연구 산출물 생성 | swing 후보 탐색 | **OFF** | 현재 불필요 지정 유지 | 없음 |
| `20:50` | Dashboard DB archive | 검증된 DB/raw 세대 압축 | 디스크·조회비용 억제 | ON | 상세검토 대기 | E9 |
| `21:05` | AI entry setup paired replay follower | offline exact candidate replay와 Main AI consumer refresh | entry/prompt 비교자료의 terminal 완결 | ON, source-only | 상세검토 대기 | E6 |
| `21:10` | Swing model retrain/auto-promote | swing 모델 재학습 | swing 모델 갱신 | **OFF** | 현재 불필요 지정 유지 | 없음 |
| `21:15` | Machine final refresh systemd | expansion→attribution→hysteresis→entry timing→approval→checklist 실행 | machine 단일 owner의 다음-session 후보 종결 | ON | 상세검토 대기 | E7 |
| `21:55~23:50` | Postclose finalization | 모든 predecessor terminal 뒤 cleanup·final detector 실행 | 미완료 원천 보존과 장후 종결 확인 | ON, fail-closed | 상세검토 대기 | E1, E8, E9 |

## 4. 20:10 main wrapper 상세 목록

표의 번호는 순차 상세검토를 위한 기존 review index다. `Wrapper immutable snapshot`은 실제 프로세스 bootstrap에서 `Bot stop`보다 먼저 고정되지만, 완료 구간 명칭인 `Bot stop ~ AVG_DOWN recovery calibration`과 index 연속성을 유지하기 위해 번호는 바꾸지 않았다.

### 4.1 격리·수집·초기 품질 단계

| # | 작업 | 목적 | 목표 | 기대효과 | 운영상태 | 상세검토 상태 | 연결 lock |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | Bot stop | 장후 자원 격리 | postclose 시작 시 bot session 중지, 완료 후 자동 재시작 금지 | 분석 중 주문·DB·메모리 경합 방지 | ON, cron=`stop` | **구현·점검 종결**; 기존 stop-only 유지 | E2 |
| 2 | Wrapper immutable snapshot | 실행 도중 wrapper 변경 격리 | syntax-checked sibling snapshot으로 한 generation 실행 | 혼합 버전 실행 방지 | ON | **구현·점검 종결**; 변경 불필요 | 임시 snapshot |
| 3 | Pipeline immutable snapshot | 장후 입력 고정 | 동일 raw hash를 모든 후속 producer가 소비 | 보고서 간 재현성 확보 | ON | **구현·점검 종결**; 변경 불필요 | E2, partition lock |
| 4 | Snapshot retention cleanup | 오래된 snapshot 정리 | 보존기간 밖의 완료 snapshot만 제거 | 디스크 증가와 scan 비용 억제 | ON | **구현·점검 종결**; live source 삭제 권한 없음 확인 | E9 |
| 5 | Threshold compact/backfill | raw event를 날짜별 compact로 변환 | checkpoint·source hash·bounded resource guard로 EOF 도달 | 후속 EV 분석 입력 안정화 | ON | **구현·점검 종결**; 기존 availability/resource fail-closed 유지 | E2, partition lock |
| 6 | Sim post-sell feedback | sim 후보의 성숙 결과 생성 | sim outcome과 monitor snapshot 완결 | sim 정책 평가 가능 | ON | **구현·점검 종결**; real execution authority 없음 확인 | E2, P16/P17 |
| 7 | Limit-down watch report | 하한가·급락 위험 관찰 | exact-date source-only 위험 보고 생성 | 급락·유동성 위험 오판 방지 | ON | **구현·점검 종결**; 별도 runtime acceptance만 남음 | E2 |
| 8 | Rising-missed finalization | 놓친 상승 후보 최종 집계 | intraday source와 blocker를 exact-date로 종결 | missed-upside 원인 분해 | ON | **구현·점검 종결**; source-quality pending은 별도 표기 | E2, E4, P15 |
| 9 | Rising-missed scout workorder | 개선 가능한 missed 원인을 구현 항목으로 변환 | stable workorder와 source-only authority 결속 | 반복되는 entry source gap 감소 | ON | **구현·점검 종결**; runtime threshold 권한 없음 | E2, P15 |
| 10 | PYRAMID feedback finalization | 추가매수 기회·차단·종료 연결 | same-event gate/BBO/resolver/terminal/coverage 보존 | 무효 추가매수 표본 제거 | ON | **구현·점검 종결, 자연증거 대기** | E2, E4, P14/P18 |
| 11 | Observation source-quality preflight | 필수 field·label·lineage 검사 | 결손 row/window 제외 또는 fail-closed | 오염 자료의 EV·runtime 승격 방지 | ON, hard gate | **구현·점검 종결**; AVG_DOWN replay frame 계약 포함 | E2 |
| 12 | PYRAMID quality calibration | 기존 min-profit 한 축의 증분 경제성 재현 | 동일 complete episode에서 current/candidate/NO_ADD와 비용 1회 비교 | 작은 유효 순기여 후보 식별, 과도한 허들 제거 | ON | **구현·점검 종결, 자연 AI/PREOPEN 증거 대기** | E2, P14/P18 |
| 13 | AVG_DOWN recovery calibration | 기존 shallow buy-pressure 한 축의 A/B/C 경제성 재현 | production frame→full-policy replay→report→AI/PREOPEN/verifier 연결 | 중복 경로·고정 종료 착시 제거, 유효 후보만 선별 | ON | **구현·점검 종결, 자연 paired/PID/EV 증거 대기** | E2; 신규 operator lock 없음 |
| 14 | Samsung machine entry tuning | 삼성 독립 머신 진입상태 분석 | 다음 PREOPEN bounded 후보 생성 | 종목 전용 진입 EV 개선 | ON | 상세검토 대기 | E2 |
| 15 | Low-price two-leg tuning | 저가주 2-leg 실제 결과·적용 정책 감사 | 실제 applied 정책 carry; 부분집합은 진단만 유지 | 허위 개선·근거 없는 정책 변경 차단 | ON | LP-F1/F2 보완; 신규 subset live 승격 제거, 50 loader-ready/3 격리 유지, 실적용·수익개선 별도 | E2 |
| 16 | Low-price expanded recommendation | 기존 두 필터 경로 비교·후보/profile 연구 | 동일기간 순이익·양수 EV, 날짜 간 HELD, half 진단 | EV 착시와 보유 단절 제거 | ON, content-bound checkpoint/resume | LP-F3~F5 보완; paired 연구·추천은 source-only, 신규 실권한 없음 | E2 |
| 17 | Machine microstructure attribution 20:10 사본 | 머신 이벤트와 micro 반응 연결 | 21:15 단일 owner 유지 | heavy 중복 실행 방지 | OFF | 상세검토 대기 | 없음 |
| 18 | Market-weakness hysteresis 20:10 사본 | 약세 상태 전이 보정 | 21:15 attribution 이후 실행 | 약세 오진입 완화 | OFF | 상세검토 대기 | 없음 |
| 19 | Machine entry timing 20:10 사본 | 즉시·지연 진입 비교 | 21:15 단일 owner 유지 | 진입 timing EV 개선 | OFF | 상세검토 대기 | 없음 |
| 20 | Machine policy approval 20:10 사본 | 머신 후보 승인 | 21:15 결과만 PREOPEN에 전달 | 이중 승인 방지 | OFF | 상세검토 대기 | 없음 |

### 4.2 진입·분할·LDM·microstructure 단계

| # | 작업 | 목적 | 목표 | 기대효과 | 운영상태 | 상세검토 상태 | 연결 lock |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 21 | One-share threshold opportunity | 차단 후보의 bounded 재검토 | source/AI/quote 조건이 닫힌 기회만 제안 | 주문 가뭄 완화 | ON | 상세검토 대기 | E2, entry operator locks |
| 22 | Scalp Entry ADM | entry 상태·행동 matrix | score 단독이 아닌 다차원 분류 | 진입 판단 정밀화 | ON | 상세검토 대기 | E2 |
| 23 | Entry AI gate backtest | AI BUY/WAIT gate 사후검증 | clean baseline 이후 경제성 비교 | 불필요한 AI 차단 식별 | ON | 상세검토 대기 | E2 |
| 24 | Scalp-sim overnight | 미결 sim 포지션 종결 | overnight outcome 완결 | sim label 누락 감소 | ON | 상세검토 대기 | E2, P16/P17 |
| 25 | Overnight OpenAI recovery | 미결 sim 결과 보완 | active-undecided가 있을 때만 bounded 호출 | sim outcome 완결성 | 조건부 | 상세검토 대기 | provider budget lock |
| 26 | Institutional flow context | 기관수급 context 생성 | lifecycle feature 제공 | regime 구분 개선 | ON | 상세검토 대기 | E2 |
| 27 | Microstructure reaction context | micro 반응 feature 생성 | entry/holding event와 결과 연결 | prompt 입력 품질 개선 | ON, non-fatal | 상세검토 대기 | E2 |
| 28 | Scale-in incremental CF | 추가 leg의 증분 효과 분리 | 기존 보유와 추가분 손익 분리 | scale-in 착시 제거 | ON | 상세검토 대기 | E2 |
| 29 | LDM daily | lifecycle 단계별 귀속 | entry→exit 병목 분류 | 개선 owner 식별 | ON | 상세검토 대기 | E2 |
| 30 | Scalp-sim scale-in approval | sim scale-in window 판정 | sim-only 확대 여부 결정 | 표본 수집 가속 | ON | 상세검토 대기 | E2, P16/P17 |
| 31 | Lifecycle AI attribution | AI 결과의 단계 귀속 | prompt 영향 분리 | AI 경제성 분석 | ON | 상세검토 대기 | E2 |
| 32 | LDM context refresh | AI attribution 반영 | same-date matrix 재계산 | context 누락 방지 | ON | 상세검토 대기 | E2 |
| 33 | Lifecycle AI context | 다음 AI 입력 context 생성 | feature bundle 완결 | prompt 품질 향상 | ON | 상세검토 대기 | E2 |
| 34 | LDM parent refinement | 얇은 child를 parent 가설로 통합 | 검증 가능한 분모 확보 | 영구 thin-bucket 감소 | ON | 상세검토 대기 | E2 |
| 35 | Lifecycle bucket daily | 신규·충돌 bucket 탐색 | daily source-only taxonomy 생성 | 이상 조기탐지 | ON | 상세검토 대기 | E2 |
| 36 | LDM rolling5d | 단기 lifecycle EV | 최근 변화 확인 | 시장 적응 | ON, trigger-gated | 상세검토 대기 | E2 |
| 37 | Bucket rolling5d | 단기 parent 집계 | daily noise 완화 | 후보 지속성 확인 | ON, trigger-gated | 상세검토 대기 | E2 |
| 38 | LDM rolling10d | 중기 lifecycle EV | 일별 변동 완화 | 안정적 방향 확인 | ON, trigger-gated | 상세검토 대기 | E2 |
| 39 | Bucket rolling10d | 중기 parent 집계 | 표본 안정성 확인 | 과적합 완화 | ON, trigger-gated | 상세검토 대기 | E2 |
| 40 | LDM MTD | 월간 lifecycle EV | promotion window 생성 | 실전 근거 강화 | ON, trigger-gated | 상세검토 대기 | E2 |
| 41 | Bucket MTD | 월간 parent 집계 | sim/live candidate 입력 | promotion 안정화 | ON | 상세검토 대기 | E2 |
| 42 | Runtime apply bridge | 후보와 실제 consumer 연결 | blocker/owner/env mapping 명시 | 보고서만 생성되는 경로 차단 | ON | 상세검토 대기 | E2, operator locks |
| 43 | Scalp-sim auto-approval | sim catalog 자동 생성 | 다음 PREOPEN sim handoff | sim 연구 자동화 | ON | 상세검토 대기 | E2, P16/P17 |
| 44 | Latency recommendation | non-entry 원인 분류 | latency/liquidity/AI/overbought 분리 | submit drought 개선 | ON | 상세검토 대기 | E2 |
| 45 | Market panic breadth | 시장 panic 폭 계산 | 개별종목과 시장 위험 분리 | 과잉 매도 방지 | ON | 상세검토 대기 | E2 |
| 46 | Panic-sell defense report | panic regime 종결 | recovery 상태 귀속 | exit 안정화 | ON | 상세검토 대기 | E2 |
| 47 | Scale-in split plan | 추가매수 분할 정책 | scale-in policy 생성 | 체결·slippage 개선 | ON | 상세검토 대기 | E2 |
| 48 | Strategy-position fact sync | 완료 거래 fact 갱신 | 실제 체결·PnL 확정 | EV 정확성 향상 | ON | 상세검토 대기 | DB writer lock |
| 49 | Scanner lookup-attention tuning | 조회자원 배분 조정 | 정책 생성 후 verify | API 효율 개선 | ON, DB 필요 | 상세검토 대기 | E2 |
| 50 | Daily threshold report | 일별·누적 후보 통합 | calibration·AI review 생성 | PREOPEN 근거 통합 | ON | 상세검토 대기 | E2 |
| 51 | Threshold AI correction | deterministic 후보 2차 검토 | parsed review 확보 | 잘못된 자동후보 차단 | ON, OpenAI | 상세검토 대기 | provider budget lock |
| 52 | Statistical action weight | 행동별 통계 가중치 | report-only 진단 | ADM 해석 개선 | ON, embedded output | 상세검토 대기 | E2 |
| 53 | Holding/Exit ADM | holding/exit matrix | exit owner 분리 | 조기·지연청산 개선 | ON, embedded output | 상세검토 대기 | E2 |
| 54 | Threshold cumulative | clean-baseline 누적 EV | daily 과적합 방지 | 적용근거 안정화 | ON, embedded output | 상세검토 대기 | E2 |
| 55 | Entry cancel-wait tuning | BUY 취소시간 CF | entry pattern별 대기시간 조정 | 체결률·기회비용 균형 | ON, 독립 family | 상세검토 대기 | E2 |

### 4.3 Swing·pattern·Entry split·Main AI 단계

| # | 작업 | 목적 | 목표 | 기대효과 | 운영상태 | 상세검토 상태 | 연결 lock |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 56 | Swing daily simulation | swing dry-run | 일별 lifecycle 생성 | swing 연구 | OFF | 현재 불필요 지정 유지 | 없음 |
| 57 | Swing strategy discovery | 8-arm 후보 탐색 | safe-pool sim 확장 | 신규 alpha 탐색 | OFF | 현재 불필요 지정 유지 | 없음 |
| 58 | Swing labels | 성숙 outcome 생성 | 후보별 결과 확정 | swing EV 계산 | OFF | 현재 불필요 지정 유지 | 없음 |
| 59 | Swing EV | 후보 경제성 계산 | 우수 arm 선별 | 저EV 후보 제거 | OFF | 현재 불필요 지정 유지 | 없음 |
| 60 | Swing LDM | swing 단계 matrix | 병목 식별 | 정책 정교화 | OFF | 현재 불필요 지정 유지 | 없음 |
| 61 | Swing buckets | swing parent bucket | Tier2 후보 생성 | 표본 안정화 | OFF | 현재 불필요 지정 유지 | 없음 |
| 62 | Swing lifecycle audit | swing 체인 감사 | review/approval 산출물 생성 | 계약 검증 | OFF | 현재 불필요 지정 유지 | 없음 |
| 63 | Swing AI review | swing Tier2 검토 | parsed 후보만 유지 | 오승격 차단 | OFF | 현재 불필요 지정 유지 | 없음 |
| 64 | Swing improvement automation | swing 개선 후보 가공 | runtime-approval 입력 | 연구 자동화 | OFF | 현재 불필요 지정 유지 | 없음 |
| 65 | Swing runtime approval | swing 적용 판정 | full-live 전 fail-closed | 실주문 보호 | OFF | 현재 불필요 지정 유지 | 없음 |
| 66 | DeepSeek swing lab | swing pattern 탐색 | 독립 후보 생성 | 패턴 다양화 | OFF | 현재 불필요 지정 유지 | 없음 |
| 67 | Claude scalp pattern lab | scalp pattern 연구 | 최신 pattern 생성 | 신규 가설 발굴 | ON | 상세검토 대기 | E2 |
| 68 | Gemini scalp pattern lab | 과거 provider lab | 자동실행 제거 | 중복비용 제거 | RETIRED | 상태 확인만 남음 | 없음 |
| 69 | Scalping pattern automation | pattern을 후보로 변환 | downstream handoff | 연구 방치 방지 | ON | 상세검토 대기 | E2 |
| 70 | Swing pattern automation | swing pattern handoff | swing 후보 변환 | swing 자동화 | OFF | 현재 불필요 지정 유지 | 없음 |
| 71 | Pattern currentness audit | pattern freshness 검사 | stale 승격 차단 | 낡은 가설 사용 방지 | ON, trigger-gated | 상세검토 대기 | E2 |
| 72 | Pattern AI review | pattern 후보 AI 검토 | 구현가능 항목 분리 | 무의미한 후보 축소 | ON | 상세검토 대기 | E2 |
| 73 | Pipeline verbosity | 중복·과다 event 분석 | producer별 비용 측정 | 저장량·runtime 절감 | ON, freshness reuse | 상세검토 대기 | E2 |
| 74 | Source-quality final audit | 후속 산출물 포함 재감사 | 최종 tuning 허용상태 확정 | 중간 gap 포착 | ON, trigger-gated | 상세검토 대기 | E2 |
| 75 | Entry split order plan | 최초진입 분할 정책 | 1·2차 가격·타이밍 후보 생성 | 체결률/slippage 개선 | ON | 상세검토 대기 | E2; operator lock 없음 |
| 76 | AI decision-quality materialization | trace/outcome/replay 입력 준비 | exact cohort 생성 | prompt EV 측정 | ON | 상세검토 대기 | E2 |
| 77 | Main AI R0–R3 | prompt 후보 수집·비교 | exact R3 manifest 생성 | 지속적 prompt 개선 | ON | 상세검토 대기 | E2, provider/storage locks |
| 78 | Main AI prompt optimizer | prompt 후보 최적화 | 경제성 후보 탐색 | Main AI 성과 개선 가능성 | ON | 상세검토 대기 | E2 |
| 79 | Holding-base replay | holding control manifest | base path hash binding | 비교 기준 안정화 | ON | 상세검토 대기 | E2 |
| 80 | Main AI prompt consumer | entry/holding path 연결 | 모든 request path 분류 | 소비경로 누락 제거 | ON | 상세검토 대기 | E2 |
| 81 | Main AI runtime family | exact R3를 PREOPEN family로 변환 | candidate-ready만 적용 | 검증 prompt 자동반영 | ON, fail-closed | 상세검토 대기 | E2 |
| 82 | AI action-outcome calibration | AI action과 사후결과 비교 | action quality 보정 | prompt 선택 개선 | ON | 상세검토 대기 | E2 |
| 83 | Codebase performance workorder | 코드 runtime 병목 분석 | 자동 성능 workorder 생성 | 장후시간 단축 | OFF | 상세검토 대기 | 없음 |
| 84 | Time-window regime CF | 시간대별 정책 비교 | regime 후보 탐색 | 장중 적응 | OFF | 상세검토 대기 | 없음 |
| 85 | Producer-gap bundle | 누락 producer 근거 수집 | gap 분석 입력 생성 | 원천 결손 해결 | OFF | 상세검토 대기 | 없음 |
| 86 | Producer-gap discovery | AI 기반 gap 탐색 | 구현 workorder 생성 | 영구 gap 해소 | OFF | 상세검토 대기 | 없음 |
| 87 | Stage-hook discovery | lifecycle hook 누락 탐색 | hook workorder 생성 | attribution coverage 확대 | OFF | 상세검토 대기 | 없음 |
| 88 | Stage-hook scaffold | hook 골격 생성 | source-only 관찰점 추가 | 결과 불능 경로 해소 | OFF | 상세검토 대기 | 없음 |
| 89 | WS freshness finalize | 장중 시세상태 종결 | exact-date freshness artifact | micro/AI 근거 보호 | ON | 상세검토 대기 | E2, E3 |

### 4.4 EV·승인·최종검증 단계

| # | 작업 | 목적 | 목표 | 기대효과 | 운영상태 | 상세검토 상태 | 연결 lock |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 90 | EV pre-workorder refresh | 최신 EV 통합 | workorder 전 기준 고정 | 잘못된 개선작업 방지 | ON | 상세검토 대기 | E2 |
| 91 | Code-improvement workorder 1차 | gap을 구현항목으로 변환 | stable ID 작업 생성 | 반복결함 해소 | ON, trigger-gated | 상세검토 대기 | E2 |
| 92 | EV post-workorder refresh | workorder linkage 반영 | downstream 최신화 | stale link 방지 | ON | 상세검토 대기 | E2 |
| 93 | Pattern propagation audit 1차 | pattern→workorder→runtime 추적 | 끊긴 handoff 식별 | 연구 방치 방지 | ON, trigger-gated | 상세검토 대기 | E2 |
| 94 | Pattern AI provenance 1차 | audit 기반 source binding 갱신 | hash/provenance 일치 | 잘못된 참조 방지 | ON | 상세검토 대기 | E2 |
| 95 | EV post-propagation | pattern 연결 반영 | approval 입력 최신화 | stale EV 방지 | ON | 상세검토 대기 | E2 |
| 96 | Runtime approval summary 1차 | family 적용상태 집계 | 적용·차단 사유 명시 | PREOPEN 판단 단순화 | ON | 상세검토 대기 | E2, operator locks |
| 97 | Runtime apply-gap audit | 산출·소비 단절 탐지 | bridge/consumer gap 분류 | 보고서-only 잔류 방지 | ON, trigger-gated | 상세검토 대기 | E2 |
| 98 | Key-lineage ledger | env key 계보 기록 | owner·충돌 확인 | authority leak 방지 | ON | 상세검토 대기 | E2, operator locks |
| 99 | Conversion lane | source→sim→live 단계 분류 | 다음 승격조건 명시 | 성급한 적용 방지 | ON, swing 제외 | 상세검토 대기 | E2 |
| 100 | Rising classifier prior | missed 분류 prior 갱신 | 누적 근거 생성 | 재검토 정확도 향상 | ON | 상세검토 대기 | E2, P15 |
| 101 | Rising workorder refresh | 새 prior 반영 | classifier/workorder 정합 | 오래된 개선안 방지 | ON | 상세검토 대기 | E2, P15 |
| 102 | Scalp-sim control refresh | 누적 prior 반영 재승인 | same-date catalog 최신화 | PREOPEN 일관성 | ON | 상세검토 대기 | E2, P16/P17 |
| 103 | Code workorder 2차 | conversion 결과 반영 | 구현목록 보완 | 누락 축소 | ON | 상세검토 대기 | E2 |
| 104 | EV post-conversion | 2차 workorder 반영 | 최종 EV 최신화 | 승인 정합 | ON | 상세검토 대기 | E2 |
| 105 | Runtime summary 2차 | workorder 이후 재집계 | 최종 blocker 반영 | stale summary 방지 | ON | 상세검토 대기 | E2 |
| 106 | Next checklist 1차 | 다음 거래일 항목 생성 | parser 가능한 owner 목록 | 후속 누락 방지 | ON | 상세검토 대기 | E2 |
| 107 | Pattern propagation final | bootstrap link 재검증 | 임시 pending 제거 | 거짓 경고 감소 | ON | 상세검토 대기 | E2 |
| 108 | Pattern AI provenance final | 최종 source binding | verifier 입력 확정 | hash drift 방지 | ON | 상세검토 대기 | E2 |
| 109 | EV final-consumer | 모든 consumer 반영 | 최종 EV 생성 | PREOPEN stale 방지 | ON | 상세검토 대기 | E2 |
| 110 | Code workorder final | 최종 source 반영 | 마지막 workorder 확정 | 누락 최소화 | ON | 상세검토 대기 | E2 |
| 111 | Runtime summary final | 최종 승인상태 | PREOPEN owner artifact 확정 | 적용 판단 단일화 | ON | 상세검토 대기 | E2, operator locks |
| 112 | Next checklist final | 최종 상태로 checklist 재생성 | 다음 거래일 owner 확정 | 중간상태 노출 방지 | ON | 상세검토 대기 | E2 |
| 113 | Verifier pending-DONE | DONE 전 구조검증 | 필수 artifact 확인 | incomplete DONE 방지 | ON | 상세검토 대기 | E2 |
| 114 | Docs backlog print-only | checklist parser 확인 | 외부 sync 없이 읽기 검증 | 문서 오류 탐지 | ON | 상세검토 대기 | E2 |
| 115 | Status/DONE marker | terminal 성공 기록 | controller/monitoring 대기 해제 | 후속 체인 진행 | ON | 상세검토 대기 | E1 |
| 116 | Verifier final | DONE 포함 최종검증 | exact-date terminal 계약 | 성공 오판 방지 | ON | 상세검토 대기 | E2 |
| 117 | Tuning performance control tower | EV/runtime 결과 요약 | 유지·중단·수정 후보 분류 | 불필요 작업 식별 | ON | 상세검토 대기 | E2 |
| 118 | Bot restart | 완료 후 runtime 재개 | 명시 승인 시에만 재시작 | 무인 운영 | OFF, stop-only | 상세검토 대기 | 없음 |

## 5. 다음 자연 실행에서 분리해 확인할 것

1. `PYRAMID`: 새 schema의 exact-ready parent episode, KRX 근거, 비용 차감 next-step EV, same-ID AI 검토, 단일 scale-in owner PREOPEN 선택.
2. `AVG_DOWN`: `avg_down_route_arbitration_observed`와 연속 `avg_down_exit_replay_frame_observed`, 격리 policy replay 결과, A/B/C 독립 terminal, source audit 허용, same-ID AI/PREOPEN/PID 소비.
3. 두 family 모두 구현 완료를 실현 수익 개선으로 표시하지 않는다. 자연 match 0은 경제성 실패가 아니며, source/adapter gap과 자연 희소성을 구분한다.
4. bot 재기동, 수동 env 적용, operator lock 변경, 주문·수량·provider·hard-safety 변경은 이 목록 갱신 범위에 포함하지 않는다.
