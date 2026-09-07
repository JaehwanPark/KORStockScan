# 2026-09-07 11:20 장중 모니터링·source-only 보완

관측 종료: 2026-09-07 11:20 KST. Pipeline/AI 집계는 `10:58:55 <= event time < 11:20:00`이며 종료 대사는 11:20:13, 읽기 전용 census 재계산은 11:20:29다. Census는 재계산 당시 존재한 capture를 사용하므로 11:20 이전의 고정 snapshot이라고 주장하지 않는다. 정규 report alias는 덮어쓰지 않았다.

판정: 메인 submit drought가 지속되고 scanner recall은 `insufficient_evidence_scanner_recall`이다. 독립 machine custody는 유지됐다. 두 source-only 코드 결함을 보완하고 재리뷰했지만 새 AI lineage 코드의 현재 PID 반영과 전체 경제성 acceptance는 OPEN이다. 이번 작업에서 봇 재기동·주문·가격·수량·threshold·provider·hard safety 변경은 하지 않았다.

## 1. 현재 실행과 독립 주문 owner

- 현재 main PID `195755`, 시작 10:58:55, 실행 코드 `cc86f4da`, startup source_dirty=false. 저장소 HEAD `314ca993`은 앞선 문서 commit이며 이번 AI 수정은 메모리의 실행 코드에 반영되지 않았다. launcher 파일은 기존 검증 hash와 동일하다.
- 종료 verifier: status=pass, pid_passed=True, PID mismatch/missing=0/0, runtime/dated policy fail=0/0. 당일 선택 22 family; 적용 자체와 자연 효과를 구분한다. 퇴역 canonical 15개 OFF 확인은 시작 검증과 같은 PID/env에 결속한다.
- 11:08:07 → 11:19:38 → 11:20:13 KRX/NXT 전체 inventory와 미체결 대사에서 종목·수량·주문번호 불변. 잔고 조회의 성공 venue 두 개와 미체결 normalization contract를 검증했다. 순이익·매수가 필드는 이 helper 출력에 없으므로 추정하지 않았다.

| Owner | 보유·목표 주문 | 판정·다음 액션 |
|---|---|---|
| 메인 | 이번 구간 신규 submit/fill/holding/exit receipt 없음 | probe/residual/scale-in/부분익절/post-sell 효과 검증할 실체결 표본 없음. 아래 drought owner로 원인 추적 |
| 위젯 Samsung | 005930 20주, SELL `0021509` 20주 | open episode와 target custody 유지; completed EV에 포함하지 않음 |
| 별도 삼성 custody | 나머지 005930 20주, SELL `0003725` | 기존 미확정 manual/legacy 귀속. 앞선 1항 제외 유지, 임의 widget/main 귀속 금지 |
| Hanwha episode | 042660 BUY `0026963/0026964`, 10주씩; SELL `0027015/0027165`, 각10주 | 두 leg TARGET_OPEN, 목표 미체결; 청산·수량 확대 없음 |
| Samsung Heavy episode | 010140 BUY `0028473` 10주, SELL `0028708`; 다른 leg `0028474` NO_FILL | 10주 custody 유지, 미체결 leg를 filled/complete로 보간하지 않음 |

- 주문가능금액 helper: `raw_amount=0`, `effective_amount=3,000,000`, `minimum_floor_applied=true`, authority=`operator_approved_2026_07_22`, rollback=0. 300만 원을 실제 broker 현금으로 보고하지 않으며 기존 승인된 보정 계약은 변경하지 않았다.
- 확인한 당일 episode state 25개는 NO_TRADE 23/TARGET_OPEN 2. Samsung 오전은 service inactive/exit0의 정상 종료 근거를 분리했고 정오·오후는 `not_yet_due`. 모든 50개 profile의 미래 기동 성공을 주장하지 않는다. Widget PID 9704, 두 TARGET_OPEN episode PID 130886/142084를 확인했다.

## 2. 독립 rising benchmark와 downstream conversion

