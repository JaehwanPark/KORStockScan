# KORStockScan

KORStockScan은 키움증권 REST/WebSocket과 연동하는 개인용 스캘핑 매매 엔진입니다. 넓은 시장을 탐색하는 메인 봇, 정해진 종목·시간대의 반복 패턴을 거래하는 에피소드 매매기계를 서로 독립된 주문 owner로 운영합니다. 위젯 자동·수동 매매와 화면·수집·연구·장후 정책 발행은 퇴역했습니다.

목표는 위험을 모두 피하는 것이 아닙니다. 감당 가능한 위험 안에서 더 많은 유효 기회를 탐색하고, probe·분할 진입·동적 수량·부분익절·trailing·hard/protect/emergency guard 같은 후단 보호장치로 기대값과 누적 순이익을 높이는 것입니다.

현재 정책과 active/open 상태의 기준은 [Plan Rebase](docs/plan-korStockScanPerformanceOptimization.rebase.md), 날짜별 실행 항목은 [Stage2 Checklist](docs/checklists/README.md), 운영 순서는 [Time-Based Operations Runbook](docs/time-based-operations-runbook.md)이 소유합니다.

- 튜닝 운영문서 현행화: `2026-09-08 KST`
- 튜닝 데이터 clean baseline: `2026-06-05T00:00:00+09:00 KST`
- baseline 이전 자료: archive/audit evidence 전용이며 현재 EV, rolling/cumulative 튜닝, runtime 승인 또는 실거래 품질 승인의 근거로 사용하지 않음

## 매매 기능

메인과 에피소드 매매기계는 신호와 주문 상태를 공유하지 않습니다. 같은 종목을 다룰 때에도 owner, episode ID, 주문번호, 보유수량과 청산 귀속을 분리해 다른 기계의 수량을 매도하거나 중복 진입하지 않도록 합니다.

### 메인 봇 매매기계

메인 봇은 당일 시장에서 새로 나타나는 스캘핑 기회를 넓게 찾고, 후보마다 진입부터 청산까지 전체 lifecycle의 기대값을 최적화합니다.

- **매매 목적:** 고정 종목에 의존하지 않고 거래대금·수급·가격 움직임이 살아나는 종목을 발견해, 유효한 상승 구간은 잡고 불필요한 하락 노출은 제한합니다.
- **매매 목표:** 한 번의 큰 수익보다 여러 기회의 순이익 합계를 중시합니다. 상황에 따라 짧은 micro-reversion, continuation, 부분익절과 runner 보유를 구분합니다.
- **강점:** 시장 전반을 탐색하는 scanner, AI 진입·가격·보유 판단, executable BBO 기반 재검증, 1주 probe-first와 residual multi-leg, 동적 수량, scale-in, 부분익절·trailing·보호 청산을 한 lifecycle로 연결합니다.

```text
scanner/WATCHING
  -> candidate 판정
  -> AI 판단
  -> submit guard
  -> 1주 probe
  -> residual multi-leg
  -> holding / scale-in
  -> partial TP / trailing / exit
  -> broker reconciliation
```

점수는 baseline prior이자 feature일 뿐 단독 BUY 명령이 아닙니다. 가격·호가·체결·분봉 freshness, venue provenance, 계좌·주문·수량·cooldown과 broker submit guard를 모두 통과해야 실제 주문으로 이어집니다.

### Main 고정감시 전환

삼성전자와 두산의 고정감시는 Main의 기존 진입·보유·청산·주문 owner를 사용한다. 두산 초기 정책은 현재 Main 비삼성 정책으로 지정하며 별도의 초기 경제성 입증을 요구하지 않는다. 두산 에피소드 신규 진입·발행·자동 확장을 제거한 작업본과 실제 설치/배포 상태는 구분한다. [전환 계획과 검증](docs/proposals/doosan-episode-retirement-main-fixed-watch-initial-policy-plan-2026-10-06.md)을 따른다.

### 위젯 퇴역

위젯 기능의 실행·설치·정책 발행 경로를 제거합니다. Main 삼성전자 고정 감시와 에피소드의 원천·주문 owner는 유지합니다. 과거 위젯 custody 기록은 감사 입력이며 새 주문 권한이 없습니다. [제거계획 및 실행 gate](docs/proposals/widget-full-runtime-postclose-retirement-plan-2026-10-06.md)를 따릅니다.

### 에피소드 매매기계

에피소드 매매기계는 특정 종목과 세션에서 반복 관측된 진입·회복 패턴을 독립 프로세스로 실행합니다. 삼성전자 시간대별 기계와 저가주 two-leg profile들이 대표적이며, 실제 활성 profile은 exact-date PREOPEN policy와 systemd schedule이 결정합니다.

