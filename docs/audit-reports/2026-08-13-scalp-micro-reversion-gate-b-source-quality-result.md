# Scalp Micro-Reversion Gate B Source-Quality Result — 2026-08-13

## 1. 판정

**Gate B는 계속 `HOLD`다.** 원시 수집과 경로 복원 품질은 P2 연구를 검토할 수준으로 개선됐지만, forward 관측 거래일이 `4/5`이고 `2026-08-13 09:00:35 KST`에 기존 canary가 정규장 전환 지연 tick을 timestamp regression으로 감지해 observer를 중단했다. 따라서 실제 경로 P2 discovery/ranking, sim, trading runtime, 주문 권한은 열지 않는다.

이번 변경은 다음 두 source-quality 결손을 닫는다.

1. 현재 HEAD와 frozen callback baseline의 source hash 불일치를 현재 소스 재측정 baseline으로 교체했다.
2. 실패 process scope를 날짜 전체가 아니라 `trade_date + venue + session + sequence_epoch`로 고정하고 P2 canonical loader가 manifest를 기본·fail-closed로 소비하게 했다.

또한 공식 `0B` FID 20은 체결시간이지만 monotonic sequence라는 계약은 없고, 실관측에서는 정규장 직후 1~2초 전 체결 tick이 뒤늦게 도착했다. 이미 canonical V3가 해당 row를 `path_consumer_eligible=false`로 저장하고 P2가 건너뛰므로, 다음 배포부터 이 현상은 observer 전체 중단이 아니라 명시적 raw-row exclusion warning으로 남긴다. queue/drop/writer/authority/latency 등 기존 hard canary stop은 유지한다.

## 2. 근거

### 2.1 정확 범위 제외 결과

Source exclusion manifest: `configs/scalp_micro_reversion_source_exclusions.json.txt`

| 항목 | 결과 |
| --- | ---: |
| 관측 거래일 | `4` (`2026-08-10`~`2026-08-13`) |
| 제외 scope | `7` |
| 제외 stream rows | `196,935` |
| 제외 event references | `5,689` |
| 보존 stream rows | `1,203,067` |
| 보존 event references | `29,213` |
| unique segments | `15,306` |
| reference coverage | `100.000%` |
| pre/active/post complete segments | `14,289` (`93.356%`) |
| duplicate canonical sequence | `0` |

제외 이유는 `2026-08-10` 초기 process-window 불합격 2개 scope, `2026-08-11` timestamp stop 1개 및 callback p99 stop 2개 scope, `2026-08-12` timestamp stop 1개 scope, `2026-08-13` timestamp stop 1개 scope다. 같은 process epoch라도 결손이 없던 KRX/장전 scope는 보존했다. 삭제나 결손 보간은 수행하지 않았다.

| 중단 시각 (KST) | 원인 | 제외 범위 |
| --- | --- | --- |
| `2026-08-10 09:40:10` | 초기 process window Gate B 불합격 및 queue drop | KRX/SOR REGULAR epoch `1786322360935918570` |
| `2026-08-11 09:00:33` | exchange timestamp regression exceeded `10` | SOR REGULAR epoch `1786402515996024117` |
| `2026-08-11 10:35:14` | callback p99 `2.012878ms > 2ms` | KRX/SOR REGULAR epoch `1786408482348143720` |
| `2026-08-12 09:00:34` | exchange timestamp regression exceeded `46` | SOR REGULAR epoch `1786488914409000129` |
| `2026-08-13 09:00:35` | exchange timestamp regression exceeded `88` | SOR REGULAR epoch `1786577221190969504` |

### 2.2 현재 소스 baseline

Baseline: `main_server_synthetic_0b_20260813T090755+0900`

| 측정 | p95 | p99 | drop/error |
| --- | ---: | ---: | ---: |
| observer-on external 0B max | `0.025986ms` | `0.039125ms` | `0` |
| observer-on internal 0B max | `0.024541ms` | `0.037579ms` | `0` |
| 별도 0D 5,000건 persistence | `0.032856ms` | `0.079557ms` | `0` |
| frozen canary limit | `1.0ms` | `2.0ms` | any nonzero hard metric stops |

0D는 `5,000/5,000` enqueue·process·persist를 완료했다. 이 측정은 callback/source 안전성 증거이며 전략 EV나 P2 정책 선택 증거가 아니다.

### 2.3 09:00 incident

