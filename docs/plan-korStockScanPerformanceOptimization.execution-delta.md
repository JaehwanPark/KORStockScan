# KORStockScan 기본계획 대비 실행 변경사항

기준 시각: `2026-04-19 KST`

이 문서는 `2026-04-11` 원안 계획과 `2026-04-19` 현재 실행 기준 사이에서 실제로 변경된 사항만 추린다.  
현재 중심 기준은 [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md)를 본다.  
`fallback_scout/main`, `fallback_single`, `latency fallback split-entry` 등 영문 축 표현은 [Plan Rebase 용어 범례](./plan-korStockScanPerformanceOptimization.rebase.md#2-용어-범례)를 우선한다.

## 1. 판정

1. 계획은 유지하되 실행 방식은 `공격적 동시 추진`에서 `원인 귀속 우선 순차 실행`으로 조정됐다.
2. 가장 큰 변경은 `split-entry 3축 동시 shadow`를 버리고 `rebase -> 즉시 재평가 -> cooldown` 순차 도입으로 바꾼 점이다.
3. HOLDING 축도 `schema 착수`와 `성과판정`을 분리해 `D+2` 판정 구조로 변경됐다.
4. `2026-04-20` 기준으로 baseline/rollback 수치 해석도 조정됐다. 문서 파생값과 rolling trend 값을 hard KPI로 섞어 쓰지 않도록 `DB 우선 실필드 기준`으로 재고정한다.
5. `2026-04-20`부터 신규 관찰축/보완축은 `shadow`를 열지 않고 `canary-only`로 운영한다.
6. `TRADING_RULES` 운영 상수, 특히 모델명/투자비율/주문한도/실전 canary 스위치는 요청 범위를 넘겨 바꾸지 않는다. 변경 필요 시 사용자 명시 승인과 롤백 조건을 먼저 기록한다.

## 2. 변경사항 요약

| 영역 | 기본계획 | 현재 실행 기준 | 변경 이유 | 현재 닫힘 시점 |
| --- | --- | --- | --- | --- |
| `Plan Rebase 문서 역할` | 날짜형 workorder가 중심 기준/체크리스트/실행로그를 함께 보유 | `plan-korStockScanPerformanceOptimization.rebase.md`를 중심축으로 신설하고, 날짜별 checklist는 실행, workorder는 상세 근거, 감사보고서는 수치 근거로 분리 | 원칙/판정축/체크리스트 혼재로 의사결정 추적성이 떨어짐 | 즉시 적용 (`2026-04-22`) |
| `Plan Rebase 중심 문서 감리 반영` | 중심 문서 구조 승인 전 상태 | `audit-reports/2026-04-22-plan-rebase-central-audit-review.md`를 감사보고서로 보관하고, S-1~S-3/B-1~B-4 중 기준화가 필요한 항목만 rebase/checklist에 반영 | 감사보고서는 매일 생성되므로 전문을 중심 문서에 흡수하지 않고, 안정 규칙/일정/guard만 기준화 | 즉시 적용 (`2026-04-22`) |
| `split-entry shadow` | `2026-04-20`에 `rebase/즉시 재평가/cooldown` 3축 동시 판정 | `2026-04-20 rebase`, `2026-04-21 즉시 재평가`, `2026-04-22 cooldown` 순차 도입 | 동일 세션 원인귀속 불가, audited table `S-1` 반영 | `2026-04-22` |
| `split-entry 판정 조건` | 표본 부족 시 결론 유예 수준의 서술형 | 각 판정 행에 `N_min/Δ_min/PrimaryMetric` 명시 필요 | audited table `S-2` 반영 | `2026-04-20 PREOPEN` |
| `rollback guard` | 문서상 점검 수준 | `reject_rate/partial_fill_ratio/latency_p95/reentry_freq` 정량화 필요 | audited table `S-3` 반영 | `2026-04-20 PREOPEN` |
| `HOLDING 성과판정` | `2026-04-21` 1일차 판정 | `2026-04-22 D+2` 최종판정 | schema 변경 직후 자기참조 오염 방지, audited table `S-4` 반영 | `2026-04-22 POSTCLOSE` |
| `AIPrompt 작업 10` | `2026-04-19` 1차 결과 평가 후 확대 여부 판정 | `2026-04-20`에는 `shadow-only 유지/확대 보류`만 판정, 최종 확대는 `2026-04-22` | `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version` 관찰축 부족 | `2026-04-22 POSTCLOSE` |
| `프로파일별 특화 프롬프트 잔여과제` | 프로파일 분기/스키마 이식 완료를 사실상 종료로 해석 가능 | `shared 의존 제거`와 `개별 특화`는 별도 잔여과제로 분리한다. `09:00~12:00` 오전 반나절 관찰 후 `2026-04-22 12:20~12:30 KST`에 `watching 특화 / holding 특화 / exit 특화 / shared 제거 / 전부 미착수` 중 하나로 강제판정한다. 미관측 후보는 추가 유예 없이 관찰축 오류 또는 live 영향 없음으로 닫는다 | 구조 이식 완료와 성능/행동 품질 개선 완료를 분리해 원인귀속 정확도 확보. `shared 제거`는 오전 중 `scalping_shared`가 주문/보유/청산 의사결정에 연결될 때만 live canary 후보이며, 미관측이면 코드정리 또는 현행 유지다 | `2026-04-22 12:20~12:30` 최종 잠금 |
| `AIPrompt 작업 8` | 핵심값 3종 투입 결과 정리 후 완료 후보 | 값 주입은 존재하나 `*_sent` 감사 로그 부족으로 미완료 유지 | 완료 기준과 감사 필드 범위 불일치 | `2026-04-20 POSTCLOSE` 재판정 |
| `원격 canary 운용` | 튜닝축 신규 변경은 원격 canary 선행을 기본값으로 사용 | `Plan Rebase` 기준으로 판정 입력은 `main-only`로 고정하고 원격/server 값은 운영 의사결정에서 제외한다. 원격 정합화는 참고/사전검증 용도에만 제한한다. | split-entry/HOLDING 우선순위 집중 + 원인귀속 혼선 제거 | 즉시 적용 (`2026-04-23 POSTCLOSE`) |
| `PYRAMID zero_qty Stage 1 반영` | 수량 패치가 유효하면 `PYRAMID/REVERSAL_ADD` 동시 범위로 확장 가능 | 현재 실행 기준은 `SCALPING/PYRAMID bugfix-only`에 한해 `main code-load(flag OFF) -> PREOPEN env/restart/log evidence -> main canary go/no-go` 순서로만 허용한다. `remote` 선행과 다축 동시 확장은 쓰지 않는다. | LIVE/OFF 축 혼동 방지 + split-entry/HOLDING 관찰축 보존 + `main-only` 기준 정렬 | `2026-04-24 POSTCLOSE` go/no-go |
| `개별 종목 이슈 해석 범위` | scale-in 이슈 중심으로 빠른 수량 패치 논의 가능 | 개별 종목은 `entry gate + latency + liquidity + holding exit` 4축 분해 관찰 후에만 로직 변경 후보화 | 단일 원인 오판 방지 + 기대값 손실의 실제 누수지점 분리 | `2026-04-21 POSTCLOSE` 재확인 |
| `물타기축(AVG_DOWN/REVERSAL_ADD)` | holding-profit-conversion 플랜 기준으로 `2026-04-20~2026-04-21` 관찰/전환 가능 | 현재 활성 플랜에서는 우선순위에서 내려 `일정 확정만` 수행하고, 실제 재오픈 여부는 `2026-04-24 POSTCLOSE`에 다음주 `shadow 금지 + canary-only 후보성` 기준으로만 판정한다. | split-entry/HOLDING 우선 + 실주문 변경축 과밀 방지 + `shadow 금지` 기준 반영 | `2026-04-23 일정 확정`, `2026-04-24 go/no-go` |
| `장전 리포트 빌드 운영` | 장전에도 필요 시 full build 실행 가능으로 운용 | `PREOPEN`에는 `sanity check` 우선, full build는 `bot_main` 동작 중 차단(락 + override 필요) | `2026-04-20` 장전 부하/장애 재발 방지 | 즉시 적용 (`deploy/run_monitor_snapshot_safe.sh`) |
| `장중 스냅샷 부하 분산 운영` | 장중 점검은 필요 시 full snapshot 반복 실행 가능 | 장중은 `intraday_light` 증분(지연/jitter)으로 워밍하고, 기준 판정은 `12:00~12:20 full` 1회로 고정한다. `performance_tuning` trend window는 가변(`trend_max_dates`)으로 운용하고, snapshot manifest를 자동 생성해 raw 압축 검증축으로 재사용한다. `bot_main` 동작 중 기존 full manifest가 있으면 duplicate full rerun은 skip한다. | 장중 세션 단절 원인인 read/write burst 완화 + 압축 검증 정합성 확보 + 일일 작업지시서 전달 기준 명확화 | 즉시 적용 (`deploy/run_monitor_snapshot_cron.sh`, `deploy/run_monitor_snapshot_incremental_cron.sh`, `deploy/run_monitor_snapshot_safe.sh`, `src/engine/log_archive_service.py`, `src/engine/notify_monitor_snapshot_admin.py`, `src/engine/sniper_performance_tuning_report.py`, `src/engine/compress_db_backfilled_files.py`) |
| `heavy report builder 운영 가드` | `performance-tuning/post-sell/trade-review`는 필요 시 즉시 foreground 재빌드 가능 | 웹/API/운영 경로에서 heavy builder 직접 호출을 금지하고 `saved snapshot 우선 -> safe wrapper async dispatch -> completion artifact + Telegram` 순서로만 재생성한다. 이 보호 규칙은 `PREOPEN/INTRADAY/POSTCLOSE`를 포함한 모든 일일작업에 공통 적용하며, `refresh=1`은 foreground rebuild가 아니라 async dispatch 의미로 해석한다. | 일중 전 구간 리포트 빌더 foreground 실행으로 인한 IO burst/세션 정지 재발 방지 + 결과 복귀 신호 표준화 | 즉시 적용 (`2026-04-24 POSTCLOSE`) |
| `보유/청산 관찰축 재분해` | HOLDING D+2 표본 미달 이후 보유/청산 다음 계획이 공백 | `holding_exit_observation` 리포트 축을 추가해 saved snapshot, post-sell, pipeline event만으로 `readiness/cohorts/exit_rule_quality/soft_stop_rebound/same_symbol_reentry/trailing_continuation/opportunity_cost/load_distribution_evidence`를 고정한다. `soft_stop_rebound` 하위에는 `whipsaw_windows`, `down_count_evidence`, `hard_stop_auxiliary`를 포함한다. live 후보는 realized loss가 큰 `soft_stop_rebound_split`을 1순위로 두고, `trailing_continuation_micro_canary`는 2순위로 둔다. hard stop은 severe-loss guard라 보조 관찰로 parking한다. | submitted 증가 시 보유/청산 표본 폭증에 늦지 않게 단일 조작점과 rollback guard를 선제 고정한다. 진입병목 canary와 보유/청산 canary는 stage-disjoint 예외 조건이 성립할 때만 병렬 live 검토하며, 판정은 provisional로 제한한다. 하방카운트가 0회에 머무는 soft_stop 표본은 “휩쏘 방지장치 미작동” 후보로 별도 분리한다. | `2026-04-27 POSTCLOSE` 승인 후보 또는 보류+재시각 확정 |
| `AI 엔진 A/B 착수` | 운영 튜닝과 병행 | 운영 튜닝 종료판정 이후에도 `main-only`, `1축 canary`, `shadow 금지`를 유지하고 `2026-04-21 15:24 KST`에 잠근 preflight 범위를 그대로 재사용한다. | 원인 귀속 혼선 방지 + 단일축 실험 유지 + Plan Rebase 기준 정렬 | `2026-04-24 POSTCLOSE` go/no-go |
| `ApplyTarget 자동화` | parser/workorder가 제목/섹션/소스의 암시 단어를 보고 `remote`를 추정할 수 있음 | `ApplyTarget`은 문서 본문에 명시된 값만 우선 사용하고, 미명시 항목은 기본 `-`로 유지한다. 제목의 `원격`/`main`만 보조 추정에 사용하며 `canary`, `section`, `source` 후처리는 제거한다. | `remote` 오판으로 Project/workorder 범위가 왜곡되는 문제 차단 | 즉시 적용 (`2026-04-23 POSTCLOSE`) |
| `신규축 실행 방식` | shadow 선행 후 canary | 신규/보완축은 `shadow 금지`, `canary-only` | 영향도 확인을 실거래 경로에서 즉시 검증하고, 다축 실험은 금지 | 즉시 적용 (`2026-04-20`) |
| `broad relax` | `latency/tag/threshold` 확장 후보를 빠르게 재오픈 | `split-entry leakage` 1차 판정 전 재오픈 금지 | 거래수 확대보다 손실축 제거 우선 | split-entry 1차 판정 후 |
| `운영판정` | 실험축별 판정 중심 | `No-Decision Day` 게이트와 `report integrity / event restoration / aggregation quality` 품질게이트 병행 | 잘못된 집계로 잘못된 승격을 막기 위함 | 장후 반복 적용 |
| `baseline source-of-truth` | 문서 baseline과 스냅샷 baseline을 혼용 가능 | `DB 우선 스냅샷 실필드`만 하드 기준으로 사용, 문서 파생값은 raw 산식 추적 전까지 참고치로 격하 | `same_symbol_repeat_flag=55.1%`, rolling trend 등 basis 혼선 정리 필요 | `2026-04-21 POSTCLOSE` |
| `운영 상수 변경 통제` | 하드코딩 제거 중 상수값까지 함께 보정 가능 | `TRADING_RULES` 모델명/투자비율/주문한도/canary 스위치는 별도 명시 승인 없이는 전략 변경 금지 | `2026-04-20` 모델명 오판 재발 방지. 하드코딩 제거와 운영 모델 전략 변경을 분리 | 즉시 적용 (`2026-04-20`) |

## 3. 변경의 의미

### 3-1. 공격성은 낮춘 것이 아니라 방향을 바꿨다

1. 거래수 확대보다 `split-entry soft-stop` 손실축 제거가 먼저라는 점이 더 명확해졌다.
2. HOLDING 축도 `지금 바로 확대`가 아니라 `측정 가능한 운영 로그 축 확보 -> D+2 판정`으로 바뀌었다.
3. 이는 보수화가 아니라 `기대값 개선 실패 확률`을 낮추는 방향의 공격성 조정이다.

### 3-2. 문서 운영도 변경됐다

1. `prompt`는 현재 기준만 남긴 경량 실행본으로 바뀌었다.
2. 계획과 실행의 차이는 이 문서에 남긴다.
3. 정기 성과 baseline은 [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)로 분리했다.
4. 단, baseline 문서에 적힌 모든 숫자가 곧바로 hard KPI는 아니다. 리포트별 소유 지표와 금지 지표를 먼저 고정한다.

## 4. 앞으로 이 문서를 갱신하는 조건

다음 중 하나가 생기면 이 문서를 먼저 갱신한다.

1. 주간 검증축 표와 날짜별 checklist가 달라질 때
2. 기본계획의 날짜/순서/승격 조건이 바뀔 때
3. shadow-only가 live canary로 바뀌거나 반대로 축소될 때
4. 성과판정 시점이 이동할 때
5. broad relax 재오픈 조건이 변경될 때

## 5. Rebase 슬림화 분리 기준 (`2026-04-27`)

`plan-korStockScanPerformanceOptimization.rebase.md`가 비대해지지 않도록, 아래 내용은 이 문서 또는 Q&A로 내린다.

| 분리 대상 | 이동 문서 | 이유 |
| --- | --- | --- |
| 날짜형 과제 레지스터 | 이 문서 | active/open 원칙보다 과거 진행 로그가 더 커지면 중심 문서의 판독성이 떨어진다 |
| 지나간 일정표 | 이 문서 또는 날짜별 checklist | 절대시각이 지난 일정은 현재 규칙이 아니라 이력이다 |
| same-day pivot / 종료 / 폐기 기록 | 이 문서 | `왜 바뀌었는가`는 delta의 역할이다 |
| 반복 해석 질문 | [Q&A](./plan-korStockScanPerformanceOptimization.qna.md) | 본문 규칙을 장문 해설로 오염시키지 않기 위함 |

## 6. 최근 날짜형 이력 요약

| 날짜 | 변화 | 현재 의미 |
| --- | --- | --- |
| `2026-04-24` | `quote_fresh family` 단일 완화축들이 제출 회복에 실패했고, `gatekeeper_fast_reuse signature/window`가 다음 후보로 올라왔음 | 이후 `gatekeeper_fast_reuse`는 live 제출 회복축이 아니라 보조 진단축으로 격하됐다 |
| `2026-04-27 11:31 KST` | `latency_block=3196`, `latency_state_danger=3000` 재집계로 주병목이 `gatekeeper_fast_reuse`가 아니라 `latency_state_danger`임을 확정 | entry 주병목 해석이 `signature/window`에서 `other_danger/ws_jitter/spread`를 포함한 residual 분해로 되돌아갔다 |
| `2026-04-27 same-day` | `SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_SIGNAL_SCORE 90.0 -> 85.0` pivot 적용 | `other_danger-only residual`을 direct blocker 관점에서 다시 열었다 |
| `2026-04-27 same-day` | `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`를 live/observe candidate에서 제거하고 historical-only로 정렬 | fallback 관련 운영/감리/후속 개발 혼선을 닫았다 |
| `2026-04-27~2026-04-28` | `latency_quote_fresh_composite`를 active entry canary로 고정하고 `same bundle + canary_applied=False` baseline, `direction-only` downgrade 규칙을 문서화 | entry 복합축은 개별 파라미터 attribution이 아니라 묶음 ON/OFF로만 판정한다 |
| `2026-04-27~2026-04-28` | `soft_stop_micro_grace`를 holding/exit live 축으로 고정 | entry와 holding/exit는 stage-disjoint 예외로 병렬 live 가능하되, 성과 판정은 단계별 분리다 |
| `2026-04-29 PREOPEN` | `2026-04-28` parquet/post_sell partition을 재생성해 same-day `ShadowDiff`를 `all_match=true`로 복구했고, 잔존 mismatch는 `2026-04-27 historical` (`latency_block -3`, `full_fill -9`, `partial_fill -9`)로 범위를 축소했다 | `QuoteFresh` hard baseline 차단 사유는 이제 `freshness 미생성`이 아니라 `historical fill 집계 품질`이다. `2026-04-28` same-day raw/duckdb 정합은 복구됐다 |
| `2026-04-29 PREOPEN` | `씨아이에스(222080)` `post_sell_evaluation`이 생성돼 `MISSED_UPSIDE`, `rebound_above_sell=True`, `mfe_10m=0.98%`, `rebound_above_buy=False`를 확인했다 | `soft_stop_micro_grace_extend`는 기대값 후보로 유지하되, single-sample whipsaw 성향이라 same-slot live 승격은 보류한다 |
| `2026-04-29 PREOPEN` | `latency_quote_fresh_composite` 기본값을 `False`로 내리고 `restart.flag`를 소모해 main PID를 `7042 -> 9267`로 교체했다 | entry 단계는 현재 live 축이 비어 있고, 같은 단계 replacement/예비축 ON은 `OFF 값 반영 -> restart provenance`를 다시 충족한 뒤에만 재개할 수 있다 |
| `2026-04-29 10:00 KST` | `VM basis shift` 1차 점검에서 `09:00~10:00` 창 `gatekeeper_eval_ms_p95=10823.4ms`, `latency_state_danger share=83.9%`로 런타임 측면 개선 신호가 있었지만, `budget_pass_to_submitted_rate=0.0567% (2/3529)`는 `2026-04-28 h1000 0.0818% (1/1223)`보다 낮았다 | `m7g.xlarge` 변경 효과는 현재 `infra-only improvement 후보`까지이며, 제출 회복/기준선 reset 근거는 아니다. `12:00` 최종창에서 `submitted/full/partial` 동반 회복이 있는지 다시 닫아야 한다 |
| `2026-04-29 10:08 KST` | `latency_signal_quality_quote_composite` 조기 replacement 가능성을 검토했지만 same-slot ON은 보류했다 | `10시 전환율 미회복`만으로는 예비축을 열지 않는다. 오늘은 `runtime basis shift day`이고 `ShadowDiff0428 historical` 잔차도 남아 있어, 예비축 승인 입력은 `12:00` VM/baseline 판정 이후에만 다시 연다 |
| `2026-04-29 12:14 KST` | `VM basis shift` 12시 최종창에서 `09:00~12:00` 기준 `budget_pass=9040`, `submitted=6`, `budget_pass_to_submitted_rate=0.0664%`, `latency_state_danger share=90.6%`, `gatekeeper_eval_ms_p95=11096.0ms`, `ws_age/ws_jitter p95=766/1009ms`를 확인했다 | `submitted` 회복은 여전히 부재하고 `submitted_orders<20, baseline<50` 방향성 게이트도 남아 있어, 오늘 entry 해석은 `VM 이후 baseline reset`이 아니라 `infra-only improvement`로 고정된다 |
| `2026-04-29 12:20~12:24 KST` | `latency_signal_quality_quote_composite`는 문서 기준으로 same-day ON 미승인이었고, `follow_through_failure`는 observe-only 스키마 범위를 재확인했다. `signal_quality_quote_composite_candidate_events=11`에 그쳤고, 월간 `follow_through_failure candidate_count=3`라 구현 범위는 `체결 후 30초/1분/3분 가격`, `AI score velocity`, `MFE/MAE`, `호가/직전 거래량`, `시장/섹터 동조성`, 저장 우선순위 `post_sell + snapshot`로 유지했다 | `follow-through`는 live 후보가 아니라 observe-only backtrace 구현축으로 계속 분리된다 |
| `2026-04-29 12:21 KST` | 사용자가 `BUY 신호 대비 submitted 급감`, `보유청산 튜닝 표본 고갈`, `진입병목 형상 유지 불허`를 명시해 `latency_signal_quality_quote_composite`를 운영 override로 ON 했다. `latency_quote_fresh_composite`는 이미 OFF라 entry 단계의 same-day replacement는 이 축 1개만 활성화한다. `restart.flag` 소모 후 main PID는 `9267 -> 30566`으로 교체됐다 | 이 결정은 hard baseline 승격이 아니라 EV/거래수 회복 우선의 운영 판단이다. 이후 평가는 기존 h1200과 합치지 않고 post-restart cohort에서 `signal_quality_quote_composite_canary_applied`, `submitted/full/partial`, `COMPLETED + valid profit_rate`, `fallback_regression=0`로 분리한다 |
| `2026-04-29 12:50 KST` | `latency_signal_quality_quote_composite` post-restart `12:21:28~12:45:59` cohort에서 `budget_pass=972`, `submitted=0`, 후보 통과 0건을 확인했다. 사용자가 운영 override 관점에서 현재 진입병목 복합축을 모두 닫고 `mechanical_momentum_latency_relief` ON을 지시해 `latency_signal_quality_quote_composite=False`, `mechanical_momentum_latency_relief=True`로 교체했다. `restart.flag` 소모 후 main PID는 `30566 -> 35539`로 교체됐다 | 새 축은 AI score 50/70 mechanical fallback 상태를 버리지 않고 `latest_strength>=110`, `buy_pressure_10t>=50`, `quote_stale=False`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`로 제한한다. 같은 post-restart 창 counterfactual 후보는 약 91건이며, 평가는 새 restart 이후 cohort로 분리한다 |
| `2026-04-29 13:13 KST` | `mechanical_momentum_latency_relief` same-day 표본에서 `latency_pass` 후 `reference_target_cap`이 현재 `best_bid` 대비 과도하게 낮아 `pre_submit_price_guard_block`과 `order_bundle_failed`가 반복되는 것을 확인했다. `target_buy_price`는 counterfactual cap으로만 남기고, 실주문 `order_price`는 `SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS` 이내일 때만 cap을 적용하도록 hotfix 했다 | guard 완화가 아니라 `실주문가 vs pre-submit guard` 내부충돌 제거다. `삼화전기(009470)` 유형의 저가 제출 반복실패를 끊고, same-day mechanical cohort는 `submitted/full/partial` 기준으로 다시 본다 |

## 참고 문서

- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)
- [2026-04-18-nextweek-validation-axis-table-audited.md](/home/ubuntu/KORStockScan/docs/archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-18-nextweek-validation-axis-table-audited.md)
- [2026-04-20-stage2-todo-checklist.md](./checklists/2026-04-20-stage2-todo-checklist.md)
- [2026-04-21-stage2-todo-checklist.md](./checklists/2026-04-21-stage2-todo-checklist.md)
- [2026-04-22-stage2-todo-checklist.md](./checklists/2026-04-22-stage2-todo-checklist.md)
