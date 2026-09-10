# 2026-09-10 12:30 종료 장중 모니터링

사용자 요청: 재기동 완료 후 12:30 KST까지 모니터링. 시작 관찰 12:02:57 KST. 이 문서는 진행 중 증거이며 종료 결과는 아래에 추가한다. 사용자는 12:11경 다른 창에서 배포·재기동이 진행 중이라고 확인했다. 따라서 이 창은 중복 재기동을 실행하지 않고 동일 owner의 배포 결과를 대사한다.

## 재기동 직후 확인과 즉시 복구 handoff

현재 PID624616, 시작12:00:27, source `/home/ubuntu/KORStockScan-runtime-releases/entry-v10-e821241521dc`, clean commit `e821241521dceb493b3b253ba0bc2c10b645d0b2`. 이 세대의 runtime env verifier PASS는 아래 결함을 해소하지 않는다.

1. **micro worker 저장 실패**: 12:00:54 snapshot `stop_required`, 0B worker error261/0D412, processed0/0, writer0/0, collector closed. release의 `data` symlink가 `path_journal._assert_no_symlink_ancestors`에 거부된다. 정확한 오류는 `path ancestor symlink is forbidden: /home/ubuntu/KORStockScan-runtime-releases/entry-v10-e821241521dc/data`. canonical 기존 data root는 같은 검사에서 통과한다. 기존 파일/자식 symlink 금지와 모든 수집 bound는 유지해야 한다. 12:00:27 이후 이 세대의 미저장 구간은 과거 원천 결손으로 보존한다.
2. **Entry Provider 전 차단**: 12:00:27~12:10:34 Entry trace36건 모두 `provider_called=false`, `result_source=input_preflight_blocked`, blocker `runtime_preflight_artifact_not_ready`. offline 동일 release/env 조회에서 multi-timeframe promotion은 `promotion_artifact_path_mismatch`; 기존 canonical 승인 경로와 release 별칭 비교가 원인이다. exact-v2 probe 파일도 없으므로 해당 fallback은 정상화하지 않는다. 이 DROP36은 모델 판단36으로 세지 않는다. 승인값·freshness를 바꾸지 않고 기존 canonical 경로의 동일 artifact/hash/승인 계약을 읽는 수리가 필요하다.
3. **SELL outbox 위치 단절**: 기존 실제 journal은 `/home/ubuntu/KORStockScan/src/data/runtime/sell_receipt_recovery/42193.json`; 새 release cwd의 상대 `data/runtime/sell_receipt_recovery`에는 없다. PID에 `KORSTOCKSCAN_SELL_RECEIPT_RECOVERY_DIR` pin도 없다. pending leg `d64e06983c4e1627c11123f2e0c11987017c80f95ed6b9fbd04230d19c7d9a3c`의 ACK는 아직 확인되지 않았다. 배포 owner는 기존 journal의 canonical 위치를 runtime의 기존 recovery consumer에 연결해야 한다. journal 복제/삭제/수동 ACK, 실현시각 합성 또는 추가 주문은 복구 방식이 아니다.

수리의 수용조건: 새 PID/code/env receipt → 기존 원천 경로의 natural 0B/0D 처리·writer persist 증가 및 error/drop 검증 → 실제 Entry prepared request/Provider response → exact SELL companion 검증 후 기존 pending leg ACK. 수집기 재개와 AI 입력 수리의 완료에 양수 EV나 추가 매매 floor를 붙이지 않는다. 거래 경제성과 1주 탐색 quota는 별도 계약이다.

재현 증거: `tmp/intraday-monitor-20260910-1230/release-storage-reproduction.json`, `input-preflight-reproduction.json`, `121017-collector.json`, `121034-funnel-summary.json`. 작업 트리에 병행 추가된 canonical-root 수리의 관련 collector/path tests는 88 PASS (`storage-targeted-tests.log`); 최초 잘못 지정한 test filename 실행은 수집0/exit4이며 통과 근거에서 제외한다. 이 시험은 배포 반영 또는 전 경로 review 완료가 아니다.

## 계좌·기계·예약 작업

12:04 readonly broker: KRX/NXT 조회 완료, 삼성전자45주·SK텔레콤10주, SELL 미체결3건(삼성전자0015751/0018662 각10주, SK텔레콤0022607 10주), exact registry owner 각1개. 삼성E&A028050은 broker0/registry10의 과거 수동매도 귀속 차이를 보존한다. 이 모니터링에서 state 또는 주문을 수정하지 않는다. 근거 `broker-120413.json`.

