# 반등·재진입 1차 구현 리뷰

## 판정

일반 2-leg episode의 flat 신규 진입에 대해 자연 원천→기존 timing 내 paired 평가→조건 통과 후 자동 PREOPEN→exact-scope live consumer를 구현했다. 후속 사용자 지시가 상시 승인으로 작동하며 별도 후보별 사용자 승인 파일은 요구하지 않는다. 생산 정책 발행·봇 재시작·실주문은 하지 않았다.

전체 최초 계획의 모든 owner/replay 범위가 완성된 것은 아니다. 위젯 순차 평균단가 target, passive/partial fill, 추적이 끊겨 terminal proof가 없는 no-entry, 세션 초과 no-stop exit는 `evaluation_scope.unsupported`와 `gap_handoff`로 명시한다. 이들은 단순 표본 대기와 다르며 유지 점검에서 수리/범위 축소를 결정해야 한다. A1은 기존 재개와의 중복 귀속으로 정리했고 별도 BUY 전략은 만들지 않았다.

## 구현과 권한

| 경로 | 동작 / 경계 |
| --- | --- |
| `trading/market/machine_rebound_reentry.py` | 기존 owner 결정 시점의 신호·기존 leg/target·cost·market receipt·causal snapshot 기록. 신규 API/AI/구독 없음. 반복 poll은 표본 수가 아니며 비적용 parent당 최초/최초 유효 반등/기존 재개 최대 세 source 기록 |
| `monitoring/machine_rebound_reentry_source.py` | immutable journal hash 검증, 최초 causal 후보/실제 owner 재개 선택, attribution의 단일 raw decode 재사용. live quote와 원시 depth 재대사, 동일 세션 종료·기존 target/양 leg quantity·비용으로 모델 비교 |
| `monitoring/machine_rebound_reentry_evaluation.py` | 실제 주문 cohort와 별도 section. A0 재개를 skip-forever/0원으로 바꾸지 않음. 원 기회 기준금액 고정, 순이익 delta 평균·cohort/rolling/holdout·coverage·p10·구조 결손 분리 |
| 기존 timing CLI / 장전 wrapper | 장후 보고서에 평가 section 자동 생성. 장전 source 재평가와 타 machine/hysteresis 선택 충돌 검사 후 immutable snapshot/exact-date receipt 발행. global auto-apply OFF 또는 non-live mode면 dry-run |
| `trading/config/machine_rebound_reentry_policy.py` / regular owner | 동일 날짜·source/evidence hash·floor·scope·owner contract·fresh 상승·충분한 depth·기존 양 leg 가격 충족 검사. 초기 동일 batch에만 유효한 짧은 permit. 부분 보유/재시도에는 재사용 불가 |
| 기존 cancel/liquidity/order/target paths | 변경 없음. market 예외는 주문 제출 지시가 아니며 나머지 owner/브로커 검사 통과가 계속 필요. exact open-buy cancellation도 유지 |

## 적용 허들

- exact scope 최소 5일·8 unique paired completed outcome·coverage 85%.
- 누적 비용 차감 ΔEV ≥0.005%p, rolling 5일 및 최신 날짜 holdout ΔEV >0, 각 창 candidate EV >0, p10 악화 ≤0.01%p.
- Samsung 자연 신호 lag 4거래일, 기타 1거래일. 10/20일 창 미완결은 unavailable 진단일 뿐 추가 적용 조건이 아니다.
- 같은 단계 machine 또는 hysteresis 신규 변경과 동시 승격하지 않는다. 승인 snapshot은 장전 08:00 전 대상 거래일에만 발행하고 이후 변경/만료/무효 시 baseline이다.
- 실제 주문이 없다는 사실은 경제성 계산의 필수 결손이 아니다. 미평가 downstream broker 검사는 `unknown_not_evaluated`로 남기며 실전에서 실행한다. modeled target touch는 actual realized나 real execution quality가 아니다.

## 반복 리뷰에서 보완한 결함

1. source-only anchor에 actual-owner eligibility를 요구해 영구 0이 되는 경로: source-quality verdict와 actual-only cohort 자격 분리.
2. 정상 source snapshot이라도 사후 원자료와 가격/수량이 다를 수 있음: 같은 epoch·causal t0 depth·freshness·bid/ask/quantity 재대사.
3. 기존 timing policy가 적용 중인데 A0를 immediate로 부르는 오차: 현재 exact-scope 정책 확인 및 baseline parity 차단.
4. SOR 원천을 KRX timing session으로 묶는 오류: source execution session과 기존 timing-policy lookup session 분리.
5. 일별 artifact hash 때문에 동일 owner recipe도 다른 실험으로 갈라짐: recipe 의미와 volatile daily hash provenance 분리.
6. 30분 markout 종료 때문에 늦은 정상 재개를 영구 결손으로 만드는 문제: owner outcome은 공통 정규 세션 관측 종료까지 평가, 강제 청산 없음.
7. 반복 poll마다 파일 생성: 비적용 natural source는 최대 세 결정으로 축약. 실제 적용 permit은 해당 시점의 별도 provenance를 보존.
8. report-only 쓰기가 기존 policy의 production source hash를 무효화할 위험: 별도 디렉터리 강제, policy publication false, production 경로 거부.
9. 장전 재검증 실패 후 기존 동일 날짜 permit 잔존 위험: family receipt를 비활성 baseline으로 원자 갱신. 일반 보고서 재생성과 적용 근거 snapshot 분리.
10. snapshot transport epoch(연결 카운터)와 raw sequence epoch(time_ns)는 다른 namespace였다. 직접 동일값을 요구하지 않고 동일 normalized 0D의 exact 수신 밀리초·bid/ask/잔량으로 유일하게 연결한 뒤 raw epoch 내 outcome만 사용한다. 모호한 다중 epoch는 제외한다. Kiwoom 요청/FID/parser는 변경하지 않았다.
11. 기존 재개가 아예 없는 약세일도 평가할 수 있도록 기존 owner loop의 연속 heartbeat·scan 종료·무보유/미시도 상태로 terminal no-entry receipt를 기록한다. 30초 초과 공백·source/unknown/ambiguous·보유/시도 상태에서는 손익 0을 인정하지 않는다. 별도 polling daemon은 없다.
12. 최종 통합 리뷰에서 live permit이 source-only 비교비용을 적용 영수증과 직접 결속하지 않은 권한 경계를 추가 발견했다. 다음 거래일 비용 계약의 값·날짜·SHA-256을 candidate와 immutable evidence에 고정하고, exact-date policy loader와 runtime이 현재 계약까지 완전 일치하는 경우에만 permit을 허용하도록 fail-closed 보완했다. 공용 상승/체결가능 판정도 live 모듈이 report evaluator를 역참조하지 않도록 runtime owner로 이동했다.

