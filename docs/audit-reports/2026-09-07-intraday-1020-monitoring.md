# 2026-09-07 10:20 장중 모니터링·보완

관측 시작 10:11 KST. 사용자 지정 종료 10:20 KST; 종료 이후 문서·리뷰 검증을 마감했다. 이 문서는 operator audit이며 자동 튜닝 입력이나 runtime apply artifact가 아니다. clean baseline은 2026-06-05 00:00 KST. 보고서별 as-of를 보존하고 일중 전체 성과로 외삽하지 않는다. 원천 digest 및 상세 표본은 `tmp/intraday_20260907_1020_evidence.json`, 읽기 전용 broker snapshot은 `tmp/intraday_20260907_1020_broker.json`에 보존했다.

## 판정

메인 실거래의 제출 부족은 확인됐지만 놓친 순수익이나 scanner 정상 포착률은 입증되지 않았다. `SUBMIT_DROUGHT_CRITICAL`과 `insufficient_evidence_scanner_recall`을 분리한다. 위젯·독립 episode 보유는 완료 EV가 아닌 open custody다. Sentinel→workorder에 남은 퇴역 LDM 의존을 보완했다. 실주문·threshold·provider·수량·bot 재기동은 수행하지 않았다.

## 현재 PID·적용 계약

- 메인 PID 46656, 시작 08:40:22, 실행 commit `327e872294b2a82b5ed99d99bf3595c23f48338f`, PID source-dirty=false. launcher SHA `648b3cd86264d72d46b9c7ee8e8d175072a3f646ebe70425f73afc95b919cf1b`.
- 당일 `threshold_runtime_env_verify_2026-09-07.json`: pass, PID 46656, mismatch/missing 0/0, runtime policy fail 0. 현재 `/proc`의 retirement_env canonical 15개는 모두 false와 일치한다. 이는 적용 계약 확인이며 family별 효과 판정은 아니다.
- selection은 당일 verify의 22개 family가 소유한다. recheck v4와 split hold_sample을 수동 적용하지 않았다. 이번 수정은 Sentinel/workorder producer용으로 메인 프로세스 동작을 변경하지 않는다.
- 기존 사용자 수정 `docs/intraday-monitoring-task-instructions.md`와 cache/generated artifact는 보존했다. Plan Rebase §1의 retirement override가 §5~7 잔존 historical LDM 설명보다 우선한다. baseline 문서는 수정하지 않았다.

## 메인 봇·AI

- 10:20:03 정규 Sentinel KRX 세션: `ai_confirmed` unique 37, budget 24, latency pass 9, submitted 0, holding_started 0. 이 각각은 단계별 진단 분모이며 동일 exact AI trace를 공유하는 하나의 인과 funnel로 단순 나누지 않는다.
- 10:10 상세 근거: latency DANGER 43 event/21 unique, micro spread 43, spread/slippage reason 41, stale reason 2. reason 중첩을 합산하지 않는다. quote refresh 22회 적용 후 latency pass 회복 8건이나 제출 0건; 회복 후 7건은 최종 Entry AI authority 재검증, 1건은 budget 이후 submit 미관측이다.
- Entry authority 8건: fresh DROP veto 4, stale/untrusted 2, WAIT observation-only veto 2. 차단이 존재한다는 사실만으로 모두 경제적으로 최적이라고 판정하지 않는다. hard-negative 해제·spread cap 완화 근거는 없다.
- 10:16 부근 exact AI trace census: entry_price Bedrock 27회 모두 parse_ok; OpenAI analyze_target 13회 중 parse_ok 11/HTTP timeout 2, scalping_entry OpenAI 5회 parse_ok, holding_score OpenAI 2회 parse_ok. **후속 raw 재검증 정정:** 최초 기재한 `parse 실패 2`는 parse_ok=false를 잘못 해석한 것으로, 두 건 모두 response ID 없는 queueing wall-clock timeout이었다([정정·회귀검증](./2026-09-07-intraday-2to5-defect-repair.md)). provider 호출 전 차단은 entry 35건·holding 1건으로 별도 분리한다. 대부분 BBO/current/tape stale 및 realtime provenance 결손이며 provider 장애나 AI 판단 실패로 합치지 않는다. 관측된 호출에 Gemini 전환은 없다. endpoint별 model/failback 전체 검증은 미완료다.
- 메인 신규 fill/terminal이 없어 probe/residual, AVG_DOWN/PYRAMID, partial TP/trailing와 post-sell 1~60분의 당일 순이익 효과는 입증되지 않았다. Holding Sentinel NORMAL은 효과 증거가 아니다.
- smoothing은 당일 raw/smoothed 동일 holding outcome 쌍을 확보하지 못했다. whipsaw 감소·exit 지연·순이익 개선 모두 미판정이며 OFF soft-stop을 활성화하지 않았다.

