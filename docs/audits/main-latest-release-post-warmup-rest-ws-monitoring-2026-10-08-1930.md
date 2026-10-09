# 최신 Main 릴리스·PID 장중 지연 및 REST/WS 관측 — 2026-10-08 19:30

## 1. 범위와 결론

- 사용자 요청: 최신 선택 릴리스와 실제 PID를 19:30 KST까지 관측하고 기계평가·평가루프·REST/WS 잔여 병목을 진단한다. 초기 기동 워밍업 지연은 주 성능 평가에서 제외한다.
- 실시간 감시는 19:05부터 19:30까지다. 계수 비교의 정확한 시작/끝은 **2026-10-08T19:05:06.387245+09:00 → 2026-10-08T19:29:19.046089+09:00**다. 성능 로그는 약 60초 주기이므로 마지막 계수 이후 19:30까지를 계수로 보간하지 않는다. PID·WS·원문 캡처는 별도 경계 관측을 보존한다.
- **평가루프와 WS 잠금 개선은 현재 PID에서 관측된다.** 주 관측 창 1,103개 루프 중 5초 초과 0개, 2초 이하 1,093개(99.09%)다.
- **남은 REST 부담은 `kt00011` 무신호 사전 조회가 가장 크다.** 주 관측 창 물리 HTTP 시작 1,849회 중 1,403회(75.88%)다.
- **개별 신호의 5초 예산과 PASS 결과 소비 연결은 미완료다.** 빠른 평균 루프만으로 신호→준비→AI→Main 소비의 적시 완료가 입증되지는 않는다.
- 프로세스·정책·provider/broker·예약·환경·임계값·guard 변경은 0이다. 기존 dirty 작업본을 보존했다. 이 보고서와 `tmp` 관측 증거만 작성했다.

## 2. 최신 선택과 실제 소비

| 항목 | 확인 결과 |
|---|---|
| 선택 릴리스 | `main-retired-postclose-cleanup-20261008-v1` |
| commit | `0c1f68968906395f12c121862876704afadc1e83` |
| 실제 PID / start ticks | `381039` / `3597010` |
| 실제 cwd | `/home/ubuntu/KORStockScan-runtime-releases/main-retired-postclose-cleanup-20261008-v1/src` |
| 기계 bundle | `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689` |
| 보조 overlay | `b8e97475121038c21d1608f99530f1c740f696f4ba084d0cfd2f9b48c4961626` |
| 관측 중 selector/PID 조합 | 1개; 선택·실행 루트 일치 |

`runtime_release_selection.json`, `/proc/381039`, 기계/보조의 당일 `consumed/2026-10-08/381039.json`, 성능 로그 및 WS 생산자 PID를 각각 대조했다. 소비 영수증의 `pid_identity`가 같은 PID/start ticks/cwd다. 검토한 10개 코드 파일의 workspace와 실제 릴리스 바이트 해시도 모두 일치했다. selector 설정만으로 실제 소비를 추정하지 않았다.

## 3. 워밍업 제외와 루프 결과

재기동은 18:48:05다. 초기 복구·최초 캐시 충전 구간을 18:50:55 성능 스냅샷까지 분리했다. 초기 pipeline 복구 11.216초, 초기 추가 reader 5초 초과 1회, policy 준비 7.996초, 초기 긴 루프 2회는 아래 차분에 포함하지 않는다. 최초 루프 1.282초도 제외한다.

| 창 | 루프 수 | 5초 초과 | 2초 이하 | p95 | p99 |
|---|---:|---:|---:|---|---|
| 19:05:06~19:29:19 주 관측 | 1,103 | 0 | 1,093 / 99.09% | (0.5, 1]초 | (1.5, 2]초 |
| 18:50:55~19:29:19 워밍업 후 보조 창 | 1,749 | 0 | 1,732 / 99.03% | (0.5, 1]초 | (1.5, 2]초 |

구간 분위수는 누적 histogram의 정확한 차분과 nearest-rank로 계산했다. 실제 관측값을 구간 중앙값으로 대체하지 않았다. `loop_work`는 의도된 polling sleep을 제외한 작업시간이다. 현재 기본 sleep 1초는 **신호 전달 지연** 분석에는 포함해야 한다.

이전 PID 206123의 14:30~15:00 관측은 849루프·5초 초과 11개, p95 (2,3]초였다. 현재 창에서 지연 감소를 관측했지만 정규장/애프터마켓·신호 수·PID·릴리스가 달라 동일 부하의 인과 효과 비율로 선언하지 않는다.

## 4. 기계평가와 보조 결과

