# 테스 사례 기반 probe-first 잔여 주문 계약 보완계획

작성: 2026-09-23 KST. 범위는 메인 SCALPING 최초 진입의 probe-first 주문과 체결 후 잔여 주문이다. 이 문서는 구현계획이며 주문·수량·임계치·TTL 변경 또는 배포 승인이 아니다. 기존 실행 owner는 `entry_split_order_plan`과 `sniper_state_handlers`, 경제성 owner는 당일 checklist의 `DirectFamilySourceRepairEntrySplit`이다. 새 주문 엔진·collector·cron·튜닝 family를 만들지 않는다.

## 1. 확인된 사실과 미확정 원인

테스(095610)의 2026-09-23 원본 파이프라인은 다음 순서다.

| 시각 KST | 원본 단계 | 확인된 내용 |
| --- | --- | --- |
| 09:42:08.500 | `entry_split_order_plan_applied` | 총 계획 8주. 사전 검사는 `ready`, 그룹은 `price_tick,signed_pressure` [47312행](../../data/pipeline_events/pipeline_events_2026-09-23.jsonl). |
| 09:42:09.041~09:42:09.783 | `probe_submitted` → `probe_filled` | 1주 실주문·체결, 제출~체결 관측 738.87ms [47314·47317행](../../data/pipeline_events/pipeline_events_2026-09-23.jsonl). |
| 09:42:09.818~09:42:12.792 | `probe_continuation_deferred` 6회 | post-fill `signed_pressure=unavailable`, `orderbook=neutral`, 방향 source 부족 [47320~47325행](../../data/pipeline_events/pipeline_events_2026-09-23.jsonl). |
| 09:42:13.051 | `residual_blocked` | 3초 기한 후 잔여 7주 미제출. 최종 원인 `timeout_source_quality_unrecovered` [47326행](../../data/pipeline_events/pipeline_events_2026-09-23.jsonl). |

현행 [`_probe_residual_admission()`](../../src/engine/scalping/entry_split_order_plan.py)은 사전 AI·호가 신선도와 `price_tick` 외 현재 준비된 그룹 한 개를 확인한다. 준비되지 않으면 probe 전에 전체 계획을 보류하는 경로도 이미 있다. 반면 [`_post_probe_direction_fields()`](../../src/engine/sniper_state_handlers.py)은 체결 후 live WS, route-proven tape, 또는 **체결 이후에 생성된** feature probe에서 방향 근거를 다시 만든다. 두 그룹이 부족하면 `DEFER`이며 기존 3초 기한 이후 잔여를 차단한다. 이 사전 검사는 미래 source의 도착을 보장하지 않는다.

테스의 사전 이벤트에는 `signed_pressure`라는 그룹명만 있고 원천·관측시각·route·갱신 경로가 없다. 첫 post-fill 검사에는 기존 feature probe가 체결 이전 자료이고 약 10.5초 경과했으며 WS tick context도 fresh가 아니라고 기록됐다. **사전 압력 근거가 어느 producer에서 왔는지, 해당 producer가 체결 후 소비 경로와 같은지는 현재 원본으로 확정할 수 없다.** 외부 WS 미도착, 입력 전달 누락, 두 단계의 서로 다른 freshness 규칙을 구별하는 것이 첫 결손이다. 가격 상승만으로 독립된 두 번째 그룹을 대체하지 않는다.

## 2. 목표 주문 계약과 기본 선택

최초 8주는 `target_qty=8`이며, 사전 검사 통과 시에만 probe 실주문 권한 `committed_qty=1`, 잔여 `conditional_qty=7`이 생긴다. `planned=8`을 `submitted=8`로 표시하지 않는다. 사전 입력이 불충분하거나 체결 후 갱신 가능한 live source 경로가 관측되지 않으면 **기본 동작은 전체 신규 진입 보류**다. 기존의 일반 다주 주문으로 자동 우회하지 않는다. 단독 1주 진입은 별도 sizing·경제성·승인 계약이 있을 때만 허용하고, 기존 8주 결정을 묵시적으로 1주 정책으로 바꾸지 않는다.

사전 검사가 통과해 probe를 보낸 뒤에도 source가 사라질 수 있다. 그때는 기존 1주 보유·청산 owner를 유지하고 잔여 7주는 안전하게 미제출한다. 상태는 `partial_plan_realized`와 `residual_not_submitted`로 명시해 누락 주문이나 브로커 거부와 구별한다. 3초 이후 원래 잔여를 자동 부활시키지 않는다. 이후 추가 매수는 새 판단·새 수량/계좌/가격 guard를 거치는 별도 owner의 행위다. 현재 3초 TTL이나 복수 근거, stale/conflict, AI·호가·계좌·주문 guard는 이 계획의 첫 수리에서 완화하지 않는다.

