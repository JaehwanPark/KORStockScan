# 2026-09-10 08:30 종료 장전 모니터링

## 범위와 판정

사용자 요청은 장중 지시문에 따른 08:30 KST까지 지속 모니터링이다. 추가로 필요한 반영의 메인봇 재기동을 명시 승인했다. 위젯·episode 재기동, 주문/수량/정책/threshold/provider 변경, 삼성E&A 원장 수정은 이번 실행에 포함하지 않았다. 중간 판정 as_of=08:20; 종료 관측은 아래에 별도 기록한다.

확인된 결함 두 개를 수리하고 메인봇에 반영했다. `get_kiwoom_base_url()` 진단 출력의 JSON stdout 오염과, 시작 시 같은 symbol의 SOR 등록 직후 요청한 NXT 관측이 REG 중복 제한에 소실되는 결함이다. 새 PID349443에서 삼성전자 NXT 0B·0D 자연 수신과 실제 NXT 저장 series를 확인했다. 이는 이후 원천 수집 복구이며 08:00 신호의 과거 누락이나 비용 후 실수익 개선을 입증하지 않는다.

## 원인·구현·검토

1. `src/utils/kiwoom_utils.py`: 성공/오류 진단 print를 stderr로 분리. 기존 URL 선택·fallback·인증·요청은 그대로다. 실제 `threshold_cycle_preopen_apply --verify` JSON이 이제 직접 parse된다. 원본 실패 stdout과 수리 후 JSON을 모두 보존했다.
2. `src/engine/kiwoom_websocket.py`: 기존 8초 normalized-symbol REG 중복 제한이 startup 005930_AL 뒤의 source-only 005930/005930_NX를 걸렀다. one-shot manifest는 재요청하지 않아 기존 PID325910의 삼성 NXT required 0B·0D 수신이 모두 0이었다. manifest/collector healthy만으로 exact route 정상 판정할 수 없는 구조적 결손이었다.
3. 누락된 현재 source-only route만 process-local code별 coalesce하고 기존 TTL 뒤 한 번 재검사/dispatch한다. 당일·transport epoch·target·process liveness를 다시 확인한다. 기존 REG budget, refresh=1 additive, REMOVE 없음, 0B·0D 요청, observation-only 권한을 유지한다. 재차 차단되면 terminal gap이고 무제한 retry나 제한 상향이 아니다. `registration_dispatch_status`는 로컬 전송 상태이며 실제 `received_realtime_types`/first-data를 대체하지 않는다. `subscribed_now` 로그를 `dispatch_requested_items`로 정정했다.
4. 자체 리뷰에서 nested lock deadlock과 이전 future callback이 새 dispatch 소유권을 제거하는 race를 발견해 보완했다. caller-lock/token 소유권 및 future cleanup, stop/date/epoch/target 변경, 재차 제한·item budget·schedule failure를 재검증했다. 직접 consumer는 기존 registration receipt→machine attribution/source-quality이고 새 상태가 실주문 선택을 만들지 않는다.

검토 범위 잔여 finding=0. 전체 저장소 또는 경제성 완료 선언이 아니다. 이전 작업의 PREOPEN/adaptive-exit 등 dirty 변경은 보존했다. 새 PID의 source_dirty=true와 전체 working tree 상태를 clean generation으로 표현하지 않는다. 독립 adaptive-exit 기계의 정책/envelope 미선정 상태를 이번 재기동으로 활성화하지 않았다.

## 공식 Kiwoom reference gate

