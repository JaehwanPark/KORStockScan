# 2026-09-22 Stage2 To-Do Checklist

## 오늘 목적

- 전일 family별 원천·경제성·정책·런타임 직접 소비 결과와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- 공통 Daily/EV 튜닝 및 generic workorder는 퇴역 상태를 유지하고 family owner의 직접 근거만 사용한다.

## 오늘 강제 규칙

- 장중 runtime 변경은 사용자 명시 지시가 있을 때만 기존 `bounded_tunable` 단일 축에 한해 허용한다. fresh/conflict-free source, 유효 effective price, 단일 blocker 인과, same-stage owner 비충돌, before/after·PID/env provenance·rollback·즉시 attribution을 모두 남긴다. hard safety, stale/conflict, price freshness, broker/account/order/quantity/cooldown, provider, bot, cap, 요청수량은 변경하거나 우회하지 않는다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
<!-- POSTCLOSE_SUMMARY_SOURCES {"allowed_runtime_apply": false, "runtime_effect": false, "schema": "postclose_summary_sources_v1", "source_date": "2026-09-21", "sources": {"independent_machine_terminal": {"sha256": "4c36765f4958ef4da912e52586a146f4868208f3459412428b27f7c21bdcbea7"}, "independent_widget_terminal": {"sha256": "2342caee57763f59c2acf9b7ba5f26d4c354d37e7714956e69e152769f467d2f"}, "runtime_approval_summary": {"sha256": "84aff3b02f8c5f53d960360aedcf70e5dfde4395412823d7054f96ea6faef39c"}}} -->
<!-- DIRECT_FAMILY_FUTURE_HANDOFF {"allowed_runtime_apply": false, "apply_date": "2026-09-22", "expected_state": "future_due", "manifest_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-09-22.json", "policy_receipts": [{"owner": "compact_auxiliary", "policy_owner": "compact_policy", "policy_sha256": "e90da43240000feb1a49aa732847f444133e0c319b2df410d08866606dbd35d8", "valid": true}, {"owner": "entry_cancel_wait", "policy_owner": "entry_cancel_wait_policy", "policy_sha256": "42932f1853303dd60cc137f7f99c991ebe46865875aea2664a98d96e8c6939f1", "valid": true}, {"owner": "entry_split", "policy_owner": "entry_split_policy", "policy_sha256": "3a4fe92bd22bd91e265e7a460e9834724c493557c3a8a48bd4af9e461e89d275", "valid": true}, {"owner": "low_price_expansion", "policy_owner": "low_price_expansion_policy", "policy_sha256": "59b4ed82c5cd4aaa174a9999d1e2d8370693a8986f17c35dbcd28d6c92642965", "valid": true}, {"owner": "low_price_two_leg", "policy_owner": "low_price_candidate", "policy_sha256": "3c6a36abebffea37b797c6dbe8ad63a30f7dbb6a7fd18a01d66ecfb3c04bef64", "valid": true}, {"owner": "machine_entry", "policy_owner": "machine_entry_candidate", "policy_sha256": "551a29e895b1018c94d693b0989d9fc6fa8fe44f473dc3c940988e2b73254326", "valid": true}, {"owner": "main_mechanistic_entry", "policy_owner": "main_mechanistic_policy", "policy_sha256": "e90da43240000feb1a49aa732847f444133e0c319b2df410d08866606dbd35d8", "valid": true}, {"owner": "rising_missed", "policy_owner": "rising_missed_policy", "policy_sha256": "277cb28b123c20c49f738bd4244bc34303a778d25777fdb2b14e92713706c4d2", "valid": true}, {"owner": "scale_in_split", "policy_owner": "scale_in_split_policy", "policy_sha256": "c44e8f442b615c8b7df219a981f5448c4d04df1ca87bbb943810476861442609", "valid": true}], "runtime_effect": false, "schema": "direct_family_future_handoff_v1", "source_date": "2026-09-21", "source_preopen_state": "pending", "verification_path": "/home/ubuntu/KORStockScan/data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-09-22.json"} -->

