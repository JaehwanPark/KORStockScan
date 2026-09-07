# 2026-09-07 장중 source 결함 보완·재리뷰

판정: 11:20 모니터링에서 드러난 source-only 결함을 수정하고 생산→snapshot→Main AI 소비 및 scanner 집계 경로를 재리뷰했다. 이번 변경 범위의 미해결 코드 finding은 0건이고 관련 655개 테스트가 통과했다. 현재 PID 적용, 실제 timestamp 지연의 원인 확정, scanner BBO/master/cadence와 경제성 floor는 별도 acceptance다. 주문 owner·가격·수량·threshold·provider route·stale/하드 가드 및 봇 상태를 변경하지 않았다.

## 1. 확인한 결함과 보완

| 결함 | 수정 | 재리뷰·수용 조건 |
|---|---|---|
| Micro timestamp reject는 누적 count만 남아 원천 시각/수신 경로를 재구성할 수 없음 | 기존 forward collector에 최근 64개 rejection tail과 누적 index를 추가. PID, symbol, item, venue, 검증 가능한 session, local observer epoch, raw numeric time, receive/check/parsed exchange 시각과 지연을 기록 | callback에서 I/O·JSON encoding·무제한 종목 map 없음. 72개 rejection에서 마지막64개만 유지하고 KRX/NXT·0B/0D·epoch 경계를 보존. 마지막64개로 전체 제외행 복구나 경제성 표본을 주장하지 않음 |
| Timestamp 차단이 많아도 canary가 source-quality 정상으로 전달됨 | pre-enqueue timestamp counter를 source-quality census에 포함. 양수 및 missing/invalid counter는 source exclusion 필요로 표시 | collector `stop_required`는 변경하지 않음. 기존 callback latency, writer/queue, authority stop 가드는 유지. bool·음수·소수·Infinity·missing을 0으로 보간하지 않음 |
| 이전 canary writer가 기록한 healthy label을 Main AI consumer가 그대로 신뢰함 | 동일 hash의 collector snapshot에서 timestamp counter를 다시 검증 | 11:20 당시 healthy artifact도 `row_exclusion_required`. Provider replay/R3 hold는 유지하되 독립 검증된 local action-neutral label과 Provider-floor census 생성은 계속 가능. 날짜 전체 raw data 폐기 아님 |
| Scanner fast/heavy 등 recall이 SLA 밖 발견까지 성공으로 포함 | `stage_counts/stage_rates_pct`는 전체 validity 내 관측값으로 보존하고 `stage_recall_counts/recall_metric_contract`를 별도 출력. upstream source/pool/watch는120초 이내, downstream은 SLA 내 발견 후 동일 lineage의300초 validity 내 소비만 recall로 집계 | primary provider reach와 promotion의 기존 SLA 기준 유지. Candidate metric이 scanner candidate pool이며 최종 BUY candidate가 아님을 명시. Retrospective 결과는 non-causal diagnostic으로 명시 |
| 재리뷰에서 missing receive time이 epoch0으로 계산돼 거대한 지연값으로 표시될 수 있음 | 진단 입력의 nonpositive receive sentinel을 null로 처리 | 실제 timestamp guard의 반환값은 그대로 INVALID. exchange→receive와 receive→check 지연도 null. 결측을 정상/0ms로 보간하지 않음 |

수정 owner는 기존 `src/engine/scalping/micro_reversion/{forward_collector,canary_monitor,ai_quality_cycle}.py`와 `src/engine/monitoring/market_opportunity_census.py`다. 새 engine root module·새 주문 owner·새 collection trigger는 만들지 않았다. AI caller ID/tee failure 보완은 앞선 변경을 보존하고 이번 통합 회귀에 포함했다. 동시에 수정되는 BUY Funnel Sentinel/conversion/workorder/postclose verifier 경로는 별도 작업이므로 이 리뷰의 finding0을 그 변경 전체에 확장하지 않는다.

## 2. 동일 원천 replay

원천: [11:20 보고서](./2026-09-07-intraday-1120-monitoring.md)의 고정 local snapshot을 재사용했다. 현재 live 파일을 덮어쓰거나 broker/Provider를 호출하지 않았다.

