# SCALPING 감시 대기열 의미적 교체 계획 — 2026-09-28

상태: 9/28 자연 재생 근거 보존. 감시 교체의 단독 구현 계획은 [시장 발견→기계 판정 제로베이스 재설계](scalping-zero-base-discovery-machine-intake-plan-2026-09-28.md)로 이관했다. 여기의 기존 스캐너 대비 paired EV 비교는 새 구조의 선택 기준이 아니다. 현재 감시 상한과 퇴출 동작은 유지한다.

## 1. 결정

감시 슬롯의 의미적 교체는 기존 `SCALPING/SCANNER` 대기열 owner 안에서 평가한다. 핵심 원칙은 **오래 자리를 점유한 종목에서 신선하고 유효한 관측이 계속 들어왔는데도 최근 반전의 기미가 전혀 없을 때만 감시 퇴출을 고려한다**는 것이다. 기계 `BLOCK/NO_EDGE`는 그 평가 시점의 판정이며 종목의 미래 순수익이 0이라는 뜻이 아니다. `RECHECK/EDGE`, 원천 결손, 주문·보유 custody, 새 후보의 실제 슬롯 경쟁을 분리한다. `NO_EDGE` 횟수는 퇴출 기준으로 쓰지 않는다.

첫 산출물은 보고 전용의 동일 예산 교체 비교다. 자연 원천과 비용 후 결과가 충분할 때만 기존 대기열의 후보 교체 규칙을 한 scope에서 검토한다. 기계 진입 임계치·AI/provider·주문가/수량·broker/account/order/cooldown·hard safety·WS/REST 프로토콜은 이 계획의 변경 대상이 아니다.

## 2. 실제 원천 재생 결과

- 원천: [9/28 장중 pipeline events](../../data/pipeline_events/pipeline_events_2026-09-28.jsonl)의 `09:58:00~10:30:00 KST`. 해당 구간은 선택 Main PID `451345`의 기계 우선 진입 흐름에서 관측됐다. 4개 관련 stage (`scalp_entry_action_decision_snapshot`, `scalping_scanner_watch_eviction`, `scalping_scanner_watch_budget_reallocated`, `entry_machine_watch_terminal`)의 투영 333개 이벤트, 86개 `(record_id, scanner_promotion_id)` 그룹을 재생했다. 투영 SHA256은 `b606998ef0d6a4d7bbcdc9ada325b0d3464bbc6eafd2c6e227ed389b29c20e4c`이다. 이 해시는 전체 증가형 JSONL의 해시가 아니라 아래 필드 순서와 시간 필터의 고정 투영 해시다.
- 방법: `emitted_at`, `record_id`, stage, promotion ID, attempt ID, 기계 관측 SHA, action, `edge_state`, 평가 상태, 퇴출 사유, 감시 terminal 사유를 원 이벤트 순서대로 compact JSON 배열로 직렬화했다 (`ensure_ascii=True`, 구분자 `(',', ':')`, 배열마다 LF). 동일 `(record_id, promotion_id, evaluation_attempt_id)`의 이중 기록은 1판정으로 셌다. 후보는 `machine_evaluation_status=assessed`의 `BLOCK/NO_EDGE`만 사용하고, 다음 판정이 다르면 연속 횟수를 초기화했다. 연속 판정 간 간격은 최소 60초다. 관측 종료에는 동일 promotion ID가 확인된 실제 퇴출/감시 terminal만 사용했다. promotion ID가 없는 budget 재배치 이벤트는 투영에는 포함하되 정확한 세대 종료로 간주하지 않고 검열했다. 나머지는 10:30에 관측을 끝냈다.
- `뒤에 EDGE·RECHECK`는 같은 감시 세대에서 후보 시점 뒤 10분 이내, 실제 퇴출 전의 자연 판정이다. `ENTER_NOW`도 같은 범위의 기계 action이며 실제 주문·체결 또는 수익을 뜻하지 않는다. 10분을 끝까지 관측하지 못한 그룹은 검열로 남긴다.

