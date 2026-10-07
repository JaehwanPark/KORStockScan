# 반전 claim 시각 계측 보완과 ENTER_NOW 희소 원인 — 2026-10-07

사용자는 계측 결함 보완·반복 리뷰·배포·재기동과 ENTER_NOW 원인 분석을 승인했다. 현재 실행 owner는 [오늘 체크리스트](../checklists/2026-10-07-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry`이며 감시 자연 수용은 `SemanticMonitorProducerConsumerRefresh1007`에 연결한다.

## 확인한 계측 결함과 수정

13:27:31 삼성전자 attempt `aims-d5fd1048f9bd3132d459`는 FIRST 신호 `:2042`가 최신 신호 `:2044`로 교체되어 native guard가 거절했다. 신호 age는 0.111991882초다. 잠금 전에 잡은 판정 시각보다 실제 잠금 안에서 읽은 최신 native observation이 15.724ms 뒤였고, 감시기는 이 시각 역전을 source issue로 유지했다. 정확한 snapshot/token/family/attempt/bundle/item/epoch/sequence/segment 검사는 모두 통과했다. Provider와 주문 호출은 없었다.

`reversal_source_diagnostics.validate_claim_with_receipt`는 기존 guard의 판정 시각·5초 TTL을 유지하면서, 잠금 안의 상태를 복사한 직후 `state_observed_epoch`를 별도로 기록한다. v2 receipt의 감시기는 판정→상태 관측→trace 시각과 최신 native observation을 각각 대조한다. v1 receipt는 원래 검사를 유지하며 과거 결손을 새 시각으로 보정하지 않는다. 신호가 교체되거나 만료된 실제 거절 결과는 유지한다.

## 반복 리뷰와 검증

- 생산자→native guard→trace projection→병목 감시 소비를 재검토했다. exact identity, snapshot/token hash, same item/epoch/sequence, native valid path, provider/order 없음과 generation 검증은 유지한다.
- 15.724ms 상태 진전, guard 동일성, 구 v1 정상/불일치 양쪽 호환, 잘못된 관측 시각·누락·NaN·다른 attempt/bundle/symbol을 회귀검증했다.
- trace의 v1/v2 receipt 원문 보존 회귀검증까지 보완한 뒤 6개 관련 pytest 파일 **369 PASS**, Python compile 및 `git diff --check` PASS. 검토 범위의 미해결 코드 결함 0이다. 외부 protocol/request/parser/REG/REMOVE 변경은 없다.
- 자연 v2 rejection과 실제 Main PID 소비는 배포 후 별도 확인한다. 테스트가 신규 ENTER·주문·체결·수익 증거를 대신하지 않는다.

## ENTER_NOW 원인 분석 — 13:50:36 KST 동결

[정확한 판정 census](../../tmp/reversal-clock-repair-20261007/trace-census.json)는 entry_screen의 attempt·symbol·bundle별 최종 행을 집계했다. 09:00 이후 삼성 110건은 BLOCK 95·RECHECK 7·contract invalid 8, ENTER 0이다. 비삼성 542건은 BLOCK 378·RECHECK 81·ENTER 3·source invalid 22·contract invalid 58이다. 실제 Provider 응답은 비삼성 2개다. 13:20 이후 현재 bundle에서는 삼성 11건·비삼성 57건 모두 ENTER가 없다.

[삼성 native branch 재생](../../tmp/reversal-clock-repair-20261007/samsung-native-replay.json)은 같은 날짜 SOR_REGULAR 파일의 동결 byte prefix와 native 정규화/분기 계산을 사용했다. Collector sequence는 live route sequence와 다르므로 이 결과로 live claim ID나 PID 실행 누락을 입증하지 않는다. invalid row·path break·동일 native identity 중복을 보존한다.

| 단계 | 건수 | 해석 |
| --- | ---: | --- |
| 삼성 정규화 관측 | 173,780 | valid 172,097 |
| 가격 하락 후 첫 상승 anchor | 38,387 | 반복 가격 반전이며 독립 거래/수익 기회 수가 아님 |
| 기존 DD5 >= 1.2% | 0 | 현 정책의 낙폭 조건에 도달하지 않음 |
| 새 분기 drop <= 0.4% | 38,387 | 모두 통과 |
| 이어 DD5 0.4~0.8% | 8,475 | 대부분의 반전 DD5는 0.4% 미만: 29,516개 |
| 이어 60초 상승률 >= 0.2% | 29 | 새 분기의 큰 축소 지점 |
| 이어 session 상승률 >= 0.4% | 29 | 같은 anchor에서 통과 |
| 이어 최근 저점 상승 | 14 | 재상승 대기 anchor |
| 5초 안 추가 상승 확인 | 4 | 나머지 10개는 원 저점 재접촉 |

필수 feature 부족 anchor는 4,827개이며 위 조건 실패와 겹친다. 개별 조건 실패 수를 독립 모집단으로 합산하지 않는다. 확인된 4개 시각은 09:02:04.644, 09:02:04.932, 09:02:06.969, 10:15:00.324이다. [새 다중 정책 최초 적용](./main-multi-policy-and-unused-raw-execution-review-2026-10-07.md)은 12:34:04.693이므로 이 4개를 새 정책의 운영 미진입으로 집계하지 않는다. 동결 원천에서는 적용 후 신규 CONFIRMED가 0개다.

비삼성의 3개 ENTER는 HPSP 09:08·09:14, 주성 13:00이다. HPSP는 실제 보조 PASS 2건 이후 제출 경로에서 fixed-watch lineage·3초 AI TTL·micro/CAUTION guard로 종료했으며, lineage 수리는 [기존 보완 검토](./main-fixed-watch-submit-and-volume-source-repair-review-2026-10-07.md)에 기록했다. 주성은 Provider 전에 `reversal_signal_expired_or_changed`로 종료했다. 해당 과거 receipt는 expiry와 change를 정확히 나눌 원천이 없어 둘 중 하나로 추정하지 않는다.

[거절 상세](../../tmp/reversal-clock-repair-20261007/contract-rejections.json)에서 삼성 contract invalid 8건은 모두 FIRST 신호 교체다. 비삼성 58건은 FIRST 신호 교체 24·expiry 또는 snapshot change 32·generation change 2건이다. 이 거절들은 정책 조건을 계산하기 전에 끝났으므로 조건 통과 ENTER를 놓쳤다는 숫자로 합산하지 않는다. 짧은 신호의 claim→평가 전달 지연 점검 대상이며 원래 5초 guard를 유지한다.

현재 삼성 ENTER 희소의 확인된 주원인은 기존 DD5 1.2% 부적합과 신규 분기의 DD5·60초 상승률·저점 상승 교집합 희소다. claim expiry/신호 교체와 필수 입력 부족은 별도 전달·원천 원인이며 기계 조건을 통과했다는 뜻이 아니다. 추가 개선은 작은 낙폭 및 느린 상승의 조건 가설을 기존 원천으로 비교하고, 적격 신호의 claim→평가 지연을 측정하는 방향이다. 이번 계측 수리만으로 threshold/provider/TTL/주문 조건을 변경하지 않는다.

## 배포 수용 기록

- 코드 커밋 `25bcd8f00df513be3cf1b32972fc1b489c3c66a3`, immutable release `/home/ubuntu/KORStockScan-runtime-releases/reversal-clock-20261007-v1`. 해당 checkout의 관련 **369 pytest PASS** 후 선택·native 장중 인계를 검증했다.
- **13:55:25 graceful 재기동 완료**, 새 Main PID `896349`/start_ticks `96975678`. 실제 cwd·commit·`source_dirty=false`·당일 bootstrap PASS다. **13:55:44 native 계좌/DB 대사 완료**, WS 계좌 통보 및 5종목 수신·기계 캡처를 확인했다.
- machine/auxiliary 12셀 전체와 연구 kernel/branch/input 계약 해시를 유지하며 release metadata만 native candidate→parent CAS로 다시 결속했다. bundle=`de73d2f60c14377efc0c1eae3e2b8846f741d678f0233c788bc9744e88ced2d5`, family=`eb10bbcce0a53a40186f682b028c75883edc140636f71bd6a879065c9d9729ca`. **13:56:25.038557 실제 PID 정책 소비 영수증**과 receipt SHA를 확인했다.
- PREOPEN/bootstrap·dated 원 정책·summary/controller·현재 체크리스트·custody 정책 등 보호 11개 SHA 동일, 에피소드 186개 pin 검증 PASS, cron 8개 표준 route PASS다. 기존 다른 owner process는 이 Main 재기동에 포함하지 않았다.
- **13:58:15 자연 확인:** HPSP의 13:57:20·13:58:04 두 rejection이 새 v2 상태 관측 시각과 원 trace에 결속되었고 감시 소비자가 `reversal_signal_expired`로 분류했다. 해당 시각 역전 race 자체의 자연 재발은 미관측이다. 기존 v1 결손 4건은 과거 원 증거대로 유지하며 새 receipt로 소급 성공 처리하지 않는다.

[작업 증빙](../../tmp/reversal-clock-repair-20261007/)의 [배포 검증](../../tmp/reversal-clock-repair-20261007/deployment-verify.json), [실제 정책 소비](../../tmp/reversal-clock-repair-20261007/policy-consumption.json), [자연 계측 소비](../../tmp/reversal-clock-repair-20261007/natural-source-semantics.json)에 원본을 보존한다. 새 정책의 적격 신호·실제 Provider/제출/체결·비용 후 수익 및 다음 자연 장후는 현재 체크리스트의 기존 owner에서 계속 확인한다.