## 독립 시장 분모와 scanner

- 최신 정규 census report as-of는 09:15:39다. 5분 capture는 10:15까지 진행했지만 보고서 정규 갱신은 09:15/12:00/15:15/19:45라서 report mtime만으로 hung 판정하지 않는다. 이 실행에서는 비싼 census를 재생성하지 않았다.
- 기준: `liquid_common/top20/forward_exact`, episode validity 300초, detection SLA 120초. 보통주 master 2026-09-04의 2551종목, artifact SHA `b2e77f68a9dac866b05afbd4049b8e67302444d53799d484532cd4cd9cd75dbc`; 23bps 비용 계약 SHA `cba509b0ff17981807f2949f46e438c9aeb7592c27b9dfcfe6b79af95d1550c0`.
- 09:15 기준 KRX primary 25 episode, promotion 2/25(8%), SLA 안 provider 0/25. NXT 70은 premarket와 overlap 합산 진단일 뿐 세션별 전략 판단 분모로 사용하지 않는다. terminal 배타합 conservation delta는 두 venue 모두 0이다.
- KRX executable BBO 19/25(76%), resolved 8, pending 9. NXT premarket 42/43(97.67%), resolved 20이나 right-censored 51.22%; overlap 21/27(77.78%), resolved 16, pending 5. 모두 경제성 floor 미달로 authoritative `source_quality_adjusted_ev_pct=null`이다. 표시된 얇은 observed EV를 실제 놓친 수익으로 주장하지 않는다.
- blocker: official master lookup gap, cadence floor, exact BBO 95% floor, resolved 20 floor, right-censored 20% ceiling. 다음 12:00 report에서 동일 session의 새 capture·원천 hash·SLA·stage lineage를 재검증해야 한다. 현재 자료로 scanner_under_discovery_confirmed를 선언하지 않는다.
- discovery, post-promotion consumption, downstream conversion의 독립 분모·지연 p50/p95 전수 재구성은 이번 창에서 미완료다. 특히 기존 promotion 42건의 반복 wave를 외부 episode 포착 성공으로 대체하지 않는다.

## Scanner-pruned observer·공통 source quality

- 10:18 부근 누적 event: full prune 9023, schedule receipt 6930. 이는 unique 기회 수가 아니다. 신규 accepted episode 48, reuse 41, capacity reject 6780, anchor delay reject 53, completed reuse 8. observation 456은 48 episode에서 발생했다.
- observation: capture pass 328, shared-read budget defer 126, provenance invalid 1, invalid/crossed BBO 1. 표본 gap을 0수익으로 보간하지 않았다. 전수 prune 대비 EV 외삽은 금지된다. accepted episode의 venue/session별 resolved·right-censored floor는 별도 consumer 계산 전이라 미확정이다.
- 현재 PID configure receipt와 자연 schedule/observation으로 hook은 확인했다. configure bound active 8/pending 80/daily 1200/min interval 0.25초. 시작 receipt의 active/pending=0을 현재 queue 상태로 재사용하지 않는다.
- 공통 rate-control 실제 ledger는 production 국내조회 5/sec, source-only 4 slot이며 execution-critical kt00007 admission을 확인했다. 주문 버킷·모의투자 scope까지 전수 stress 검증한 것은 아니다. cap·retry는 변경하지 않았다.
- micro observer 10:12:29: 0B 307825, 0D 268317 callbacks; 0B p95/p99 0.034609/0.04584ms, 0D 0.032319/0.042824ms. queue drop·worker error·writer self-disable 0; stop_required=false. 시각 역행 초과 142개는 raw-row exclusion 필수다. stale exchange timestamp 차단 비율 71.6%가 존재하므로 healthy collector를 payload 유효성 정상으로 확대 해석하지 않는다.
- 디스크 약 12GiB free/88% 사용, 관측 snapshot low-disk warning 없음. source-only 수집은 계속되지만 경제성 승인이나 Provider replay 허가는 아니다.
- limit-down 당일 manager heartbeat·enabled=true, active candidate/slot 0, active live policy key 없음. `healthy_no_natural_sample`에 해당하는 manager 증거는 있으나 신규 ordered 0B+0D 자연 표본 acceptance는 미완료다.
- 당일 final observation_source_quality_audit artifact와 Main AI R1/R2/R3는 아직 없다. R0 exact trace/request는 수집 중이다. prepared→paired→terminal→cost/master→net-economic eligible 당일 final census는 미계산 상태이며 0으로 단정하지 않는다. 정규 장후 consumer 이전에 Provider replay·R3·실행효과를 주장하지 않는다.

