# Main 최신 릴리스·PID 19:30까지 가동 점검 — 2026-10-08

판정: **가동·정책 인계 PASS, 자연 제출 연결은 미검증 구간이 남는다.** 요청 수신 후 19:05~19:30 KST 동안 선택 릴리스와 실제 PID를 추적했다. 마지막 실측은 19:30:09이며 관찰 중 릴리스 변경·Main 재기동·중복 Main PID는 발견되지 않았다. 봇·정책·환경·주문 경로를 변경하지 않았고, 모니터가 수행한 Provider·broker 호출은 0이다.

현재 owner는 당일 체크리스트의 `DirectFamilySourceRepairMainMechanisticEntry`다. 체크리스트와 봉인된 handoff는 수정하지 않았다. [이전 16:52 점검](main-pid-241227-auxiliary-compact-operating-status-2026-10-08.md)의 PID와 실패 상태는 당시 증거이며 이번 실행 상태와 구분한다.

## 1. 실행·정책 소비·인계

- 선택 릴리스: `/home/ubuntu/KORStockScan-runtime-releases/main-retired-postclose-cleanup-20261008-v1`.
- 실행 commit: `0c1f68968906395f12c121862876704afadc1e83`. 선택 시각 18:47:57, Main PID `381039`, start ticks `3597010`, 기동 약 18:48:04. 실제 cwd는 위 릴리스의 `src/`이며 selector의 실제 PID 영수증과 일치한다.
- 기계 bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`: 현재 PID의 128 경로 신규 소비와 `actual_pid_consumed=true`를 확인했다.
- 보조 overlay `b8e97475121038c21d1608f99530f1c740f696f4ba084d0cfd2f9b48c4961626`: 현재 PID 소비 영수증이 같은 overlay·release commit을 가리킨다. 발행 파일의 불변 `actual_pid_consumed=false`와 별도 PID 소비 영수증을 구분했다.
- current-PID bootstrap은 18:48:06 PASS다. 실제 선택 릴리스의 `intraday_release_handoff.verify`를 반복 실행한 결과 19:30에도 PASS / findings 0이다. 현행 체크리스트 SHA `4aee28ee1c0fa26d34d8f7f7ecac25432e6680ab226ec805c59b635bb11b48ed`는 handoff 봉인값과 일치한다.
- 작업본 HEAD `270e870340502e8a0b15eb547b90239d258343a6`는 후속 배포 기록 commit이다. 실행 commit 대비 `src/bin/scripts/config` 코드 diff는 없고, [직접 비교한 핵심 source 7개](../../data/report/auxiliary_compact_adoption/2026-10-08/operating-monitor-to-1930/code-alignment-summary.json)의 작업본·릴리스 바이트도 모두 일치한다.

## 2. 상시감시 5종목과 자연 판정

read-only DB에서 삼성·두산·HPSP·알테오젠·주성 모두 `KRX_NXT_AFTERMARKET / WATCHING`을 확인했다. ID는 각각 49157·49158·49159·49160·49161이고 `buy_qty=0`이다. Main heartbeat도 감시 5 / Main 보유 0이다. 이는 broker 전체 또는 수동·퇴역 owner의 잔여 수량이 flat이라는 증거가 아니다.

이전 HPSP·알테오젠·주성의 REGULAR 세대 잔류는 현재 AFTER 세대로 해소됐다. 현행 `main_fixed_watch._new_symbol_session_eligible`는 integrated REGULAR/AFTER를 기존 Main 세션 계약으로 편입하고 추가 당일 NXT 편입 증명은 NXT-only PRE에 한정한다. 당일 NXT eligibility 원천을 새로 채웠다는 의미는 아니며 실행 직전 quote·route 안전 확인은 별도다.

| 종목 | 현재 감시·평가 경로 | 현재 PID 자연 ENTER_NOW → AI 시도 | 이번 19:05 이후 신규 시도 |
| --- | --- | --- | --- |
| 삼성전자 005930 | AFTER / WATCHING, 반복 pipeline 관측 | bounded trace에서 미관측 | 0 |
| 두산에너빌리티 034020 | AFTER / WATCHING, 반복 pipeline 관측 | bounded trace에서 미관측 | 0 |
| HPSP 403870 | AFTER / WATCHING, 반복 pipeline 관측 | bounded trace에서 미관측 | 0 |
| 알테오젠 196170 | AFTER / WATCHING, 상세 기계·AI 도달 | 5시도: PASS 3 / transport timeout 2 | 5 |
| 주성엔지니어링 036930 | AFTER / WATCHING, 상세 기계·AI 도달 | 3시도: PASS 1 / transport timeout 2 | 0 |

위 8건은 현재 PID에서 보존된 실제 호출 시도 수이며, 독립 승리 기회·주문 수·승률의 분모가 아니다. 주성 3건은 18:55~19:02의 관찰 시작 전 baseline이고, 이번 창의 신규 5건은 알테오젠에서 발생했다. transport timeout을 AI veto 또는 손실로 집계하지 않는다. 마지막 AI 회로 상태는 enabled / 연속 실패 0이다.

반복 pipeline의 `blocked_vpw`·`blocked_strength_momentum`이라는 stage 이름만으로 실제 진입 차단을 단정하지 않았다. `gate_action=risk_context_only`와 `source_quality_block`을 구분했으며 실제 source block 사유에는 `trade_tick_quiet`, `extreme_sell_dominant`가 관측됐다. 희소 체결을 API 결함으로 단정하지 않는다.

새 compact-v2 wire는 삼성 AFTER와 비상시 PRE/AFTER의 4경로다. 이번 자연 호출은 주성·알테오젠의 기존 union `reversal_entry_geometry_v5` 경로였다. **새 4경로의 자연 v2 요청·응답 검증은 이번 창에서 미관측**이며 PID overlay 로드 성공으로 대체하지 않는다.

## 3. PASS 이후 제출 연결 — 남은 결손

현재 PID의 주문 physical API `kt10000/kt10001/kt10002` 시작 수는 0이고 submit guard 표본도 0이다. 감시 행은 WATCHING으로 유지됐다. 따라서 이번 창에서 자동 주문 제출은 관측되지 않았으나, AI trace의 `actual_order_submitted=false`만을 최종 주문 영수증으로 전용하지 않았다.

알테오젠 PASS 3건은 실제 AI 행동 BUY다. [정확 판정 ID·시계 요약](../../data/report/auxiliary_compact_adoption/2026-10-08/operating-monitor-to-1930/alteogen-decision-clock-summary.json)에서 원 신호의 5초 예산을 대조했다.

| 판정 시각 KST | evaluation attempt | AI 판정 시 원 예산 잔여 |
| --- | --- | --- |
| 19:15:27.735 | `aims-29c09add92d32848e9d9` | 약 0.739초 |
| 19:17:14.679 | `aims-d37f15a4907ddb798fad` | 약 −0.100초 |
| 19:18:48.134 | `aims-a2bf764066d21c596b7f` | 약 0.143초 |

직접 확인된 것은 응답 이후 Main 소비 여유가 매우 짧다는 점이다. 선택 릴리스의 `FixedWatchGeneration.from_claim`는 원 5초 예산 만료를 거절하고, caller `_resolve_scanner_async_entry_ai`는 late result를 배출한 뒤 `commit_rejected`를 반환하는 경로가 있다. **실제 PASS 3건의 최종 미소비·미제출 사유는 같은 trace ID의 소비·종료 영수증과 연결되지 않아 미확정**이다. 이 코드 경로를 원인 후보로 기록하되 모두 TTL 때문에 폐기됐다고 단정하지 않는다.

[bounded pipeline 요약](../../data/report/auxiliary_compact_adoption/2026-10-08/operating-monitor-to-1930/alteogen-pass-terminal-summary.json)의 19:15:38~19:19:58 suffix에는 19:17:33 timeout 시도의 `scanner_async_result_commit / commit_allowed`와 WAIT terminal이 같은 trace ID로 연결됐다. PASS 시도의 연결된 commit·terminal은 관측되지 않았다. 특히 첫 PASS는 해당 suffix 시작 전이므로 전체 경로 부재를 증명하지 않는다. 현재 PID Main commit metric은 3이며 성공 AI 응답 4와 같은 분모가 아니다.

다음 조치는 기존 Main 구현 owner에서 **native late-result 폐기의 exact attempt/trace/claim 사유 영수증을 보강하고, 준비·응답·Main 소비의 원 예산 배분을 점검**하는 것이다. closure는 자연 ENTER_NOW → PASS → 같은 claim의 commit 또는 명시적 reject terminal 연결과 주문 API 시도 대조다. 이번 모니터링에서 TTL·Provider timeout·매매 안전 조건을 변경하지 않았다.

## 4. 성능·health·디스크

- 마지막 retained 성능 snapshot은 19:29:19이며 warm loop 1,831회: p95 약 0.689초 / p99 약 2.030초, 최대 9.951초, 누적 5초 초과 2회다. 관찰 초기에도 2회여서 마지막 성능 영수증까지 추가 증가는 없다. 19:30 pipeline·health가 계속 갱신된 사실과 성능 영수증 시각을 구분한다. 원인 stack은 이번 창에서 확정하지 않았고 경제 효과나 전체 latency 개선율로 전용하지 않는다.
- preparation failure는 비어 있고 마지막 건강 점검의 process/thread·resource·artifact freshness·auth·log scanner·lock은 PASS다. 퇴역 owner 상태는 `retired_not_expected`다.
- overall health warning은 `log_rotation_cleanup`·`postclose_finalization`의 오전 06:50 cutoff 이후 recovered-late 2건이다. 현재 `strict_checklist_generation_stale` 또는 `finalization_chain_generation_changed` 실패는 없다. 이 저녁 관찰 결과로 다음 장후·장전 closure를 선행 인정하지 않는다.
- 19:30 실측 root disk 72% 사용, 여유 약 41GiB다. 모니터링은 작은 요약만 저장했고 대형 AI 비교 원장을 복제하거나 새 Provider 연구 호출을 만들지 않았다.

## 5. 증거 범위·검증·종료

[최종 상태](../../data/report/auxiliary_compact_adoption/2026-10-08/operating-monitor-to-1930/latest.json), [주기 관찰](../../data/report/auxiliary_compact_adoption/2026-10-08/operating-monitor-to-1930/observations.jsonl), [중복 제거된 자연 판정 요약](../../data/report/auxiliary_compact_adoption/2026-10-08/operating-monitor-to-1930/decision-summary.jsonl)을 보존한다. 주기 JSON은 19:11 이후이며 그 이전은 당일 19:05~19:11 직접 점검이다. 대형 입력은 매번 최대 16MiB suffix만 읽고 원본 전체 재스캔·복제는 하지 않았다. 이 범위를 모든 과거 기회나 전체 종목 평가의 완전 분모로 사용하지 않는다.

검증은 selector·실제 PID/cwd/start ticks, exact-date PID 영수증, 실제 릴리스 handoff 재검증, read-only DB, bounded trace/payload/pipeline, health·성능·physical REST 증거와 source 바이트 비교로 수행했다. 문서 링크, print-only parser의 현재 Main owner 1개, `git diff --check`를 확인했다. 매매 코드를 수정하지 않아 pytest/compile·Provider replay·장후 재생성·외부 sync·배포·재기동은 수행하지 않았다. 19:30 종료조건을 충족하여 이번 지속 모니터링은 종료한다. 기존 Main owner의 자연 제출 연결과 compact-v2 자연 호출 검증은 미완료로 유지한다.