현재 PID의 워밍업 후 정확한 기계 캡처 10건: `{'ENTER_NOW': 8, 'RECHECK': 2}`. 각각 캡처의 attempt ID와 보조 trace를 연결했다. 주 관측 창의 ENTER_NOW는 5건, 보조 결과는 `{'not_evaluated_transport': 2, 'pass': 3}`다.

| 종목 | 정확한 평가 attempt | 신호→기계 캡처 | 보조 상태 | trace 시각 | durable outbox |
|---|---|---:|---|---|---|
| 036930 | `aims-7793fcc0b31449c3d864` | 2.223초 | pass | 18:55:49 | response_received |
| 036930 | `aims-caa38145e25109947075` | 2.005초 | not_evaluated_transport | 18:57:54 | transmission_uncertain |
| 036930 | `aims-dc8264684748b99c8a1d` | 2.646초 | not_evaluated_transport | 19:02:50 | transmission_uncertain |
| 196170 | `aims-594b8cbbba0ba418b46e` | 1.780초 | not_evaluated_transport | 19:14:57 | transmission_uncertain |
| 196170 | `aims-29c09add92d32848e9d9` | 1.835초 | pass | 19:15:27 | response_received |
| 196170 | `aims-d37f15a4907ddb798fad` | 1.919초 | pass | 19:17:14 | response_received |
| 196170 | `aims-7cdd7ef595b43d27a744` | 2.334초 | not_evaluated_transport | 19:17:33 | transmission_uncertain |
| 196170 | `aims-a2bf764066d21c596b7f` | 2.224초 | pass | 19:18:48 | response_received |

ENTER_NOW 8건은 주성 3건·알테오젠 5건이다. 누적 보조 PASS 4건·물리 응답 시간 초과 4건이다. 원문으로 PID/기계 캡처 연결을 확정하지 못한 별도 입력 거절 trace는 이 분모에 합치지 않았다.

RECHECK 2건은 주성 18:55:55와 알테오젠 19:14:41이다. `required_feature_current_price_stale`, `required_feature_provider_trade_late`, `required_feature_source_time_skew`, `required_feature_tape_stale`가 함께 기록됐으며 캡처의 체결 가격 나이는 각각 약 4.026초·4.715초다. 새 신호 당시 자료와 평가 시 자료를 구분해야 한다.

별도 탐색의 source-only 기계 캡처는 `{'BLOCK': 47}`다. 이 관측은 실주문 권한을 가진 Main 평가·보조 호출·주문 수의 분모가 아니다. 탐색 `ready`와 실제 claim도 각각 기록하되 차이를 자동으로 놓친 주문으로 계산하지 않는다.

## 5. 남은 병목: 신호별 시간 예산

| 단계 | 현재 PID 관측 수 | 최대 |
|---|---:|---:|
| native 확인→Main claim | 12 | 2.490초 |
| claim→기계판정 | 8 | 1.845초 |
| source 준비 | 12 | 1.307초 |
| capacity 준비 | 12 | 0.678초 |
| provider 물리 transport | 8 | 2.316초 |

서로 다른 건의 최대값을 합산하지 않는다. 각 캡처까지 신호 나이는 표와 같이 1.780~2.646초이며, timeout 4건의 실제 HTTP 예산은 각각 2.337초·1.309초·2.160초·1.876초였다. 19:17:33의 worker 전체 `ai_response_sec=3.326776`은 HTTP transport 시간과 다른 범위다. 네트워크 시간 초과와 원천/claim 무효를 혼합하지 않는다.

PASS trace 기록 당시 신호 나이는 약 4.876초·4.261초·5.100초·4.857초다. `decision_ts`는 함수 완료 시각이 아니므로 이것만으로 timely Main commit을 보장하지 않는다. 초기 첫 응답 처리의 `response_validate` 4.422초 이후 응답 3건은 모두 (0.25,0.5]초다. 최초 응답 시 trace ID 중복 방지의 `_load_seen`이 당시 약 416MB 일일 trace를 전체 JSON decode하는 코드가 확인됐다. **초기 첫 사용 비용의 유력 원인**이며 직접 하위 구간 계측이 없어 4.422초 전부를 단정하지 않는다. 이후 반복 지연으로 관측되지는 않았다.

성능 `main_commit`은 허용된 결과에만 기록된다. 현재 3건, 최대 0.016초다. 이 값은 모든 PASS의 commit 지연 분포가 아니다. 19:17:33 실제 commit 한 건은 transport 미평가 WAIT였고 `result_to_commit_sec=0.131786`이었다. 네 PASS의 durable outbox는 모두 `response_received`, `intent_assigned`는 미관측이다.