## 위젯·독립 episode·broker

10:15:25 읽기 전용 KRX/NXT 모두 조회 성공. 조회 범위는 active machine universe 18종목이며 계좌 전체 종목 완전 대사를 주장하지 않는다. snapshot SHA `d7f0117921e34a292681928e5915a4957b4ec8faf4f45e4a429face1a1b11f04`.

| Owner | 당일 상태 | exact 주문·수량 |
| --- | --- | --- |
| 삼성 위젯 | ENTRY_CAUTION 이후 신규/추가매수 합계 20주, target open | target 0021509, 269000원, 20주; broker 잔량 20 일치 |
| 삼성 잔여 custody | 당일 위젯과 분리된 20주, owner 미확정 | target 0003725, broker 잔량 20. current registry에 삼성 row 없음; 수동/legacy owner를 추정해 흡수하지 않음 |
| 삼성 오전 독립 머신 | NO_TRADE/NO_FILL, qty 0 | BUY 0009163/0009130 각각 10주, validity 종료 취소 1회씩, 09:30:02 잔량 0 receipt |
| 한화오션 late-morning episode | TARGET_OPEN, 10주×2 | BUY 0026963@86500, 0026964@86400; SELL 0027015@86900/0027165@86800 각각 10주. exact episode registry 결속 |
| 제주반도체 위젯 | 주문 없음 | main ownership exclusion 미충족 차단; 완료된 매매/실현손익으로 세지 않음 |

삼성 aggregate 40=당일 위젯20+미확정 잔여20, 한화오션20=episode10+10이다. 위젯의 prior_day_unmanaged_qty=40은 broker-reconciled=false인 legacy provenance라서 현재 별도 보유 40주로 더하지 않는다. 주문 4건의 수량 보존은 확인했지만 삼성 잔여20주·0003725의 exact owner는 후속 receipt 확인이 필요하다. 누락된 계좌 전체/주문가능금액 확인 때문에 전 owner 충돌 0을 확정하지 않는다. open episode는 completed EV에서 제외하며 비용 차감 실현 순이익은 미확정이다.

## Process 감사

- main tmux bot 1개, 현재 PID heartbeat와 scanner/engine progress 확인. 위젯 trader 및 advisory/research/runtime collector 가동. late-morning 8개 service running(두산·한세·한화오션·카카오·한국전력·미래에셋·삼성E&A·삼성중공업).
- 삼성 오전은 valid NO_FILL terminal 뒤 종료, 정오/오후는 아직 not_yet_due다. 전일 state 파일로 오늘 기동 실패를 선언하지 않는다.
- CJ CGV 오전 preflight exit 4: `research_half_robustness_review_requires_new_profile_revision`, exact-date policy invalid에 의한 terminal quarantine. 임의 재시도·조건완화 대상이 아니다.
- census 5개 설치 cron과 정규 capture DONE, Sentinel 정규 producer 진행 확인. runbook/traceability 주기는 일치했다. 전체 timer/cgroup/lock/consumer field 전수 감사는 미완료이며 다른 process의 dead/hung/orphan 부재까지 확정하지 않는다.
- retirement canonical 15 OFF, Swing 별도 process 관측 없음. scalp/swing sim은 성과·shortage 대상에서 제외했다. 확인 범위에서 신규 실주문 authority 누출은 관측하지 않았지만 Sentinel/workorder의 retired metadata residue는 실제 결함으로 보완했다.

