# 튜닝 운영기반문서·장후 지시문 현행화 리뷰

기준: `2026-09-07 KST`, 문서/스킬 변경만. 실행 owner: `TuningOperatingDocsRefresh0907`.

## 범위와 판정

장후 상세검토 진행과 자연 acceptance를 분리하고 운영기준의 오래된 owner/권한 설명을 정정했다. 보완→재리뷰→문서/파서 검증을 닫았으며 이 변경·직접 대조 계약 범위의 미해결 finding은 0이다. 이 판정은 장후 자연 terminal, 런타임 적용 또는 EV 개선 완료가 아니다. 실제 매매·장후 producer 코드는 이번 작업에서 수정하지 않았다.

| 대상 | 반영 내용 |
| --- | --- |
| [장후 상세검토 목록](2026-09-05-postclose-work-inventory.md) | review index 1~119 유지; #8/#9 완료 유지; #11/#119/#23/#49/#76/#78/#82 자연 acceptance 분리; 우선 상세검토와 자연 관찰 대기열 분리 |
| [장후 모니터링 지시문](../postclose-tuning-result-review-task-instructions.md) | 문서 수정/실행 권한 분리, 예정 전·정상 대기·실패 구분, intake 전수보존, terminal retry 금지, late calibration/consumer와 finalization marker 순서 |
| [AGENTS](../../AGENTS.md), [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md), [session pointer](../plan-korStockScanPerformanceOptimization.prompt.md) | 현재 owner 요약, clean baseline, 수량 산식, 완료/자연/성과 구분; retired/OFF 및 #81와 별도 entry owner 분리 |
| [Runbook](../time-based-operations-runbook.md), [traceability](../report-based-automation-traceability.md), [threshold README](../../data/threshold_cycle/README.md), [report README](../../data/report/README.md), [root README](../../README.md), [문서 지도](../README.md), [장중 지시문](../intraday-monitoring-task-instructions.md) | 같은 권한·입력·후행 순서와 현재 운영 의미 반영; LDM historical contract를 현재 적용 허들로 사용하지 않음 |
| `/home/ubuntu/.codex/skills/korstockscan-review-gate/` | SKILL.md와 agents/openai.yaml: 작업 모드별 권한, 문서 전용 검증, 수리/자연/EV 분리, generation fixed-point 기준. 저장소 밖 파일이므로 repo commit 대상 아님 |

## 확인한 근거

- [#119 최신 리뷰 §11](2026-09-07-buy-funnel-submit-drought-handoff-review.md#11-r1r5-보완-구현과-최종-재리뷰): schema5/exact2, retry/terminal/비차단 fallback, consumer 대사 수리 종결. 다음 자연 owner는 `EntryRecheckNaturalAttribution0907`.
- [#49 v4 최종 리뷰](2026-09-07-scanner-lookup-attention-final-review.md#r1r5-보완-구현과-최종-재리뷰): 자원배분 pair와 실제 full-fill base/holdout을 분리. 자연 owner는 `ScannerLookupAttentionNaturalEvidence0908`.
- [#76→#82 v5 리뷰](2026-09-07-ai-decision-action-outcome-calibration-final-review.md): 부분 정상행 학습, hash/cohort 보존, frozen optimizer 및 metadata-only 재결속. 자연 owner는 `AIDecisionActionOutcomeNaturalEvidence0908`.
- `deploy/run_ai_entry_setup_paired_replay_postclose.sh`: 상세 terminal→calibration→optimizer→metadata binding→holding manifest→consumer. `src/engine/scalping/main_ai_quality_live_policy.py`의 legacy authority false를 확인했다.
- `deploy/run_threshold_cycle_postclose.sh`: ADM/LDM/bridge/institutional OFF와 비-LDM scalp-sim control-tower/prior surviving 실행을 구분했다. Widget wrapper는 producer 4개 사이 EOD gate, machine final wrapper는 expansion→attribution→weakness→timing→approval→checklist다.
- 17:05 읽기 전용 설치 확인: EOD20:05, main/controller/monitoring20:10, archive20:50, replay21:05, finalization21:55; widget timer20:10/machine timer21:15. 이후 자연 실행 성공을 이번 확인으로 대체하지 않는다.
- 16:59 배포 receipt는 [당일 checklist](../checklists/2026-09-07-stage2-todo-checklist.md)의 완료 기록으로만 인용했다. 위젯 배포/표식 전환 및 다음-session acceptance는 OPEN을 유지했다.

## 리뷰와 보완

1. 퇴역 LDM/greenfield와 Swing ON 설명, 6/4 clean 시작 시각, 5월 checklist pointer, 10~30%/옛 7개 수량 후보를 현행 기준과 분리·정정했다.
2. Surviving scalp-sim control tower 전체를 retired로 읽게 하던 traceability 문구를 실제 wrapper와 맞췄다. sim 신규 튜닝 작업은 열지 않았다.
3. 진단 수리 완료에 positive EV/all-horizon MFE/one-share promotion을 붙이지 않도록 하고, 코드 PASS·배포·자연/실수익을 분리했다.
4. 추천 전수 ledger에 code_patch/objective followup·검증되지 않은 already-implemented·비구현/권한 결손·이전 세대 removed 항목을 빠짐없이 분류하도록 보완했다.
5. 1차 검증의 trailing whitespace 및 table row 분리 오류를 수정했다. 링크 검증의 review-index census는 우선순위 표의 1~3이 아니라 실제 실행목록 §4만 읽도록 검증 범위를 정정했다.

## 검증

- 문서/parser targeted tests: `test_metric_decision_contract_docs.py`, `test_plan_rebase_qna_docs.py`, `test_sync_docs_backlog_to_project.py` **50 PASS**, 보완 후 재실행 **50 PASS**. 전체 runtime/전략 테스트 결과가 아니다.
- Print-only backlog parser PASS; 현행화 완료 항목과 기존 자연 OPEN owner를 분리해 인식한다. 외부 동기화는 하지 않았다.
- 변경 문서14개에서 추가/수정된 로컬 링크 target21개·anchor4개: 결손0. 실제 실행목록 §4의 index1~119 중복/누락0; 기존 자연 acceptance owner4개 OPEN 보존. 우선순위 표의 숫자는 review index가 아니다.
- 외부 skill의 quick_validate 및 UI YAML(명칭·설명 길이·명시 skill invocation) PASS. git diff --check PASS. 새 task mode·집계식·후행 순서·OFF/retired·권한 경계를 재리뷰했다.
- 실 provider·broker 호출, runtime test 전체, 비용 큰 운영 report 재생성, bot 재기동은 문서-only 범위라 실행하지 않는다. 경제성/자연 실행은 기존 OPEN owner가 소유한다.
- Project/Calendar sync·token 검사·commit/push는 수행하지 않는다. 원래 dirty cache와 자연 생성 report/runtime 파일을 보존한다. 작업 도중 추가된 widget runtime-verification 코드/테스트는 병행 변경이며 이 문서 검토의 구현·검증 실적에 포함하지 않았다.
