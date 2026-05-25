# KORStockScan

KORStockScan은 한국 주식 매매를 자동으로 관찰하고, 장중 판단과 장후 복기를 이어 붙여 다음 장전의 실행 후보를 준비하는 개인용 리서치/운영 시스템입니다.

짧게 말하면 세 가지를 함께 합니다. 장중에는 키움 시세와 계좌 상태를 보며 스캘핑 후보를 평가하고, 장후에는 실제 매매와 시뮬레이션 결과를 비교해 무엇이 나았는지 계산합니다. 그리고 그 결과를 다음 장전의 제한된 실행 후보로만 넘겨, 실계좌 변경이 조용히 커지지 않도록 막습니다.

이 저장소의 현재 기준 문서는 [Plan Rebase](docs/plan-korStockScanPerformanceOptimization.rebase.md)입니다. 날짜별 실행 항목은 [stage2 checklist](docs/checklists/README.md)가 소유하고, 시간대별 운영 절차는 [Time-Based Operations Runbook](docs/time-based-operations-runbook.md)을 따릅니다.

현재 기준일: `2026-05-24 KST`

## 무엇을 하는가

KORStockScan은 단순한 매수/매도 봇이 아니라, 매매 판단을 계속 검증하는 자동화 체인에 가깝습니다.

장중에는 키움 REST/WebSocket 데이터, 호가와 체결, 계좌 상태, 보유 포지션, AI 판단을 모아 후보를 평가합니다. 스캘핑은 빠른 진입과 보유/청산 품질을 중점적으로 보고, 스윙은 추천부터 진입, 보유, 추가매수, 청산까지의 흐름을 dry-run 중심으로 추적합니다.

장후에는 하루 동안의 이벤트를 다시 엮습니다. 실제 주문이 들어간 경우와 시뮬레이션으로만 남긴 경우를 분리하고, 놓친 진입이나 피한 손실도 따로 복기합니다. 여기서 중요한 기준은 단순 승률이 아니라 기대값과 순이익입니다.

다음 장전에는 장후 산출물 중 안전장치와 검증을 통과한 항목만 제한적으로 runtime env에 반영합니다. 장중에 임의로 한계값을 바꾸거나, 리포트 하나만 보고 실주문 범위를 넓히는 방식은 사용하지 않습니다.

## 주요 기능

**스캘핑 엔진**

장중 후보를 감시하고, AI 점수, 유동성, 호가 품질, 지연 상태, 과열 여부, 수급 맥락을 함께 봅니다. 점수는 중요한 특징값이지만 단독 매수 명령은 아닙니다. stale quote, 브로커 제출 가드, 계좌/수량/쿨다운 같은 안전장치는 항상 우선합니다.

**스윙 dry-run과 제한된 real canary**

스윙은 기본적으로 dry-run self-improvement 체인입니다. 실제 주문 없이 추천, 진입, 보유, 추가매수, 청산 흐름을 추적하고 장후에 결과를 평가합니다. 단, AI Tier2 검증과 source-quality gate를 통과한 일부 phase0 후보는 1주 단위 real canary로 실행 품질을 수집할 수 있습니다. 이것은 전체 스윙 실매매 전환이 아닙니다.

**시뮬레이션과 놓친 기회 복기**

실계좌 예수금 부족, 1주 cap, 현재 selected family 여부는 시뮬레이션 후보 제외 사유가 아닙니다. 대신 provenance로 남깁니다. 실제 매매, 시뮬레이션, 합산 분석은 분리해서 보며, 실주문 품질 판단에는 real-only 데이터를 사용합니다.

**장후 리포트와 자동 보완 후보**

하루 동안 쌓인 이벤트는 threshold cycle, lifecycle matrix, sentinel, panic report, swing audit, bottom rebound research, pattern lab 같은 리포트와 분석으로 정리됩니다. 자동화는 여기서 다음 장전 적용 후보, sim-auto 후보, 코드 보완 workorder를 만들 수 있습니다.

**운영 감시**

