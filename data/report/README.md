# Report Directory Operations

작성 기준: `2026-08-20 KST`

`data/report/`는 장중·장후 producer가 생성한 운영, source-quality, attribution,
calibration 산출물을 저장한다. JSON/JSONL이 canonical data이고 Markdown은
운영자가 읽는 요약이다. 파일이나 디렉터리가 존재한다는 사실만으로 현재
producer, consumer 또는 runtime authority가 있다고 판단하지 않는다.

현재 producer/consumer/apply 계약의 source of truth는
[report-based-automation-traceability.md](../../docs/report-based-automation-traceability.md)다.
시간대별 실행과 장애 복구는
[time-based-operations-runbook.md](../../docs/time-based-operations-runbook.md),
현재 active/open 판단은
[Plan Rebase](../../docs/plan-korStockScanPerformanceOptimization.rebase.md)와
당일 Stage2 checklist가 소유한다.

## 데이터와 권한 기준

- clean tuning baseline은 `2026-06-05T00:00:00+09:00 KST`다.
- baseline 이전 report/analytics는 archive/audit evidence 전용이며 EV,
  rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern
  promotion 또는 실거래 품질 승인에 쓰지 않는다.
- `threshold_cycle_preopen_status`와 `threshold_cycle_postclose_status`는
  operational freshness 상태이며 tuning EV report가 아니다.
- report는 기본적으로 판단 근거 또는 handoff다. `runtime_effect=true`와 검증된
  PREOPEN apply lineage가 없는 report가 주문, threshold, provider, bot, cap 또는
  hard-safety를 직접 바꿀 수 없다.
- real, sim, probe, source-only를 분리하고 full/partial fill, 실현손익과
  post-sell counterfactual, KRX/NXT/PREMARKET_KRX_LIKE를 합산하지 않는다.

## 현재 핵심 report 흐름

| 영역 | 대표 산출물 | 운영 목적 |
| --- | --- | --- |
| 운영 상태 | `threshold_cycle_preopen_status`, `threshold_cycle_postclose_status`, `postclose_done_controller` | wrapper 시작·완료·실패, artifact 순서와 controller `DONE` 확인 |
| source quality | `observation_source_quality_audit`, `intraday_ws_freshness_monitor`, BUY/HOLD-EXIT sentinel | 결손 row/window 제외, stale/BBO/venue/provider provenance 분리 |
| lifecycle | `lifecycle_decision_matrix`, entry/holding/scale-in bucket attribution, `rising_missed_intraday_feedback`, `scalping_pyramid_intraday_feedback` | selection부터 exit까지 실제·미진입·반사실 흐름 재구성 |
| AI 품질 | exact payload/control/outcome 및 main AI quality R0~R3 계열 | 호출·입력·판단 품질과 same-payload replay 후보 검증 |
| 위젯 | widget signal/runtime/calibration 및 microstructure attribution | 종목별 독립 owner의 signal, fill, target, terminal 결과 검증 |
| 에피소드 | Samsung/low-price tuning, expanded research, microstructure attribution | exact-date profile, two-leg fill·비용·미청산 custody와 다음 PREOPEN 후보 검증 |
| 자동화 handoff | `threshold_cycle_ev`, `runtime_approval_summary`, `runtime_apply_gap_audit`, `code_improvement_workorder`, `threshold_cycle_postclose_verification` | bounded apply 후보, 차단 사유, 구현 작업, 최종 verify 연결 |

스윙 관련 산출물은 operator OFF가 기본이다. OFF 날짜에는 부재나 stale을 현재
스캘핑 체인의 실패로 세지 않는다. 과거 panic-buying, opening rotation,
previous-limit-up rotation, quote consistency standalone report처럼 제거된 계열은
historical artifact가 남아 있어도 재기동 경로가 아니다.

## Full monitor snapshot

`15:45` full snapshot은 `deploy/run_monitor_snapshot_safe.sh`의 격리 worker가
생성한다. 대용량 JSONL은 memory-bounded streaming 또는 compact projection으로
읽고, manifest에 stage별 completion, duration과 process RSS를 남긴다. timeout,
OOM, lock skip, stale manifest를 성공으로 처리하지 않는다. 반복 장중 freshness
monitor는 append offset을 재사용하며 파일 교체·축소·state 손상 때만 full rebuild한다.

## 새 report 계약

새 producer는 역할에 맞는 package에 두고 최소한 아래 필드를 선언한다.

- `metric_role`
- `decision_authority`
- `window_policy`
- `sample_floor`
- `primary_decision_metric`
- `source_quality_gate`
- `forbidden_uses`

EV는 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct` 또는
`source_quality_adjusted_ev_pct`처럼 계약된 이름을 사용한다. 승률은
`diagnostic_win_rate`, 단순 수익률 합계는 진단값이며 EV를 대신하지 않는다.
consumer가 없거나 후속 판정을 만들지 않는 report-only producer는 기본 OFF 또는
삭제 대상으로 재검토한다.

## 운영 확인

1. target date, schema, `generated_at`, source hash와 source-quality 상태를 확인한다.
2. traceability 문서에서 실제 consumer와 apply authority를 확인한다.
3. PREOPEN 반영은 apply plan, runtime env JSON/env, verify artifact와 실제 PID env가
   모두 일치할 때만 인정한다.
4. POSTCLOSE는 required predecessor와 final verifier가 통과한 뒤 controller가
   `DONE`인지 확인한다.
5. 같은 날짜 report 재생성은 source hash와 lineage diff를 먼저 비교한다.

Markdown이 없는 canonical JSON/JSONL은 정상일 수 있다. raw stream, compact
partition, checkpoint, manifest에 사람이 읽는 Markdown을 일률적으로 추가하지
않고, 운영 판정이 필요한 경우 기존 summary consumer에서 요약한다.