- **매매 목적:** 일반 scanner 경쟁이나 범용 threshold에 맡기기 어려운 종목·시간대별 반복 패턴을 재현 가능한 작은 거래 단위로 포착합니다.
- **매매 목표:** 신규 episode는 서로 분리된 10주 두 leg, 최대 20주 범위에서 진입하고 profile별 tick/가격 목표를 추구합니다. 목표 미체결 보유분은 해당 episode owner가 계속 관리합니다.
- **강점:** 종목·venue·시간창별 명시적 profile, 결정론적 두 leg 가격, 체결분만을 기준으로 한 목표가, 독립 lock/state/ledger, 정확한 주문 귀속과 PREOPEN calibration을 갖습니다.

에피소드 매매기계의 entry·target·재진입 규칙은 profile마다 다릅니다. 보편 규칙으로 임의 완화하지 않으며, legacy 1주 보유는 custody compatibility로만 관리하고 신규 수량으로 확대하지 않습니다. 자세한 내용은 [Low-price Two-leg Machines](docs/low-price-two-leg-machines.md)와 [Samsung Episode Machine](docs/samsung-morning-one-share-machine.md)을 참고합니다.

## 튜닝축

튜닝은 매매기계를 하나 더 만드는 작업이 아니라, 관찰한 결과를 기존 single owner에게 되돌려주는 품질 갱신입니다. clean baseline 이후의 rolling/cumulative 표본, source-quality와 비용 반영 EV를 우선하며, 단일 날짜의 승률이나 단순 수익률 합계로 실거래 권한을 넓히지 않습니다.

### Micro-reversion

급등 직후의 위험 신호가 있더라도 신선한 호가, 제한된 spread, 회복 가능한 tape와 짧은 목표가가 함께 성립하면 소규모로 치고 빠질 수 있는지를 평가합니다.

- risky micro episode는 우선 source-only 반사실로 관찰합니다.
- passive `bid+1`, 짧은 TTL, 제한적 ask 진입을 수수료·slippage·target/adverse first-hit과 함께 비교합니다.
- stale quote, BBO 결손, 과도한 spread, 명백한 tick deceleration은 완화 대상이 아닙니다.
- 충분한 거래일과 filled-terminal 표본이 쌓이기 전에는 실주문 승격 근거로 쓰지 않습니다.

### AI 판단 품질 개선

AI 호출 성공 여부만 보지 않고 호출, 입력, 판단 결과를 각각 검증합니다.

- **호출 품질:** 실제 provider, timeout, failback, parse, cache와 transport provenance
- **입력 품질:** 분봉, executable price/BBO, 체결 tape, venue, 시각, 결측 처리와 exact payload
- **판단 품질:** `BUY/WAIT/DROP/HOLD/EXIT` 이후의 MFE·MAE, target/adverse 순서와 실제 손익

정확한 입력에서도 오판이 반복되면 feature, prompt, reason-code와 판단 계약을 고치고 real payload를 replay합니다. 비정상 응답을 임의로 유효 판단처럼 해석하거나 AI가 broker·hard safety를 우회하게 하지 않습니다.

Main AI R0–R3는 변경 요청이 있을 때만 실행하는 작업이 아니라 성숙한 exact 근거로 더 나은 prompt/input을 계속 찾는 offline 연구입니다. #76→#82 v5→#78 optimizer의 환류와 21:05 terminal 후속 갱신을 사용하되, #81 legacy live family는 DISABLED입니다. 지원 KRX V2.14/V2.15의 별도 `entry_setup_live_policy` 승격·PREOPEN·PID receipt 없이는 자동 실적용을 주장하지 않습니다.

### 퇴역 연구

위젯 종목·신호·보조판정 연구는 실행하지 않습니다. 과거 결과와 공통 원천은 감사 및 살아 있는 소비자의 재현에 필요한 범위로 보존합니다.

### 에피소드

에피소드 튜닝은 profile별 시간창, leg 가격과 목표가가 실제 체결 및 terminal 결과에 적합했는지 갱신합니다.

- 두 leg의 제출·부분체결·취소·목표가 귀속을 분리해 평가합니다.
- 종목과 KRX/NXT/PREMARKET_KRX_LIKE 실적을 섞지 않습니다.
- clean baseline 이후 rolling 결과와 최소 표본을 충족한 profile만 다음 PREOPEN 후보가 됩니다.
- 수량은 튜닝축이 아니며 신규 episode의 두 개 10주 leg 계약을 유지합니다.