System Error Detector가 프로세스, cron, 로그, artifact freshness, 리소스, stale lock을 감시합니다. 이 감시는 전략 변경 도구가 아니라 운영 상태 점검 도구입니다. 장애가 발견되면 원인 복구나 instrumentation 보강으로 라우팅합니다.

## 안전 원칙

KORStockScan의 기본 철학은 “자동화하되, 실계좌 위험이 커지는 지점은 명확히 분리한다”입니다.

장중 runtime threshold mutation은 금지합니다. 변경은 장후 리포트와 검증을 거쳐 다음 장전 runtime env로만 들어갑니다.

AI는 제안자이자 검토자입니다. AI가 단독으로 브로커 주문 안전장치, stale quote 차단, 계좌/수량/쿨다운 가드, hard/protect/emergency stop을 우회할 수 없습니다.

sim-auto, dry-run, bounded live, bounded real canary까지는 AI Tier2 검증과 hard gate를 통과하면 자동 판정될 수 있습니다. 하지만 최종 full-live 전환, cap 해제, provider 변경, bot restart, hard safety 완화는 사용자 승인 경계로 남깁니다.

내부 prompt와 JSON contract는 영어 label을 기준으로 합니다. 오래된 한국어 label은 명시된 compatibility map으로만 정규화하고, 정의되지 않은 새 label이 나오면 source-quality FAIL로 표면화합니다.

## 프로젝트 구조

저장소는 “실시간 실행”, “장후 분석”, “운영 문서”가 한 프로젝트 안에 같이 들어 있는 구조입니다. 처음 볼 때는 모든 파일을 한 번에 따라가기보다, 아래 세 흐름만 잡으면 됩니다.

실시간 실행 흐름은 `src/`와 `deploy/`가 중심입니다. 봇은 장전 runtime env를 읽고, 키움 시세와 계좌 상태를 받아 후보 평가, 주문 안전장치, 보유/청산 관리를 수행합니다. 장후 분석 흐름은 `data/report/`, `data/threshold_cycle/`, `analysis/`에 결과를 남깁니다. 운영 문서 흐름은 `docs/`가 맡고, 현재 원칙과 날짜별 실행 항목을 분리해서 관리합니다.

```text
KORStockScan/
├── src/                 # 봇, 엔진, 리포트, 웹 대시보드, 테스트
├── analysis/            # 오프라인 패턴 분석과 pattern lab
├── data/                # runtime event, threshold cycle, report, config
├── deploy/              # cron, systemd, nginx, 운영 wrapper
├── docs/                # 기준 문서, runbook, checklist, workorder
└── logs/                # 운영 로그
```

자주 보는 위치는 다음과 같습니다.

| 위치 | 내용 |
| --- | --- |
| `src/bot_main.py` | 운영 봇 진입점 |
| `src/engine/` | 매매 엔진, AI, 리포트, 자동화 CLI |
| `src/engine/swing/` | 스윙 자동화와 승인 컨트롤 |
| `src/web/` | Flask 대시보드와 API |
| `data/report/` | 장중/장후 리포트 |
| `data/threshold_cycle/` | 장전 apply plan과 runtime env |
| `docs/checklists/` | 날짜별 실행 항목 |
| `docs/code-improvement-workorders/` | 자동 생성된 코드 보완 지시서 |

조금 더 세부적으로 보면 `src/engine/`은 여러 성격의 모듈이 함께 있습니다. 스캘핑 실행 로직, AI 응답 계약, 리포트 생성기, threshold cycle, source-quality audit, bottom rebound research 같은 CLI가 여기에 모입니다. 스윙처럼 독립적인 하위 도메인은 `src/engine/swing/` 아래에 두고, 단순히 새 코드를 모두 `src/engine/`에 넣는 방식은 피합니다.

`data/`는 운영 중 계속 쌓이는 작업 공간입니다. 장중 raw event는 `data/pipeline_events/`, 자동화 체인이 읽는 compact event는 `data/threshold_cycle/`, 사람이 확인하는 리포트는 `data/report/`에 모입니다. JSON/JSONL이 기준 데이터이고, Markdown은 사람이 빨리 읽기 위한 요약입니다.