현재 outer loop는 fixed-watch 완료를 WATCHING handler에 맡기고, handler의 source gate는 완료 소비 전에 `return False`할 수 있다. 기본 1초 sleep도 남아 있다. 이 구조는 **PASS가 남은 원 claim 예산 안에 소비되는지 별도 검증할 지점**이다. 현재 증거만으로 네 PASS 모두의 정확한 탈락 원인을 확정하지 않는다. 원 claim+5초·quote/native/order guards를 유지한 채 completed/expired/rejected 결과별 terminal 소비 사유가 필요하다.

현재 AI 회로는 `enabled`, 연속 실패 0이다. 앞선 다른 PID의 비활성화 상태를 현재에 승계하지 않았다.

## 6. REST의 실제 부담과 WS 재사용

| API | owner | 요청 class | 물리 시작 수 |
|---|---|---|---:|
| kt00011 | `entry_capacity_prefetch` | source_only | 1,403 |
| ka10027 | `zero_base_discovery_panel` | source_only | 166 |
| ka10080 | `zero_base_machine_probe` | source_only | 73 |
| kt00005 | `kiwoom_utils.kt00005` | runtime_required | 64 |
| ka10023 | `zero_base_activity_panel` | source_only | 44 |
| ka10075 | `kiwoom_utils.ka10075` | runtime_required | 32 |
| kt00008 | `kiwoom_utils.kt00008` | runtime_required | 16 |
| kt00007 | `kiwoom_utils.kt00007` | runtime_required | 16 |
| ka10076 | `kiwoom_utils.ka10076` | runtime_required | 16 |
| ka10080 | `kiwoom_utils.ka10080` | runtime_required | 14 |
| ka10059 | `kiwoom_utils.ka10059` | runtime_required | 4 |
| ka10005 | `kiwoom_utils.ka10005` | runtime_required | 1 |

주 관측 창 terminal 차분은 `{'timeout': 0, 'started': 1849, 'terminal': 1849, 'response': 1849, 'inflight_unknown': 0}`다. response는 HTTP 응답 관측이며 업무 데이터의 완전성과 정책 적격성을 대신하지 않는다. 시작/terminal/inflight 계수를 분리했고 최근 128건 리스트를 전체 호출 수로 사용하지 않았다.

### `kt00011` 반복 사전 조회

현재 PID의 마지막 purpose 누적 계수: `{'admission_attempts': 2426, 'exact_usable': 2424, 'http_attempts': 2425, 'logical_requests': 2426, 'outside_retained_day_window': False, 'results': {'deferred': 1, 'fresh_success': 2424, 'http_failed': 1}, 'unknown_http_requests': 0}`.

- `_resolve_scanner_async_entry_ai`는 fixed-watch native claim이 없어도 `_request_entry_capacity_preparation`을 예약한다.
- 최초 bounded tail에서 1,497개 capacity read 중 `expired_or_invalid_receipt` 1,479개, `exact_price` 변경 13개, 최초 `absent` 5개였다. 거의 모든 호출이 매번 만료된 증빙을 재충전한다.
- 재사용 TTL 2초·가격/계좌/재고 identity 검증은 유지해야 한다. 이번 진단의 개선 대상은 무신호 상태에서 계속 신선한 용량을 유지하려는 예약 빈도다.
- 기본 Main 수요와 필수 잔고/주문 확인보다 source-only 준비가 공유 read 여유를 소비한다. 현재 HTTP 응답률은 높지만 호출량 절감 효과를 상쇄한다.

### 체결과 분봉

워밍업 후 `ka10003` 준비 수요 12회 중 WS exact 체결 재사용 11회, REST fallback 1회로 HTTP 회피를 관측했다. 모든 430봉 분봉 수요를 WS만으로 충족하는 합성은 아직 미지원이다. 계측된 `ka10080` 논리 수요는 `rest_retained`로 남고 물리 호출은 owner별 표와 같다. 정규장/애프터 자료 합성·이력/마감/route 의미 검증 없이 REST를 끄거나 이력 길이를 줄이는 근거가 되지 않는다.

## 7. WS 수신과 잠금

- 주 관측 창 잠금 대기 120,062회 중 50ms 초과 37회. p99는 10ms 이하다.
- 잠금 보유 120,062회는 전부 10ms 이하다. frozen frame을 만들고 큰 JSON materialization을 잠금 밖으로 옮긴 효과와 부합한다.
- WS 연결은 현재 PID/transport epoch 1로 관측됐다. completed-bar writer loss/projection error는 마지막 증거에서 모두 0이다. 이 값은 전체 시장 WS 패킷 무손실 보장이 아니다.
- 30초 간격 snapshot 표본 33개. `_AL|krx_nxt_integrated`의 producer frame 기준 나이는 다음과 같다. 파일 배송 나이와 봇의 in-memory source 나이를 혼합하지 않는다.

