# KORStockScan

KORStockScan은 키움증권 REST/WebSocket과 연동하는 개인용 스캘핑 매매 엔진입니다. 넓은 시장을 탐색하는 메인 봇, 종목별 신호를 집행하는 위젯 매매기계, 정해진 종목·시간대의 반복 패턴을 거래하는 에피소드 매매기계를 서로 독립된 주문 owner로 운영합니다.

목표는 위험을 모두 피하는 것이 아닙니다. 감당 가능한 위험 안에서 더 많은 유효 기회를 탐색하고, probe·분할 진입·동적 수량·부분익절·trailing·hard/protect/emergency guard 같은 후단 보호장치로 기대값과 누적 순이익을 높이는 것입니다.

현재 정책과 active/open 상태의 기준은 [Plan Rebase](docs/plan-korStockScanPerformanceOptimization.rebase.md), 날짜별 실행 항목은 [Stage2 Checklist](docs/checklists/README.md), 운영 순서는 [Time-Based Operations Runbook](docs/time-based-operations-runbook.md)이 소유합니다.

- 문서 기준일: `2026-08-20 KST`
- 튜닝 데이터 clean baseline: `2026-06-05T00:00:00+09:00 KST`
- baseline 이전 자료: archive/audit evidence 전용이며 현재 EV, rolling/cumulative 튜닝, runtime 승인 또는 실거래 품질 승인의 근거로 사용하지 않음

## 매매 기능

세 매매기계는 신호와 주문 상태를 공유하지 않습니다. 같은 종목을 다룰 때에도 owner, episode ID, 주문번호, 보유수량과 청산 귀속을 분리해 다른 기계의 수량을 매도하거나 중복 진입하지 않도록 합니다.

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

### 위젯 매매기계

위젯 매매기계는 종목별 위젯이 만든 고맥락 신호를 독립된 소규모 실주문 episode로 집행합니다. 현재 core widget과 날짜별 calibration으로 선택된 동적 widget 사양을 사용하며, 정확한 대상은 runtime policy가 소유합니다.

- **매매 목적:** 사람이 위젯에서 확인하던 종목별 신호를 일관된 규칙으로 실행해 짧고 반복 가능한 수익 기회를 놓치지 않습니다.
- **매매 목표:** 체결가 또는 episode 평균가를 기준으로 정책에 정의된 가까운 목표가를 추구하며, 한 episode의 위험과 주문 수량을 제한합니다.
- **강점:** 신호 source-quality 검증, 중복 episode 차단, 체결 확인 후 목표가 생성, 정확한 주문번호 기반 취소·정정·청산, 일일 상태 초기화와 main bot owner 격리가 명확합니다.

위젯 매매는 일반 스캐너의 점수 완화 수단이 아닙니다. 위젯이 소유한 신호와 policy가 일치할 때만 동작하고, 전일·수동·다른 전략의 보유수량은 청산하지 않습니다. 자세한 운영 계약은 [Widget Signal Auto Trading Runbook](docs/widget-signal-auto-trading-runbook.md)을 참고합니다.

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

### 위젯

위젯 튜닝은 종목별 신호가 실제로 체결 가능한 가격에서 반복 이익을 만드는지 검증합니다.

- signal source와 체결·목표 주문의 lineage를 같은 episode로 연결합니다.
- 진입 가격, target tick, cooldown, episode 종료 조건을 종목·venue별 rolling 결과로 비교합니다.
- main bot 또는 episode 기계와 같은 종목을 동시에 소유하지 않는지 검증합니다.
- 적용은 exact-date policy와 rollback 값이 있는 bounded 변경으로 제한합니다.

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

장후 작업은 당일 이벤트를 복기해 다음 장전의 bounded 후보를 만드는 자동화 체인입니다. 현재 소비되는 핵심 경로만 요약하면 다음과 같습니다.

```text
장중 raw event와 broker receipt 종료
  -> source-quality audit
  -> entry / submit / holding / scale-in / exit lifecycle 재구성
  -> micro-reversion / AI / widget / episode calibration
  -> rolling·cumulative EV와 반사실 비교
  -> PREOPEN apply candidate 또는 source-only workorder
  -> artifact 순서·consumer·provenance verifier
  -> controller DONE
  -> 다음 세션 post-apply attribution
```

1. **Source-quality preflight:** clean baseline, 필수 필드, venue, 시각, executable price와 provenance를 검증합니다. 계약이 깨지면 tuning input을 차단하고 보완 workorder로 넘깁니다.
2. **Lifecycle 복기:** 실제 주문, 미진입, probe/residual, scale-in, 부분익절·trailing·최종 청산을 같은 흐름으로 재구성하되 real·sim·source-only를 분리합니다.
3. **Calibration:** 네 튜닝축과 smoothing 경로를 raw 대안과 비교하고 비용 반영 EV, MFE/MAE, first-hit, 표본 충족 여부를 계산합니다.
4. **적용 후보 생성:** 기존 owner의 한 축만 바꾸는 bounded PREOPEN 후보와 rollback 값을 만듭니다. 계측·리포트·provenance 결손은 `runtime_effect=false` workorder로 분리합니다.
5. **검증과 종료:** producer/consumer 순서, AI provider, artifact freshness, runtime env와 apply plan을 검증합니다. 필수 산출물이 닫힌 뒤에만 controller가 `DONE`을 표시합니다.
6. **다음 세션 귀속:** 실제 PID가 어떤 env와 policy를 읽었는지 확인하고, 적용 전후 outcome을 다음 rolling 갱신에 돌려줍니다.

장후 리포트의 존재 자체는 효과의 증거가 아닙니다. 누가 소비했는지, sim 또는 runtime에 실제 반영됐는지, 반영 후 EV가 어떻게 변했는지까지 연결돼야 합니다. 전체 계약은 [Report Automation Traceability](docs/report-based-automation-traceability.md)를 따릅니다.

## 안전과 권한 경계

- stale/conflict, price freshness, hard/protect/emergency stop, broker/account/order/quantity/cooldown은 hard safety이며 튜닝이 우회하지 않습니다.
- `position_sizing_dynamic_formula`가 메인 봇의 신규·추가매수 수량을 소유합니다. 위젯·에피소드 수량은 각 독립 owner의 계약을 따릅니다.
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
│   └── trading/                    # 위젯·에피소드 등 독립 주문 owner
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
| [Widget Runbook](docs/widget-signal-auto-trading-runbook.md) | 위젯 매매 owner와 운영 계약 |
| [Episode Machines](docs/low-price-two-leg-machines.md) | 종목별 two-leg 에피소드 계약 |
| [Stage2 Checklist](docs/checklists/README.md) | 날짜별 실행 항목 |

## 주의

이 프로젝트는 개인 자동매매와 리서치 운영 코드이며 README와 리포트는 투자 조언이 아닙니다. 실계좌 권한, API key, 주문가능금액, 세금·수수료와 거래소·브로커 장애는 운영자가 직접 관리해야 합니다.

실주문 범위가 넓어지는 변경은 runtime owner, source-quality gate, rolling evidence, approval boundary와 rollback guard를 먼저 확인합니다.