`docs/`는 의사결정의 기준입니다. Plan Rebase는 현재 정책과 금지선을, runbook은 시간대별 운영 절차를, checklist는 특정 날짜의 실행 항목을 소유합니다. README는 전체 안내서 역할만 하며, 세부 판정 기준은 기준 문서로 연결합니다.

## LDM의 구성

LDM은 Lifecycle Decision Matrix의 줄임말입니다. 이름은 조금 딱딱하지만, 하는 일은 단순합니다. 후보가 처음 발견된 순간부터 진입, 제출, 보유, 추가매수, 청산까지의 전 과정을 같은 형식의 행으로 정리하고, 어느 구간에서 어떤 선택이 더 나았는지 장후에 비교합니다.

LDM은 기존의 고정 점수표를 대체하는 “단독 매수 엔진”이 아닙니다. 점수, 수급, 지연, 유동성, 과열, 가격 품질, 보유 손익, 시장 레짐 같은 값을 특징으로 모으고, 사후 수익률, 놓친 상승, 피한 손실, MFE/MAE 같은 결과와 분리해서 봅니다. 장중에 알 수 없는 사후 결과는 runtime 판단에 넣지 않습니다.

구성은 크게 다섯 단계입니다.

| 단계 | 보는 것 | 예시 판단 |
| --- | --- | --- |
| `entry` | 후보를 지금 살지, 더 기다릴지 | 방어적 진입, 재호가 대기, AI no-buy 유지 |
| `submit` | 실제 주문 제출 전 품질 | stale quote 차단, latency 위험, 브로커/계좌 가드 |
| `holding` | 보유를 이어갈지 줄일지 | soft stop 유지, HOLD/EXIT 보정 |
| `scale_in` | 물타기/불타기 후보 | AVG_DOWN, PYRAMID, 가격/수량 가드 |
| `exit` | 청산 품질 | 빠른 손절, 추세 보유, missed upside 복기 |

장후에는 `entry_bucket_attribution`, `scale_in_bucket_attribution`, `overnight_bucket_attribution` 같은 bucket attribution이 만들어집니다. bucket은 “점수 60대이면서 유동성은 충분하지만 stale 위험이 있었던 후보”처럼 비슷한 상황을 묶는 단위입니다. 각 bucket은 표본 수, 기대값, source-quality, 후속 hook 준비 여부를 기준으로 분류됩니다.

현재 기준으로 자동 생성되는 주요 bucket 축은 아래와 같습니다.

| bucket 묶음 | 현재 축 | 주로 답하는 질문 |
| --- | --- | --- |
| Entry bucket | `score_band`, `source_stage`, `chosen_action`, `stale_bucket`, `liquidity_bucket`, `strength_bucket`, `overbought_bucket`, `time_bucket`, `exit_rule`, `combo_entry_spot` | 어떤 진입 조건 조합이 기대값을 만들었는가 |
| Submit bucket | `submit_source_stage`, `revalidation_state`, `quote_age_bucket`, `price_resolution_bucket`, `would_limit_fill`, `actual_order_submitted`, `broker_order_forbidden`, `combo_submit_quality` | 주문 직전 품질 문제인지, 실제 제출/브로커 계약 문제인지 |
| Scale-in bucket | `arm`, `blocker_namespace`, `blocker_reason`, `profit_band`, `peak_profit_band`, `held_bucket`, `ai_score_band`, `ai_score_source`, `supply_pass_bucket`, `price_guard_reason`, `qty_reason`, `time_bucket` | 물타기/불타기 중 어느 조건이 좋거나 위험했는가 |
| Overnight bucket | `overnight_action`, `overnight_status`, `confidence_band`, `profit_band`, `peak_profit_band`, `held_bucket`, `price_source`, `source_quality_gate`, `combo_overnight_decision` | 장마감 sim 포지션을 당일 가상청산할지, 다음날 carry할지 |
| Swing entry bucket | `origin`, `block_reason`, `position_tag`, `gap_bucket`, `score_bucket`, `vpw_bucket`, `strategy`, `entry_price_provenance`, `qty_source` | 스윙 후보가 어디서 왔고 어떤 진입 병목을 가졌는가 |
| Swing holding/exit bucket | `mfe_bucket`, `mae_bucket`, `held_bucket`, `exit_reason`, `panic_context`, `ofi_state`, `qi_state` | 보유를 더 이어갔어야 했는지, 청산이 늦거나 빨랐는지 |
| Swing scale-in bucket | `add_type`, `source_quality_status`, `qty_source`, `price_policy` | 스윙 추가매수 후보의 수량/가격 정책이 적절했는가 |
| Swing discovery arm bucket | `entry_policy`, `sizing_policy`, `exit_policy`, `sector`, `theme_tags`, `legacy_ml_cohort` | 여러 가상 arm 중 어떤 조합이 살아남는가 |

