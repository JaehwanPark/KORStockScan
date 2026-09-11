# 9/11 10:00까지 장중 모니터링

대상2026-09-11, 시작09:21 KST, 종료 목표10:00. 종료 관찰10:00:27 KST. 종합 YELLOW: 수신 복구 완료, drought·원천/진입 결손 미해결. 이전08:50 모니터링·후속217개 테스트 리뷰는 [이전 기록](2026-09-11-intraday-monitoring-0850.md)이며 현재 receipt와 분리한다. 이번 실행에 필요시 우아한 재기동 승인이 있으나 보고 분류 변경에 불필요한 재기동은 하지 않는다. 다른 창의 기존 배포/복구와 주문 owner를 보존한다.

## 초기 확인09:21~09:25

- main34365/widget34176 가동. 삼성 오전35141은09:00:20 exit0이며 아래 진입 결손 때문에 단순 정상 성과로 보지 않는다. 공통 선택b4de92bf/실제main root main-owner-scope-20260911 유지.
-09:20 sentinel 자연 DONE, KRX scope validator PASS. raw51시도 중 자금·배정 한도 부족5개 제외. 남은 denominator AI17/budget23/latency3/submit0, terminal upstream30/latency13/AI authority2/price1. excluded raw·사유 보존 확인. CONFLICT scope는 eligible KRX와 분리하며 그 validation invalid를 전체 정상으로 표시하지 않는다.
-09:23 broker cached-token 읽기 전용 inventory KRX/NXT 성공: 삼성26주=08:27 기존25+새 widget1. 미체결SELL0014048/1주, ka10075 request_succeeded=true/normalization_gap0/429없음. 실제금액·비용/실현손익은 아직 대사 미완료이며 추정0원으로 채우지 않는다. `tmp/intraday-monitor-20260911-1000/broker-start.json`.
- widget 삼성 ENTRY_BUY0014018/1주259000 체결, 목표SELL0014048/1주260500 미체결. 선행 NOT_SENT4건은 체결/실현수익이 아니다. 두산·한화 주문0. 오늘1주 override의 실제 소비 확인이며 기본 entry_qty10 표시와 구분한다.
- CJ CGV 오전 preflight는 research revision/비용 재검증 quarantine으로09:05와09:09 exit4. 이미 격리된 profile의 의도한 거래 차단이다. 임의 재실행·quarantine 해제 없음.
- low-price 7개 당일 state READY/bar_evaluated_no_signal/position0 확인. 저가주 다음 예약은 별도 관찰한다.
-09:24 micro healthy_with_source_row_exclusions, stop_required=false. invalid_depth_timestamp13 exact pre-enqueue receipts, path timestamp regression44 원천 제외 요구. 이후 정상 수집 유지와 해당 row 제외를 분리한다. detector09:23 PASS.
-09:15 census는 partial_diagnostics_ready. official master lookup gap/capture cadence floor/BBO outcome floor 미달로 whole_population insufficient_evidence_scanner_recall. KRX source cohort26/Provider도달1, BBO17/26, resolved9는 제한 관측이며 전체 시장 포착 정상이나 실현수익으로 외삽하지 않는다.
-09:23까지 AI trace37행: entry_price15/entry_screen22. provider32호출(OpenAI17/Bedrock15), evaluated31/transport_timeout1/preflight미호출5. Entry action DROP13/WAIT9는 미평가5를 포함하므로 전부 모델 오판으로 세지 않는다. 실제 KRX V2.14 activation16 receipt와 수익/submit0은 별도다.

## 삼성 오전 기계 최초 결손

당일 state 두 leg의 `signal_decision_at=08:23:45`는 open_price0인 예약 기동 시각이다.09:00 SOR 시가 확보 뒤 `entry_adverse_flow`는 이 값을 t0로 사용하여 두 leg 모두SKIP_DEADLINE/checkpoints{}·NO_FILL, buy_submit_attempt0으로 끝났다. 근거 `data/runtime/samsung_morning_one_share_state.json`, `src/trading/samsung_morning_one_share/machine.py`의 pre-arm signal_features와 `src/trading/order/entry_adverse_owners.py::episode_prepare`.