```text
8주 목표 → 사전 source/AI/호가/갱신 경로 관측
          ├─ 부족: 주문 0주, 다음 신선한 평가를 기다림
          └─ 준비: probe 1주만 제출 → 체결 후 신선한 복수 방향 근거 재검증
                                      ├─ 충족: 현재 guard 안에서 잔여 최대 7주 제출
                                      └─ 미충족/기한: 실제 1주 보유, 잔여 7주 미제출 확정
```

| 상황 | 제출 수량 | 다음 상태 | 금지되는 해석 |
| --- | ---: | --- | --- |
| 사전 두 번째 source 또는 post-fill 소비 경로 미확인 | 0 | `admission_deferred` | 브로커 거부·8주 주문 실패 |
| 사전 준비, probe 미체결/거부 | probe 주문 최대 1 | 실제 broker terminal을 기다림 | 1주 보유로 가정 |
| probe 1주 체결, 최신 복수 근거 확보 | 1 + 검증된 잔여 | 기존 가격·계좌·주문 guard를 거쳐 잔여 제출 | 8주 자동 체결 |
| probe 1주 체결, source 소실·충돌·기한 종료 | 1 | 실제 보유 1주, 잔여 미제출 확정 | 잔여 7주를 취소/거부 또는 손익 0으로 계산 |

사전 판정은 `source available`, `source directional`, `post-fill successor path observed`를 별도 필드로 기록한다. 현재 관측된 source의 생산·전달 경로만 확인하며 미래 갱신을 약속하지 않는다. 기존 방향 기준에서 명백히 부정적인 source라면 준비됐다는 이유만으로 probe를 허용하지 않는지 기존 machine/AI·entry owner와 대조한다. 중립 source를 무조건 긍정 신호로 승격하지 않으며, 별도 임계치를 만들지 않는다.

## 3. 기존 코드에 대한 최소 구현 순서

1. **원천 추적을 먼저 보완한다.** 기존 `entry_split_order_plan_applied`/`probe_submitted` receipt에 사전 두 번째 그룹의 source 이름, source event/receive timestamp, age, route·venue·session, quality, 동일 입력의 짧은 hash, post-fill 소비 가능 경로를 기록한다. 기존 `probe_continuation_deferred`에는 각 그룹의 `missing/stale/neutral/negative/conflicted`, 실제 post-fill source 시각과 사전 source 연결 결과를 남긴다. raw tick 전체 복제·provider 재호출은 하지 않는다. 이 변경만으로 실행 판단을 바꾸지 않는다.
2. **동일 의미의 admission 계약을 맞춘다.** 사전 `signed_pressure`/`orderbook`의 단순 수치 존재와 post-fill의 live·route·age·direction 판정을 매핑한다. 사전 자료가 feature probe에만 있고 체결 후 사용할 live WS/호가 producer 경로가 확인되지 않으면 `residual_source_path_unavailable`로 전체 주문을 보류한다. 실제 두 방향 그룹의 최종 강약 판정은 체결 후 최신 자료로만 한다. 재사용 가능한 작은 검사/필드만 기존 두 owner에 두고, 두 번째 주문 엔진을 만들지 않는다.
3. **계획/실행 수량을 분리한다.** 기존 bundle과 이벤트에 `target_qty`, `probe_committed_qty`, `residual_conditional_qty`, `actual_submitted_qty`, `filled_qty`, `residual_terminal_qty`, `residual_terminal_reason`을 같은 bundle ID로 결속한다. 원래 8주의 합계는 probe 1주 + 조건부 7주로 보존하지만, 미제출 7주를 취소·거부·체결로 기록하지 않는다. 보유·청산에는 실제 체결 1주만 전달한다.
4. **사전 경계에서 보류를 끝낸다.** source/AI/호가 중 하나라도 계약 미달이면 `probe_residual_admission_deferred`와 함께 주문 0주로 종료하고, 새 평가에서만 다시 판단한다. 체결 후에는 기존 quote/P1/방향/AI/계좌/브로커/손절 우선순위와 3초 기한을 유지한다. 첫 수리의 범위는 producer 연결·관측·수량 정합성이며 TTL 연장, 한 그룹 허용, 무조건 전체수량 제출은 별도 경제성 검증 대상이다.

