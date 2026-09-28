# S6 `DirectFamilySourceRepairScaleInSplit` — 추가매수 원천 계약

실행일: **2026-09-28 KST**. 범위: [S3 인계](2026-09-27-intraday-postclose-handoff-S3.md), [S3-EXIT-05 수리](2026-09-28-intraday-postclose-handoff-S6-S3-EXIT-05.md), [현재 체크리스트](../checklists/2026-09-28-stage2-todo-checklist.md)의 `DirectFamilySourceRepairScaleInSplit`. **판정: 장중 체결→보유 수량→fact 투영→`scale_in_split_order_plan` 직접 reader의 확인된 계약 결손을 작업본 fixture에서 수리했다. 자연 추가매수 경제성·독립 paired holdout은 표본 부족으로 열려 있다.** 정책·주문 동작·서비스·배포는 변경하지 않았다.

## dispatch·owner와 보존 원천

| 구간 | 확인한 생산자→artifact→첫 소비자 | 범위·상태 |
| --- | --- | --- |
| 장중 main real AVG_DOWN | `sniper_state_handlers`의 추가매수 판단·제출→`sniper_execution_receipts._handle_add_buy_execution`의 중복 제거/영속 `HoldingAddHistory`·`scale_in_executed`→`pipeline_events` | `record_id`·`position_episode_id`·`scale_in_decision_id`·order/execution·route/session·실제 제출 여부와 증분/누적 체결·보유 수량을 분리한다. `PYRAMID`는 퇴역, sim/probe·widget/episode/manual은 real main 모집단이 아니다. |
| 최초 장후 투영·평가 | `strategy_position_performance_report.sync_trade_performance_for_date`의 정확 날짜 fact-sync status 및 `scale_in_execution_projection`→`scale_in_split_order_plan.build_report`→`runtime_approval_summary` | `deploy/run_threshold_cycle_postclose.sh`가 플래그 기본 `true`일 때 모듈과 JSON·정책 파일을 직접 호출·대기한다. 선택 릴리스/과거 출력만으로 이번 작업본이나 자연 실행을 주장하지 않는다. |
| 9/23 보존 artifact | `scale_in_split_order_plan_2026-09-23.json` SHA-256 `d81847ae766463dff529ee89389d43312aabdec7f3a880731fe33735fca3b20a`; 당시 fact-sync status SHA-256 `c1088b7132d27a72ac9b323cdaa63ad1744c54f743a17f1b55457e95f3f721b6` | `daily_unique_attempt_count=0`, `skipped_no_applicable_fill`. DB 실제 체결 이력 원본 4건은 과거 날짜의 누적 inventory이고 9/23 신규 attempt 4건이 아니다. 3건은 요청수량 1, 4건은 당시 frozen anchor에서 market-like로 제외되며 두 제외 집합은 겹친다. 적격 0, 완료·비용 평가 0. 당시 입력은 `actual_execution_db_inventory`만 읽어 raw bytes 0; 원천 모집단 전수검증 증거가 아니다. |

9/23 압축 pipeline 원천은 437,234,985 byte다. 해당 report와 fact-sync status를 재작성하지 않았고 과거 source generation, 체결 ID 또는 실제 비용을 소급 생성하지 않았다. `evaluation_state.actual_completed_receipt_count=4`와 `daily_unique_attempt_count=0`은 **다른 범위**다. 과거 누적 fill 4건의 terminal clock 결손 2건도 그대로 유지한다.

## 실패 재현과 수리 owner

| 재현된 결손 | 실패 fixture→작업본 수리·닫힘 |
| --- | --- |
| 체결 증분과 보유 수량 불일치가 경제성 연결 통과 | `2026-09-28` full-fill fixture에서 보유 증가량 3·체결 2여도 기존 reader는 `real_outcome_joined=true`; 최초 회귀는 `pre_fill_buy_qty` 투영 누락으로 실패했다. `sniper_execution_receipts.py`가 체결 전후 보유 수량을 관측 필드로 발행하고 `scale_in_split_order_plan.py`가 두 필드·결정 ID를 투영한다. 각 fill의 `post-pre=fill_qty`와 연속 partial fill의 수량 연결을 확인하며 누락·불일치는 `missing_position_quantity_receipt`/`position_quantity_mismatch`로 경제성 분모에서 제외한다. 9/28 이전 영수증에는 `legacy_unobserved`로 표시해 새 필드를 소급 요구하지 않는다. |
| 최초 reader가 다른 날짜·충돌 중복·손상 원천을 조용히 수용 | fact 투영 행의 날짜·시각·record·symbol·order/execution identity와 서명된 catalog/projection SHA를 대사한다. 같은 행 중복은 한 번만 보존하고 내용이 다른 동일 identity는 거절한다. 잘못된 투영 계약을 raw fallback으로 넘기지 않는다. 작은 fallback 원천은 strict JSONL reader로 검사한다. missing 원천, 손상, 다른 날짜, valid-empty, late partition의 투영 부재를 각각 재현했다. late 또는 압축 대용량 원천은 서명된 producer 투영을 요구해 무제한 raw replay를 하지 않는다. |
| fact catalog 재생성 뒤 과거 평가 재사용 | 같은 투영 행에서 catalog SHA만 바꾼 fixture가 기존에는 `skipped_unchanged_filled_outcome`이었다. 평가 버전에 fill/source·sell 날짜의 fact catalog 세대 SHA를 포함해 새 세대는 다시 평가하고, 동일 세대는 기존 중복 실행 방지를 유지한다. |
| terminal·비용 의미 혼합 | full BUY fill이라도 SELL terminal clock·lot 수량과 직접 영수증 조건이 없으면 `real_outcome_joined=false`로 둔다. broker 실제 과금 원천은 현재 이 묶음에 없으므로 `broker_actual_cost_krw`·`broker_actual_realized_pnl_krw`는 `null`이다. 기존 비교 모델은 `fixed_comparison_cost_model`로만 해석하며 이를 broker 실현손익으로 승격하지 않는다. |