12:00 monitor_snapshot은 `intraday_light`로 정상 종료했으며, census report는12:00:27 자연 생성됐다. KRX liquid_common/top20 official-master eligible78개 중 SLA 내 Provider 도달1개(1.28%), promotion recall20.51%; 발견/전달/실행 경제성을 분리한다. KRX BBO61/78, resolved20m33개, observed cohort EV -0.50575193%이나 floor 미충족으로 decision EV null이다. 전체 scanner 정상·기회 부재 판정은 허용하지 않는다. 12:05 WS 보고서는 snapshot freshness와 subscription-state 결손을 분리한다. 예약 전 오후 기계는 지연 기동하지 않는다.

## 체크리스트 경계

기존 OPEN12개 중 WidgetEpisodeApprovedNextDayExecution0910, MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0910, RuntimeEnvIntradayObserve0910, SimProbeIntradayCoverage0910은 도래한 acceptance 미완료 owner로 계속 대사한다. 나머지8개는14:20 이후 각각의 TimeWindow까지 `not_yet_due`다. 장후 전체 재생성/Provider replay/외부 동기화는 이 모니터링의 실행이 아니다. 새 중복 owner를 만들지 않는다.

## 12:24 배포 전 독립 검증

병행 배포 owner가 준비한 `/home/ubuntu/KORStockScan-runtime-releases/entry-v10-9e0044b89de1`의 승인 code hash mismatch0. 동일 실제 PID의 context env를 모두 읽은 별도 offline 검증에서 기존 promotion SHA `f5e8df9127ce9ddd3a7c61a4f10e6fd3227080cd67bef95a328c87d69685abd8`에 결속해 `ready_operator_directed_exact_v2`, context active=true, runtime_env_readback complete_exact_v2. micro default root도 원 canonical data/observations 경로가 되어 ancestor check PASS. 기존 승인 계약을 유지한 경로 보완이며 Provider 호출이나 runtime 실행은 하지 않았다. 첫 보조 검사에서는 context env 일부를 누락해 `operator_directed_runtime_env_not_loaded`였으므로 운영 실패/통과 근거로 사용하지 않는다. 최종 근거는 `release-offline-path-acceptance-complete-env.json`이다.

고정 배포본에서 collector/path/context/promotion 네 모듈 **130 PASS**, 2.42초 (`release-storage-context-tests.log`). 이 수치는 반복 시험을 고유 테스트 수로 합산하지 않는다. 일반 입력 freshness, stale/conflict, approval hash와 자식 symlink 차단을 완화하지 않는다. 아직 PID624616이면 code 수리와 실제 소비는 분리한다.

새 승인 파일 `entry_setup_intraday_2026-09-10_9e0044b89de1_100.json`에는 다른 창의 별도 사용자 지시 참조와 일일 탐색100이 기록돼 있다. 이 모니터링은 해당 한도를 생성/변경하거나 승인하지 않았다. 실제 PID가 소비한 값, 기존3건 ledger carry와 자연 주문 owner를 사후 대사한다. 기존 PID의3/3과 새 후보 한도를 현재값으로 혼합하지 않는다.

## 12:24~12:28 자연 복구 수락

실제 전환은 12:24:06 PID657193, source `/home/ubuntu/KORStockScan-runtime-releases/entry-v10-680773d59c88`, clean commit `680773d59c882a775d31979ad8a069b5ea06a1b8`다. 9e0044b 대비 변경은 restart.sh와 해당 test뿐이며 위130개 시험 대상은 동일하다. 현재 approval SHA `95a10c8513acedad7044678cf026ce47ecf5c2f041aeec107ee8f3341da20da0`, PID recheck/recovery daily100. 실제 release cwd에서 readonly env verify PASS, PID missing/mismatch0, policy/dated fail0. 이 창은 중복 재기동/정책 변경을 실행하지 않았다.

12:25:40부터 micro `healthy_observer_canary`; 12:27:41 0B 처리10895/0D17016, writer3+3, persisted10846/16924, worker/queue/writer error0. 0D callback17107 중 invalid snapshot91은 정상행으로 보간하지 않는다. 수리 후 저장이 다시 흐르는 자연 증거이며 오전 원천 및12:00 세대의 손실을 복원한 것은 아니다. Provider replay source hold와 through-close owner는 OPEN이다.

12:27:50까지 새 세대 AI9호출: Entry OpenAI DROP4/WAIT2, entry_price Bedrock USE_DEFENSIVE3, 모두 provider_called/parse_ok=true·input blockers0. 이전 세대 Provider 전 차단과 모델 판단은 분리된다. 단기 호출 복구가 판단 경제성 개선 입증은 아니다.

원익IPS240810 12:25:38 1주 주문0045965,12:26:00 원주문 취소확인 후127300원 재가격0046010,12:26:30 미체결1주 취소확인. 일일 probe ledger는 기존3개 signature를 유지한 채4로 증가; 재가격을 신규 독립 probe로 합산하지 않는다. 체결0/새 실현수익 없음. 12:24:26 및12:26:32 broker 보유/기존 SELL3/owner 각1개 불변.

