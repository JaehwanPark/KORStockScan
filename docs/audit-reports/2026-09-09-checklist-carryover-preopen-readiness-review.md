# 9/9 미완료 checklist 이관·장전 실행 준비 리뷰

기준 시각: `2026-09-09 00:52 KST`. 장후 source date는 `2026-09-08`, 다음 정규 실행일은 `2026-09-09`다.

## 판정과 변경 범위

사용자의 `다음액션 실행 후 코드리뷰` 요청에 따라 앞서 확인한 누락 owner6개를 이관하고, 승인된 TYM·SK이터닉스의 다음 정규 실행 경로와 필수 evidence를 점검했다. `$korstockscan-review-gate`의 구현→리뷰→보완→재검증을 적용했다. 이번 변경은 전일/당일 checklist와 이 기록에 한정하며 Python·wrapper·cron·systemd·baseline 문서는 수정하지 않았다. 기존 dirty 변경은 보존했다.

이관/준비 점검은 완료이며 해당 검토 범위 미해결 finding0이다. 실제 PREOPEN 정책 선택·PID 소비·submit drought 해소·비용 차감 순익은 완료가 아니며 기존 OPEN owner에 남긴다. 미래 작업을 현재 실행하거나 원천/경제성 차단을 해제하지 않는다.

## 이관 결함과 보완

`sync_docs_backlog_to_project.parse_checklist_tasks`는 현재 날짜보다 과거인 checklist 파일을 기본 입력에서 제외한다. 지난 파일의 미래 Due 또는 본문 링크만으로 오늘 executable task가 되지 않는다. 이는 기존 parser 계약이며, 원인은 남은 OPEN owner의 이관 누락이다. 과거 체크박스를 무차별 되살리는 parser 변경은 하지 않았다.

| stable ID | 현재 파일의 Due / TimeWindow | 남은 확인 |
| --- | --- | --- |
| OperatorPolicySuccessionAcceptance0908 | 9/9 · 07:35~08:45 | 정규 PREOPEN·25개 lock 승계/유지·receipt, first-use 표본 guard |
| DailyThresholdNaturalAcceptance0908 | 9/9 · 20:10~21:55 | 장전 선행 receipt 이후 새 source·PID·비용 순익 |
| EntryRecheckNaturalAttribution0907 | 9/9 · 20:10~21:50 | 장전 선택 이후 동일 scope funnel·exact3거래일 controller·실제 귀속 |
| ScannerLookupAttentionNaturalEvidence0908 | 9/9 · 20:10~20:40 | 장전 receipt 이후 scanner→runtime→R6·새 report와 경제성 |
| SniperMarketCloseHeartbeatNaturalAcceptance0909 | 9/9 · 20:00~20:10 | 정상 코드 로드 이후 자연 heartbeat→finally→detector |
| ScannerLookupAttentionCalendarMaintenance1002 | 10/2 · 20:10~21:55 | 20유효 source일 선도래 또는 10/2 유지·통합·폐기 판단 |