| 가상 규칙 | 퇴출 후보 감시 세대 | 이후 `EDGE·RECHECK` | 이후 `ENTER_NOW` | 10분 완전 관측 | 실제 terminal 관측 | 판정 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 첫 `BLOCK/NO_EDGE` | 26 | 4 | 1 | 4 | 18 | 빠른 퇴출 위험이 직접 관측됨 |
| 같은 세대 연속 2회, 60초 이상 간격 | 1 | 1 | 0 | 1 | 0 | 유일한 후보도 뒤에 `EDGE·RECHECK`; 기각 |
| 같은 세대 연속 3회, 60초 이상 간격 | 0 | 0 | 0 | 0 | 0 | 슬롯 절감 효과를 시험할 표본 없음 |

이 표는 횟수 기반 조기 퇴출을 배제하는 근거다. `047040`, record `48376`은 같은 promotion `SCANPROM-047040-1790557810254`에서 10:12:05와 10:15:21에 서로 다른 `BLOCK/NO_EDGE`를 냈으나 10:18:22에 `RECHECK/EDGE`로 바뀌었다. `251970`, record `48486`은 10:12:41 `BLOCK/NO_EDGE` 뒤 같은 promotion에서 10:16:07 `ENTER_NOW/EDGE`를 냈다. 그 `ENTER_NOW`의 `actual_order_submitted=false`이므로 놓친 실현이익으로 계산하지 않는다. 복수 pipeline 기록과 새 promotion을 독립 판정 또는 같은 대기 세대의 연장으로 중복 세지 않는다.

### 체류시간·반전 부재 재생

같은 원천의 `09:00~10:40 KST` 판단과 `10:50`까지의 후행 관측을 고정했다. 세 stage (`scalp_entry_action_decision_snapshot`, `scalping_scanner_watch_eviction`, `entry_machine_watch_terminal`)의 원본 순서 933행, 492개 `(record_id, promotion_id)` 그룹이다. `emitted_at`, record ID, stage, promotion ID, attempt ID, 기계 action/edge/평가상태, 캔들·venue·machine source quality, 퇴출·terminal 사유를 순서대로 compact JSON 배열+LF로 직렬화한 투영 SHA256은 `0aff461ef584c1d1ea3fed1b17617c97729aa6380262e0cc8b7dc5688cce3a50`이다. promotion 시작은 기록된 `scanner_promotion_emitted_epoch`, 판단 시점은 중복 attempt 제거 후의 자연 기계 판정으로 잡았다. 같은 promotion의 실제 퇴출/terminal 뒤 이벤트는 후보·후행 회복에서 제외했다.

시험용 반전 신호는 source가 유효한 `EDGE`와 `RECHECK` 또는 `ENTER_NOW`의 조합이다. 신선한 `assessed`, `entry_candle_source_quality_status=fresh_consistent`, `venue_source_quality_status=pass`, machine source invalid 아님을 요구했다. 감시 시작 또는 마지막 반전 이후 지정 시간 동안 현재 `BLOCK/NO_EDGE`이고, 그 사이 유효한 앞선 판정이 있으며 관측 간격이 6분을 넘지 않을 때 첫 후보만 셌다. 이 간격은 **재생의 관측 가능성 검사**이며 제안한 라이브 임계치가 아니다. 이 시험은 가격·체결강도·호가의 모든 반전 징후를 대변하지 않으므로 신호 부재를 곧바로 경제적 무가치로 해석할 수 없다.

| 반전 없이 지난 시간 | 후보 감시 세대 | 뒤 10분 내 유효 `EDGE/RECHECK` | 해석 |
| --- | ---: | ---: | --- |
| 5분 | 4 | 2 | `356680`(09:43:46→09:50:11), `047040`(10:15:21→10:18:22) 회복; 퇴출 기준으로 부적절 |
| 10분 | 0 | 0 | 이 구간에서 교체 효과·기회 손실을 시험할 대상 없음 |
| 15분 | 0 | 0 | 마찬가지로 실시간 기준을 정할 표본 없음 |

