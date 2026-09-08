# Report Directory Operations

작성 기준: `2026-09-08 KST`

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

상세검토 진행은 [장후작업 목록](../../docs/audit-reports/2026-09-05-postclose-work-inventory.md),
명시적으로 호출된 모니터링·복구·추천 구현은 [장후 지시문](../../docs/postclose-tuning-result-review-task-instructions.md)을 따른다.
문서 현행화는 이 절차의 실행 요청이 아니다. 코드 검토 완료, 자연 산출물, 정책 선택,
PID 소비와 비용 차감 EV를 구분하고, 완료한 #8/#9 등은 새 결함 없이 다시 열지 않는다.

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

최종 요약 계약은 `postclose_summary_sources_v1`이다. tower의
`source_generation_contract`와 마지막 checklist의 `POSTCLOSE_SUMMARY_SOURCES`가
실제 원본 SHA256/date와 일치해야 strict verifier `--require-summary-handoff`로
닫힌다. verifier/controller self hash는 순환 방지를 위해 제외한다.
후행 파일이 늦게 도착하거나 바뀌면 앞선 요약 PASS는 최신성 증거가 아니다.

`threshold_cycle_ev`의 미대사 PnL은 `null`과 `realized_pnl_status`로 표시한다.
`main_scalping_lifecycle_paired`는 검증된 CF route 관찰과 actual ADD/NO_ADD를
분리하며, 과거 손익의 귀속 복원을 신규 수익으로 표시하지 않는다.
AI source-only/metadata terminal과 provider 평가·live promotion은 별도다.
frozen canonical ledger와 이후 native metadata projection/별도 승인 ledger는
원본 path/row/hash로 대사한다. projection은 새 경제성 산출물이 아니며
두 ledger의 중복 항목을 합산하거나 원본 결손 이력을 지우지 않는다.

| 영역 | 대표 산출물 | 운영 목적 |
| --- | --- | --- |
| 운영 상태 | `threshold_cycle_preopen_status`, `threshold_cycle_postclose_status`, `postclose_done_controller` | wrapper 시작·완료·실패, artifact 순서와 controller `DONE` 확인 |
| source quality | `observation_source_quality_audit`, `intraday_ws_freshness_monitor`, BUY/HOLD-EXIT sentinel | 결손 row/window 제외, stale/BBO/venue/provider provenance 분리 |
| lifecycle | raw candidate/submit/fill/terminal lineage, `rising_missed_intraday_feedback`, `scalping_pyramid_intraday_feedback`, dedicated AVG_DOWN/Samsung replay | 실제·미진입·반사실을 분리; ADM/LDM/bucket은 retired라 소비·복구하지 않음 |
| AI 품질 | exact payload/control/outcome, R0~R3, #76→#82 v5→#78 offline optimizer 및 terminal follower consumer | 지속적 prompt/input 개선; #81 legacy live OFF와 별도 KRX entry_setup_live_policy를 구분 |
| 위젯 | widget signal/runtime/calibration 및 microstructure attribution | 종목별 독립 owner의 signal, fill, target, terminal 결과 검증 |
| 에피소드 | Samsung/low-price tuning, expanded research, microstructure attribution | exact-date profile, two-leg fill·비용·미청산 custody와 다음 PREOPEN 후보 검증 |
| 자동화 handoff | `threshold_cycle_ev`, `runtime_approval_summary`, `runtime_apply_gap_audit`, `code_improvement_workorder`, `threshold_cycle_postclose_verification` | bounded apply 후보, 차단 사유, 구현 작업, 최종 verify 연결 |

스윙 관련 산출물은 operator OFF가 기본이다. OFF 날짜에는 부재나 stale을 현재
스캘핑 체인의 실패로 세지 않는다. 과거 panic-buying, opening rotation,
previous-limit-up rotation, quote consistency standalone report처럼 제거된 계열은
historical artifact가 남아 있어도 재기동 경로가 아니다.
전용 institutional aggregate와 ADM/LDM·greenfield도 retired다. 비-LDM scalp-sim
control tower/prior는 별도 surviving source-only owner이며 sim 성과 튜닝은 현재 우선순위가 아니다.
#11 source-quality 감사가 예약 stage 전 아직 없으면 `not_yet_due`다. 수동 재생성은
자연 증거가 아니며, 실제 결손의 row/window 격리와 소비자별 tuning 차단을 구분한다.

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