공식 [Kiwoom REST API](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/234560d213acd8871ae344b5481aecd2f30287fa) SHA `234560d213acd8871ae344b5481aecd2f30287fa`, 최초 조회 `2026-09-10T08:09:15.769154+09:00`, 추가 파일 확인 08:14까지. 현재 tree에는 `kiwoom_docs`가 없어 이 부재를 보존하고 `kiwoom/realtime/packets.py`, `stream.py`, `decoders.py`, `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 0B/0D, `kiwoom/core/client.py`, `ws_client.py`, Postman을 대조했다. LOGIN/control, REG refresh/types, plain KRX/`_NX` NXT/`_AL` SOR route를 확인했고 SOR 실제 venue를 NXT로 추론하지 않았다. 예제 주문은 실행하지 않았다.

원문 snapshot 및 SHA/time receipt: `tmp/intraday-monitor-20260910-0830/official/`. 프로토콜/FID/인증·주문 parser 변경은 없다.

## 검증과 실제 반영

- websocket/market-data/token-cache 영향 테스트 **156 PASS** (`tests-final.log`); 재기동 flag race/Samsung authority handoff **17 PASS** (`restart-tests.log`). 반복 실행 수를 합산하지 않았다.
- 변경 Python 4개 compile, `bash -n restart.sh src/run_bot.sh`, `git diff --check` 통과. 문서 최종 parser는 종료 검증에 기록한다.
- 사용자 승인 뒤 `./restart.sh` 정상 종료(exit0). PID325910→349443; 같은 날짜 Samsung authority prepare/commit 성공. 강제 kill, 독립 machine 재시작 없음.
- 새 PID runtime verify PASS: missing/mismatch0, policy fail0, dated override fail0, selected18, retired selected0. recheck false는 유지된다. code/source hash는 `deployed-source-hashes.json`, verify는 `runtime-verify-after-restart.json`, restart 원문은 `restart.log`.
- 08:19:17 전/08:19:49 후 KRX·NXT broker inventory 삼성전자25주, 미체결0 동일. 삼성 오전 PID327358, widget PID327676·NRestarts0 유지. NXT 오전 buy2개는 08:10 기존 machine 계약에서 취소 후 SOR fallback PLANNED 상태로 전환돼 재기동 전부터 미체결이 없었다.
- 삼성 NXT 첫 0B `08:19:54.685`, 첫 0D `08:19:54.784` KST. 새 source sequence epoch `1788995984118403506`; `005930|NXT|NXT_PREMARKET` series의 persisted sequence 증가 확인. 전 세대 epoch와 합쳐 과거 신호 window를 채우지 않는다.
- 08:20:04 canary healthy/stop=false, queue/drop/writer error0, callback p95≈0.102ms/p99≈0.118ms. writer 0B/0D 각각2는 NXT/SOR 두 partition이며 duplicate writer 증거가 아니다. free bytes 약37.78GB, low watermark5GiB보다 높다. 다른 requested KRX item의 개장 전 first-data 미수신과 삼성 실제 NXT 결손을 구분한다.

## 매매·원천 현황과 남은 경계

- 메인: 08:14까지 promotion33, 반복 WATCHING heavy completion510, submit-attempt terminal16은 모두 returned_false. 이 숫자는 실제 주문16건이 아니다. 관측 차단은 latency/spread와 실제 주문가능금액에 따른 quantity0 등이다. 당시 AI trace의 새 날짜 파일은 미관측이므로 과거 DROP194/WAIT79 집계를 오늘 AI 품질로 대체하지 않는다. 준비/전달과 provider 판단을 별도로 검증해야 한다.
- 메인 예수금 raw83,393원과 기존 사용자 승인 minimum floor를 반영한 표시 effective3,000,000원을 분리했다. 후단 실제 종목 주문가능금액 cap이 작동하며 표시 floor를 실제 현금으로 보고하지 않는다. 원래 수량/guard는 변경하지 않았다.
- scanner-pruned BBO는 새 PID에서도 source-only admission/capture가 계속되고 daily1200/active8/pending80 bound를 유지한다. 독립 시장 benchmark 정규장 수집 예정 전이므로 `insufficient_evidence_scanner_recall`; scanner 내부 count로 시장 포착률 정상을 선언하지 않는다.
- micro shortage: `micro_continuity:005930:NXT:NXT_PREMARKET:20260910:startup_reg`의 최초 고갈 stage는 REG admission. repair_status=reviewed, deployment_status=PID349443, 이후 natural route/persistence는 복구 확인. 08:00 신호 전후 -30~+6초는 historical exclusion 유지. through-close·새 신호의 전체 창·downstream attribution/economic acceptance는 기존 continuity owner OPEN이다. 과거 손실에 finite ETA 또는 재생 replay를 붙이지 않는다.
- machine timing 당일 scopes는 비어 있어 immediate baseline이다. micro 수신 성공이 timing 선정이나 매수 권한이 아니다. 비용·terminal 미대사 headline은 `realized_pnl=null`, `realized_pnl_status=not_reconciled_for_monitoring_cohort`로 둔다.
- 퇴역 selected family0; Swing/ADM/LDM/greenfield/비우선 sim은 실수익 튜닝 모집단에서 제외한다. historical artifact의 0건에 shortage/승격 작업을 만들지 않는다.

## 삼성E&A 수동매도 대사

사용자 설명과 9/9 broker 내역을 대사했다. 028050 현재 broker 잔고0. SELL0056859는 원주문0053225의 수동 정정 successor, 10주@50,600원 체결/미체결0, 매체 `영웅문S#`; 원주문시각15:03:41은 실제 fill timestamp로 대체하지 않는다. 별도 SELL0053552 10주와 entry0053206/0053207도 exact 번호로 보존했다. 원문 `samsung-ea-manual-sale.json`.