이 목록은 “고정 매매 규칙” 목록이 아니라 관찰과 분류의 기준입니다. 예를 들어 `liquidity_bucket=liquidity_unknown`이 나왔다고 해서 즉시 매수를 금지하는 것이 아니라, 해당 bucket의 표본 수, 기대값, source-quality, 후속 hook 준비 상태를 보고 `keep collecting`, `candidate_tighten_or_exclude`, `sim_auto_approved`, `runtime_blocked_contract_gap` 같은 상태로 닫습니다.

2026-05-22 장후 산출물 기준으로는 raw attribution bucket row가 총 4,487개, discovery가 후보로 분류한 bucket catalog가 총 769개입니다. 이 숫자는 새 source와 bucket 축이 추가되면 계속 늘어날 수 있으므로, README에는 최신 스냅샷으로만 기록합니다.

| 구분 | 최신 bucket 수 | sim-auto 후보 | 비고 |
| --- | ---: | ---: | --- |
| Scalping entry attribution | 139 | 11 | 진입 조건과 action bucket |
| Scalping scale-in attribution | 3,507 | 105 | AVG_DOWN/PYRAMID 및 blocker bucket |
| Scalping overnight attribution | 35 | 0 | 장마감 sim carry/가상청산 bucket |
| Scalping stage-policy candidates | - | 3 | submit/holding/exit weighted ADM policy 후보 |
| Swing entry attribution | 159 | 0 | 스윙 discovery/probe 진입 병목 bucket |
| Swing holding/exit attribution | 31 | 4 | 스윙 보유/청산 outcome bucket |
| Swing scale-in attribution | 0 | 0 | 현재 2026-05-22 표본 없음 |
| Swing discovery arm attribution | 616 | 0 | entry/sizing/exit/sector/theme arm bucket |
| 합계 | 4,487 | 123 | sim-auto 123개 중 positive recovery 성격은 8개 |

`sim_auto_approved`는 모두 좋은 방향이라는 뜻이 아닙니다. 일부는 “더 열어볼 후보”이고, 일부는 “나쁜 조건이 반복되어 sim 정책에서 더 조여볼 후보”입니다. 아래 표는 그중 기대값이 양수이고 `candidate_recovery_or_relax` 성격으로 해석된 좋은 sim bucket만 따로 모은 것입니다.