예약 시각과 executable 진입시점 anchor의 경계 문제이며 단순 자연 신호 부재가 아니다. 실제 BUY/WAIT 판단 입력의 변경은 source-only 수리 권한과 분리하여 검토한다. 종료된 오전 기회를 늦게 주문하거나 기존 state/시각을 소급 변경하지 않는다. 코드/기존 guard 계약과 이후 유효한 반영 범위를 추가 점검한다.

## 체크리스트 전수 분류

현재15 OPEN: KRX startup/기계 startup/micro through-close는 부분수용 후 잔여 자연·경제성 OPEN.08:50 env와08:55 scout,09:05~09:20 runtime 항목은 실제 source/apply/PID/consumer 대사로 이번 실행에서 점검한다.09:35~09:50 SimProbe는 해당 slot에 최소 분리 검증.14:20 source audit,16:30 Daily,17:00 intervention,21:15 workorder,21:30 machine,21:40 summary/source final 및9/14수량 만료는 not_yet_due. 예정 전 장후 작업 조기 실행 없음.

## 증거와 종료

`tmp/intraday-monitor-20260911-1000/snapshot-*.json`에 시각·원천 hash·scope 집계·micro·widget/episode 상태를 보존한다.10:00 종료 관찰 및 남은 acceptance는 이후 기록한다.

## 09:25~09:51 후속과 복구

- widget 목표 SELL0014048은09:25:54 로컬 broker reconciliation에서 FILLED1/260500으로 확인됐다. BUY0014018/259000과 같은 owner의 왕복이며 가격차1500원은 gross다. 정확한 수수료·세금 대사 전 실현 순이익은 null이다.09:49/09:50 전시장 broker 잔고25주·미체결0과 일치한다.
- 카카오 오전은 actual signal09:31:03.779에서 checkpoint0/3초 CONTINUE,1초 MISSED_CHECKPOINT, pre-transport depth/trade source gap 뒤 SKIP_DEADLINE으로 두 leg NO_FILL/주문0. 롯데케미칼09:25:04.369는0/1/3/5초 starting/ending depth·trade watermark 결손으로 SKIP_SOURCE_UNAVAILABLE/주문0. 삼성 예약 anchor 결함과 합치지 않는다.
- LX세미콘/삼성E&A09:40 preflight success,09:44 실제PID115821/115813. SK이터닉스09:45 preflight success,09:49 PID121122. 이는 정책/기동 receipt이며 아직 신호·체결·수익 성공이 아니다.
-09:29:59 canonical source audit는 실행exit0이나 `source_quality_raw_changed_during_audit`로 report FAIL이다.34571행 hard gap0/unknown stage2. append 중 파일의 세대 변경을 무시하지 않았다. 동일 파일을 반복 재생성하지 않고 완전한 행 경계의 고정 prefix를 복사·inode/동일 prefix SHA256 검증했다. 해당35531행만 audit warning/hard gap0이며 `canonical_publish_allowed=false`; 이후 append와 observer enqueue 이전 결손을 승인하지 않는다. 근거 tmp 하위 source-audit.log/prefix-audit.json/pipeline-prefix.jsonl.
- Micro09:35 첫 지연 burst410건 뒤09:43~09:46 재증가.09:48 snapshot의 timestamp rejection24079(0B12888+0D11191), tail64만 보존되어 exact exclusion 전수 증명은 불가능하다. stale와invalid0B는 같은 표본이므로 중복 합산하지 않는다. worker/writer error0/queue full0, callback p99 정상이어도 source quality 완료가 아니다. 과거 epoch1789082605829799438의 ingress gap과 regression44는 보존한다.
- WS1006 뒤 자동 LOGIN ACK/재등록은 있었으나 삼성전자·삼성E&A SOR0B/0D가09:49:38까지 약180초 stale였다. 자동 재연결 이후 필수 first-data 결손이 지속되어 사용자 기존 `필요시 우아한 재기동` 승인으로 복구했다. 선택 root/commit clean과 broker25주/미체결0, 삼성 오전 owner inactive를 확인한 뒤09:50 `bash restart.sh` 표준 flag handoff를1회 실행했다.
- old34365 정상 종료→new122602, selected main-owner-scope-20260911/b4de92bfee5e8f9f68f522292dd4b71509e14d28/source_dirty=false, exact-date verify PASS/pid_mismatch0/missing0. supervisor와 선택 원장·env·정책 변경 없음. post-restart broker25주/미체결0/normalizationgap0, widget PID34176 연속가동.09:50:36 삼성 SOR0B/0D fresh, 삼성E&A0D first-data 확인; 전체 필수 type·지속 회복은 계속 점검한다. 새 process의 transport_epoch1은 과거 process의1과 합치지 않는다.
- 보고 코드의 cash-shortfall 분류는 workspace sentinel09:20/25/30/35/40/45/50 자연소비를 확인했다.09:50 KRX AI35/budget83/latency17/submit0, 제외9, terminal upstream62/latency44/AIauthority10/price13. 이 stage count들은 단일 인과 전환율이 아니며 exact attempt terminal을 별도 보존한다. 고정 main/장후 코드에 workspace 변경을 묵시 배포하지 않았다.