- Micro 0B timestamp 차단33,171, depth timestamp 차단21,433이 `source_quality_row_exclusions`와 Main AI `row_exclusion_required`에 전달된다. Stale 0B33,171은 invalid0B33,171의 부분집합이므로 두 count를 더해 별도 손실로 집계하지 않는다. `exact_rejected_row_exclusion_proven=false`: 원천 차단 원인을 표시한 것이고 완전한 제외행 ledger가 복구된 것은 아니다.
- Source-only stage gate: `observer_blocks_action_neutral_label_generation=false`, `observer_blocks_provider_floor_materialization=false`, `observer_blocks_provider_replay=true`, `observer_blocks_r3_promotion=true`. Provider route나 실거래 판단 guard는 바뀌지 않는다.
- 동일 KRX104개 opportunity episode의 scanner 수치는 아래와 같다. 이것은 통계 계약 수정이며 탐색·순이익 개선 효과가 아니다.

| Metric | 수정 전 | 수정 후 |
|---|---:|---:|
| source_seen_recall_pct | 94.23% | 61.54% |
| candidate_recall_pct (scanner pool) | 94.23% | 61.54% |
| watch_admission_recall_pct | 21.15% | 13.46% |
| promotion_recall_pct | 13.46% | 13.46% |
| fast_precheck_recall_pct | 19.23% | 11.54% |
| heavy_eval_recall_pct | 19.23% | 11.54% |
| entry_ai_provider_reach_rate_pct | 0% | 0% |

관측 event·episode 분모104·BBO·economic outcome·비용은 변경하지 않았다. Primary scanner 상태는 여전히 `insufficient_evidence_scanner_recall`이며 master/cadence/BBO 결손과 실제 submit drought를 threshold 변경으로 해소하지 않는다.

## 3. Prune report와 남은 표본

`intraday_ws_freshness_monitor`의 기존 소비 경로 `scanner_unique_funnel.economic_cohorts.executable_bbo_attribution.prune_observer_selected_venue_session_economics`를 확인했다. 11:35:10 정규 report의 전일/전체 분모가 아니라 당일 누적 selected cohort 집계이며, 앞선 PID 구간8episode/80observation과 다른 window다.

| KRX_REGULAR cohort | Master eligible | Exact BBO joined | Coverage | Resolved (floor20) | Right-censor (max20%) |
|---|---:|---:|---:|---:|---:|
| general_slot_limit | 20 | 5 | 25% | 2 (18 부족) | 60% |
| market_gainer_reserved_full | 27 | 8 | 29.6296% | 5 (15 부족) | 37.5% |
| non_gainer_not_rising_repeat | 13 | 5 | 38.4615% | 5 (15 부족) | 0% |

모두 BBO95% floor 미달이며 EV=null이다. PREMARKET_KRX_LIKE16개는 별도 cohort로 보존하고 KRX 분모에 합치지 않는다. Consumer가 없어서 생긴 구조적 고갈로 오판하지 않으며 현재 유효 BBO 부족은 원천 gap으로 남긴다. 과거 missing BBO를 재조회 현재가로 채우거나 34/80 observation 비율을 episode coverage로 대체하지 않는다. 시간해결형 ETA는 검증된 동일 denominator 유입 근거가 없어 산출하지 않는다. 이 결과의 next owner는 기존 `Intraday1120SourceAcceptance0907`다.

## 4. 검증과 반복리뷰