현재 owner는 [9/9 checklist 추가 이관 절](../checklists/2026-09-09-stage2-todo-checklist.md#전일-미완료-owner-추가-이관-99)이다. 이전 [9/8 checklist](../checklists/2026-09-08-stage2-todo-checklist.md)의 체크박스는 `[x]` 완료로 바꾸지 않고 비실행 이관 기록으로 변경했다. 기존 본문/Acceptance/역사6개를 그대로 보존하고 오늘 원천 확인 순서를 별도로 추가했다. 기존 Due가9/8인3개는 다음 자연 수용을9/9로 이어갔으며 원래 시각/원천을 새 성공으로 재라벨링하지 않았다. 나머지3개는 원래 Due를 유지했다.

6개는 모두 현재 `not_yet_due`이며 장전 선행 확인 시각은 각 본문에 명시했다. 이미 종료한9/8 진단과 미완료 자연 수용은 독립이다. 10/2 항목은 미래 일정으로 유지하며 먼저 도래하는20유효 source일 trigger를 제거하지 않았다.

## 승인 profile 실행 준비

설치된 두 live service의 `WorkingDirectory=/home/ubuntu/KORStockScan`, `ExecStart=deploy/run_low_price_two_leg_live.sh <profile>`와 preflight `Requires/After`를 확인했다. preflight wrapper는 기존 policy_apply mutex·exact-date apply·main-bot-active gate를 사용하고 live wrapper는 프로젝트 `.venv`의 `src.trading.low_price_two_leg.service`로 연결된다. 즉 현재 로컬 실행 경로의 코드/파일 존재를 확인했으며, 새 PID의 실제 소비나 다른 배포처 반영을 주장하지 않는다.

- TYM 기존 timer: preflight09:05 / live09:09.
- SK이터닉스 오전후반 기존 timer: preflight10:40 / live10:44.
- 4개 모두 `enabled/active`, 다음 실행일9/9. 서비스의 과거 `Result=success`는9/8 실행 근거이며9/9 성공이 아니다.
- [승인 원장](2026-09-09-widget-episode-approved-implementation-ledger.json)의 code/terminal byte hash8개가 실제 파일과 일치했다. 필수 [승인 evidence](2026-09-08-low-price-recommendation-apply-evidence.json)와 승인 원장2개가 `.gitignore`의 정확한 예외에 포함되는 것을 확인했다. 커밋/푸시는 하지 않았다.
- 현재 후보를 읽는 `build_applied_policy(target_date=2026-09-09)` 메모리 검증은 `candidate_validated_profile_revision_applied`, validator PASS, mutation0, policy hash `36a38b1e3ad6015388966cff9e1606f55cebc78d478f6284871d80a23494f3df`다. 두 profile의 research evidence validator도 ready이며 실제9/9 applied 파일은 아직 없다. 이 preview는 정책 publish가 아니다.
- widget9/9 policy byte hash `2f337b7341d8460614464adcb84cc0065110e1c4ad48d9b623f87f25cf76acb4`와 로더의080220 단독 반환을 확인했다. 실제9/9 PID 소비는 미확인이다.

기존 profile56/runtime eligible53/quarantine3, 20주·10주씩 두 leg와 승인 대상 밖 actual policy 보존 계약을 회귀 검증했다. 신규 추천·profile·권한은 추가하지 않았다. 영원무역/두산의 경제성 미달이나 source gap을 승인으로 바꾸지 않는다. 후속 실행/자연 수용은 [WidgetEpisodeRecommendationApplyAcceptance0908](../checklists/2026-09-09-stage2-todo-checklist.md)에 기록했다.

## 반복 리뷰·검증

1. 이관 전 parser33개 중 해당6개가0개임을 확인했다. 수정 후 전체39개·오늘 checklist OPEN23개이며 해당6개는 각각1개로 파싱된다. ID 유일성, 올바른 source path/Due, 과거 OPEN 제거를 assertion으로 검증했다.
2. 기존6개 본문/Acceptance/과거 이력이 전일과 당일 파일에 그대로 남음을 수정 전 snapshot과 대조했다. source marker는 두 checklist 모두 변경하지 않았다.
3. builder의 `_existing_manual_task_ids`가6개를 인식하고 `_upsert_auto_block` 후 수동 영역이 그대로 보존됨을 파일을 쓰지 않고 검증했다. 상대 Markdown 문서 링크도 존재한다.
4. `test_sync_docs_backlog_to_project.py`, `test_build_next_stage2_checklist.py`, `test_low_price_recommendation_revision_20260909.py`, `test_low_price_recommendation_revision_20260908.py`, `test_low_price_two_leg.py`, `test_widget_symbol_runtime_policy.py`: **318 passed**. 실제 broker/Provider 호출은 하지 않았다.
5. 관련 Python compile, 두 low-price wrapper의 `bash -n`, `git diff --check`, print-only parser를 통과했다. source8의 `verify_summary_handoff`를 읽기 전용으로 재실행해 tower/checklist PASS·issues0을 확인했다.
6. 최종 링크 점검에서 source9/9의 source-quality audit/workorder/EV/verifier4개는 예약 전 미발행 링크로 분리했다. 모든 JSON 링크가 지금 존재해야 한다는 검사 전제를 바로잡고, 문서·현재 필수 evidence 존재 및 source9/8 handoff 검사를 재통과했다. 미래 산출물을 생성하거나 missing failure로 처리하지 않았다.

검토 결과는 이관 문서·직접 parser/builder/summary consumer 및 승인 profile의 실행 준비 경로에 한정한다. 무관한 저장소 변경 전체의 finding0을 주장하지 않는다. 코드 추가 수리나 비용 큰 report 재생성은 필요하지 않았다.

## 운영 상태와 남은 경계

9/8 strict verifier와 controller는 원래 **9/9 00:27:14** terminal/hash를 유지한다. 이번 읽기 전용 handoff 검증은 새 controller/strict CLI 실행이나 finalization 성공이 아니다. source9/8을 소비하는 오늘 checklist의 AUTO 블록과 요약 원천은 변경하지 않았으므로 verifier/controller/cleanup/detector를 재실행하지 않았다. 전일 파일 AUTO 영역 안의3개 OPEN도 이관 기록으로 바뀌었지만 그 파일의 source9/7 marker·원천은 그대로 보존했다. 실행 중인 관련 postclose wrapper도 관측되지 않았다.

이번 작업의 주문·취소·policy/env/lock 작성·매매 process 재기동·예약 변경·외부 sync는0이다. 다음07:35 정기 PREOPEN부터 기존 owner의 원천/선택/receipt를 확인하며 해당 승인/안전 guard를 유지한다. main 증거 차단8건과 실제 drought/경제성 잔여는 기존 ledger와 OPEN acceptance에 남는다. Project/Calendar sync는 당일 checklist의 표준 명령으로 사용자가 수행한다.