### 공통 smoothing 원칙

Smoothing은 순간적인 tick·호가·OFI/QI 흔들림 때문에 진입·보유·청산 판단이 왕복하는 것을 줄이는 공통 품질축입니다. 별도 주문 owner나 위험 완화 권한은 아닙니다.

- 현재 live 경로의 대표 구현은 bounded holding-flow 내부의 `holding_flow_ofi_smoothing`입니다. OFI와 QI로 만든 raw micro score를 EWMA와 연속 관측 횟수로 안정화해 `stable_bullish`, `neutral`, `stable_bearish` regime을 만듭니다.
- raw 값, smoothed 값, snapshot age, persistence count, policy version과 최종 action을 함께 남겨 사후 재현이 가능해야 합니다.
- stale snapshot, observer unhealthy, 입력 부족이면 smoothed 값을 사용하지 않습니다. smoothing은 freshness, executable BBO, hard/protect/emergency, broker/account/order/quantity/cooldown guard를 숨기거나 우회할 수 없습니다.
- soft-stop whipsaw와 대안 보유/청산 경로는 exact-path source-only 관찰로 raw action 대비 반사실 EV를 계산합니다. source-only 결과는 즉시 live action을 바꾸지 않습니다.
- 조정값은 같은 venue·session의 성숙 outcome과 연결해 rolling/cumulative EV로 검증하고, 단일 표본은 누적 학습행 하나만 갱신합니다.

## 장후 작업 흐름

장후 작업은 당일 원천을 검증하고 전용 owner별 평가·승계·정책 발행과 다음 기동 준비를 수행하는 자동화 체인입니다. 핵심 경로는 다음과 같습니다.

설치 예약·stage 의존관계·내부 producer·정책 소비·OFF/퇴역 구성은 [장후작업 현행 활성 목록](docs/audit-reports/2026-09-05-postclose-work-inventory.md), 당일 실행·Acceptance는 checklist가 소유합니다. 실행·복구는 명시적으로 호출된 [장후 지시문](docs/postclose-tuning-result-review-task-instructions.md)을 따릅니다. 문서 현행화는 실행 요청이 아닙니다. ADM/LDM·bucket·greenfield·전용 institutional aggregate와 정규 scalp-sim chain은 퇴역, Swing과 Episode 신규 후보 연구는 OFF입니다. 기존 Episode 실매매·승인 정책과 real post-sell 관찰은 각 owner에서 유지합니다.

```text
장중 raw event와 broker receipt 종료
  -> source-quality audit
  -> entry / submit / holding / scale-in / exit lifecycle 재구성
  -> Main 승률·full 전략 / compact AI / 전용 family 평가
  -> 독립 machine-group stage terminal과 OFF receipt
  -> owner별 비용·검증·후보 또는 정상 carry·정책 소비
  -> summary / tower / checklist / strict verifier
  -> 전체 controller DONE
  -> 다음 거래일 05:00 최종화 / cleanup / source-date detector
  -> 격리된 장전 prepare·verify
  -> 실제 PREOPEN / PID / 다음 세션 attribution
```

1. **Source-quality preflight:** clean baseline, 필수 필드, venue, 시각, executable price와 provenance를 검증합니다. 결손 row/window를 안정적으로 격리해 정상 입력을 보존하고, 전역 계약 결손·격리 실패는 전체 차단합니다. 예약 stage 전 미생성은 실패가 아닙니다.
2. **Lifecycle 복기:** 실제 주문, 미진입, probe/residual, scale-in, 부분익절·trailing·최종 청산을 같은 흐름으로 재구성하되 real·sim·source-only를 분리합니다.
3. **평가:** 기계 v7은 미진입 회복 우선·성공 보존, 보조 v4는 PASS/VETO/CAUTION의 full-cost 비교와 동결 후보 검증을 적용합니다. 새 계약은 10/2 원천의 장후 계산부터이며 갱신 원천은 9/29 이후 적격 자료입니다. 전용 family의 진단·경제성 분모와 source gap을 구분합니다.
4. **정책 선택:** dated PREOPEN 정책, Main full 전략의 검증된 current/parent CAS, 독립 Episode 정책은 각 owner의 적용 경계를 따릅니다. 후보 부족·결손은 기존 유효 정책 승계와 원천 수리로 구분하고 정책 선택을 PID 소비로 대신하지 않습니다.
5. **검증과 종료:** producer/consumer 순서, AI provider, artifact freshness, runtime env와 apply plan을 검증합니다. tower와 마지막 checklist의 exact source hash 및 strict verifier 명령이 성공한 뒤에만 controller가 `DONE`을 표시합니다. 이전 PASS artifact로 새 명령 실패를 숨기지 않습니다.

