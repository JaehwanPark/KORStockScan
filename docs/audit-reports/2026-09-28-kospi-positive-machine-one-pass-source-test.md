# 9/28 KOSPI 상승 종목 기계 판정 1회 시험 — 11:25:30 KST 고정

상태: **부분 표본 16종목의 동일 정책 재실행 완료; KOSPI 상승 종목 전수 재실행은 원천 결손**. 보고 전용이며 스캐너·감시 상한·정책·API 주기·주문·런타임을 변경하지 않았다.

## 결정

오늘 저장된 상승 종목을 판정기에 한 번씩 통과시키는 요구를 실제 원천으로 시험했다. 확인 가능한 KOSPI 보통주 상승 표본 113개 중 유효한 원문 기계 입력이 남은 16개를 종목당 첫 1회 재실행했다. 16개 모두 당시 action과 일치했으며 `BLOCK` 7, `RECHECK` 8, `ENTER_NOW` 1이었다. 113개 중 나머지 97개와 순위 패널 밖 보통주 691개에는 이 시험의 정확 입력이 없다. 이 결손을 가상 `BLOCK`이나 기회수익 0으로 대체하지 않는다.

## 원천·고정 방법

| 원천 | 고정 경계·역할 |
| --- | --- |
| [9/25 보통주 마스터](../../data/report/micro_reversion_economic_reference/machine_source_inputs/2026-09-25/daily/2026-09-25/symbol_product_master.json) | `effective_from/to`가 9/28을 포함하는 `KOSPI/EQUITY` 804코드. 9/28 당일 신규상장·상품 전체의 완전한 공식 마스터라는 주장은 하지 않는다. |
| [9/28 시장 조사](../../data/market_opportunity_census/market_opportunity_census_2026-09-28.jsonl) | `KRX/KRX_REGULAR`, 정상 `all`·`liquid_common` 패널에서 `change_rate_pct>0`의 첫 관측시각을 종목별로 고정. 읽기 시작 시 파일 prefix 7,343,697 bytes, `captured_at <= 11:25:30 KST`. 정상 패널 49개·원천 미가용 패널 11개, 마지막 정상 capture 11:25:16.201322 KST. 관측된 패널당 최대 200행이므로 전종목 시세가 아니다. |
| [9/28 진입 이벤트](../../data/pipeline_events/pipeline_events_2026-09-28.jsonl) | 읽기 시작 시 prefix 1,572,722,152 bytes. 같은 cutoff 이전, 해당 종목의 첫 상승 관측 이후 사건만 사용. promotion·기계 snapshot·제출은 서로 다른 사건이다. |
| [기계 판정 함수](../../src/engine/scalping/entry_setup_evidence.py)와 [정책 loader](../../src/engine/scalping/mechanistic_entry_runtime_policy.py) | 이벤트의 `entry_mechanistic_policy_decision.effective_setup_evidence`를 안전한 literal로 해석하고 schema·self hash·`fresh_consistent`·`KRX/KRX_REGULAR`·bundle hash를 검증했다. 정확한 첫 유효 입력을 같은 `mechanistic_entry_policy_decision()`과 그 scope의 `machine_policy`에 종목당 한 번 넣었다. bundle SHA256 `6785d52e1ebb9b4ae4da4382b07f35baf1a7022e0b4c87025dcb48851900bc87`. 함수 파일 SHA256은 작업공간·당시/현재 선택 릴리스에서 동일한 `6ff0d2e2e289cc9a0838d662ee3e2a12538e0adbf15a5c4303763bfb524b7497`였다. |

상승 포착 코드 정렬 목록 SHA256은 `de9ed4f83be99e01d48332f59d99e8d5e73345028f2fce4d0ee436b59e1cda70`, 선택한 `(code, 평가시각, evidence_sha256)` 목록 SHA256은 `2cab9ea5449bacee9b04ff91bbe4885c0300ff980fb5e7dcff16d1173d4e7b41`이다. 진행 중인 JSONL 전체의 해시로 읽지 않는다. `ka10027`의 상승 포착시각과 기계 입력시각은 서로 다르며, 후자가 앞서면 재생 대상에서 제외했다. 결정 기록 안의 effective evidence를 재사용한 결정론적 재생이며 원시 WS/REST 시퀀스로 특징을 독립 재구성한 검증은 아니다.

## 결과와 분모