- 새 canary/consumer 검증의 초기 실패는 기존 healthy test fixture의 timestamp counter 결손을 드러냈다. 유효 fixture에는 explicit0을 추가하고 별도 missing/invalid 회귀에서는 fail-closed source-quality를 검증했다. 과거 실제 artifact의 missing을 0으로 수정하지 않았다.
- Canary→Main AI consumer 재리뷰에서 invalid exclusion container가 예외를 만들지 않도록 정규화했고, missing receive epoch0 진단을 수정한 뒤 회귀를 추가했다.
- 테스트: census, micro forward collector, canary monitor, AI quality cycle, OpenAI transport, AI trace, AI snapshot, threshold wrappers **655 PASS**. 전체 저장소/동시 작업의 미검증 diff까지 통과했다고 주장하지 않는다.
- 변경한 8개 Python 파일 Ruff PASS, production module compile PASS, diff check PASS. Checklist parser(`--print-backlog-only --limit 500`) PASS.
- 표준 synthetic valid0B 5,000×5 preflight: internal p95 최대0.026488ms/p99 최대0.045926ms, queue drop0/worker error0. 별도 rejection5,000회는 retained64, enqueue0, p95 0.010737ms/p99 0.016138ms였다. Synthetic 과거 입력의 절대 receive→check 지연은 성과/신선도 판단에 사용하지 않는다.
- [preflight·고정 원천 replay](./2026-09-07-micro-timestamp-source-repair-preflight.json.txt)를 보존했다. 기존 frozen latency 기준1ms/2ms와 원래 측정값/측정일은 그대로 유지하고, 기존 baseline artifact의 source_provenance_updates에 코드 hash와 새 검증 근거만 추가했다. 원래 측정 수치의 텍스트도 보존했다.

## 5. 공식 API 근거와 권한

Upstream [Kiwoom-REST-API commit234560d](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/234560d213acd8871ae344b5481aecd2f30287fa)을 2026-09-07T11:32:23+09:00에 재확인했다. Inspected: `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`, `kiwoom/realtime/decoders.py`, `kiwoom/realtime/packets.py`. 현재 upstream에는 `kiwoom_docs` directory가 없으므로 존재하지 않는 문서의 의미를 추정하지 않았다. 0B FID20 체결시간, 0D FID21 호가시간의 HHmmss와 REAL item/type envelope를 확인했다. Local normalized timestamp 입력을 관측할 뿐 FID·REG/REMOVE·재접속·endpoint·인증·주문 protocol은 수정하지 않았다. Upstream SDK는 missing keyring으로 import하지 못해 packaged JSON/spec source를 직접 읽었으며 패키지를 설치하지 않았다.

## 6. Runtime 반영·rollback·후속

현재 PID195755는 앞선 실행 코드cc86f4da를 사용한다. 이번 collector/canary/AI trace 계측은 코드 보완 상태이며 fresh PID natural receipt 미확인이다. Source-only report/AI quality cycle은 다음 정상 producer 실행 시 새 코드를 읽을 수 있으나 그 소비 전 runtime/경제 효과를 선행 주장하지 않는다. 이번 작업에서 bot restart·live apply·report alias 강제 재생성·Provider replay를 수행하지 않았다.

- `micro_timestamp_source_20260907`: 새로 명시된 source-quality gap과 64개 tail은 진단 보완 완료다. 실제 외부 송신/로컬 수신 지연 원인은 향후 허용된 PID에서 fresh rejection sample이 있어야 확정할 수 있다. `collecting_after_structural_repair`/resolved로 아직 바꾸지 않는다.
- `scanner_recall_krx_20260907`: 지표 SLA 혼입 보완 완료. 다음 정규 report가 새 `stage_recall_counts/recall_metric_contract`를 실제 소비하는지와 source/master/cadence/BBO gate를 기존 acceptance에서 확인한다.
- `scanner_prune_bbo_krx_20260907`: 기존 report consumer 확인. selected cohort별 source gap/floor는 OPEN이며 census source quota나 observer request cap을 높이지 않는다.
- `ai_trace_record_lineage_20260907`: 이전 trace-only 보완을 회귀 검증했으나 현재 PID 미반영. 추가 재기동 권한은 이 구현 완료에서 발생하지 않는다.

Rollback은 이 source-only 수정과 그에 대응하는 code-hash provenance를 함께 복원하고 테스트/파서를 다시 검증한다. Timestamp stale 기준·latency auto-stop 한도·broker guards를 낮추는 rollback은 없다. 다음 실행은 `Intraday1120SourceAcceptance0907` 및 `Intraday2to5SourceAcceptance0907`, BUY Funnel core5축은 별도 `BuyFunnelSubmitDroughtExactAttemptRepair0907`에 귀속된다.