6. **최종화와 다음 기동:** main wrapper DONE 뒤 독립 작업·전체 controller/strict·cleanup·최종 detector를 확인합니다. 장전 준비 PASS와 전체 장후 완료는 별도이며 실제 PREOPEN/PID·적용 버전의 비용 후 outcome을 자연 receipt로 확인합니다.

장후 리포트의 존재 자체는 효과의 증거가 아닙니다. 누가 소비했는지, sim 또는 runtime에 실제 반영됐는지, 반영 후 EV가 어떻게 변했는지까지 연결돼야 합니다. 전체 계약은 [Report Automation Traceability](docs/report-based-automation-traceability.md)를 따릅니다.

## 안전과 권한 경계

- stale/conflict, price freshness, hard/protect/emergency stop, broker/account/order/quantity/cooldown은 hard safety이며 튜닝이 우회하지 않습니다.
- `position_sizing_dynamic_formula`가 메인 봇의 신규·추가매수 수량을 소유합니다. 에피소드 수량은 각 독립 owner의 계약을 따릅니다.
- KRX, `PREMARKET_KRX_LIKE`, NXT 데이터와 성과를 분리합니다.
- full fill과 partial fill, 실현손익과 매도 후 반사실 기회, real과 sim/source-only 결과를 합산하지 않습니다.
- AI provider, bot 상태, cap, hard safety 또는 실주문 권한 변경은 리포트 단독으로 실행하지 않습니다.
- System Error Detector는 프로세스, cron, 로그, artifact freshness와 리소스를 감시하지만 매매 전략을 변경하지 않습니다.

## 프로젝트 구조

```text
KORStockScan/
├── src/
│   ├── bot_main.py                 # 메인 봇 진입점
│   ├── engine/                     # lifecycle, AI, monitoring, automation
│   └── trading/                    # 에피소드 등 독립 주문 owner
├── data/
│   ├── pipeline_events/            # 장중 raw event
│   ├── threshold_cycle/            # compact event, apply plan, runtime env
│   └── report/                     # 장중·장후 리포트
├── deploy/                         # cron, systemd, 운영 wrapper
├── docs/                           # 기준 문서, runbook, checklist, workorder
└── logs/                           # 운영 로그
```

JSON/JSONL이 canonical data이며 Markdown은 운영자가 읽는 요약입니다. 새 producer는 역할에 맞는 package에 두고 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 선언해야 합니다.

## 설치와 실행

Python 작업은 프로젝트 `.venv`를 기본으로 사용합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp data/config_sample.json data/config_prod.json
```

서버 환경에 키움 API, DB, AI provider 등 필요한 자격 증명을 설정하고 민감정보는 git에 커밋하지 않습니다. 메인 봇은 운영 wrapper를 통해 시작합니다.

```bash
cd src
bash run_bot.sh
```

장전 runtime env 생성과 상세 운영 명령은 [Time-Based Operations Runbook](docs/time-based-operations-runbook.md)을 따릅니다. 기본 진단은 다음과 같습니다.

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run
```

## 핵심 문서

| 문서 | 역할 |
| --- | --- |
| [Plan Rebase](docs/plan-korStockScanPerformanceOptimization.rebase.md) | 현재 튜닝 원칙, active/open 상태와 금지선 |
| [Time-Based Operations Runbook](docs/time-based-operations-runbook.md) | 시간대별 운영 절차와 확인 기준 |
| [Report Automation Traceability](docs/report-based-automation-traceability.md) | 장후 산출물, consumer와 apply 계약 |
| [Threshold Cycle README](data/threshold_cycle/README.md) | PREOPEN apply plan과 runtime env |
| [Widget Retirement](docs/widget-signal-auto-trading-runbook.md) | 퇴역 경계와 과거 증거 보존 |
| [Episode Machines](docs/low-price-two-leg-machines.md) | 종목별 two-leg 에피소드 계약 |
| [Stage2 Checklist](docs/checklists/README.md) | 날짜별 실행 항목 |

## 주의

이 프로젝트는 개인 자동매매와 리서치 운영 코드이며 README와 리포트는 투자 조언이 아닙니다. 실계좌 권한, API key, 주문가능금액, 세금·수수료와 거래소·브로커 장애는 운영자가 직접 관리해야 합니다.

실주문 범위가 넓어지는 변경은 runtime owner, source-quality gate, rolling evidence, approval boundary와 rollback guard를 먼저 확인합니다.