기준은 `liquid_common/top20/forward_exact`, stable symbol×venue×session×episode, validity 300초, scanner detection SLA 120초다. 공식 master artifact는 `data/report/micro_reversion_economic_reference/micro_reversion_symbol_master_2026-09-04.json`, artifact SHA `b2e77f68a9dac866b05afbd4049b8e67302444d53799d484532cd4cd9cd75dbc`, 확인된 master 2,551행이다. 이름에 common이 있다는 이유로 master 통과를 대체하지 않는다. Missing code는 주식/ETF 여부를 추정하지 않고 제외 근거 결손으로 남긴다.

- 종료 재계산 source snapshot 140개: valid 94, unavailable 46, invalid contract 0. 앞선 11:05까지 unavailable 41개는 모두 shared-read-budget defer였고, 끊긴 과거 cadence는 기다려도 복구되지 않는다.
- KRX primary 분모 104 episode: source/candidate pool 98(94.23%), watch 22(21.15%), promotion 22 중 SLA 내14(13.46%), attach18, fast/heavy20(19.23%), exact AI trace/provider0, authority11, submit safety/submit0. Fast/heavy는 300초 validity 기준이며 promotion의 120초 SLA 성공률과 같은 지표로 비교하지 않는다. `candidate_recall_pct` 역시 현재 producer의 candidate-pool 단계이며 최종 BUY candidate 성공률이 아니다.
- 최초 미도달의 배타적 합은 104, delta0: candidate_not_promoted75(일반slot15/reserved31/신규limit2/cooldown27), tracegap5, authorityblock1, late8, post-authority submit-safetygap6, sourceunseen6, fastgap2, sourceguard1. 현재 report taxonomy를 기록했으며 모든 미도달을 전략 결함으로 단정하지 않는다.
- Benchmark→source p50/p95 112.23/275.76초, promotion111.65/271.67초, fast128.17/273.30초, heavy155.90/279.01초. Promotion→fast17.24/151.50초, →heavy27.63/159.60초. AI causal latency는 exact join0으로 산출 불가.
- Post-promotion consumption은 별도 분모다: 같은 PID 관측 구간 promotion ID68, attach ID68(75events), fast58 IDs(798events), heavy55 IDs(288events). 이는 외부 benchmark 104의 recall 분자와 합산하지 않는다. 전체 소스의 여러 promotion wave와 수신 반복을 분리한다.
- Downstream 관측: budget_pass30events/13record IDs, ai_confirmed22/15, latencyblock17/10, authorityguardblock5/3, zero_qty4/4, submitted0. 서로 다른 eligible 분모이며 일렬 funnel로 빼기 계산하지 않는다. BUY Funnel 5축 exact-attempt 결함은 별도 기존 `BuyFunnelSubmitDroughtExactAttemptRepair0907`가 소유한다.

| Venue/session | Episode | BBO | Resolved | Right-censored | 제한된 관측 cohort EV | 판정 |
|---|---:|---:|---:|---:|---:|---|
| KRX / KRX_REGULAR | 104 | 78 (75.0%) | 37 | 31.48% | -0.74571792% | economic floor 미충족 |
| NXT / NXT_PREMARKET | 43 | 42 (97.67%) | 20 | 51.22% | -0.15223401% | economic floor 미충족 |
| NXT / NXT_REGULAR_OVERLAP | 106 | 78 (73.58%) | 52 | 31.58% | 0.21443713% | economic floor 미충족 |

위 EV는 bounded executable ask→bid·고정 비교비용 23bps를 적용한 관측 cohort 진단이다. 전체 상승 모집단 EV, 실제 체결 또는 실제 순이익이 아니며 authoritative `source_quality_adjusted_ev_pct=null`, 외삽 금지다. 1주 표시잔량의 fill feasibility를 대규모 체결 가능성으로 확장하지 않는다. KRX 65 executable rows는 adverse19/target13/timeout5/pending11/right-censored17로 보존된다. 독립 source/master/cadence/BBO gate가 미완료여서 `scanner_under_discovery_confirmed`나 정상 coverage를 주장하지 않는다.

## 3. Scanner-pruned bounded observer와 공통 조회