현재 registry의 잔여10주 때문에 `owner_registry_broker_quantity_deficit`가 남는다. 이는 실보유가 아니라 과거 manual successor 귀속 미반영이며 07:32 owner publisher의028050 제외를 설명한다. 잔고0만으로 COMPLETE/비용/체결시각을 합성하지 않았고 자동 state 수정은 실행하지 않았다. 기존 `WidgetEpisodeApprovedNextDayExecution0910`에서 정확한 successor/custody/비용 대사 후속을 유지한다.

## 도래 항목 전수 분류

현재 체크리스트 OPEN14개는 모두 최초 window08:40 이후로, 08:30 종료 기준 `not_yet_due`다. RunbookOps `PreopenAutomationHealthCheck20260910`의08:00~09:00 반복 확인은 이번 범위에서 수행했다:07:20 scanner DONE,07:32 owner publisher,07:35 wrapper/별도07:46 수정 receipt,07:55 기동 및 승인된08:19 재기동/verify, detector PASS. 과거 source9/9 전체 장후 producer를 다시 실행하지 않았다.

| 기존 OPEN ID | Due 9/10 TimeWindow | 이번 점검 / 남은 acceptance |
| --- | --- | --- |
| WidgetEpisodeApprovedNextDayExecution0910 | 08:40~09:00 | 현재 machine/broker 대사; 미래 profile preflight·signal·terminal 및 EA registry 후속 |
| MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0910 | 08:40~08:45 | REG 수리/새 PID 자연 NXT 수집; exact 신호창·through-close·consumer |
| ThresholdEnvAutoApplyPreopen0910 | 08:50~08:55 | 현재 PID verify PASS; 해당 slot 최신 apply/handoff 재확인 |
| RisingMissedScoutRuntimePreopen0910 | 08:55~09:00 | source-only/선택 차이와 해당 slot receipt |
| RuntimeEnvIntradayObserve0910 | 09:05~09:20 | 실제 eligible/pass/block/submit/fill/exit 귀속 |
| SimProbeIntradayCoverage0910 | 09:35~09:50 | source-only 및 실주문/리소스 간섭 최소 확인 |
| IntradaySourceQualityGateCheck0910 | 14:20~14:35 | 당일 후속 원천 audit·row exclusion |
| ThresholdDailyEVReport0910 | 16:30~16:45 | source9/9 결과 점검 |
| HumanInterventionSummary0910 | 17:00~17:15 | source9/9 개입 분류 |
| MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0910 | 18:00~18:20 | 같은 primary trace의 paired/mature/sidecar/net 교집합 |
| CodeImprovementWorkorderReview0910 | 21:15~21:25 | 최신 원천 workorder 대사 |
| MachineLifecycleTurnoverObjectiveFollowup0910 | 21:30~21:40 | 독립 machine 후속/경제성; 기존 미완료 보존 |
| AutomationTriggerDecisionSummary0910 | 21:40~21:55 | 정상 예약 producer/consumer receipt |
| PostcloseSourceQualityGateReview0910 | 21:40~21:55 | 최종 원천 감사와 다음 PREOPEN handoff |

