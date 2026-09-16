# 공통 데이터 health·미진입 기회비용 1차 구현 리뷰

기준: `2026-09-17 KST`. [통합 계획](../proposals/entry-opportunity-cost-full-population-tuning-implementation-plan-2026-09-17.md)의 §2.2 부분 H 릴리스에 해당한다. **U0–U12 전체 구현 완료 기록이 아니다.**

## 1. 구현 범위와 최초 결함

| 경로 | 결함 | 이번 보완 | 남은 경계 |
| --- | --- | --- | --- |
| WS → quote consistency / enrichment / latency | program·transport 갱신이 오래된 executable quote를 fresh로 보이게 함 | 기존 `quote_consistency.py`의 공통 `ws_quote_receive_age_ms`를 세 소비자가 호출. 0D 원시각·epoch, 실제 FID27/28의 exact 0B inline BBO만 사용 | direct REST/gateway/widget/episode 전체 parity는 별도 미완료 |
| WS → getter / snapshot writer | 체결 공백과 getter 호출 반복을 분리할 공통 사실 부재 | existing WS exact route record에 bounded `QuietTapeState`, 공통 health metadata, JSON-safe 관찰 receipt 추가 | 반복 quiet 상태는 관찰값일 뿐 ENTER/SELL 권한 또는 시장 무체결 확정이 아님 |
| observer → latency cache | fresh observer quote의 원 나이를 버리고 현재시각으로 재기록 | 기존 quote age를 보존하여 캐시에 재결속. 누락/future 입력은 prior caller의 freshness를 빌리지 않음 | single-flight·전체 scheduler budget 수리는 미완료 |
| #74 → #82 compact screening | 전부 VETO한 날 PASS terminal0 때문에 valid 미진입 CF 평가 금지 | operational terminal gate는 유지하고 `decision_counterfactual_tuning_input_allowed` 분리 | 전체 기계/가격/수량·독립 owner 선정 계약은 미완료 |
| #82 case census | 같은 exact RECHECK 중복 collapse 뒤에도 원 input 수를 learning denominator로 계산 | deduplicated eligible case 수로 수정 | opportunity/capacity 전수 대사는 미완료 |

새 Python module, collector, 서비스, cron, 장후 producer를 만들지 않았다. 기존 price/quantity/scale-in/action/compact model owner를 변경하지 않았다.

