# 물타기 체결 복원·장후 결속·불타기 퇴역과 zero-base WS 진단 통합 배포 — 2026-09-29

## 통합 범위와 리뷰

- 요청 승인에 따라 [물타기 구현 리뷰](2026-09-29-avg-down-rebound-receipt-and-pyramid-retirement-implementation-review.md)의 A1–A4 작업과 `zero_base_discovery_source.py`/`zero_base_probe.py`의 WS 원천 진단 수정을 한 불변 릴리스로 묶었다. 다른 세션의 무관한 dirty 작업은 포함하지 않았다.
- 후보 릴리스의 첫 통합 회귀에서 실패 3건을 검토했다. 범위 밖 source-quality 테스트 기대값 2건은 후보에서 제외했다. 남은 1건은 계산 결과가 맞지만 마지막 이벤트를 잘못 가정한 테스트라 해당 stage를 직접 고르게 수정하고 재검토했다.
- 영향 13개 테스트 파일 **2,144 passed**; 공유 데이터/가상환경 연결 후 smoke **89 passed**. 변경 Python compile, `git diff --check`, 배포 wrapper `bash -n`, 문서 print-only parser(24개 작업, 현행 물타기 owner 1개) 통과. 기존 `pandas_ta` 경고 1건 외 실패는 없었다.

## 배포·재기동 영수증

| 항목 | 확인 결과 |
| --- | --- |
| 통합 불변 릴리스 | `/home/ubuntu/KORStockScan-runtime-releases/integrated-avgdown-zero-base-20260929-fb77a749`, commit `fb77a7494e7fbcd628c70036f26aad29de9102c1` |
| 이전 릴리스 | `zero-base-exact-flush-20260928-e4117982`, 이전 PID `1025608` |
| 선택 | `data/runtime/runtime_release_selection.json`가 2026-09-29 08:56:29 KST에 새 릴리스 선택. 이전 선택 백업은 `tmp/integrated-avgdown-zero-base-selection-before-20260929T085629.json` |
| 재기동 | `bash deploy/run_runtime_release.sh restart` 성공; 이전 PID 종료 후 새 Main PID `1149836` 기동 |
| 실제 소비 | 08:56:43 KST PID 영수증의 release root/commit과 `/proc/1149836/cwd`가 새 릴리스 `src`에 일치. `actual_pid_consumed=true` |
| 운영 확인 | 당일 bootstrap `status=pass`, PID·policy·dated override 검사 통과. release-set·cron 검사 통과. Main loop, 계좌/DB 동기화, Kiwoom WS 연결·로그인 및 첫 0D 수신 확인 |

## 자연 사용 경계

- 새 PID가 08:56:56 KST에 보유 `48376`의 `holding_buy_fill_receipt_v1` sidecar를 생성했다. 원천은 `legacy_path_vote_exact_buy_legs`, 최초 BUY 1주와 identity가 기록됐다. 이는 실제 PID의 과거 BUY 식별자 복원 사용 증거다. 계좌 수준 broker 대사나 신규 AVG_DOWN 주문·체결 증거는 아니다.
- 스캐너의 매수 가능 구간은 `08:03–08:40`, `09:03–15:10`, `16:00–19:40`이다. 08:56 재기동 직후에는 탐색 구간 밖이므로 새 PID의 zero-base discovery/probe 이벤트가 없는 것은 예정된 동작이다. 첫 09:03 이후 자연 주기를 별도로 확인한다.
- 자연 ADD 투표·주문·체결, 장후 완료·정확 비용 및 no-ADD 짝비교 증분 순익은 아직 수용하지 않았다. 이 단계의 성과 판정은 `pending`이다. 정책·provider·threshold·주문 수량은 배포 과정에서 수동 변경하지 않았다.

## 정규장 첫 자연 주기 관측 (09:03–09:09 KST)