미완료: 기존 흥구석유024060 journal42193의 SELL companion ACK. 새 PID에도 recovery dir pin이 없고 release/src/data가 없어 기존 canonical journal을 읽는 consumer 연결이 남아 있다. owner=`RuntimeEnvIntradayObserve0910`, shortage class=`structural_population_exhaustion`(durable pending leg1→intended recovery consumer0), repair/deployment pending, economic acceptance not_applicable_attribution_repair. 기존 main recovery에 정확한 경로를 연결한 뒤 checksum·owner·companion 검증과 자연 ACK가 closure다. journal을 수동 완료/삭제하지 않는다. 병행 배포 owner에 문서·체크리스트로 handoff하며 다음 재개/배포 확인 때 우선 대사한다.

## 12:30 종료 판정

12:30:25 최종 확인: PID657193 singleton 유지, micro healthy/worker·queue·writer error0, 0B 처리20533/0D32112, writer3+3·persisted20482/32031. 0D invalid snapshot243은 제외 상태이며 callback 전수를 유효 원천으로 세지 않는다. callback p95 0.101699ms/p99 0.119574ms, free30.80GB. 마지막 broker12:29:25 보유 삼성45/SKT10, 기존 SELL3/owner 각1개, 삼성E&A 과거 registry 차이 유지.

새 PID 자연 AI12호출: Entry OpenAI DROP5/WAIT3, entry_price Bedrock USE_DEFENSIVE4, 모두 parse_ok=true, input blocker0. 이전 PID의 provider 미호출 Entry79/entry_price94는 모델 판단 표본에서 제외한다. 원익IPS 1주 주문은 미체결 취소됐으며 일일 accepted probe4 유지; 새 실현수익/비용 후 EV 개선을 주장하지 않는다. 흥구석유42193 ACK와 과거 원천 손실, scanner coverage·through-close·경제성 acceptance는 미완료다.

이 창의 변경은 모니터링 증거·감사 문서·기존 체크리스트 갱신이다. 배포·코드 수리는 사용자가 확인한 병행 작업에서 진행됐으며 이 창은 원인 재현, 수리된 고정 배포본130 tests와 실제 PID 소비를 검증했다. 요청한12:30 모니터링을 종료하며 이후 상시 감시를 약속하거나 미완료 전체를 finding0으로 보고하지 않는다.

| 기존 ID | TimeWindow | 12:30 분류·다음 수락 |
|---|---|---|
| `WidgetEpisodeApprovedNextDayExecution0910` | 08:40~09:00 | overdue_unresolved; through-close/오후 profile·경제성 수락 |
| `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0910` | 08:40~08:45 | collecting_after_structural_repair; 신규 persist 확인, 과거 제외/through-close OPEN |
| `RuntimeEnvIntradayObserve0910` | 09:05~09:20 | overdue_unresolved; 입력 경로 복구, SELL journal consumer/ACK·경제성 OPEN |
| `SimProbeIntradayCoverage0910` | 09:35~09:50 | overdue_unresolved; 비우선 성과 튜닝 제외, 권한/원천 간섭 경계 확인 유지 |
| `IntradaySourceQualityGateCheck0910` | 14:20~14:35 | not_yet_due; 해당 예정 창의 원 producer/consumer 수락 |
| `ThresholdDailyEVReport0910` | 16:30~16:45 | not_yet_due; 해당 예정 창의 원 producer/consumer 수락 |
| `HumanInterventionSummary0910` | 17:00~17:15 | not_yet_due; 해당 예정 창의 원 producer/consumer 수락 |
| `MainAIQualitySourceGapMainAIMicroExactEconomicIntersectionRepair0910` | 18:00~18:20 | not_yet_due; 해당 예정 창의 원 producer/consumer 수락 |
| `CodeImprovementWorkorderReview0910` | 21:15~21:25 | not_yet_due; 해당 예정 창의 원 producer/consumer 수락 |
| `MachineLifecycleTurnoverObjectiveFollowup0910` | 21:30~21:40 | not_yet_due; 해당 예정 창의 원 producer/consumer 수락 |
| `AutomationTriggerDecisionSummary0910` | 21:40~21:55 | not_yet_due; 해당 예정 창의 원 producer/consumer 수락 |
| `PostcloseSourceQualityGateReview0910` | 21:40~21:55 | not_yet_due; 해당 예정 창의 원 producer/consumer 수락 |

검증: 고정 배포본 관련130 tests PASS, print-only parser/current checklist unique12, git diff --check. 외부 Project/Calendar sync 및 token 검사는 미실행.

필요 시 사용자 실행 동기화 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