## 구현·리뷰·후속

1. `buy_funnel_sentinel.py`: drought owner/next artifact/required downstream/repair 안내에서 LDM 제거, 현행 postclose workorder 유지.
2. `build_code_improvement_workorder.py`: source-only `entry_submit_drought_attribution`으로 귀속해 retirement filter가 현행 workorder를 버리지 않도록 보완. legacy required-downstream residue 제거. 과거 LDM summary는 현재 receipt/terminal 검증 완료 근거로 사용하지 않는다.
3. 리뷰에서 nested implementation provenance와 weak-contract helper의 잔여 LDM 의존을 추가 발견·보완했다. actual submit이 있는데 receipt 결속이 없으면 open provenance gap을 유지한다.
4. 신규 모듈 없이 기존 producer/test 위치를 유지했다. runtime/env/order/provider/bot 권한 추가 없음. 다음 cron은 새 producer를 읽지만 메인 PID 코드 반영·수익 개선을 뜻하지 않는다. rollback은 이 source-only 변경 diff를 되돌리는 것; 거래 guard나 정책 rollback은 없다.

| shortage_id | 분모·현재·최초 결손 | 판정·다음 due/acceptance |
| --- | --- | --- |
| main_krx_submit_20260907 | KRX Sentinel AI37/budget24/submitted0; final authority·spread/price path | blocked_missing_evidence. positive executable EV 동일 causal cohort 전에는 유한 ETA 불가. 장후 exact trace→submit safety 분모 보존 및 blocker 별 반사실 확인 |
| scanner_recall_krx_20260907 | 09:15 primary25/BBO19/resolved8; 필요 coverage95%·resolved20 | blocked_missing_evidence. 12:00 정규 capture/master/cadence/SLA와 BBO outcome 재검증. 기존 영구 BBO 결손과 미성숙을 분리 |
| main_ai_net_economic_20260907 | R0 존재, 당일 prepared/terminal/economic final census 미생성 | pending_declared_window. 장후 R0→R3 각 stage 전수 분모와 earliest gap 확인, Provider floor 미충족 시 replay 금지 |
| samsung_custody_owner_20260907 | 삼성 잔여20주와 SELL0003725 exact owner 미확정 | blocked_missing_evidence. 당일 기존 주문·수동/legacy receipt와 전시장 수량 exact match; owner 추정·state 수정 금지 |

실행 owner는 당일 체크리스트 `Intraday1020Followup0907`과 기존 `ContextDeliveryNaturalEvidence0907`, `AdmLdmRetirementNaturalEvidence0907`에 연결한다. 퇴역 family의 표본모집·ETA·승격 작업은 만들지 않는다.

## 최종 검증

- 관련 pytest 221 PASS: Sentinel, workorder, runtime approval summary. Ruff PASS, Python compile PASS, git diff --check PASS. 문서 parser PASS 및 신규 후속 ID 인식 확인.
- clean-baseline 당일 10:20:03 Sentinel을 현재 producer/consumer 함수로 읽기 전용 replay하여 source-only owner, 필수 downstream, retirement filter 이후 workorder 보존을 확인했다(`tmp/intraday_1020_target_date_replay.json`).
- 수정 후 재리뷰 finding 0. 주문·runtime apply·재기동·Provider 호출·비싼 report 재생성을 수행하지 않았다. 10:20 정규 cron 산출물은 새 Sentinel owner를 이미 소비했다. 장후 workorder 실제 소비는 기존 정규 일정의 후속 acceptance이며 수익 개선으로 선행 주장하지 않는다.
- 미검증 운영 항목은 위 섹션에 명시했다. 이번 종료는 전체 시스템 경제성 승인 또는 모든 source gap 해소를 뜻하지 않는다.