관측 원문은 `tmp/intraday-monitor-20260910-0830/`의 시각별 immutable snapshot·`snapshots.jsonl`·broker 전후 내역·source hash에 보존한다. 해당 경로는 복구/감사 증거이며 tmp 이름으로 삭제하지 않는다.

## 08:24 추가 대사

08:23:15 기준 원본211,457,400bytes까지 pipeline census: malformed0, promotion ID48, submit attempt terminal27, BBO captured119/source gap9. 9개 gap은 shared-read-budget deferred이며 budget을 높이지 않았다. `limit_down_watch_source_loaded`는 새 PID에서도 candidate0/source pass/active live0으로 manager load가 확인돼 현재 자연 대상 없음으로 분리한다.

08:18:01 나우로보틱스459510의 실제 `scalping_entry` AI1건을 확인했다. OpenAI `gpt-5.4-nano`, evaluated/live/DROP, exact trace `analyze_target:459510:1788995877402:5697f8b0`. Entry-price는 Bedrock Qwen3 32B의 별도 trace다. freshness가 확인된 동일 symbol Entry-price context handoff를 사용했고 final authority guard는 모델 DROP을 보존했다. `ai_confirmed` 이름은 BUY 성공을 뜻하지 않는다. 08:14 미관측 설명은 그 시점의 기록이며 오늘 하루 AI0건이라는 결론이 아니다. 두 호출은 이전 PID 시점으로 이번08:19 재기동 효과로 귀속하지 않는다. 당일1건만으로 모델 품질/양수 EV를 판정하지 않는다.

증거: `pipeline-census-0823.json`, `ai-receipts-0824.json`. Print-only parser exit0, 현재 checklist OPEN14 unique/미분류0; 전체 parser30에는 별도 RunbookOps와 과거 reference 항목이 포함된다.

08:24 source 재대사:08:23:06 별도 작업이 같은 WS 파일에 `ws_receive_expectation.classify_receive_gap` 진단 import/row projection 5줄을 추가했다. 이 부분은 PID349443 시작 뒤 변경이므로 미반영이다. 해당 추가만 제거한 content hash가 보존된 배포 hash와 정확히 일치하여 이번 deferred-REG 수리 본문은 동일함을 확인했다. 별도 작업의 미완료 코드를 이번 review finding0 또는 자연 소비로 포함하지 않으며, 검증 전 추가 재기동하지 않는다.

## 사용자 지적 후 나우로보틱스 기회 누락 재검토

08:26:11 WS snapshot은459510 현재가/매수호가16,420원, 매도호가16,470원이었다. AI 시점 exact payload best ask15,830원→이후 bid16,420원은+3.7271% 호가 간 변화다. 사용자가 지적한15,800→16,000 이상 상승이 실제 저장 시세에서도 확인된다. SOR 원천이며 NXT exact 체결·전 구간 adverse-first·실현비용·재기동 사이 경로 완전성을 확인한 실현손익은 아니다. 그 제한 때문에 이 사례를 정상 DROP으로 승인해서도 안 된다.

모델은 예상 upside0.4%, downside-1.0%, confidence78, NO_EDGE/DROP을 반환했다. 입력에는 trusted10ticks/buy-pressure99.32%/net aggressive+1009주, supportive tape/liquidity, ask-sweep70/bid-replenishment70이 있었다. 반면 completed1m/3m slope 음수, microVWAP 대비-95.97bp, peak drawdown-2.1001%, 최근 volume ratio0.391이었다. 당일 volume_ratio_pct800.87과 최근 봉 volume_ratio0.391은 분모가 달라 같은 지표의 모순으로 단정하지 않는다. 모델 reason은 edge_absent/trend_adverse/volume_confirmation_missing/risk_reward_unfavorable이고, adapter는 DROP을 유지했다. semantic repair는 enum/reason 정합 보완이며 경제적 판단 성공이 아니다.