- 같은 PID 구간 full prune 2144events, schedule receipts 1728: 신규8/재사용9/capacity rejection1711. 선택8episode의 observation80: captured34/source-quality-gap46. Rejected schedule ID를 admitted episode 분모로 세지 않는다.
- 마지막 schedule receipt는 active8, pending7, process 일일 scheduled80/1200, worker alive/error0/emit failure0. 마지막 schedule의 captured31/gap41은 이후 observation 34/46과 시간축이 달라 혼합하지 않는다. 설정 active8/pending80/day1200/간격0.25초 유지.
- source-only 조회는 token-wide domestic read5/sec 중4slot 제한, runtime_required/execution_critical 한slot 예약이다. 현재 공유 ledger에서 max5/source_only4와 runtime_required PID195755 ka10004 admission을 확인했다. 주문 bucket/모의 token+origin+api-id 분리는 계약이며 이번 snapshot만으로 모든 caller의 부하 시험을 통과했다고 주장하지 않는다.
- Rate-limit 감지 후 정상 복구 warning과 exhausted failure, local budget defer를 구분한다. Exact response route/BBO invalid는 captured로 보간하지 않는다. Prune observer resolved20/coverage95%/right-censor20% floor는 이 실행에서 별도 경제 report로 닫지 못해 `blocked_missing_evidence`; 전체 prune EV 외삽 금지.

## 4. AI·micro·smoothing·limit-down

- 현재 PID 자연 AI trace 31건: input-source-timing 31/31, parse18, preflight 미호출12, transport timeout1. Provider 호출19/미호출12. 앞선 source timing/parse 보완의 자연 소비는 확인됐다.
- 실제 route: entry_price Bedrock Qwen3 32B 9건, analyze_target OpenAI gpt-5.4-nano 9건, scalping_entry OpenAI 1건. Preflight의 provider=None은 호출 전 차단이며 route 장애로 세지 않는다. Holding_flow 신규 자연 호출은 이 구간 효과 분모가 아니다.
- 11:02:57 request `analyze_target:387690:1788746572094:36eb542c`는 응답5026ms/provider4963ms, deadline_exceeded/attempt1; parse 실패로 오분류하지 않았다. 지연·가격·전략 threshold 변경 근거로 사용하지 않는다.
- record_id 없는 entry_screen preflight12/live1의 caller identity 전달 결함을 trace-only whitelist로 수정했다. 유효한 기존 caller ID만 복사하며 과거 missing ID를 code/time join으로 복구하지 않는다. 현재 PID는 미반영이다. 외부 census exact trace0은 자연 provider 호출 부재와 동의어가 아니다.
- R0 source는 축적되지만 exact payload→action-neutral mature→lifecycle terminal→effective cost/master→net-economic funnel의 최종 유효 분모는 이번 실행에서 확정하지 못했다. R1/R2 정규 장후 해석과 R3 source-only manifest는 해당 producer/floor owner가 소유한다. Provider replay·새 prompt 적용·R3 성공은 수행/주장하지 않았다. 현재 request 크기나 parse 성공으로 EV 표본을 대체하지 않는다.
- Micro 11:20:10 snapshot: canary stop=false, 0B65,850/0D64,079; callback p95/p99 각각0.126659/0.850927ms, 0.136261/0.612602ms. Trade/depth writer3/3alive, queue drop/error0, free minimum12,030,812,160bytes로5GiB/1GiB watermark 위다.
- **Source-quality 미해결:** stale 0B timestamp33,171/65,850(50.373576%), depth timestamp rejection21,433. 정상 canary status는 입력 품질 정상 판정이 아니다. 현재 rejection은 timestamp guard가 차단하며 제외행을 0EV/유효 BBO로 보간하지 않는다. 기존 142 regression/69 quarantine 등 이전 PID 결손은 PID counter reset으로 사라진 것으로 세지 않는다.
- 11:12:16 invalid-opcode WS REG 오류6건 뒤 11:12:19 재연결, 11:12:21 재등록 및 새 sequence epoch의 수신·writer 진행 확인. 오류 burst만으로 재기동하지 않았다. Timestamp 차단 급증의 외부 송신/로컬 receive/queue 최초 원인과 새 epoch별 stale 분포는 미확정으로 후속 workorder에 남긴다. Epoch 간 0B/0D join 금지.
- Risky micro source-candidate20events/11record IDs와 BBO331events/8IDs는 별도 source-only 계측이다. Passive fill/ask depletion/refill/trade backing/target-adverse·tail-loss exact economic census를 완료하지 못했으므로 유리한 micro entry나 주문 권한을 주장하지 않는다.
- Limit-down manager source-loaded1, 11:18:41 heartbeat, natural candidate/slot0, active live policy empty. `healthy_no_natural_sample`이며 전일 ordered0B+0D acceptance는 resolved 아님.
- holding_flow smoothing은 당일 guarded ON 계약을 유지하나 real holding/exit paired 표본이 없어 whipsaw 감소·매도 지연·순이익 효과 미확정. soft_stop_whipsaw는 OFF/source-only다.