각 단계는 앞 단계의 원본·회귀 통과 후 진행한다. 1단계의 계측으로 테스 당시 사전 `signed_pressure`가 체결 후 live WS 경로와 무관한 캐시였는지 먼저 판별한다. 그렇다면 기존 사전 검사에서 그 캐시를 잔여 준비 source로 세지 않는 최소 수정이 우선이다. source는 같았지만 새 event가 늦게 도착했다면 이를 계약 결함이 아닌 관측된 외부 공백으로 남기고 수량 표시·경제성 평가를 고친다. 로그만으로 어느 쪽인지 모르면 `unknown`이며 보호조건 변경 근거로 쓰지 않는다.

## 4. 리뷰·회귀·수용

테스 원본과 동등한 고정 fixture로 `사전 ready → 1주 체결 → 두 번째 그룹 소실 → 7주 미제출`을 재현한다. 다음 경우를 같은 bundle 보존식으로 검사한다: 사전 source 없음(0주), live 경로 없음(0주), 체결 후 새 두 그룹 도착(허용된 잔여만 제출), second group neutral/negative, stale/conflicted quote, AI 권한 만료, 늦은 체결 receipt, 3초 timeout, 재시작/중복 receipt, 기존 1주 계획·sim·KRX/NXT/SOR. 모든 잔여 제출 시험은 기존 가격·수량·계좌·hard stop guard 통과를 요구한다. 코드 리뷰는 producer→consumer 원천, 체결 전후 시계, partial fill·중복 제출, holding/exit 수량, 실패 시 무주문을 확인한다.

수용 증거는 (a) 실제 테스 원인 `source_lost_after_submit`와 `pre/post_source_contract_mismatch` 중 하나를 원천시각으로 판별하거나 `unknown`으로 남기는 것, (b) 실제 주문이 `target=probe+conditional`, `submitted=probe+submitted_residual`, `filled≤submitted`를 만족하는 것, (c) 사전 미준비에서 주문 0건과 무우회, (d) 새 PID의 배포본·당일 정책 소비, (e) 자연 probe의 잔여 제출률·source-gap률·partial exposure·실제 체결 비용과 청산을 분리 보고하는 것이다. 코드/배포 통과는 잔여 7주 실현이나 EV 개선 증명이 아니다. 비용 차감 경제성은 `COMPLETED + valid profit_rate`와 동일 모집단의 주문/미제출 기회로 별도 판정하며, 표본 부재는 0 EV로 바꾸지 않는다.

산출물 owner는 기존 entry split 이벤트·runtime bundle·당일 checklist `DirectFamilySourceRepairEntrySplit`을 재사용한다. 구현할 때 원본 테스 이벤트와 변경 전/후 고정 fixture, 회귀 결과, 선택 release, PID, 롤백 commit을 남긴다. 운영 문서·checklist/자동화 규칙 변경이 실제로 필요해지는 경우에만 해당 owner를 함께 갱신한다.

구현·리뷰가 닫힌 뒤 배포가 별도로 승인되면 불변 release와 기존 안전 재기동 절차를 사용한다. 배포 직후 사전 보류율, 실제 probe/잔여 제출·체결 수량, 같은 원인의 `residual_revalidation_timeout`, 잘못된 일반 다주 주문 fallback, 중복 잔여 주문, holding 수량 불일치를 확인한다. fallback·중복·수량 불일치 또는 stale/conflict 우회가 1건이라도 확인되면 이전 commit/release로 복귀하고 해당 bundle을 원천 대사한다. 잔여 제출률만 높아진 것은 수용 근거가 아니며, 자연 체결·청산과 비용 차감 EV는 후속 별도 판정이다.

## 5. 구현 경계

이후 사용자의 구현·배포 요청에 따라 기존 두 owner에 사전 live WS/호가 successor 원천 시각·품질 검사와 미준비 시 무주문 보류를 연결했다. probe bundle·파이프라인에는 사전 source 식별자와 목표/조건부/실제 제출 수량을 보존한다. 체결 후 판단·3초 기한·기존 안전 가드는 유지한다. 테스 당시의 사전 source producer는 과거 이벤트만으로 단정할 수 없으며, 새 계측으로 발생하는 자연 사례에서 원천 연결을 판별한다. 코드 회귀와 배포는 자연 잔여 제출 또는 비용 차감 EV의 증명이 아니다.