실제 사용된 V2.13 prompt는 BUY를 `clean_continuation_probe.eligible` 또는 `recovery_confirmation_probe.eligible`로 제한한다. recovery는 structural/reclaim/precursor, completed recovery와 trusted trigger, cost≤0.25%, peak drawdown>-2% 등 선행 조건을 요구한다. 해당 입력에서는 구조 floor/recovery/trusted trigger 모두 false이고, exact peak drawdown은-2.1001%였다. 따라서 강한 단기 체결 회복만으로 BUY를 내기 어려운 설계임을 확인했다. 이는 모델 호출 품질과 분리된 **작은 수익 기회 포착 목적의 제약/과소평가 검토 finding**이다. 단일 사례로 전 거래일 모델 오류율이나 양수 EV를 확정하지 않지만, 이 사례를 수익기회 없음으로 종료하지 않는다.

기존 `RuntimeEnvIntradayObserve0910` 및 `MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0910`에서 다음을 대사한다: 같은 promotion의 DROP 뒤 watch/recheck 지속·fresh price/tape 변화에 따른 다음 평가 유무; missed-opportunity를 actual-filled-only floor와 분리한 기존 CF cohort의 exact input/outcome 수용; 완성봉 확인 이전의 supportive tape·refill·executable BBO를 독립 단기 회복 후보로 평가할 수 있는 기존 bounded owner; Control 대비 비용 후 수익/손실 꼬리/회전시간. 임의 BUY 강제·하드 guard 해제·Provider 변경은 하지 않는다. 조건 달성 불가 또는 구조적 고갈이 입증되면 현행 선택 프롬프트/재평가 owner 수정 대상으로 분리하며 수집 대기로 무기한 넘기지 않는다. 이 후속의 economic/design finding은 이번 REG/CLI 수리 finding0 범위에 포함되지 않는다.

근거: `nau-ai-payload.json`, `nau-ai-prompt.json`, `ws-snapshot-0826.json` 및 exact trace SHA. 이번에 추가 Provider replay는 호출하지 않았다.

후속 경로도 확인했다(`nau-post-drop-path.json`):08:18:08 첫 watch eviction=`rising_missed_not_rising_budget_reallocated`/candidate_gate_backoff_active.08:25 재승격 뒤 estimator warmup3회,08:26:14 Entry-price 재호출,08:26:16 tick_acceleration_ratio_lt_1 제출 차단,08:26:19 queue-lag budget 재배분으로 watch eviction. 따라서 계속된 기회 누락은 최초 AI DROP 외 재발견 지연·warmup·tick-speed·slot 회수도 연결된 복합 문제다. 두 번째 가격 AI 호출을 Entry AI 재판단 성공으로 세지 않는다. 새 PID로 estimator가 초기화된 운영 영향도 함께 보존한다.

## 장후 프롬프트 개선 작업에 반영할 판단

source9/9 cycle의 실제 상태는 `source_only_blocked_or_deferred`, provider_call_performed=false/current_provider_replay_complete=false, research/source candidate0, CF eligible/candidate0, runtime apply=false다. blocker는 observer row exclusion 및 `paired=24:economic=0` exact 교집합 결손이다. 따라서 보고서 생성만으로 이번 유형의 과차단을 탐지·개선·실적용하는 루프가 정상 작동한다고 할 수 없다.