| 영역 | bucket | 표본 | source-quality EV | 진단 승률 | 해석 |
| --- | --- | ---: | ---: | ---: | --- |
| Scalping scale-in | `blocker_reason=trend_not_strong` | 37 | 2.8673 | 1.0000 | trend 부족으로 막힌 scale-in 후보가 sim에서는 회복/완화 관찰 대상 |
| Scalping entry | `source_stage=wait6579_ev_cohort` | 35 | 2.3199 | 0.7714 | wait65-79 계열 source가 positive recovery 후보 |
| Scalping entry | `stale_bucket=fresh_or_unflagged` | 35 | 2.3199 | 0.7714 | stale 문제가 없거나 표시되지 않은 entry 후보가 positive recovery 후보 |
| Scalping entry | `score_band=score_66_69` | 28 | 1.6584 | 0.8214 | 66-69 점수대가 단독 확정은 아니지만 sim recovery bucket으로 관찰됨 |
| Scalping entry | `score_band=score_63_65` | 16 | 1.5141 | 0.4375 | 낮은 승률에도 EV가 양수라 diagnostic win rate와 분리해 관찰 |
| Scalping scale-in | `blocker_reason=profit_not_enough` | 3,633 | 0.3993 | 0.9408 | 수익 부족으로 막힌 scale-in 조건 일부가 sim에서는 완화 후보 |
| Swing holding/exit | `mfe_high / mae_green / held_missing / trailing_after_mfe_stop` | 4 | 18.5745 | - | 고 MFE/양호 MAE 이후 trailing stop 계열 holding/exit sim 후보 |
| Swing holding/exit | `mfe_high / mae_low / held_missing / trailing_after_mfe_stop` | 5 | 10.9526 | - | 고 MFE/낮은 MAE 이후 trailing stop 계열 holding/exit sim 후보 |

이 표에 올라온 bucket도 실주문 승인 근거가 아닙니다. 다음 PREOPEN sim policy 또는 pre-final 후보의 입력일 뿐이며, live 적용은 별도의 Tier2 검증, env mapping, runtime hook, rollback/post-apply attribution을 통과해야 합니다.

분류 결과는 대략 네 갈래로 흘러갑니다. 계속 관찰할 것은 source-only로 남고, 시뮬레이션에 바로 적용 가능한 것은 `sim_auto_approved`가 됩니다. 실제 runtime에 연결할 준비가 된 pre-final 후보는 `live_auto_apply_ready`가 될 수 있지만, parsed AI Tier2 검증과 env mapping, runtime hook, rollback/post-apply attribution이 닫혀야 합니다. 계약이 부족한 경우는 `runtime_blocked_contract_gap` 또는 code workorder로 라우팅됩니다.

중요한 금지선도 있습니다. LDM은 hard safety, 브로커 제출 가드, stale quote, 계좌/수량/쿨다운 가드를 우회하지 않습니다. 또한 점수가 높을수록 항상 좋은 매매라는 가정을 쓰지 않습니다. 점수는 feature일 뿐이고, 최종 판단은 장후 기대값과 source-quality를 함께 봅니다.

## 시뮬레이션 자동화

시뮬레이션 자동화는 아래 흐름으로 움직입니다. 핵심은 “장중에는 넓게 관찰하고, 장후에는 숫자로 분류하고, 다음 장전에는 검증된 작은 변경만 반영한다”입니다.

```text
장중 후보 수집
  -> sim/probe 가상 lifecycle 생성
  -> 장후 결과 라벨링과 EV 계산
  -> pattern lab source-only 분석
  -> LDM bucket attribution
  -> lifecycle bucket discovery
  -> threshold cycle / runtime approval summary / code improvement workorder
  -> 다음 PREOPEN sim policy 또는 제한된 runtime env 후보
  -> 다음 장후 post-apply attribution으로 다시 검증
```

| 단계 | 쉽게 말하면 | 산출물/다음 연결 |
| --- | --- | --- |
| 장중 후보 수집 | 실제 주문 여부와 무관하게 “살 수도 있었던 후보”를 넓게 모읍니다. | pipeline event, threshold compact event |
| sim/probe lifecycle | 주문하지 않은 후보도 가상으로 진입, 보유, 추가매수, 청산 흐름을 태웁니다. | sim position, probe row, swing dry-run row |
| 장후 라벨링과 EV 계산 | 실제로 이후 가격이 어떻게 움직였는지 보고 기대값과 놓친 기회를 계산합니다. | daily EV, post-sell evaluation, swing label/report |
| pattern lab | 스캘핑/스윙 fact table과 EV 결과를 패턴 단위로 다시 읽어 AI review payload, backlog, source-quality warning을 만듭니다. | `analysis/*_pattern_lab/outputs/`, source-only warning, candidate/workorder input |
| LDM bucket attribution | 비슷한 조건을 bucket으로 묶어 어떤 조건 조합이 좋았는지 봅니다. | entry/submit/holding/scale-in/exit bucket |
| bucket discovery | bucket을 계속 관찰, sim-auto, pre-final 후보, code gap으로 분류합니다. | `sim_auto_approved`, `live_auto_apply_ready`, `runtime_blocked_contract_gap` |
| threshold cycle | 장후 리포트와 검증을 모아 다음 장전 적용 후보를 만듭니다. | apply plan, runtime env, runtime approval summary |
| code improvement | 데이터는 좋은데 hook, source, schema, parser가 부족하면 구현 지시서로 넘깁니다. | `docs/code-improvement-workorders/` |
| 다음 장후 재검증 | 적용되었거나 적용되지 않은 후보의 결과를 다시 비교합니다. | post-apply attribution, 다음 bucket 갱신 |