## 5. Process와 수정·리뷰

Expected owner는 runbook/traceability와 설치된 trigger, 당일 policy를 기준으로 읽었다. Main195755의 종료 heartbeat main11:20:12/sniper11:20:11/scanner11:18:41, widget와 TARGET_OPEN 두 machine의 progress를 확인했다. Samsung 오전 정상 종료와 정오/오후 미도래를 dead로 분류하지 않는다. Crisis thread alive이지만 last marker10:59:11만으로 모든 기능의 진행 정상까지 증명하지 않는다. 모든 systemd timer/cgroup/consumer 전수 완료 주장은 하지 않으며 미검증 future profile은 not_yet_due/blocked_missing_evidence다.

Census capture는 5분 trigger에서 계속 생성된다. Canonical report는 09:15/12:00/15:15/19:45 schedule이므로 09:15 alias를 임의 stale incident로 처리하지 않았다. 이번 read-only report는 operator 감사용 last consumer이며 다음 PREOPEN 효과가 아니다. 퇴역 ADM/LDM/greenfield/institutional/latency 추천 및 Swing은 `not_applicable_retired_or_deprioritized`; canonical OFF 확인 외 성과·shortage/ETA를 만들지 않았다. Sim source event는 real submit에 포함하지 않는다. 관측한 process에서 sim의 실주문 누출 증거는 없으나 모든 broker caller의 resource 전수 감사 완료를 주장하지 않는다.

| 보완 | 재현·검증 | 현재 반영·rollback |
|---|---|---|
| Census wrapper가 tee 실패를 exit0으로 숨김 | producer 실패는 기존에도 nonzero. tee만 실패할 때 false success를 재현 후 pipefail 전체 상태 보존. capture/report/log 각 실패 및 정상5회귀 통과 | 11:10 자연 capture DONE. 기존 crontab5줄 불변 검증 후 installer의 receipt 생성 경로로 wrapper hash 갱신. 되돌릴 때 wrapper와 receipt를 함께 복원하고 exact trigger verifier 재확인 |
| AI early preflight/cache caller identity 누락 | current caller record222가 cache donor111보다 우선하며 provider 미호출/action 보존 테스트 | code-only, PID195755 미반영. 다음 별도 허용 restart 때 natural trace acceptance. rollback은 trace whitelist 보완 revert, live authority 변경 없음 |

Wrapper SHA `3007a252254ae8a51d2fbea295b1ba96dce6be3fcddb7920896322e8dd34147c`, refreshed trigger artifact SHA `9f5b1ead5f2d667738205353490c3dfb5db6bf3a6f1dc1e96f5d5389a366a322`, installed lines SHA `7cce2bb8de1c895221b0f9f43814c5fda3d2444dcb8cd06b8848588dbfe4ed7f`.

Review→fix→re-review로 위 두 변경 범위 unresolved finding0. Targeted suite 417 PASS(transport/trace/snapshot/census/wrappers), bash syntax·Python compile·diff check PASS. Ruff는 AI 파일의 기존26건과 동일하고 새 경고0; 전체 lint clean이라고 주장하지 않는다. 문서/checklist parser(`--print-backlog-only --limit 500`) exit0 및 최종 diff check PASS. 동시 작업의 BUY Funnel review/inventory/traceability 및 Sentinel·conversion/workorder/verifier 코드 변경은 보존했다. 이 보고서의 finding0/417 PASS는 위 두 보완의 검증 시점과 범위에 한정되며 다른 작업의 이후 diff까지 승인하지 않는다.

## 6. 부족 ledger와 다음 acceptance