## 점검·리뷰 범위

이번 모니터링에서는 매매 코드를 수정하지 않았다. 이전 cash-shortfall 보고 코드의217 targeted tests/compile 리뷰 완료와 이번 workspace cron 자연소비를 구분한다. 새 삼성 anchor 진입입력 변경은 사용자 답변 대기이며 미구현을 완료로 표시하지 않는다. 이번 문서·체크리스트는 korstockscan-review-gate로 현재 owner·시각·권한·링크·과거/신규 epoch 및 실현/추정비용 구분을 재검토했다. print-only parser 성공, 현재13 OPEN 중복ID0, git diff --check 성공. 이 검증은 미해결 매매/원천 결함 finding0을 뜻하지 않는다.

시작15 OPEN 중 ThresholdEnvAutoApplyPreopen0911은 applied_guard_passed_env, RisingMissedScoutRuntimePreopen0911은 source_only_no_runtime_authority로2건 종결. 나머지13개 전수 점검/미래 Due 분류, 미분류0. 삼성·micro·runtime·source-audit·고정 장후 consumer 후속은 기존 ID에 기록했다. Sim은 과거 상태/현행 source-only 권한 최소 확인이며 과거 terminal 결손을 수리 완료로 바꾸지 않았다.

외부 sync/token 검사는 실행하지 않았다. 필요할 때 사용자가 실행하는 표준 명령:
```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 10:00 종료 판정

10:00:05 자연 sentinel: KRX AI43/budget107/latency22/accepted submit0, 자금부족 제외10. exact terminal upstream80/latency56/AIauthority13/price16, broker0. SUBMIT_DROUGHT_CRITICAL 유지. latest event/source hash는 snapshot-100027.json에 고정했다. 재기동은 수신 복구이며 drought 해소/새 수익 효과가 아니다.

10:00:27 삼성전자·삼성E&A·롯데케미칼·카카오의 required0B/0D age0~361ms, micro 새epoch1789087832039585927 timestamp exclusion1·stopfalse·p99 0.126ms, detector10:00:02 PASS. main122602/widget34176 유지, 새 runtime verify PASS. broker 최종 삼성25주/KRX+NXT/미체결0/request success/normalizationgap0. 원장상 widget 왕복1건과 gross1500원, 실제 순이익 null 구분을 유지한다.

요청한10:00 관찰을 종료한다. 남은 삼성 오전 anchor live입력 수리 승인 대기, 카카오·롯데 source/transport 기한 결손, 과거micro 전수 exclusion/장후 source 감사, 메인 drought/경제성은 기존 체크리스트 owner에서 계속 추적한다. 수신 복구를 전체 결함 finding0으로 표현하지 않는다. 별도 승인되지 않은 거래조건 변경·늦은 오전 주문 재시도는 실행하지 않았다.

## 모니터링 종료 후 사용자 요청 코드 재리뷰

요청 범위는 장중 변경된 BUY Funnel cash-shortfall 제외 코드·공통 validator·회귀 테스트와 운영 기록이다. 10시 이후 상시 모니터링 연장이 아니며 매매 판단 코드는 수정하지 않았다.

1차 리뷰에서 P2 검증 결함2개를 확인·수정했다.

1. 제외 원장의 record_id가 attempt_key와 달라도, 또는 terminal_axis가 잘못돼도 기존 검증이 PASS할 수 있었다. 제외 행의 record binding·UPSTREAM terminal·허용 stage·submitted 부재를 검증하도록 보완했다.
2. 제외 후 남은 시도는 개수·stage 합계만 같으면 다른 producer_attempt_id로 바뀌어도 검증을 통과했다. 제외하지 않은 원장과 결과 원장의 전체 행을 대사한다. 제외 과정에서 바뀔 수 있는 파생 cycle ordinal만 비교에서 빼고 record/producer/parent/시각/상태/terminal 등은 모두 보존한다. 같은 record의 첫 cash-blocked call 제외 후 두 번째 별도 call이 정상 보존되는 반례도 검증했다.

수정 파일: `src/engine/automation/submit_drought_contract.py`, `src/tests/test_buy_funnel_sentinel.py`. 기존 `buy_funnel_sentinel.py`의 source dedup·call-finish 결속·raw summary gap 보존·cache/summary4개 경로도 재검토했다. scope evidence→recheck, workorder/verifier/conversion-lane의 공통 validator 소비를 확인했다.

2차 재리뷰 결과 이 변경 범위의 미해결 finding0. sentinel/contract/recheck221개 + drought handoff20개 =241 tests PASS, 관련3파일 py_compile PASS, git diff --check PASS. 최신 자연 source의 byte hash와 scope 검증은 `tmp/intraday-monitor-20260911-1000/review-consumer-validation.json`에 보존했다. KRX는 구조 오류[]/source_quality_blocked, PREMARKET PASS, 기존 CONFLICT scope는 exact_critical_decision_mismatch로 계속 invalid다. 원천 결손을 PASS로 바꾸지 않았다.

선택된 fixed main/postclose release는 교체하지 않았다. 이번 수정은 source-only validator이며 매매 재기동·보고서 재생성·Provider 호출 없음. 기존 삼성 anchor의 live입력 변경·과거 micro 결손·실현비용 미대사는 이 코드 리뷰의 finding0에 포함하지 않으며 기존 OPEN owner/권한 대기를 유지한다.

## 잔여 결함 수리와 최종 재리뷰

후속 사용자 지시에 따라 삼성 오전 예약 anchor 결함을 구현·검토했다. 앞 절의 미구현/권한 답변 대기는 당시 기록이며 이번 코드 수리 상태로 승계한다. 10시 이후 지속 모니터링이나 별도 machine 배포를 실행한 기록은 아니다.

- 삼성 오전 SOR 사전 예약의 시각을 실제 진입 판단 시각으로 사용해 개장 직후 adverse deadline이 이미 만료되는 결함을 수정했다. 신규 예약에 clock basis를 기록하고 첫 유효 opening price로 가격 계획이 만들어질 때 한 번만 signal 시각·source event·signal bar를 결속한다. 이전 예약 시각/event/bar는 별도 provenance로 보존한다. 재시도·유동성 대기·원장 reload에서는 기한을 갱신하지 않는다. 종료된 window와 기존 NO_FILL은 되살리지 않는다.
- Samsung 테스트가 운영 symbol-owner policy를 읽어 격리 계좌와 충돌하던 fixture를 임시 policy 경로로 격리했다. 실제 정책 파일은 변경하지 않았다.
- Micro frozen-source 검증은 검토된9e0044b8의 trusted data mount resolve 변경만 정확한 byte 치환으로 비교한다. 나머지 모든 byte/hash를 검증하고 임의 추가 변경은 거절하는 반례를 추가했다. 기존9/10 측정 receipt·latency 한도·collector 로직은 변경하지 않았다.

수정 경로는 `src/trading/samsung_morning_one_share/machine.py`, `src/tests/test_samsung_morning_one_share.py`, `src/tests/test_entry_adverse_owners.py`, `src/tests/test_micro_reversion_canary_monitor.py`다. 실제 adverse owner 연결 테스트에서 개장 시 checkpoint0이 실행되며 불리한 흐름이면 BUY를 차단한다. 창 만료·재시도·reload·동적 timing 및 기존 현금부족 제외/후행 handoff도 함께 검증했다.

리뷰→수정→재리뷰 후 이번 변경 범위 미해결 finding0. 관련10개 suite **559 tests PASS(8.56초)**. compile·문서 print-only parser·diff 검증은 아래 최종 검증 결과를 따른다. 예상 효과는 예약 시각 때문에 유효한 개장 기회가 평가 전 탈락하는 오류 제거이며 BUY 증가나 비용 차감 수익 개선은 아직 입증하지 않았다.

`code_review_closed=true`, `selected_release_updated=false`, `actual_pid_consumed=false`. 별도 machine 배포·재기동·정책/주문 변경·Provider 호출·고비용 보고 재생성은 하지 않았다. 기존 machine startup owner에서 검토 코드 배포 및 다음 정상 신호의 소비를 확인해야 한다. 과거 micro ingress 결손, 카카오/롯데 실제 source-quality 차단, canonical append-audit 세대 결손과 실현비용 미대사는 정상으로 바꾸지 않고 기존 OPEN을 유지한다.

최종 검증: 변경4파일 py_compile PASS, print-only backlog parser exit0(외부 sync 없음), git diff --check PASS. 기존 OPEN owner에 후속 상태를 기록했으며 신규 중복 작업을 생성하지 않았다.

## 사용자 승인 배포와 재기동

후속 “배포재기동” 승인으로 검증된 변경만 기존 배포 root에서 별도 worktree로 구성했다. 공통 main/장후는 `residual-main-20260911` / `486b9cc2aac2113656bc099113e7529320ee7af8`(보고 코드2파일과 테스트1파일), 삼성 오전은 `residual-samsung-20260911` / `acf139cd09fe7a84f3926731705ac0c257f94b95`(machine1파일과 테스트2파일)이다. 실제 배포 root에서 각각241/110 tests PASS, source clean 확인. workspace 병행 변경·캐시·정책·원장은 배포 코드에 포함하지 않았다.

공통 선택 원장을 원자 교체하고 cron9개 경로 검증 PASS. 삼성 오전 service와 morning preflight만98 drop-in2개로 연결하고 machine manifest의 해당 unit override를 갱신했다. 위젯·저가주·삼성 정오/오후의 배포는 유지했다. 당시 삼성 오전은 inactive/success로 종료됐고 오전창이 지났으므로 강제 재기동·지난 신호 재제출은 하지 않았다. 다음 정상 예약에서 새 코드를 소비하도록 설치했으며 실제 삼성 PID/신호 효과는 미확인이다.

표준 `bash restart.sh`가122602 정상 종료→drained supervisor 교체→새 main165934를 기동했다. 실제 cwd는 새 main release/src, source_dirty=false. 당일 runtime verify PASS/pid_mismatches[]/pid_missing[]. 삼성 handoff는 morning_owner_not_active/not_required.10:26:58 신규 registration receipt에서 삼성전자 KRX/SOR·삼성E&A·카카오0B/0D 자연 수신을 확인했다. 전 endpoint/전체 경제성 검증을 뜻하지 않는다.

broker10:24:38 전/10:26:44 후 KRX+NXT 조회 모두 삼성25주·348340 1주·417840 1주, 미체결0으로 동일했다. 두1주 보유는 기존 registry external_manual_remainder로 보존했으며 machine custody로 흡수하지 않았다. deposit raw224417원과 기존 승인 floor가 적용된 effective3000000원을 구분하며 이번 배포에서 floor/수량/주문 guard를 변경하지 않았다.

선택 원장·기계 manifest·이전 drop-in 백업과 전후 broker/WS/runtime verify/restart 로그는 `tmp/residual-deployment-20260911/`, canonical receipt는 `data/runtime/residual_repair_deployment_20260911.json`에 보존했다. rollback은 이전 common b4de92bf/삼성e0116f6d와 백업 selection·unit별 override를 사용하되 이후 주문/owner 변화부터 대사한다. 새 원장·보유·정책을 과거 snapshot으로 되돌리지 않는다. 코드 배포/메인 재기동 완료와 삼성 다음 자연 소비·장후 consumer·비용 후 수익 검증은 별도다.