Official reference receipt (`2026-09-17T01:15:02+09:00` 재확인 기록): upstream [953e5dbff123f437ab4d11a78a95191a685eb51f](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f). `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 0B/0D, `kiwoom/realtime/{events,decoders,schemas,packets,stream}.py`, `kiwoom/core/ws_client.py`, `postman/kiwoom-openapi.postman_collection.json`을 확인했다. 이 revision의 `kiwoom_docs`와 Postman의 WS0B/0D request 예시는 부재다. packaged official spec에서 0B FID20=HHmmss·10=현재가·15=부호 체결량·27/28=최우선 ask/bid와 0D FID21=HHmmss를 확인했다. 기존 wire/FID 가격·수량 해석, LOGIN/REG/REMOVE/retry/real-demo 분리는 변경하지 않았고 미정의 venue를 추정하지 않았다. 실제 API/주문 호출 없음.

## 2. 공통 health와 안전 경계

- schema: `kiwoom_market_data_health_v1`; WS getter와 기존 snapshot 경로에서 전달. enrichment는 consume 시점에 pure 재계산한다.
- 공백 관찰 기본은 10초, 반복 상태는 서로 다른 공백 episode 3회. 긴 30초 한 공백·getter100회는 episode1이다. 10초 연속 활동은 반복 이력을 reset한다.
- fresh0D 연속성, 같은 exact item/epoch/scope, 실제 누적량 증가를 요구한다. provider trade 시각 누락/late/future/regression과 quote 연속성 단절은 `OBSERVATION_UNPROVEN`이다.
- route/date/epoch/session 경계에서 state를 reset한다. 상태는 existing route record에만 저장하고 getter가 계수를 올리지 않는다.
- 관찰 continuity 기준 3초는 기존 quote 역할의 validity를 보존하는 조건이다. **무체결 판정을 다시 3초로 설정한 것이 아니다.** 10초를 executable quote TTL 또는 micro1초 window로 전용하지 않는다.
- `market_no_print_proven=false`, `decision_authority=false`. quiet를 공격적 BUY/trade backing/refill로 보간하지 않으며 기존 tape/price/venue/micro/submit guard를 건너뛰지 않는다.
- 0B inline BBO는 공식 FID27/28의 실제 양수 값이 표시 frame과 일치할 때만 별도 호가 원천이다. cached/depth-derived BBO나 다른 item은 fresh 근거가 아니다. depth/1초 micro validity는 따로 유지한다.

## 3. 미진입 gate·자동화·조건의 합리성

- 신규 CF gate는 exact target date, 필수 count 필드, 음수/소수/bool 없는 보존식, exact lineage-gap/pending key 계약을 요구한다.
- 전부 BLOCK 또는 VETO여서 `ai_pass=0`인 보존식은 정상 empty operational denominator다. actual terminal0을 이유로 CF 연구를 금지하지 않는다.
- 기존 `economic_tuning_input_allowed`는 PASS 후 terminal 의미로 보존한다. unresolved/pending PASS key를 CF case에서 제외하고 누락 손익을 만들지 않는다.
- 신규 CF gate의 명시적 false를 legacy true로 우회할 수 없다. 이전 frozen receipt에서 새 필드가 없을 때만 그 receipt의 기존 더 엄격한 true gate를 인정한다.
- #82는 source quality, exact identity, 현재 compact prompt/partition, Provider 실제 호출·semantic pass, executable 후행 path·비용을 계속 확인한다. legacy/mixed prompt를 current compact 효과로 재라벨링하지 않는다.
- 실제 경제성 표본은 기존 bounded registered compact selector → `mechanistic_entry_runtime_policy` next-date publisher → PREOPEN/dated loader로 환류한다. 이번 수리는 이 경로의 표본 진입 결함을 닫으며 free-form prompt/model 교체나 수동 env 적용을 만들지 않는다.
- 기존 compact20 표본·관련 denominator5/error3 조건은 actual fill을 요구하지 않아 all-VETO CF로도 달성 가능하다. 이것을 오늘 실수익 개선이나 전체 자동 선정의 완료로 확대하지 않는다.
- common machine·price grid의 절대0.10% gate, 전수 기회/capacity·stress/holdout·four-arm 계약은 아직 U7–U11 검토/보완 대상이다. 원천 수리에 그 경제성 floor를 추가하지 않았다.

## 4. 리뷰·테스트

- 초기 교차 테스트: 476 passed. 추가 exact-case/gate·latency 테스트: 493 passed.
- 보완 중 cached danger 정보를 덮어쓰는 회귀를 발견했다. source age가 기존 cache age/safety보다 더 보수적인 경우만 강화하도록 수정하고 재검증했다.
- 최종 작업본 targeted suite: **845 passed**, pandas `mode.copy_on_write` deprecation warning1. 실제 Kiwoom/Provider/주문 호출 없음.
- 검증 파일: 기존 quote consistency, MarketDataCache, WS, enrichment, sniper latency, #74 audit, #82 calibration, AI snapshot, Kiwoom quote normalization, compact runtime policy, runtime release router test 파일.
- Python compile과 `git diff --check` 통과. 전체 미검토 U0–U12에 finding0을 선언하지 않으며 수정된 위 경로의 리뷰 closure와 구분한다.
- 9/16 BUY sentinel JSON은 stat상 약79MB다. 이번 검증에서 운영 raw/report 전체 scan 또는 장후/Provider 재실행을 하지 않았다. 자연 generation acceptance는 미관측이다.

## 5. 통합 work package disposition

| Package | 상태 | 다음 구현/검증 |
| --- | --- | --- |
| U0 | partial | 계획 부록306 후보의 실제 loader/filter/SQL·direct/injected API reader 전수 의미 대사 |
| U1 | scoped implemented / validated | 현재 WS 공통 facts·quiet state. local-drop·모든 external adapter의 parity는 잔여 |
| U2 | partial | WS→getter/writer·enrichment 연결. REST/direct-client 전체 결속 잔여 |
| U3 | partial | quote normalization/enrichment/latency 공통 clock. 기계/AI·price/sizing/holding stage 의미 전수 잔여 |
| U4 | pending | Widget/episode/micro/exit/web direct/pass-through parity |
| U5 | partial | observer 원 나이·prior-frame freshness 결손 수정. single-flight/scheduler budget 잔여 |
| U6 | partial | operational/decision-CF gate와 중복 case 분모 수정. 전체 row disposition/census 전수 잔여 |
| U7 | pending | current-incumbent common/hierarchy 전체 population replay·선정 계약 |
| U8 | partial | all-VETO CF intake와 legacy/current guard. CAUTION/INSUFFICIENT router 경제성 추가 대사 |
| U9 | pending | price-ready no-submit/no-fill·quantity/leg four-arm Daily contract |
| U10 | pending | 독립 owner CF admission 및 active family fill-bias 실제 결손 수리 |
| U11 | pending | family별 auto handoff·floor 달성 가능성·최종 요약 closure |
| U12 | scoped validation complete | 부분 H managed release 통합 검증·오늘 기존 PREOPEN/start route. 전체 fixed-point 미완료 |

## 6. 배포 조건과 receipt

- 작업본 main과 origin/main·기존 selected release가 다른 이력을 가진다. foreign dirty wrapper/verifier/env/custody/generated 변경을 이번 source commit에 섞지 않는다.
- 기존 선택 릴리스 `13b72d6b6b554cbd0b03328e9939a65db65f8fcb`와 이번 source commit을 별도 managed release에서 안전하게 통합하고 그 source에서 검증한 뒤 publish한다. force push/reset/stash 또는 기존 선택 release 파일 덮어쓰기 금지.
- 최종 release/root/hash·기동 routing 검증은 existing `data/runtime/runtime_release_selection.json`과 router print-plan receipt가 소유한다. 해당 receipt의 최신 값은 이 문서의 초기 기준보다 우선한다.
- 01시대 KST는 expected bot runtime window 밖이고 main PID도 관측되지 않았다. 장후 isolation을 밤중에 깨지 않는다. 오늘 기존 PREOPEN→07:55 start를 사용하며 print-plan을 실제 기동/PID 소비로 표시하지 않는다.
- selected release, PID consumption, 자연 source/policy, actual submit/fill, 비용 후 경제성은 각각 별도 판정한다.

## 7. 기대효과와 잔여

확인된 효과는 false freshness 제거, 공백 반복 분모 보존, all-VETO의 valid 기회비용 평가 경로 복구다. 이들이 놓친 작은 수익의 튜닝 표본을 보존할 수 있지만, 전체 기계 진입 병목 해결·후행 CF 선정 수익·실현 순익 증가는 아직 입증되지 않았다. U7–U11 미완료를 자연 표본 대기로 숨기지 않는다.

Project/Calendar 동기화는 실행하지 않는다. 사용자 표준 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
