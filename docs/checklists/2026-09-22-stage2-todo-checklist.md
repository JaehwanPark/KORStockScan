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

- [ ] `[PostcloseStageRunnerSeparation] 통합 장후 실행기와 단계별 완료·재시도 분리` (`Due: 2026-09-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~23:30`, `Track: RuntimeStability`)
  - Source: [실행기 분리 계획](../proposals/machine-postclose-runner-separation-implementation-plan-2026-09-22.md).
  - Acceptance: main/auxiliary/widget/episode 독립 stage receipt·writer·retry, label 선행 barrier, 전체 완료와 장전 정책 준비 분리, scheduler/router/운영문서 동시 정합, 실패 주입·대상 검증 및 실제 단계별 재개.
  - 문서 계획 단계이며 현재 cron/서비스/producer는 변경하지 않았다.

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] 기계정책 조합 탐색·유형 원천·장중 적용 보완` (`Due: 2026-09-22`, `Slot: INTRADAY`, `TimeWindow: 08:00~19:30`, `Track: RuntimeStability`)
  - Source: [기계정책 보완 계획](../proposals/main-nonentry-threshold-postclose-runtime-implementation-plan-2026-09-21.md).
  - Acceptance: 실제82좌표 제한예산에서 다축/selector 탐색, train 재개·holdout 분리, metadata/row fallback, 적격 scope 합성, 고정 source 재계산, 장중 component CAS·실제 PID 소비·다음 정책까지 승계.
  - 9/22 구현: M1–M5 대상 검증648건 통과. 독립 machine-only stage를 기존 장후 wrapper에 연결했고, 최종 고정 원천 계산·immutable 배포·자연 PID 소비를 진행한다. [변경·검증·운영 영수증](../audit-reports/2026-09-22-main-machine-policy-repair-review.md).
  - 기존 source gap/독립 검증 이력은 [9/21 복구 리뷰](../audit-reports/2026-09-21-postclose-source-order-repair-review.md)에 보존한다. 새로 확인한 탐색 결함으로 재개하며 과거 장후 성공을 취소하지 않는다. AI/portfolio 증거는 기계정책 적용 gate가 아니다.

- [ ] `[AuxiliaryAIBidirectionalTuning] VETO 기회비용·PASS 오진입 양방향 AI 튜닝과 장중 적용` (`Due: 2026-09-22`, `Slot: INTRADAY`, `TimeWindow: 08:00~19:30`, `Track: RuntimeStability`)
  - Source: [보조 AI 전체 계획](../proposals/auxiliary-ai-opportunity-error-tuning-runtime-implementation-plan-2026-09-22.md).
  - Acceptance: 실제 ENTER_NOW 호출 모집단의 양방향 paired 평가, soft 임계치와 fixed safety 분리, raw/effective 응답 binding, runtime 공유 판정, 새 basis 발행·AI component CAS·실제 PID 소비·독립 장후 갱신.
  - 현재는 계획 수립이며 provider 호출·정책 변경·배포·재기동 미실행. 학습/발행/PID/실현손익을 분리하고 기계정책·주문/보유 hard safety를 보존한다.