시뮬레이션 자동화의 목적은 “실주문을 늘리기 전에 더 많은 후보를 가상으로 따라가 보는 것”입니다. 실제로 주문하지 않은 후보도 장중에는 가상 진입, 보유, 추가매수, 청산 흐름을 만들고, 장후에 결과를 계산합니다. 이렇게 하면 실계좌를 키우지 않고도 어떤 조건이 좋은지, 어떤 조건이 반복적으로 나쁜지 더 넓게 볼 수 있습니다.

스캘핑 쪽에서는 BUY 후보를 실제 주문 여부와 무관하게 추적합니다. 예수금 부족, 1주 cap, 현재 selected family 여부 때문에 후보를 버리지 않고, `actual_order_submitted=false` provenance를 붙여 sim/probe로 남깁니다. sim position은 이후 post-sell evaluation과 daily EV에 연결되어, 놓친 상승이나 피한 손실을 따로 계산합니다.

스윙 쪽에서는 safe pool 후보를 여러 arm으로 확장합니다. 기본 discovery sim은 후보마다 진입 방식, 보유 기간, 청산 정책 같은 조합을 나누고, label builder가 1일/5일/10일 및 policy exit 결과를 채웁니다. bottom rebound source 후보는 돌파 확인을 기다리는 방식이 아니라 다음날 선제 진입 시나리오를 따로 만들어 비교합니다.

Pattern lab은 이 시뮬레이션 자동화의 장후 해석 계층입니다. `analysis/gemini_scalping_pattern_lab`, `analysis/claude_scalping_pattern_lab`, `analysis/deepseek_swing_pattern_lab`가 fact table과 EV 결과를 다시 묶어 손실/수익 패턴, opportunity cost, source-quality gap, AI review payload를 생성합니다. 이 산출물은 `code_improvement_order`, `auto_family_candidate`, workorder 입력으로만 쓰며, 단독으로 실주문, threshold apply, provider 변경, bot restart를 실행하지 않습니다.

자동화는 sim 결과를 다음 세 가지로 나눠 소비합니다.

| 결과 | 의미 | 다음 처리 |
| --- | --- | --- |
| 좋은 sim bucket | 기대값이 개선되고 source-quality가 통과한 후보 | 다음 PREOPEN sim policy 또는 pre-final 후보로 전달 |
| 나쁜 sim bucket | 손실이나 missed upside가 반복되는 조건 | bucket tighten 후보나 code-improvement workorder로 전달 |
| 불완전한 sim bucket | 표본 부족, source 누락, hook 미구현 | keep collecting, source-quality blocker, contract gap으로 보류 |

sim-auto 승격은 사람이 매번 승인하지 않아도 됩니다. 다만 이것은 어디까지나 시뮬레이션 정책 승격입니다. 실주문, cap 해제, provider 변경, bot restart, hard safety 완화로 직접 이어지지 않습니다. bounded live나 bounded real canary 단계도 AI Tier2 검증과 hard gate를 통과해야 하며, 최종 full-live 전환은 사용자 승인 경계로 남습니다.

## 처음 실행할 때

Python 작업은 프로젝트 `.venv`를 기본으로 사용합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

운영 설정은 샘플을 복사한 뒤 서버 환경에 맞게 채웁니다.

```bash
cp data/config_sample.json data/config_prod.json
```