| Stable shortage_id | required/current/deficit와 최초 결손 | 판정·ETA | 다음 owner / acceptance |
|---|---|---|---|
| scanner_recall_krx_20260907 | BBO95%/75%/20%p, resolved20/37/0, censor≤20%/31.48%/11.48%p 초과; capture cadence/master 결손 선행 | affected cadence window는 structural_population_exhaustion; 전체 recall blocked_missing_evidence. 지난 source 공백은 시간으로 복원 불가 | Intraday2to5SourceAcceptance0907, 12:00 정규 report의 master/SLA/venue별 분모와 다음 valid capture 연속성; slot/threshold 변경 금지 |
| main_krx_submit_20260907 | submit0; exact 5축 denominator 미폐쇄, 필요한 floor 자체를 이번 실행에서 확정 못함 | blocked_missing_evidence, finite ETA 없음. upstream event 다수로 시간해결형 판단 금지 | BuyFunnelSubmitDroughtExactAttemptRepair0907; core5축 exact record/순서/verifier 회귀 후 corrected natural attempt |
| ai_trace_record_lineage_20260907 | eligible trace31 중 identity missing13; caller trace 전달이 최초 결손. 허용 missing0/현재13 | structural_population_exhaustion, 코드 보완/PID 미반영. ETA 없음 | Intraday1120SourceAcceptance0907; 별도 허용된 다음 PID에서 caller ID 있는 preflight/cache/live exact receipt, missingcaller는 gap 유지 |
| main_ai_net_economic_20260907 | exact source→mature→terminal→cost/master→economic 전수 count/floor 미확정 | blocked_missing_evidence; R1/R2/R3 일일 장후 예정과 structural join 결손 구분 | 기존 Main AI source-gap와 Intraday2to5SourceAcceptance0907; local label raw-row exclusion 및 common-parent/terminal/effective hash 검증 |
| micro_timestamp_source_20260907 | timestamp valid0B 32,679/65,850; rejected33,171, depth rejected21,433; exact admissible clock window 원인 미결 | blocked_missing_evidence, finite ETA 없음; healthy process를 source-quality pass로 대체 금지 | Intraday1120SourceAcceptance0907; 새 epoch·symbol·route별 raw exchange/receive/queue 분포와 rejected row/consumer exclusion 보존 |
| scanner_prune_bbo_krx_20260907 | 8selected/80observations 중 captured34; episode coverage/resolved/right-censor 유효 분모는 미산출 | blocked_missing_evidence; 단순 34/80을 episode coverage로 대체 금지 | Intraday1120SourceAcceptance0907; bounded cohort official master·exact BBO·maturity로20/95%/20% floor 산출 |

현재 profile의 HELD/TARGET_OPEN은 종료일 확정이 없어 ETA 산정에 넣지 않는다. 삼성 잔여20주 custody는 기존 Intraday1020Followup0907 미확정 owner로 유지하며 이번 보완 범위를 확대하지 않는다. 이 기록과 next due는 추가 restart/주문/Provider replay 권한이 아니다.

## 7. 재현 evidence

Local evidence: `tmp/intraday1120_broker_start.json`, `tmp/intraday1120_broker_end.json`, `tmp/intraday1120_start_verify.txt`, `tmp/intraday1120_end_verify.json`, `tmp/intraday1120_census_readonly.json`, `tmp/intraday1120_census_end.json`, `tmp/intraday1120_pipeline_end.json`, `tmp/intraday1120_ai_end.json`, `tmp/intraday1120_end_micro.json`, `tmp/intraday1120_end_limit_down.json`, `tmp/intraday1120_end_heartbeat.json`, `tmp/intraday1120_episode_states.json`, `tmp/intraday1120_trigger_before.json`, `tmp/intraday1120_trigger_after.json`.

Pipeline captured prefix SHA `db418a02cc886bf251284e73fd64bea10fc466a080b092aaaccd237822c41fc5`, bytes=976658410; census read-only report SHA `2e4d9fe8d0ed398f2864644ea0c8731035770ba53aeae1f67548c57cce6b9516`. 원천은 당일 pipeline/AI trace/census JSONL과 owner state이며, 실행 시각 이후 변화와 이 snapshot을 분리한다.
