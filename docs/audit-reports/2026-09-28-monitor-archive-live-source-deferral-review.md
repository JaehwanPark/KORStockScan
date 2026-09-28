# 15:47 모니터 아카이브의 활성 pipeline 원천 경합 — 2026-09-28

## 원인과 영향

Main PID `688047`의 15:45 예약 `generate_monitor_archive_job`가 모니터 스냅샷과 로그 보존보다 먼저 `sync_trade_performance_for_date(2026-09-28)`를 실행했다. 15:47:23 `strategy_position_fact_sync_2026-09-28.status.json`은 `source_blocked`, `consumer_ready=false`, `issues=[scanner_pipeline_source_invalid:jsonl_artifact_changed_during_read:...pipeline_events_2026-09-28.jsonl]`, artifact SHA `b81d32cf185476bc63ce85226376ceb5b2b348571503bfa041a919ae98543d0d`를 기록했다. 당일 원파일은 약 3.61GB/237,780행이며 15:50–15:52 사이에도 늘었다. strict 독자는 파일의 전체 세대가 읽는 동안 바뀌면 거부하는 계약이다. 이는 실제 활성 append 경합이며 오류를 정상 source 또는 수익 0으로 치환할 수 없다. fact sync가 먼저 예외를 낸 탓에 독립적인 모니터 스냅샷·로그 아카이브도 시작하지 못했다. 실패 영수증은 보존한다.

## 수정과 권한

15:45 모니터 예약 작업은 스냅샷·로그 보존만 수행하고 `performance_sync={status:deferred_to_postclose, owner:threshold_cycle_postclose, reason:live_pipeline_source_unsealed}`를 반환한다. 정규 20:10 장후 `deploy/run_threshold_cycle_postclose.sh`의 정확 fact sync·영수증 검증은 그대로 유지한다. strict JSONL 독자, DB 쓰기 문턱, 비용·완료 census, postclose 실패 판정은 완화하지 않는다. 20:10 이후 실제 원천 세대 안정성은 별도 자연 실행 영수증으로 확인한다.

영향 테스트는 bot_main의 15:45 경로에서 fact sync를 호출하지 않아도 스냅샷/아카이브가 실행되고 명시적 defer를 반환함을 검증한다. `test_bot_main_scheduler.py`, `test_strategy_position_performance_report.py`, `test_verify_threshold_cycle_postclose_chain.py` 53건이 1차 통과했다. 확장 검증에서 기존 릴리스도 실패하던 `test_bot_main_import.py`의 퇴역 환경변수 기대 2건을 현재 namespace 제거 계약으로 수정했다. 최종 영향 회귀 71건, Python compile, `git diff --check`, 문서 print-only parser를 통과했다. 실제 3.61GB 원파일 재스캔이나 수익성 재생은 실행하지 않았다.

## 15:56 KST 배포·재기동 영수증

- 코드·체크리스트·리뷰 문서 커밋 `50f914502fe5ba6edc7a7fa42085be8215cef81a`를 불변 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/integrated-all-work-20260928-factsync-50f91450`로 선택했다. 이전 선택 포인터 백업은 `tmp/factsync-selection-before-deploy-20260928T155628.json`이며 이전 통합 릴리스 `d8aa4a64`는 복구 지점으로 보존했다.
- 릴리스 경로에서 71개 영향 테스트 통과, 런타임 소스 clean. 정상 재기동한 Main PID `694346`의 cwd는 선택 릴리스 `src`, `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=false`, `KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED=true`이다. 15:56:35 KST 정확 날짜 정책 handoff PASS, release-set PASS·124 owner 대사 및 선택 Main PID 결속 PASS를 확인했다.
- 15:45 예약은 이미 지난 상태이므로 새 코드의 실제 다음 예약 실행은 미관측이다. 15:47의 `source_blocked` 영수증을 성공으로 덮지 않았다. 20:10 장후 정확 fact sync의 새 terminal/status·완료 census/비용과 다음 15:45 스냅샷·로그 보존은 각각 자연 실행에서 확인한다.