08:29 기존18:00 AI micro exact owner에 이번 exact case와 전수 CF 평가 요구를 추가했다. 검토 축은 (1) 중첩 V2 규칙과 offline/live 의미의 혼재를 제거한 일관된 현재-stage prompt 계약, (2) 지속상승·완성봉 회복 외 fresh micro 회복의 비용후 작은 순이익 기회 분류, (3) DROP 이후 조건 변화에 따른 재평가와 slot 유지, (4) 미진입의 기회손실과 회피손실을 함께 평가하는 full census, (5) actual fill이 없는 연구 평가와 live 승격 gate 분리, (6) 기존 승인/PREOPEN/PID consumer의 실제 연결 및 달성 가능한 조건이다. source 없는 과거를 만들거나 한 종목 정답을 prompt에 넣지 않는다. 현행 R3 legacy bridge OFF를 신규 candidate의 자동실적용으로 설명하지 않는다.

## 08:30 종료 확인

08:30:11 최종 snapshot(생성08:30:07): PID349443, canary healthy/stop=false, 0B51,435·0D52,271 callback, queue/drop/writer error0, p95 0.083916ms/p99 0.110164ms, free bytes37,547,307,008. detector08:30:02 PASS. 08:28 현재 PID readonly env verify PASS. 삼성 오전/위젯은 기존 process를 유지하며 최종 broker 내역은 `broker-end.log`와 해당 dated JSON에 보존했다.

요청된08:30 모니터링을 종료한다. 이후08:40부터 도래하는14개OPEN과 장후 prompt 개선 수용조건은 현 체크리스트에 보존했다. 이번REG/CLI 수리 검토156 tests+restart17 tests/compile/shell/diff가 통과했고, prompt 경제성·설계 finding은 별도 미해결로 남는다. 문서 최종 print-only parser/링크 검사 결과를 아래에 기록한다.

최종 검증: print-only parser exit0/당일14 unique, 이번 추가 문서 링크 결손0; 기존 checklist의 미래 예정 artifact 링크5개(중복 제외4경로)는 아직 미생성으로 not_yet_due, git diff --check PASS. 최종 inventory005930 25주/미체결0, Samsung327358·widget327676 NRestarts0. 종료0B writer3은 KRX/NXT/SOR 세 partition이며 중복 process가 아니다.

## 08:39~08:45 사용자 요청 코드 재리뷰·수정

사용자가 장중 수정분의 리뷰·수정보완 및 결함이 없을 때까지 반복을 요청했다. 기존 REG/CLI 변경과 직접 consumer를 재검토했으며 다음 경계 결함을 보완했다. 기존08:15 테스트/08:19 배포 receipt는 당시 버전의 기록으로 보존한다.

1. **전송 대기 중 세대 변경**: 최초 delay 후 검사만으로는 `_send_reg`의 LOGIN/batch await 중 epoch/date/manifest/target/stop 변경을 막지 못했다. deferred source-only caller가 전달한 `dispatch_guard`를 대기와 실제 send 직전·직후에 재검사한다. 이미 wire에 나간 요청은 취소했다고 주장하지 않고 새 세대의 로컬 등록 상태에 결속하지 않는다. 기존 일반 REG caller는 optional guard 미지정으로 기존 계약을 유지한다.
2. **늦은 callback·동일일 manifest 교체**: 이전 callback이 후속 상태를 덮는 문제와, 새 manifest가 이전 pending token에 막혀 새 요청을 잃는 문제를 재현했다. current receipt/token 소유권으로 쓰기를 제한하고, 새 manifest는 pending admission과 dispatch 표시를 초기화해 새 누락 route를 예약한다. 오래된 future는 기존 bounded delay 뒤 generation guard에서 종료한다. 원래 first-data 정보는 합성하지 않는다.
3. **부분 성공의 전체 실패 표시**: 여러 code 중 하나만 재차 TTL에 막혀도 모든 row가 terminal gap으로 기록됐다. code별 blocked/registered 결과로 분리했다.
4. **대기 중 budget 변화**: LOGIN 대기 동안 다른 등록이 늘어나는 경우 실제 outgoing batch에 기존 item budget을 다시 적용한다. 제한 상향이나 retry 증가 없음.
5. **오류 경로 JSON stdout 재오염**: base URL 실패 분기에서 호출한 일반 logger 자체가 실패하면 stdout에 진단이 남을 수 있었다. 이 startup 오류는 stderr 단일 진단으로 통일했다. 테스트에서 logger를 무음 monkeypatch해 숨기는 부분을 제거했다. 기존 URL/production fallback 정책은 변경하지 않았다.