## 검증 상태

`korstockscan-review-gate`로 구현→리뷰→수리→재리뷰→검증을 반복했다. 1차 통합 회귀 **1,075 PASS**(18개 test module) 후 위 비용 권한 결속 결함을 추가 보완했다. 최종 변경범위 통합 회귀는 **1,562 PASS**(20개 test module), rebound 단독 **34 PASS**, 변경 Python 47개 Black/Ruff/compile, wrapper 3개 `bash -n`, backlog parser 42개 OPEN 인식, `git diff --check` PASS다. 검토 범위의 미해결 finding은 0건이며 미지원 replay 범위는 완료로 포장하지 않는다. 이전 실행 수치는 중복이므로 합산하지 않는다.

최종 코드로 8/31~9/4 timing JSON/Markdown 5세트를 `/tmp/korstockscan-rebound-review.UGdb1F/`에 격리 재생성했다. 별도 `--write`/정책 발행 없이 `--report-only-dir` 실행면을 사용했다.

| 거래일 | 신규 section 없는 입력 보고서 수 | 유효 rebound pair / 후보 | wall / peak RSS |
| --- | ---: | --- | --- |
| 2026-08-31 | 11 | 0 / 없음 | 0.61초 / 135,368 KB |
| 2026-09-01 | 12 | 0 / 없음 | 0.71초 / 168,952 KB |
| 2026-09-02 | 13 | 0 / 없음 | 0.73초 / 170,940 KB |
| 2026-09-03 | 14 | 0 / 없음 | 0.77초 / 176,108 KB |
| 2026-09-04 | 15 | 0 / 없음 | 0.80초 / 180,352 KB |

각 날짜 rebound 판정은 `source_contract_gap`: 과거에 새 owner journal/source section을 수집하지 않았기 때문이다. 위 11~15는 누적 입력 **보고서 개수**이며 기회/거래 수가 아니다. 현행 코드로 과거 미수집 원천을 합성하지 않았다. 이 결과는 실제 개선 EV의 존재나 부재를 입증하지 않으며 새 자연 기회로 검증해야 한다. 양의 paired fixture에서는 후보 선정→추가 승인 없는 PREOPEN→정확한 scope live permit을 통과하고, 음의 holdout/횡보/stale/변조/동일 단계 충돌/trace gap은 거부하는 테스트를 통과했다.

이번 측정은 기존 보고서 소비형 격리 평가 비용이다. 장후 raw attribution 전량 처리 비용이나 실전 수익/지연 개선율을 측정한 것이 아니다. 신규 독립 schedule·AI/broker API 호출은 0개다.

생산 보호 확인:

- 9/4 production timing JSON SHA-256: `a1e6b1b9d6be2ae501033bb16ad63c7e768e7901895e4f02869e602c12573897`, 전후 동일.
- 9/7 production timing policy SHA-256: `462b0312169039a7e95f29541acfa75de36d75d3a9bbebe0850cb84f087a7f69`, 전후 동일.
- 기존 9/7 loader는 전후 `ready`, selected scopes `0`이다. rebound production journal/policy 디렉터리는 생성하지 않았다. 실제 적용·PID 소비·실체결 개선은 미확인이다.
- 9/7 최초 장전에는 과거 section 부재를 crash로 오인하지 않고 `baseline_no_candidate`로 처리한다. 9/7 이후 source-date 보고서의 신규 section 부재는 verifier/장전 재검증 결손으로 노출한다.

## 남은 자연 검증 / 범위 판정

`MarketWeaknessNaturalEvidence0907`에서 새 코드가 정상 예정 기동에 로드되는지, exact-route 원천과 journal이 생성되는지 확인한다. `MarketWeaknessReboundReentryRetention0911`에서 source→유효 pair→완료 yield, 지원 범위 비율, 미지원 replay의 구현 비용과 개선 가능성을 판정한다. 기존 2026-08-31~09-04 자료에 새 owner journal이 없으면 이를 사후 합성하지 않으며, 실제 개선 EV가 존재한다는 결론도 내리지 않는다.