최소한 키움 API 정보, DB 접속 정보, OpenAI API key가 필요합니다. Telegram, GitHub Project, Google Calendar 연동은 선택입니다. 민감정보는 git에 커밋하지 않습니다.

스캘핑 live AI route는 OpenAI를 기준으로 둡니다.

```bash
export OPENAI_API_KEY="..."
export KORSTOCKSCAN_SCALPING_AI_ROUTE=openai
export KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws
export KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true
```

기본 검증은 아래 명령으로 시작합니다.

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run
```

## 운영 흐름

장전에는 전일 리포트와 검증 결과를 읽어 당일 runtime env를 만듭니다.

```bash
THRESHOLD_CYCLE_APPLY_MODE=auto_bounded_live \
THRESHOLD_CYCLE_AUTO_APPLY=true \
THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI=true \
./deploy/run_threshold_cycle_preopen.sh "$(TZ=Asia/Seoul date +%F)"
```

봇은 `src/run_bot.sh`를 통해 실행합니다. wrapper는 당일 runtime env를 source하고, 필요한 경우 장전 apply 생성을 시도합니다.

```bash
cd src
bash run_bot.sh
```

장후에는 threshold cycle, 스윙 dry-run, panic report, lifecycle matrix, workorder, EV attribution 같은 산출물이 만들어집니다. 운영 cron과 상세 시간표는 [Time-Based Operations Runbook](docs/time-based-operations-runbook.md)을 기준으로 봅니다.

## 리포트 읽는 법

JSON/JSONL이 canonical data입니다. 사람이 빠르게 확인해야 하는 결과만 Markdown으로 같이 생성합니다.

| 경로 | 의미 |
| --- | --- |
| `data/pipeline_events/` | 장중 raw event stream |
| `data/threshold_cycle/threshold_events_YYYY-MM-DD.jsonl` | 자동화 체인이 읽는 compact stream |
| `data/report/threshold_cycle_ev/` | daily EV와 적용/미적용 귀속 |
| `data/report/runtime_approval_summary/` | 자동/수동 승인 경계 요약 |
| `data/report/lifecycle_decision_matrix/` | lifecycle bucket과 후보 정책 |
| `data/report/swing_*` | 스윙 dry-run, audit, approval 관련 리포트 |
| `data/report/error_detection/` | 운영 감시 결과 |

전체 report inventory는 [data/report/README.md](data/report/README.md)를 참고합니다.

## 문서와 동기화

Plan Rebase, runbook, README, prompt, AGENTS 같은 기준 문서는 사용자가 명시적으로 요청했을 때만 수정합니다. 문서 변경 후 checklist parser 검증은 AI가 실행합니다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

GitHub Project와 Google Calendar 동기화는 사용자가 아래 표준 명령으로 직접 실행합니다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 핵심 문서

| 문서 | 역할 |
| --- | --- |
| [Plan Rebase](docs/plan-korStockScanPerformanceOptimization.rebase.md) | 현재 튜닝 원칙, active/open 상태, 금지선 |
| [Time-Based Operations Runbook](docs/time-based-operations-runbook.md) | 시간대별 운영 절차와 확인 기준 |
| [Report Automation Traceability](docs/report-based-automation-traceability.md) | 자동화 산출물과 소비 계약 |
| [Threshold Cycle README](data/threshold_cycle/README.md) | 장전 apply plan과 runtime env 운영 방식 |
| [Data Report README](data/report/README.md) | 정기 report 목록 |
| [Stage2 Checklist](docs/checklists/README.md) | 날짜별 실행 항목과 Project/Calendar source |

## 주의

이 프로젝트는 개인 자동매매와 리서치 운영 코드입니다. README와 리포트는 투자 조언이 아닙니다. 실계좌 주문, API key, 계좌 권한, 주문가능금액, 세금/수수료, 거래소/브로커 장애는 사용자가 직접 관리해야 합니다.

실주문 범위가 넓어지는 변경은 항상 approval boundary, runtime owner, rollback guard, source-quality gate를 확인한 뒤 다룹니다.