## Family 직접 증거 상태

- source date: `2026-09-21`; next apply date: `2026-09-22`.
- direct source: `1/1`; direct state: `complete`.
- economic state: `source_gap`; validated edge: `0`; policy candidate: `0`.
- PREOPEN: `pending`; natural acceptance: `not_due`.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| `entry_cancel_wait` | `source_gap` | `blocked` | `producer_contract_repair` |

## 실행 항목

- [ ] `[DirectFamilyPreopenPolicyHandoff] direct family 날짜별 정책·bootstrap 장전 소비 확인` (`Due: 2026-09-22`, `Slot: PREOPEN`, `TimeWindow: 07:35~08:05`, `Track: RuntimeStability`)
  - 전체 작업본 통합: 기존 widget/episode 수정과 최신 main 소스를 통합 검증1,122tests PASS. 정책·timer·custody 유지, 단일 release 경로/실제 PID 인계는 [통합 리뷰](../audit-reports/2026-09-22-integrated-workspace-release-review.md)와 그 deployment/acceptance receipt로 확인한다. 자연 장전/성과 확인은 이 owner를 유지한다.
  - Widget/episode pre-submit AL adapter:dfe202068 pushed/deployed;706 source +706 release tests PASS;66 service bindings verified;widget PID32218 and morning terminal-preserving PID32298 checked; broker route and terminal identities preserved. Partial/duplicate/stale integrated source stays blocked. [Review and deployment](../audit-reports/2026-09-22-entry-adverse-integrated-ws-route-repair.md); future natural orders/outcomes remain separate.
  - Samsung morning incident recovered08:08:38: old preflight release rejected the current PID baseline-date contract; repinned only the preflight to98c70f566 after103 tests. Same-date authority ready; morning PID19091 started then exited0/NO_TRADE at08:08:56, main PID13962 retained. Automatic health08:09:18 PASS/one_shot_completed. A separate pre-submit adverse-flow source gap (exact_route_missing_or_duplicate; no submitted order) remains for source/consumer inspection, without terminal reset or guard bypass. [Recovery and rollback](../audit-reports/2026-09-22-samsung-morning-preflight-release-binding-recovery.md). This closes the scoped startup incident, not all family/natural economic acceptance.
  - Source: [runtime_approval_summary_2026-09-21.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-21.json)
  - 판정 기준: source_date=`2026-09-21`, apply_date=`2026-09-22`, preopen_state=`pending`, due_policy_receipts=`entry_cancel_wait(valid=True, handoff=blocked)`의 schema·semantic hash·scope와 bootstrap accepted/rejected 결과를 확인한다.
  - incumbent 정책은 runtime override가 0이어야 하고 validated edge는 단일축 allowlist·operator lock·retired OFF·same-stage guard를 통과해야 한다.
  - 금지: bootstrap 생성·선택을 실제 PID 소비, 자연 행동 또는 비용 후 EV 개선으로 보고하지 않는다.