| 단계·서로 다른 종목 | 수 | 해석 |
| --- | ---: | --- |
| 전일 유효기간 마스터의 KOSPI 보통주 | 804 | 조사 대상 참조 분모. |
| 오늘 순위 패널에서 상승 확인 | 113 | KOSPI 상승 종목 전수가 아닌 관측 표본. 나머지 691은 등락 미관측. |
| 첫 상승 포착 이후 promotion 있음 / 기계 snapshot 있음 | 41 / 28 | 중첩 24, promotion만 17, snapshot만 4, 둘 다 없음 68. 이 두 건수를 직렬 funnel로 나누지 않는다. |
| snapshot 28 중 정확 판정 입력 있음 | 16 | 4개는 decision field 없음, 4개는 필수 feature 부족의 사전 `RECHECK`, 4개는 사전 source invalid. 나머지 85개는 snapshot 자체 없음. |
| 기계 함수 1회 재실행 | 16 | 기록과 action 일치 16/16; `BLOCK` 7, `RECHECK` 8, `ENTER_NOW` 1. |
| 같은 포착 표본의 `order_bundle_submitted` / `order_leg_sent` | 1 / 1 | 제출 영수증이다. 전량 체결·종료·비용 후 수익을 의미하지 않는다. |

재실행한 `BLOCK` 7개의 reason은 `mechanistic_hard_or_source_block`이다. `RECHECK` 8개는 `local_breakout_confirmation_required` 4, `TRIGGER_CONFIRMATION_RECHECK` 3, `MICRO_PRICE_RESPONSE_RECHECK` 1이다. `ENTER_NOW` 1개는 `047040`의 `MECHANISTIC_SETUP_AND_THRESHOLD_PASS`다. 상승 종목에 기계 판정이 도달하기 전의 관측/승격 손실과, 판정 후 확인 대기가 모두 존재한다. 이 표본은 순위 패널 선택 편향이 있어 `1/16`을 전체 KOSPI 기계 통과율로 외삽하지 않는다.

## 전수 시험의 첫 blocker와 후속 폐쇄 검사

첫 blocker는 **인과시각이 확인된 전종목 상승 명단과 종목별 완전한 기계 입력 생산 부재**다. KRX [전종목 시세](https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd?screenId=MDCSTAT015)는 시장구분·등락률을 제공하지만 당일 표시는 지연될 수 있고, 이번 시험 시각에 인과시각을 맞춘 전종목 행을 확보하지 못했다. 현행 `ka10027` 상위 순위 패널을 KOSPI 전체로 확대하지 않는다. 그 밖의 691개에 정확 호가·테이프·완료 캔들·route/source 시각을 가정하지 않는다. 사용자 화면의 상승 900개 이상은 상품·시장·시각 범위가 확인되지 않아 9/25 마스터의 KOSPI 보통주 804개와 동일 모집단으로 대조할 수 없다.

다음 생산·검사는 기존 [시장 조사 owner](../../src/engine/monitoring/market_opportunity_census.py)에서 전체 보통주 명단·상승 판정시각을 먼저 고정하고, 기존 [기계 입력 owner](../../src/engine/scalping/entry_setup_evidence.py)에 **그 상승 포착 이후** 유효한 원천이 있는 종목만 1회 평가하는 것이다. 종목별 `assessed`, `required_feature_insufficient`, `source_invalid`, `unobserved`를 빠짐없이 남기고 scanner discovery→promotion→snapshot→machine action→auxiliary/submit→terminal을 같은 promotion/attempt로 묶는다. 전수 입력이 마련되기 전에는 평가된 부분집합과 전체 상승 분모를 혼동하지 않는다. 현행 [공유 읽기 예산](../proposals/kiwoom-read-observation-cadence-and-exact-reuse-implementation-plan-2026-09-28.md)은 전체 5회/초·source-only 4회/초이므로 장중 전종목 개별 조회를 즉시 병렬 호출하는 방식은 이 시험의 후속 실행 경로가 아니다. 과거 응답을 새로운 호가 관측으로 재사용하지 않는다.

판정 재생은 기존 파일 읽기와 순수 기계 함수 호출만 사용했다. 새 Kiwoom 시세·계좌·주문 API 호출, 봇 재기동, 정책·임계치·감시 슬롯·주문 변경은 0건이다. KRX 페이지는 전종목 시세 계약 확인용으로만 열람했다. 코드 일치와 판정 재현은 배포·PID 소비 또는 미진입 종목의 실현 EV 증거가 아니다.