5분 후보 중 `009830`은 후행 10분이 끝나기 전 실제 terminal이 발생했다. 따라서 관측되지 않은 후속 회복/실현손익을 0으로 채우지 않는다. **10분 후보 0은 `10분 뒤 회복 0`을 뜻하지 않는다.** 단순히 감시 체류가 10분 이상이고 현재 `BLOCK/NO_EDGE`인 관측은 9건·5세대였다. 이 중 8건·4세대는 직전 10분에 이미 유효한 반전 신호가 있었고, 나머지 1건·1세대는 관측 공백으로 반전 부재를 확정할 수 없었다. 이 5세대 중 3세대에서 해당 장기 체류 `NO_EDGE` 관측 뒤 10분 내 유효한 양성 `EDGE`도 관측됐다. 따라서 장기 체류만으로 퇴출해도 안전하다는 결론은 나오지 않으며, 반전 부재 조건을 함께 만족한 10분 후보의 회복률이나 슬롯 절감 효과는 아직 측정되지 않았다.

현재 로직은 terminal blocker, cooldown, stale, queue lag와 최대 30분 TTL을 처리한다. `entry_economic_watch_lifetime`는 기존 TTL의 관측 필드일 뿐 EV 퇴출 계산이 아니다. 종목은 새 promotion ID로 다시 들어올 수 있어 동일 record ID의 마지막 상태만으로 슬롯 점유기간을 계산하지 않는다. [퇴출 계약](../../src/engine/kiwoom_sniper_v2.py), [terminal stage 계약](../../src/engine/sniper_state_handlers.py), [현행 scanner lookup 비교 경계](scanner-lookup-attention-evaluation-consolidation-and-runtime-plan-2026-09-18.md)를 따른다.

## 3. 오래 점유·반전 부재 후보의 입력과 결정

1. 기존 scanner owner가 `(source date, record ID, promotion ID, code, exact venue/session, machine policy hash, attempt ID)`별로 **감시 시작 시각, 마지막으로 확인된 반전 시각, 현재 판정 시각**과 원천 신선도를 기록한다. 중복 이벤트는 attempt/관측 SHA로 제거한다. 정확한 세대 시작을 모르면 체류시간 후보로 삼지 않는다.
2. 후보는 **충분히 긴 동일 세대 슬롯 점유**와 **충분히 긴 반전 부재**, 현재의 유효한 비진입 판정이 함께 있을 때만 발생한다. 반전이 확인되면 반전 부재 시간은 그때부터 다시 센다. 반전 징후는 우선 유효한 기계 `EDGE/RECHECK·ENTER_NOW`로 재생하고, scanner 재가속 및 가격·테이프·호가의 반전 신호가 실제로 생산·소비되는지 확인하여 신선한 양성 신호를 보수적으로 포함한다. 어느 필드든 결손·stale·`INSUFFICIENT_DATA`면 `unknown/source_gap`이지 `반전 없음`이 아니다. 예정된 재검사나 주문·보유 상태가 있는 세대는 기존 custody를 따른다. 재진입은 새 원천·시각·promotion identity가 있어야 하며 동일 결손의 즉시 재등록으로 절약한 슬롯을 다시 채우지 않는다.
3. **실제 슬롯이 경쟁할 때** 동일 owner/quota, venue/session, 예약석, 경과시간, 원천 신선도와 hard guard를 고정한 incumbent 대 incoming pair를 구성한다. 기존 scanner lookup의 complete partition/resource pair를 재사용할 수 있지만 관심도 가중치 효과와 감시 퇴출 효과는 다른 분석축으로 기록한다. 실제 교체가 불가능했거나 재현되지 않는 pair는 `source_gap`이며 후보 이득으로 세지 않는다.
4. 비교 지표는 동일 기회당 비용 후 paired EV, 관측일당 순익 변화, 원래 성공 진입 유지율, 새 후보의 진입/제출/전량·부분·무체결, 누락 상방, tail 및 자본 점유시간이다. 실제 PnL은 `COMPLETED + valid profit_rate`와 정확 비용만 사용한다. 미선택 종목의 180~360초 시세 snapshot은 source-only 기회 proxy이고 체결·청산 EV가 아니다. 원천이 없는 비용/체결/exit은 0이나 `no_edge`로 대체하지 않는다.
5. 먼저 보고 전용으로 슬롯 점유·반전 부재 시간을 함께 바꿔 동일 frozen 분모에 재생한다. 오늘의 5분은 회복 손실이 관측됐고 10·15분은 후보가 0이므로 어떤 분 단위도 현재 실시간 값으로 고르지 않는다. 날짜별 source exclusion과 이후 독립 날짜 holdout을 분리하고, 후보별 실제 슬롯 회수·놓친 기회·검열·API/루프 비용을 출력한다. 횟수 기반 `NO_EDGE` 조기 퇴출은 비교 설명용으로만 남긴다.