| 종목 | 호가 수신 나이 | 체결 수신 나이 |
|---|---:|---:|
| 005930 | 7.4~245.7ms | 6.5~806.9ms |
| 034020 | 7.6~1906.2ms | 10.8~5914.7ms |
| 403870 | 8.7~2805.7ms | 203.4~13508.2ms |
| 196170 | 8.2~3106.0ms | 8.4~13699.2ms |
| 036930 | 8.1~1551.8ms | 110.5~14907.8ms |

삼성의 체결은 관측 표본에서 계속 최근이었다. 일부 비삼성은 호가는 최근인데 체결만 오래된 경우가 있다. `QUIET_TAPE_OBSERVED`와 `OBSERVATION_UNPROVEN`를 분리하며 체결 희소를 API/WS 장애로 단정하지 않는다. 개별 WS packet의 모든 queue/dispatch latency는 현재 보고서로 전수 입증되지 않았다.

약 1.3MB shared snapshot을 기본 1초 주기로 작성하는 경로와 Main PID의 높은 write byte 증가도 남아 있다. 잠금 개선과 전체 materialization/쓰기 비용 절감은 다른 문제다. 현재 증거로 CPU 포화나 실제 평가 지연의 직접 원인까지 확정하지 않는다.

## 8. 우선 보완 권고와 종료 검증

| 우선순위 | 대상/owner | 다음 작업 | 종료 검증 |
|---|---|---|---|
| P0 | fixed-watch claim→worker→Main / `sniper_state_handlers`, `kiwoom_sniper_v2` | native 원 예산을 보존하고 완료 결과를 다음 sleep·source 재평가 전에 소비/거절하는 순서를 검토; exact attempt별 완료/소비/거절 terminal 사유 확보 | 자연 PASS마다 response→completed→Main guard 결과 전수 연결, 반복 전송/주문 0, 5초/원천/주문 안전 유지 |
| P1 | 무신호 capacity 사전 예약 / `entry_capacity_prefetch` | native 준비/확인 수요와 연결해 무신호 만료 재조회 축소; 실제 initial sizing의 exact 증빙 경로는 유지 | 동일 신호·원천 부하에서 capacity 물리 호출 감소와 준비 지연/결손 악화 없음; 가격·계좌·재고 변경 회귀 |
| P1 | 최초 trace 중복 방지 / `ai_decision_trace` | 기존 증분 ledger 계획과 연결해 최초 provider 응답 안에서 큰 일일 JSONL 초기화 제거 | 새 PID의 첫 자연 응답도 bounded local processing, 중복/불완전 append 처리 보존 |
| P2 | 430봉 source composition / REST/WS owner | 이력·완성봉·venue/session 동일성 증거를 확보한 경우에만 WS 합성 확대 | 동일 입력에서 완전성·계산 parity, 결손 시 기존 REST fallback |
| P2 | shared snapshot 반복 출력 / `kiwoom_websocket` | 실제 소비 범위와 프레임 분모를 보존하며 직렬화/쓰기 비용 측정 | receipt·필수0B/0D·completed bars 유지, writer loss 0, 대기/p99 악화 없음 |

이번 사용자 요청은 관측·진단이다. 위 권고는 구현/배포 영수증이 아니다. 원천·기계·보조 결과와 제출/체결/비용 성과를 구분했고 경제성 개선은 선언하지 않았다.

## 9. 증거와 검증

- [주 관측 요약](../../tmp/main-latest-pid-monitor-20261008-1930/summary.json), 동일 디렉터리의 `performance-history.jsonl`, `performance.jsonl`, `identity_proc.jsonl`, `ws.jsonl`, bounded/incremental 캡처·trace, capacity 계수, 검토 코드 해시를 보존했다.
- [REST/WS 및 준비 경로 계획](../proposals/main-post-warmup-latency-rest-ws-bottleneck-remediation-implementation-plan-2026-10-08.md).
- [앞선 PID 관측](main-pid-206123-post-warmup-latency-rest-ws-monitoring-2026-10-08.md), [통합 검토](main-post-warmup-bottleneck-compact-integration-review-2026-10-08.md).
- 원문 active JSONL은 최초 최대 16MiB tail, 이후 offset 증분만 읽었다. 약 3.5GB pipeline 전체 재스캔·report 재생성·추가 broker/provider 호출은 실행하지 않았다.
- Python 관측/집계 스크립트 실행과 차분 histogram 보존식을 검증했다. 문서/링크/`git diff --check` 및 print-only backlog parser를 확인한다. 런타임 코드 수정이 없어 매매 pytest·배포·재기동은 수행 대상이 아니다.
