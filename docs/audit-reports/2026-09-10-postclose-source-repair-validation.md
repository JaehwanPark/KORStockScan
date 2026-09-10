# 9/10 장후 재개 — source-only 수리·검증 근거

대상 source date `2026-09-10`. 22:53:16 KST부터 기존 모니터링을 이어받았다. 이 문서는 처리 companion의 비순환 검증 근거이며 최종 운영 시각은 별도 재개 리뷰에 기록한다.

## 수리·운영 경계

- 수리 tree: `/home/ubuntu/KORStockScan-runtime-releases/review-postclose-source-paths-20260910`, branch `fix/postclose-source-paths-20260910`, commit `a023ca6a`. 기존 검토 `5104a5c0` 위의 세 가지 보완이다. 공통 선택 `b665e0a3`와 별도 machine 선택 `273807e3`는 변경하지 않았다.
- `deploy/run_threshold_cycle_postclose.sh`: WS finalization의 명시적 종목 master 경로에서 top-level 공유 data mount만 canonical 경로로 결속한다. 하위 파일/디렉터리 no-follow, master 본문 hash·effective date·정식 종목 검증을 유지한다. 원 master SHA256 `5b64313bab84d48ca31b0b1ee4d6114b2541f255ecd4ff786e5bb0b08e2473d7`는 canonical reader에서 2,549종목 verified다. release 경로 오류를 시장 전체 미관측으로 취급하던 최초 결손을 수리한다.
- `deploy/run_logs_rotation_cleanup_cron.sh`: data/logs/tmp가 공유 symlink인 경우 schema·workspace·선택 root/HEAD·세 mount 일치로만 canonical state root를 선택한다. 코드 root는 기존 별도 변수를 유지한다. lock child symlink는 계속 거절하며 selector 불일치는 최상단에서 실패한다. Python 최적화에도 사라지지 않는 명시적 검사다. raw purge/unknown-writer 삭제 권한을 추가하지 않았다.
- `src/engine/build_code_improvement_workorder.py`: 기존 `entry_recheck_drought_controller/natural_acceptance_pending/maintenance_review/defer_evidence`의 두 비권한 필드가 확인된 행은 반복 횟수만으로 implement-now에 재승격하지 않는다. `source_gap` 반례의 반복 escalation은 유지한다. 초기 ON·경제성·maintenance bound 계약을 변경하지 않았다.
- 실제 cleanup 복구는 수정 배포 없이 원 선택 코드의 기존 `PROJECT_DIR=canonical workspace`/`KORSTOCKSCAN_CODE_ROOT=selected release` 분리 기능을 단회 실행했다. 실행기 증거는 `tmp/postclose-monitoring-20260910/resume-2253/run-selected-cleanup.sh`다. root/HEAD/selector/mount/clean을 검사하고 기존 finalization의 cleanup override로만 연결했다. 배포 원장·cron·매매 PID·정책/env·Provider·주문 변경은 없다.

## 검증·재리뷰

- 수리 관련 고유 270 tests의 최종 코드 검증: 마지막 재검증 191 PASS와 변경 영향 없는 앞선 79 PASS. 전수 중간 실행의 268 PASS/1 FAIL은 별도 보존했다. 한 FAIL은 테스트 shell 실행 도중 이 세션이 파일 길이를 바꿔 발생한 parser offset 오류였다. 수정 파일을 고정한 뒤 cleanup/workorder와 신규 mount-reader 검사를 모두 다시 실행해 191 PASS로 닫았다. 운영 선택 wrapper는 수정하지 않았다.
- 최초 원 선택 cleanup/finalization 65 PASS는 원 코드·기존 실행 옵션 점검이며 위 270개와 고유 합계로 합산하지 않는다.
- 새 회귀는 유효 선택 mount, 잘못된 commit, 하위 lock symlink 보존, master top-level mount 및 하위 artifact symlink 거절, natural acceptance 반복과 실제 source gap의 차이를 검증한다. Ruff/Black·Python compile·두 shell의 bash -n·git diff --check PASS.
- producer→직접 reader→workorder→runtime summary→strict handoff, silent-fail·원본 hash/date·retired/live authority 경계를 재리뷰했다. 이 세 가지 코드 수리 범위의 미해결 P0~P2 finding 0이다. source-only 재생성 후 consumer/current generation 확인은 재개 리뷰에서 별도로 기록한다. 배포·자연 표본·경제성 수용을 코드 PASS로 대체하지 않는다.

## Native 요청의 남은 직접 근거