- 기존 PID `41346`, observer epoch `1786577221190969504`
- 중단 시각: `2026-08-13 09:00:35 KST`
- 원인: `path_exchange_timestamp_regression_exceeded_count=88` (snapshot 이후 저장자료 최종 exceeded row `97`)
- 원시 형태: 여러 SOR 종목에서 `09:00:32`를 본 뒤 `09:00:30` 체결 tick이 local receive `09:00:32~33`에 도착
- 해당 SOR regular scope: stream `2,843`, event reference `87`, consumer-ineligible row `218`, regression-exceeded row `97`
- 주문/전략 영향: `actual_order_submitted=false`, `broker_order_forbidden=true`, `trading_runtime_effect=false`

### 2.4 Kiwoom 공식 reference gate

- upstream: `Kiwoom-Securities/Kiwoom-REST-API`
- revision: `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`
- retrieval: `2026-08-13T09:03+09:00`
- inspected: `kiwoom_docs/실시간시세.md` 0B, `kiwoom/realtime/packets.py`, `kiwoom/realtime/decoders.py`
- 확인: 운영 WS URL, REG/REMOVE packet, KRX/NXT/SOR item suffix, 0B FID `20=체결시간`, `10=현재가`, `15=거래량`, `27/28=BBO`, `9081=거래소구분`
- 공식 문서는 FID 20의 도착 순 monotonic을 보장하지 않는다. 따라서 실관측한 지연 도착 row를 재정렬하거나 timestamp를 보간하지 않고 raw provenance와 exclusion을 유지한다.

## 3. 구현 및 코드리뷰 경계

- P2 loader는 source exclusion manifest가 없거나 schema/metric/authority/count 계약이 틀리면 fail-closed한다.
- 제외된 reference는 stream 파일을 읽기 전에 거부한다.
- canonical V3의 bounded/exceeded timestamp regression row는 모두 P2 point에서 제외한다.
- timestamp regression exceeded는 다음 배포부터 `healthy_observer_canary_with_source_row_exclusions`로 보고하되, 해당 row는 detector/path/P2에 들어가지 않는다.
- queue/drop, worker/writer, liveness, duplicate/out-of-order sequence, local receive regression, storage, authority leak, latency breach는 기존처럼 observer hard stop이다.
- discovery flag와 selection authority는 계속 false다. 주문·AI·ADM/LDM·threshold·provider·quantity·cap은 변경하지 않았다.

## 4. 다음 액션과 수용 기준

1. 리뷰 완료 뒤 main bot을 표준 graceful 경로로 한 번 재기동해 source-only observer를 재연결한다.
2. 신규 PID에서 callback p95/p99 `<1/2ms`, queue/drop/worker/writer error `0`, reference coverage `100%`, depth persistence 증가를 확인한다.
3. timestamp regression이 재현되면 observer가 살아 있고 affected row만 `path_consumer_eligible=false`, canary status가 `healthy_observer_canary_with_source_row_exclusions`, `raw_row_exclusion_required=true`인지 확인한다.
4. `2026-08-14` 장후 5번째 거래일을 포함해 같은 exact-scope exclusion으로 Gate B를 재집계한다.
5. Gate B 통과 전 P2 actual-path discovery/ranking을 실행하지 않는다. 통과 후에도 별도 frozen discovery/confirmation 없이는 sim 또는 실거래로 승격하지 않는다.

## 5. 코드리뷰 결과

- micro-reversion 전체 + Kiwoom WebSocket targeted regression: `260 passed`
- checklist parser/build regression: `58 passed`
- Ruff, compileall, JSON parse, `git diff --check`: 통과
- current-source frozen hash guard: 통과
- producer/consumer 검토: canonical V3 row quarantine → manifest exact-scope exclusion → P2 default consumer 연결 확인
- silent-fail 검토: manifest missing/invalid/schema/authority/provenance/count/window drift는 모두 예외로 중단
- authority 검토: discovery/selection/sim/trading/broker/threshold/provider/bot/quantity/cap 권한 추가 없음
- 최종 미해결 코드 finding: `0`
- 게시 CI 보완: 저장소 전체 Black gate가 기존 미포맷 4개 파일을 검출해 기계적 포맷만 적용했다. `p2_replay.py`의 동작·측정값·frozen limit는 변하지 않았고, frozen artifact의 해당 source hash만 `a05dde76... -> 2cc8cb78...`로 갱신해 `reason=black_formatting_only_no_runtime_or_measurement_change`, `runtime_effect=false` provenance를 남겼다.

실행 중 observer는 기존 코드가 09:00 incident에서 이미 fail-closed했으므로 현재 중단 상태다. 변경 소스는 아직 로컬 커밋 전이어서 runbook의 clean runtime provenance 규칙에 따라 이 보고서 작성 시점에는 bot을 재기동하지 않았다.