- 첫 정규장 cycle(09:03:06)은 SOR/KRX+NXT 통합 `_AL` route의 KOSPI·KOSDAQ 1분 거래량 및 상승률 패널 4개를 수신해 337개 후보 generation을 갱신하고 12개 프로브를 요청했다. 09:03–09:07 다섯 cycle 중 09:05 KOSDAQ 거래량 패널 한 번만 `source_unavailable`이었으며, 같은 시각 공용 REST 읽기 제한으로 해당 `ka10023` 요청의 전송 전 보류가 기록됐다. 이후 `_AL` REG/REMOVE 및 정확한 `_AL` 0B/0D를 사용한 기계판정이 실제로 발생했다. 이는 정규장 경로가 작동한다는 증거이지 모든 후보의 WS 수신 성공 보증은 아니다.
- 09:08:39 시점 `zero_base_probe_result` 360건 중 `assessed` 86건(**23.9%**), `source_unavailable` 235건, `required_feature_insufficient` 39건이다. 그 시점 판정 86건은 `RECHECK` 59, `BLOCK` 27, `ENTER_NOW` 0이었다. 기존 Main loop의 감시 수는 1 수준이며 감시슬롯 상한이 이 구간의 판정 전 병목이라는 증거는 없다.
- 주요 판정 전 결손은 `route_snapshot_missing` 164건, WS 등록 로컬 future 3초 대기 초과 `ws_registration_timeout` 30건, `0B_age_exceeded` 17건, `0B_missing` 13건, 판정 직전 `0B_age_exceeded` 8건이다. `route_snapshot_missing`은 모두 정확한 `_AL` 0B/0D 수신 0건에서 3초 빈 수신 flush가 발생한 결과다. REG 전송 로그는 있으나 broker subscription ACK나 그 뒤 수신 부재의 원인을 증명하지 않는다. 최초 빈 수신 75개 종목 중 8개는 뒤 재시도에서 판정돼 일부 결손이 일시적임을 확인했다. 이 수치만으로 모든 미수신이 체결 부진 또는 대기시간 부족이라고 단정할 수 없다.
- 수신 뒤에도 `source_quality_blocked_before_assessment` 17건과 `tick_or_candle_missing` 15건이 남았다. 09:03–09:09 `KIWOOM_READ_TR_DEFERRED`는 전송 전 보류 23건(프로브 `ka10080` 15, `ka10003` 7, 거래량 패널 `ka10023` 1)이고 사유는 `shared_read_rate_wait_budget_exhausted`, 당시 유효 제한은 4회/초였다. 확인한 로그에는 broker 429가 없었다. 12개를 한 번에 청구하고 10초 간격으로 반복하는 패턴이 REG와 REST 읽기 버스트를 만든다는 것은 코드와 시계열의 **추론**이며, 한계 조정 전에는 분산 청구/재사용 실험이 필요하다.
- 09:08:59 durable discovery 장부 899행 중 312행은 정규장 비대상 프리마켓 `_NX`이고, 정규장 `_AL` 587행 중 349행은 아직 첫 claim도 받지 못했다. 이는 감시슬롯 899개가 아니라 후보 장부의 관측 대기다. `activity` 후보 판정은 82/255건(32.2%)인 반면 `gainers`는 4/105건(3.8%)이다. 상승률 단독 후보의 낮은 수신·판정 수율과 반복 재시도가 기계판정 비율을 낮추며, 신규 후보 증가 속도가 첫 claim 처리 속도를 앞섰다.

**판정:** 정규장 `_AL` 통합 경로와 신규 릴리스 PID 적용은 확인됐다. 기계판정 진입률은 낮고, 우선 병목은 빈 정확경로 WS 수신과 등록 대기, 다음은 REST 읽기 제한과 입력 부족이다. 후속 변경은 원천별 수율·등록 지연·REST 전송 전 보류를 같은 구간에서 재현해 검토해야 하며, stale/route/주문 안전장치는 유지한다.

## 첫 편입에서 발견한 venue 결함과 후속 수정

- 09:09:04 `005930`, 09:09:26 `095610`이 정규장 `_AL` 기계 `ENTER_NOW`를 받고 보유한 감시 record `48810`/`48811`로 편입됐다. 그러나 편입 처리자가 명시된 `KRX` venue와 `krx_nxt_integrated` **시세 경로**를 서로 다른 venue로 오인해 `UNKNOWN`으로 바꿨다. 두 record의 downstream에 `explicit_target_venue_missing`이 남았고 `095610`은 약 8초 뒤 `session_changed`로 감시 종료됐다. 이 두 record의 관측 이벤트에는 broker 수락/실제 제출 증거가 없다. 따라서 첫 릴리스의 정규장 downstream 정상 적용은 **실패**로 판정했다.
- `kiwoom_sniper_v2._scanner_runtime_target_venue_fields`에서 명시된 venue끼리 먼저 대사하고, 시세 경로는 명시 venue가 전혀 없을 때만 fallback으로 사용하도록 고쳤다. 정규장 `KRX` + `_AL` + `SOR` 및 프리마켓 `PREMARKET_KRX_LIKE` + `_NX` 회귀를 추가했다. 관련 venue/runtime 테스트 364개와 entry/queue/scale-in 회귀 1,216개 통과, Python compile·`git diff --check` 통과. broker route, 원천 신선도, 주문 안전장치는 변경하지 않았다.
- 후속 불변 릴리스 commit `d6bf529e93c116830411471dc34825997798b84a`를 09:15:16 KST 선택하고 09:16:18 KST에 재기동했다. 이전 PID `1149836` 종료, 새 PID `1161612`의 cwd/선택 릴리스·당일 bootstrap·release-set 검사 통과. WS 재연결·로그인과 `_AL` REG 및 첫 0D 수신을 확인했다.
- 수정 후 자연 편입 `338220`(09:18:21, record 48819), `001820`(09:19:25, 48820), `005930`(09:19:45, 48821) 3건 모두 편입·후속 평가 영수증에서 `effective_venue=KRX`, `market_session_bucket=krx_regular`, 원천 경로 `krx_nxt_integrated`를 유지했다. `_AL` 재등록도 관측했다. `session_changed` 감시 종료는 없었다. `338220`은 34초 뒤 강도 미달, `005930`은 11초 뒤 강도 미달, `001820`은 83초 뒤 진입 쿨다운으로 각각 `scalping_scanner_watch_eviction` 처리되어 슬롯 회수가 실제 작동했다. `001820`의 관측된 제출 시도 2건은 모두 `submit_call_broker_accepted=false`다. 이 영수증은 실제 체결이나 순익을 증명하지 않는다.
- 09:16:20–09:21:40 새 PID의 프로브 345건 중 78건(**22.6%**)만 기계판정됐고 `route_snapshot_missing`은 202건이다. **venue 복원 결함은 해소됐지만 판정 전 WS 수신 병목은 계속**된다. 이번 후속 릴리스는 대기시간·REST 제한·후보 우선순위를 조정하지 않았다.