추가 경계 테스트: LOGIN 대기 중 epoch/target/manifest 교체, wire send 도중 epoch 변경, late item-budget 차단, 부분 dispatch, 이전 future의 늦은 cancel callback, 새 manifest의 successor 예약. 기존 stop/date/reblocked/budget/schedule-failure 테스트도 유지했다. 1차162 PASS→manifest successor 보완 뒤221 PASS→late-budget/재기동 계약 포함 **239 PASS**(7.04초), 직접 freshness report/entry-setup-policy consumer **71 PASS**(1.87초). 이는 최종 서로 다른310 tests이며 이전 반복 결과와 합산하지 않는다. Python compile, bash syntax, git diff --check PASS. pandas_ta의 기존 deprecation warning1개.

공식 reference HEAD를08:39:19 KST 재조회: `234560d213acd8871ae344b5481aecd2f30287fa`로 앞선 공식 파일 snapshot과 동일. packets.py additive refresh1,0B/0D,기존spec/route/LOGIN 계약을 재대조했다. wire/FID/parser/auth/order 계약 변경은 없다. `review-validated-hashes.json`에 검증 코드 hash를 보존했다.

이번 변경/직접 경로 재리뷰의 잔여 finding0. 병행 adaptive-exit 구현 전체·AI 프롬프트 경제성·과거 manual custody는 별도다. 위에서 확인한 prompt 기회 누락 finding을 이 수리 완료로 닫지 않는다. 후속 런타임 반영은 사용자 기존 메인봇 재기동 승인으로 수행하며 새 receipt를 별도로 기록한다.

재리뷰 후 실제 반영: `review-restart.log` exit0, oldPID349443→newPID375167, Samsung same-date authority handoff committed.08:46 현재 verify PASS/missing·mismatch0/policy fail0, 검증한9개 source hash와 파일 일치. `review-cli-json-smoke.json`은 실제 CLI stdout으로 JSON parse PASS. 삼성 NXT 0D08:46:14.751/0B08:46:14.752 첫 수신과 누적 증가 확인. 재기동 전08:44:42/후08:46:24 broker KRX·NXT inventory005930 25주/미체결0 동일, independent Samsung327358/widget327676 NRestarts0. 원장 snapshot helper도 기존 registry lock 아래 일관된 read로 보완했다. EA 과거10주 registry 차이는 그대로이며 live inventory0과 분리한다. 이 반영은08:30 모니터링 재개가 아닌 별도 사용자 코드리뷰 요청과 기존 재기동 승인에 따른 수리 검증이다.

08:47:20 반영 후 collector 확인: healthy_observer_canary, stop=false, 0B/0D callback1702/1775, queue/drop/writer error0, 두 route partition writer각2, p95 0.099628ms/p99 0.108401ms. 최종 parser 당일14 unique/미분류0, 검증 source hash 일치, diff-check PASS. 자연 경계 발생 전인 cancellation/manifest 교체 반례는 격리 테스트로 확인했으며 실제 사고가 발생했다고 보고하지 않는다.

커밋 준비 검증: CI와 같은 Black26.5.1로 이번 REG/CLI 관련4파일을 포맷한 뒤 동일 영향310 tests PASS(8.00초)를 재확인했다. 포맷은 동작 변경이 아니며08:46 PID의 load receipt를 새로운 commit/hash 소비로 재라벨링하지 않는다. 이번 커밋 범위는 REG/CLI 수리·테스트와 이 모니터링 기록/기존 checklist handoff이며, 병행 adaptive-exit·별도 prompt 적용 작업은 각 작업의 검증과 커밋 범위로 유지한다.