| Native ID | 최초 결손 및 유지할 수용조건 | 다음 owner |
| --- | --- | --- |
| `order_entry-prompt-revision-bed8f761b614ab7c301f47d0` | KRX exact parent 3개(452450/004090/032820)의 `exact_cost_aware_label_parent_missing`. 영어 appendix/기존 parent hash는 있으나 같은 부모의 검증 비용 입력이 없다. 비용을 0으로 만들거나 입력 없는 반복 Provider 평가를 하지 않는다. | 다음 Main AI source/RuntimeEnv·CodeImprovement owner |
| `order_entry-prompt-revision-bd884523626671f7b54eab4d` | NXT 488280 exact parent 2개의 같은 비용 label 결손. 1789026706633 parent는 ask-depletion sidecar source-quality invalid도 명시됐다. 기존 prompt·당일 선택과 cohort를 보존한다. | 다음 Main AI source/RuntimeEnv·CodeImprovement owner |
| `order_microstructure_v3_evaluation_anchor_contract_missing` | 024060, 09:51:15.309349, evaluation `d235934e11f043eb853ce32e032d1700`의 record_id null. 시각/UUID만으로 record·real/sim identity를 발명하지 않는다. | 다음 Main AI/원천 품질 owner |
| `order_microstructure_v3_evaluation_venue_missing_or_conflicting` | 108 evaluations에 micro 원천 venue 결손. 예 459510/record42160/08:18:01.726430의 effective PREMARKET 값으로 원 micro route를 추정하지 않는다. | 다음 Main AI/원천 품질 owner |
| `order_observation_source_quality_unknown_token_provenance_gap` | avg-down market unavailable 1; scanner source-fetch JSON UNKNOWN 2553 및 venue/effective 각10; candidate-pool JSON UNKNOWN 281; retired stat prior neutral/unknown19. upstream venue/의미 증거 없이 정상 라벨로 치환하지 않는다. raw 한 행 격리/hard0/unknown4의 원 consumer를 보존한다. | PostcloseSourceQualityGateReview0911 |
| `order_pipeline_event_compaction_v2_shadow` | raw179568/producer178681, 차이887. completed common minute/identity 불일치, flush deadline20:01:59.809962 종료·pending false다. 원 producer flush/원천이 없는 과거를 raw-derived copy로 덮지 않으며 suppression을 활성화하지 않는다. | CodeImprovementWorkorderReview0911 |
| `order_scanner_scan_generation_conservation_gap` | `SCANGEN-994933-1789028295689-39388329775646`, ranked301/terminal291·missing rank10. 원 PID 종료/후속 재기동 전의 당시 receipt 결손은 보고서 재생성으로 합성하지 않는다. 새 exact generation 전수 terminal이 필요하다. | RuntimeEnvIntradayObserve0911 |
| `order_ws_decision_stage_stale_backoff_attribution` | 35365 stale/backoff에서 repair state not_observed25480. snapshot/source→repair→queue/eviction의 exact receipt 결손은 개수만으로 외부/내부 원인 귀속할 수 없다. | RuntimeEnvIntradayObserve0911 |
| `order_ws_subscription_stale_repair_observability` | pipeline subscription stale1191과 장후 snapshot recommended0은 서로 다른 시각/분모다. 원 REMOVE/REG/cooldown/receipt 없는 row를 야간 재구독으로 완료하지 않는다. | RuntimeEnvIntradayObserve0911 |
| `order_ws_total_stale_escalation` | both stale1191 중 repair state1172 미관측, persistent18/reissued1. 당시 exact receipt·주문 freshness 경계를 보존한다. | RuntimeEnvIntradayObserve0911 |
| `order_ws_trade_tick_quiet_low_liquidity_classification` | quiet3713: signed-tape-only cumulative volume missing1806, cumulative volume missing1907. 당시 ordered cumulative-volume 근거 없이 저유동성 정상 또는 WS 장애로 단정하지 않는다. | RuntimeEnvIntradayObserve0911 |
| `order_scanner_eligible_no_heavy_closed_loop` | eligible-no-heavy46의 원 consumer/미관측을 분리한다. official-master 경로 수리는 현재 세대에서 검증하고, 남은 exact BBO/terminal receipt 결손은 같은날 raw 합성 없이 유지한다. | RuntimeEnvIntradayObserve0911 |
| `order_scanner_funnel_executable_bbo_join` | master reader 결손을 먼저 복구한다. bounded observer의 미수집/지연/불완전 BBO는 독립 모집단 recall/실체결 EV가 아니다. 수리 후 직접 보고서의 잔여 원천/경제성 분모를 그대로 인계한다. | RuntimeEnvIntradayObserve0911 |
| `order_pattern_lab_ai_review_ai_review_followup` | source가 직접 intended consumer를 발급하지 않아 intake가 차단했다. review artifact 없이 lab/provider 실행을 추정하지 않는다. | CodeImprovementWorkorderReview0911 |
| `order_pattern_lab_currentness_audit_scalping_ldm_threshold_reentry_sources` | intended consumer 결손. 퇴역 LDM을 복원하지 않고 생존 threshold feedback의 명시적 consumer/acceptance가 필요하다. | CodeImprovementWorkorderReview0911 |

각 차단은 구현 완료가 아니다. source 수리에 양수 EV·실체결·추가 승격 floor를 요구한 것도 아니다. 현재 source/row hash와 final disposition은 같은 generation companion에 결속하며, 원본 67행과 후속 pass를 별개 고유 작업으로 더하지 않는다.