- [ ] `[DirectFamilySourceRepairEntryCancelWait] entry_cancel_wait 직접 family 원천·경제성 계약 수리` (`Due: 2026-09-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, `Track: RuntimeStability`)
  - Source: [runtime_approval_summary_2026-09-21.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-21.json)
  - 증거: runtime_summary_sha256=`84aff3b02f8c5f53d960360aedcf70e5dfde4395412823d7054f96ea6faef39c`, source_artifact=`/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-09-21.json`.
  - 상태: family=`entry_cancel_wait`, task_role=`producer_contract_repair`, comparison_status=`source_gap`, resolution_mode=`producer_repair`, prospective_resolution_mode=`-`, first_blocker=`execution_compact_coverage_unproven`.
  - 완료 기준: closure_owner=`entry_cancel_wait_tuning`, closure_test=`native_execution_census_cancel_terminal_cost_and_independent_holdouts`. policy_receipt_valid=`True`, source_date=`2026-09-21`의 원천·비용 EV·정책·consumer 날짜와 해시를 다시 대조한다.
  - 권한 경계: null을 0/no-edge로 바꾸거나 threshold·provider·주문·수량·cap·custody·operator lock·hard safety를 우회하지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- compact_auxiliary_direct:start -->
<!-- compact_auxiliary_direct_sha256:bdac2fcd39f3b9232653692ce905d9d1e445fa9eff29ff4641456778199063c9 -->

## Compact auxiliary 직접 증거

- 평가 원천 2026-09-21; 발행 2026-09-21; 적용 2026-09-22. 평가 상태 `blocked_source`, 선정 상태 `incumbent_preserved`.
- paired `1c906179b02325fccc39940f42d10b6b134f13468813161cacd602c52e4f6c9a`; 정책 bundle `6e5a0a9702bf4ea80dfaea11dd9e3078048f907e820bbacbcfd0cf607988cca0`; consumer `996c88a66773414e25ca0439dd8f3f5b22da75bd2e456bcca3e92f9fcc11aa17`.
- 다음 확인 `existing_main_owner_execution_cf_and_portfolio_replay` / `full_cost_stop_owner_plan_portfolio_and_forward_holdout_receipts`. 실제 PID 소비와 비용 후 자연 성과는 별도 수용 조건이다.

<!-- compact_auxiliary_direct:end -->

## 장후 복구 진행 근거

- 9/21 계산의 9/22 장전 인계는 [원천·순서·영수증 복구 리뷰](../audit-reports/2026-09-21-postclose-source-order-repair-review.md)가 소유한다. 기계정책 생성·현재 closure 검증·9/22 명시 main/compact 인계 검증이 완료되었다. 01:13 최종화 DONE 및 전체 strict 검증 PASS. 자연 PREOPEN/PID 소비는 기존 direct-family 작업으로 검증한다.

- 장후 적용일 복구: 9/21 분석·발행 / 9/22 적용을 명시해 생산자·요약·체크리스트의 날짜를 검증한다. 자정 후 자동 생성된9/23 임시 인계는 최종 근거로 사용하지 않는다.

## 단계별 튜닝 보완 구현

- [x] `[SubmissionBottleneckMonitorNatural0921] 개선된 기계정책의 의미 감시 현행화·배포·재검사` (`Due: 2026-09-22`, `Slot: INTRADAY`, `TimeWindow: 08:00~19:55`, `Track: RuntimeStability`)
  - 9/22 후속 결함: historical-only 점검 알림 억제·정상 관측1회·재발 재통보를 같은 owner에서 보완 완료. [알림 보완 리뷰](../audit-reports/2026-09-22-machine-source-identity-and-gap-review.md#notification-lifecycle-follow-up).
  - 18:25 자연 확인:c8f9565fa push·배포, source/릴리스286tests PASS, PID294296/환경 인계 PASS. 정기 감시 정상54·결손0·과거7 보존·알림 대기0; 외부 시험 알림 없음.
  - Source: [의미 감시 현행화](../proposals/intraday-semantic-entry-monitoring-and-telegram-alert-feasibility-plan-2026-09-20.md#922-기계정책-개선에-따른-감시-현행화). 기존 stable ID를 승계하며 과거 이력/원천·자연 성과의 한계는 [9/21 owner](./2026-09-21-stage2-todo-checklist.md#제출병목-지속-감시)에 보존한다.
  - Acceptance: 기계/후단 source 결손 분리, 당시 policy/scope/leaf/실효 임계치 대사, 표본 보정 선정 계약, 판정 revision/종료 요약 분리, 대상 회귀·고정 배포본 소비·무통보 재검사. 자동 threshold/AI/주문 변경 및 실현수익 입증을 포함하지 않는다.
  - 9/22 12:27 완료: 의미 감시/판정 echo 현행화82c31f34f push·배포, source/배포본288tests PASS. 배포본 Sentinel/monitor 실제 PID exit0·무통보 재검사, 정책 실효값/PID62건 일치·연결충돌0. 원천 invalid10/필수 입력17(부분89표본), source 경보17·후단5·비진입 관측39는 별도 분모/owner로 보존. 위 Source 문서의 최종 배포·재검사 절 참조. 메인/정책/주문 변경 없음.

- [ ] `[PostcloseStageRunnerSeparation] 통합 장후 실행기와 단계별 완료·재시도 분리` (`Due: 2026-09-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~23:30`, `Track: RuntimeStability`)
  - Source: [실행기 분리 계획](../proposals/machine-postclose-runner-separation-implementation-plan-2026-09-22.md).
  - Acceptance: main/auxiliary/widget/episode 독립 stage receipt·writer·retry, label 선행 barrier, 전체 완료와 장전 정책 준비 분리, scheduler/router/운영문서 동시 정합, 실패 주입·대상 검증 및 실제 단계별 재개.
  - 9/22 구현·리뷰 완료: R1–R6 stage registry/독립 writer·bounded child2/label barrier/summary 인계 구현.458+최종94tests 및 완료 원천 복사본의 실제 collector 재개 PASS; 원 정책 유지. 최종90c5cbad3 push/배포10:28 확인, 배포본451+추가98tests·두 unit/cron route PASS. [코드·재실행·배포 리뷰](../audit-reports/2026-09-22-postclose-stage-separation-review.md). 남은 자연 확인은 오늘 정기 source_date=9/22 각 stage의 실제 PID/terminal과9/23 정책 loader/부트스트랩이며 이 owner를 유지한다.

- [x] `[MainMachineSuccessReferenceEvaluation] 성공 ENTER_NOW 참조를 포함한 기계정책 장후 평가 보완` (`Due: 2026-09-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~23:30`, `Track: RuntimeStability`)
  - Source: [기계정책 성공 참조 보완계획 §9](../proposals/main-nonentry-threshold-postclose-runtime-implementation-plan-2026-09-21.md#9-성공-enter_now-참조를-포함한-장후-평가-보완계획).
  - 완료:747 source/release tests PASS,35eb8e489 push/deploy, PID269562 bootstrap PASS.17:25:36 bundle0c329961 기계 component 발행, 정규장 성공3건 유지·선택6→11기회·승률50→54.55%·평균 경로EV−0.45184→−0.39440%(공통분모 개선−0.00170%p). AI/통합/장전 승계, 자연3건 bundle 소비·최종 source clock 일치, 장후 명령/출력/cron 연결 확인. [리뷰/한계/rollback](../audit-reports/2026-09-22-machine-success-reference-and-input-latency-review.md).
  - Acceptance: 성공/실패/미진입 동일 비용 경로·기회 분모, 평가된 기존 진입 변경 허용, 부모 포함 승률 우선 비교, v3/v4 checkpoint·발행 호환, 동일 원천 비교와 장중 무추가 I/O·지연 검증, 승인된 후속 실행의 독립 stage·machine CAS·승계·PID 소비. 성공 표본/성과가 없으면 결손·부모 유지를 구분한다.

- [ ] `[MainMachineSuccessReferenceNaturalKRX] 성공 참조 정책의 갱신 KRX 분기 자연 소비 확인` (`Due: 2026-09-23`, `Slot: INTRADAY`, `TimeWindow: 09:00~10:00`, `Track: RuntimeStability`)
  - Source: [성공 참조 정책 배포·자연 소비](../audit-reports/2026-09-22-machine-success-reference-and-input-latency-review.md).
  - Acceptance: 최신 적격 successor 또는0c329961 bundle의 실제 KRX_REGULAR attempt/PID/release/leaf/임계치를 대조한다. 현 통합시장 자연 소비를 갱신 KRX 분기 사용으로 바꾸어 해석하지 않는다. 해당 session 자연 발생이 없으면 대기 상태로 유지하며 확인용 주문·재기동은 실행하지 않는다.

- [x] `[DirectFamilySourceRepairMainMechanisticEntry] 기계정책 조합 탐색·유형 원천·장중 적용 보완` (`Due: 2026-09-22`, `Slot: INTRADAY`, `TimeWindow: 08:00~19:30`, `Track: RuntimeStability`)
  - Source: [기계정책 보완 계획](../proposals/main-nonentry-threshold-postclose-runtime-implementation-plan-2026-09-21.md).
  - Acceptance: 실제82좌표 제한예산에서 다축/selector 탐색, train 재개·holdout 분리, metadata/row fallback, 적격 scope 합성, 고정 source 재계산, 장중 component CAS·실제 PID 소비·다음 정책까지 승계.
  - 9/22 완료09:40: M1–M6 구현·검증, source admission654건 복원, 3scope×96회 계산·즉시 발행. 최종3a79e240f push/배포/PID60693, 자연4판정에서a552d63 bundle과tape60/tail2.5 소비, 전scope AI 보존·날짜 승계·장후/cron route PASS. 신규 전환은 scope별1기회(KRX100%/+0.10%, 통합0%/−1.1884%, 장전0%/−1.2831%)로 실현손익 증명이 아니다. 제출 후 기록 중복 키 예외도172건 검증 후 수리. [변경·검증·운영 영수증](../audit-reports/2026-09-22-main-machine-policy-repair-review.md).
  - 9/22 추가11:21: 표본 보정 승률·기존 진입 보존·과거 발행 호환 수리644582695 push/배포,311tests PASS. 3scope×96회 재생성 후 통합시장 ask_wall_spread_bp50→80bp만 발행(bundle1114428c), 정규장·장전은 적격 신규 후보 없어 승계. 통합 신규1기회/0%/순 경로EV−1.25425%이며 수익 개선 증명이 아니다. PID60693 자연 정규장 판정에서 새 bundle 소비,9/23 승계·cron route PASS; 변경된 통합시장 임계치의 자연 사용은 해당 장후 세션 확인 범위다.
  - 기존 source gap/독립 검증 이력은 [9/21 복구 리뷰](../audit-reports/2026-09-21-postclose-source-order-repair-review.md)에 보존한다. 새로 확인한 탐색 결함으로 재개하며 과거 장후 성공을 취소하지 않는다. AI/portfolio 증거는 기계정책 적용 gate가 아니다.

- [ ] `[AuxiliaryAIBidirectionalTuning] VETO 기회비용·PASS 오진입 양방향 AI 튜닝과 장중 적용` (`Due: 2026-09-22`, `Slot: INTRADAY`, `TimeWindow: 08:00~19:30`, `Track: RuntimeStability`)
  - Source: [보조 AI 전체 계획](../proposals/auxiliary-ai-opportunity-error-tuning-runtime-implementation-plan-2026-09-22.md).
  - Acceptance: 실제 ENTER_NOW 호출 모집단의 양방향 paired 평가, soft 임계치와 fixed safety 분리, raw/effective 응답 binding, runtime 공유 판정, 새 basis 발행·AI component CAS·실제 PID 소비·독립 장후 갱신.
  - 현재는 계획 수립이며 provider 호출·정책 변경·배포·재기동 미실행. 학습/발행/PID/실현손익을 분리하고 기계정책·주문/보유 hard safety를 보존한다.

- [x] `[MainMachineSourceIdentityRepair] 기계판정 후속 식별자 및 갱신 공백 근거 보완` (`Due: 2026-09-22`, `Slot: INTRADAY`, `TimeWindow: 17:50~19:55`, `Track: RuntimeStability`)
  - Source: [식별자·공백 보완 리뷰](../audit-reports/2026-09-22-machine-source-identity-and-gap-review.md).
  - Acceptance: 현재 판정의 canonical venue/session 전달, 원천 연속성 근거 보존, 대상 검증·고정 배포본·재기동 PID 확인. 과거 원천 복구·무체결 확정·EV 개선으로 해석하지 않는다.
  - 18:07 완료:4b1631d3b push·배포, 릴리스1096tests PASS(기존 실패2건 재현 후 제외), PID286554/환경 인계 PASS. 자연9판정의14후속 이벤트 exact identity14/14,003670 정상; 새 원천9건 연속성 근거 포함. 기존 정책 유지·과거 공백 복구 주장 없음.