## 분모·source quality·닫힘

새 fixture의 기본 full attempt 1건은 원본/투영 1·유효 수량 1·비용 후 **실제** 손익 미관측 1이다. 같은 fixture에서 보유 수량 불일치 1 또는 receipt 필드 누락 1은 경제성 유효 0·격리 1, 두 부분체결을 가진 하나의 attempt는 체결 이벤트 2·attempt 1로 검증했다. 투영의 완전 동일 중복 2행은 raw 2·유효 1·중복 제외 1이고, 같은 identity의 값 충돌 2행은 원천 계약 거절이다. 작은 원천 valid-empty는 raw/유효 0으로, missing·손상은 `valid-empty`가 아닌 실패로 구분한다. 9/23의 0 attempt와 이 fixture의 가상 1 attempt는 합산하지 않는다.

자가 리뷰에서 부분체결 각각의 수량 증가·연속성, 구세대 catalog 재사용, SELL lot/clock의 분모 과대계상, late 파일을 fallback에서 놓치는 문제를 추가로 찾아 보완했다. **검토한 이 묶음의 미해결 코드 결함은 0**이다. 다음 자연 source date에는 원본 real AVG_DOWN 판정·제출·체결 전량과 `HoldingAddHistory`→fact-sync status의 source generation/catalog SHA→첫 평가 attempt·owner·수량을 양방향 대사하고, 격리·미관측과 valid-empty를 따로 확인한다. 정확 terminal·broker 실제 비용·독립 paired holdout 없이는 수익성 또는 정책 승인으로 닫지 않는다.

잔여 원천 한계: 9/23 보존 영수증에는 새 증분 보유 필드와 account 원천이 없다. 새 필드가 실제 main PID에서 나오는지와 owner/account·route/session의 완전한 직접 결속은 다음 자연 체결에서 확인한다. 없는 account나 비용을 fixture의 값으로 보충하지 않는다. fact producer의 source generation 영수증은 catalog SHA에 묶였지만, 이 작업에서는 437MB 압축 raw 전체를 다시 읽어 물리 원천의 현재성을 주장하지 않았다.

## 검증·상태 인계

- 실패 회귀를 먼저 실행해 `pre_fill_buy_qty` 투영 누락, missing/손상 원천의 빈 입력 전환, catalog 재작성 뒤 과거 평가 재사용을 확인했다. 압축본만 있을 때는 검증된 fact 투영을 요구하는 fixture도 통과했다. 수리·재리뷰 후 `test_scale_in_split_order_plan`·`runtime_approval_summary`·`strategy_position_performance_report` **134 passed**, producer 연관 선택 회귀 **907 passed**. 변경 Python/test `py_compile`, `git diff --check` 통과. shell wrapper 변경이 없어 `bash -n`/shell 계약 검사는 비대상이다.
- Ruff 검사 대상 전체에는 기존 진단 41건이 남지만 **이번 변경 줄의 진단 0건**이다. 보고서 링크 3개 모두 유효하고 current checklist owner 및 print-only parser(`count=32`)를 확인했다. Project/Calendar 외부 동기화는 실행하지 않았다.
- 2026-09-28 조회 시 선택 포인터는 `30e66ae584a78911211d461483c01ecf03f6887c`/`full-workspace-20260928-30e66ae5`이며 포인터에는 기존 PID 수용 영수증이 있다. **이번 S6 수정은 미커밋 작업본이므로 그 선택 릴리스·PID의 소비 증거가 아니다.** 별도 세션의 미커밋 변경과 릴리스는 보존한다.
- `S5-FIN-05`는 새 자연 source date의 조건부 재현, 전체 데이터·성능·terminal은 S7, 릴리스·PREOPEN·이번 수정의 실제 PID 소비는 S8에 남긴다. Kiwoom API/파서·정책·수량·timeout·서비스·provider·threshold·실주문·취소·배포·정규 장후작업·PREOPEN은 변경하거나 실행하지 않았다.