## 4. 단계별 수용과 권한

| 단계 | 산출물과 종료 검사 |
| --- | --- |
| 원천 결속 | 같은 promotion의 기계 판정→감시 유지/퇴출→새 후보 admission→후행 주문/terminal을 연결한다. 대상/제외/검열과 중복·새 promotion 경계를 공개한다. 새 broker/provider/REST/WS 요청 0건. |
| 동일 예산 재생 | baseline과 교체 후보의 실제 동시 슬롯 경쟁을 재현한다. 후보가 비운 슬롯에 들어온 종목의 source/route와 원래 종목의 이후 기회를 함께 보존한다. 재현 불가 pair·불완전 가격 경로·fill/exit 결손은 해당 행을 제외/검열한다. |
| 비용·holdout | 날짜가 분리된 독립 검증에서 비용 후 paired EV와 일별 순익이 개선되고, 성공 진입 유지·tail·source coverage·루프/API 지연이 악화되지 않는 후보만 `ready`다. 양성 근거 부족은 `hold_sample`, 원천 결손은 `source_gap`, 적격 비교에서 우위 없음은 `hold_no_edge`다. |
| 런타임 변경 검토 | 경제성 `ready` 뒤에도 정확 scope·owner·cap 16 불변·rollback·정책 SHA·PREOPEN·선택 release·PID·자연 terminal을 따로 검증한다. 이번 계획·장중 재생·PASS 문구 자체는 실시간 퇴출 권한이 아니다. |

첫 blocker는 **10분 이상 반전이 확인되지 않은 장기 점유 후보와, 동일 슬롯 경쟁에서의 비용·체결·청산 paired 원천 및 독립 holdout의 부족**이다. 9/23 기존 rolling scanner prune 경제성도 source quality/표본 hold 상태였으며 snapshot 비교는 실주문 EV가 아니다. 다음 검사는 9/28 자연일이 닫힌 뒤 기존 scanner resource/position fact를 같은 promotion pair로 대사하고, 실제 장기 점유 후보·반전 입력의 관측 가능성·새 후보 admission을 확인하는 것이다. 불가한 필드는 owner별 source gap으로 명시한다.

## 5. 변경 범위와 검증

이 문서는 보고 전용 후보 연구의 설계와 당일 재생 결과를 기록한다. 현재 `KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE=16` hot override, 동적 min 16, 실제 scanner/기계 판정, 주문 및 API 주기는 변경하지 않았다. 후속 구현은 기존 scanner runtime·`scalping/scanner_lookup_attention_resource.py`·`monitoring/intraday_ws_freshness_monitor.py` 소유 경로를 먼저 사용하고 새 독립 정책 family/cron 또는 engine-root 모듈을 만들지 않는다. 신규 수리 시 기존 affected regression, compile, 성능/호출수 및 `git diff --check`를 통과시킨다. 실제 경제성·PREOPEN/PID 수용은 별도다.
