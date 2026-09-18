# 2026-09-18 저가주 서로 다른 정책의 경제성 비교 수리·결과

Owner: `LowPriceExpandedResearchRepair0918`. 사용자 승인: [LP0–LP6 상세계획](../proposals/low-price-two-leg-expanded-candidate-economic-logic-improvement-plan-2026-09-18.md) 구현·반복 리뷰/수정·검증, commit/push·배포 및 장후 결과 갱신. 기존 정책·원본 보고서·ledger·quantity/cost/grid/sample/provider/custody·hard safety를 보존한다. 이 기록은 전일 전체 postclose DONE 또는 실제 경제성 PASS가 아니다.

## 결정과 수치 결과

앞서 보고한 성숙 비교3건은 후보와 기존 정책이 같은 자기 비교였다. 이번에는 기존 정책이 calibration 1위여도 **기존 정책과 다른 적격 후보1개**를 별도 고정·평가한다. 자기 비교는 incumbent 보존으로 분리하고 미청산 부분 실현 순익 차이는 개선 근거에서 제외한다.

기존 로직64개만 기존 로컬 원천으로 재평가했다. 신규 API/계좌/provider 조회0, 전체1,020개 재실행0. 원 native calibration grid와 calibration/holdout split, 비용0.23%를 보존했다. 실행156.6초, 새 버전 checkpoint hit0/miss64. 각 profile의 최대 distinct challenger1개를 manifest로 사전 고정했고 calibration 결과만으로 선택했다. 과거 holdout은 이미 관측했으므로 `exploratory_previously_observed_holdout`이다.

| 상태 | 프로필 수 | 해석 |
| --- | ---: | --- |
| 서로 다른 정책·양측 완료·표본 충족 | 2 | EV·일별 순익 동시 개선0 |
| 미청산 또는 terminal 결손 | 55 | 부분 실현 차이는 진단; 경제성 우열 null |
| 완료 표본 부족 | 4 | 승격/경제성 확정 근거 아님 |
| 정상 flat·완료 결과 없음 | 1 | EV null; 무거래0과 carry0를 분리 |
| 다른 적격 후보 없음 | 2 | 후보를 강제로 만들지 않음 |

| holdout 비교 | 기존 EV → 후보 EV | 기존 → 후보 일별 순익 | 정책 차이·결정 |
| --- | --- | --- | --- |
| 팬오션 오전후반 | 0.459536% → 0.459536% | 16.661250 → 16.661250원 | 주문 유효5봉→3봉; 경제 결과 동일, 기존 보존 |
| SK텔레콤 오전 | 0.207996% → 0.205177% | 94.976250 → 70.721875원 | drawdown 필터 변경; EV −0.002819%p, 일별 순익 −24.254375원, 기존 보존 |

위 금액은 두 initial leg의 **단위 touch replay 모델**이다. 실제10주 순익이나 실체결 증거로 환산하지 않는다. 팬오션 두 번째 다리는 기존/후보 모두 완료4·미체결2·실현106.71원, 첫 번째는 완료6·159.87원이다. SK텔레콤 두 번째 다리는 기존 미체결9·후보7·완료0이며, 첫 번째 완료8→6으로 참여가 줄었다. EV와 참여/완료빈도/순익을 함께 보지 않으면 필터 강화의 손실을 놓친다. H1–H4 전 조합의 추가 인과 실험은 반복하지 않고 선택된 정책의 변경 필드·다리별 기여·노출/MAE 진단을 남겼다. H2 native offsets 변경은 두 다리 가격을 함께 바꾸며 둘째 다리만의 인과 효과로 부르지 않는다.

[제한 재평가 최종 JSON](../../data/report/postclose_research_successor_20260917_20260918/distinct_economic_review_20260918/low_price_existing_logic_full_comparison_2026-09-17.json), [고정 범위 manifest](../../data/report/postclose_research_successor_20260917_20260918/distinct_economic_review_20260918/checkpoints/review_manifest.json). 입력 원본 SHA256 `a5320f9059fa1bade86af9876c14875964d0e11167974a8ad4ae43ecb209c290`를 실행 전후 확인했다. baseline은 target-date 원 보고서의 effective parameters/hash/source를 승계하며 receipt가 없는 hash는 null로 보존한다.

## 구현·리뷰·보완

기존5개 source module과 기존3개 test 파일만 수정했다. 새 Python module/service/성능 guard를 만들지 않았다. producer → profile checkpoint → recommendation validator → prospective validator → native auto policy reader → machine attribution schema 연결을 검토했다.

- LP0/LP2: canonical policy identity, baseline·calibration winner·distinct research challenger 분리, scoped identity와 변경 필드. incumbent1위면 운영 selected는 기존 정책이며 별도 challenger의 연구 양수만으로 승격하지 않는다.
- LP1/LP3: EV 분모를 COMPLETED entry notional로 맞추고 attempted-notional 실현 수익률은 다른 필드로 보존한다. 다리별 completed/held/no-fill·순익, 표본·빈도·미청산 위험을 함께 기록한다. 비용/완료값 null·bool·NaN/Inf는 거부한다.
- LP1/LP4: 비용/날짜·정책 차이·terminal resolution을 독립 검증한다. carry0 실현은 경제적0이 아니다. 현재 분봉에는 실제 custody 청산 사건이 없으므로 carry terminal을 합성하지 않고 `custody_censored_or_terminal_gap`으로 남긴다.
- LP2: retrospective proxy의 half-floor 선언과 실행 불일치를 `robustness_diagnostic_not_standalone_veto` 계약으로 명시했다. 별도 prospective family의 half3/full10/holdout3signal·4leg 승격 guard는 유지한다.
- LP5: 기존 expanded producer 안에 cached-only review CLI를 추가했다. 원 profile inventory≤64·원천 content hash·cost·baseline·grid·implementation hash를 검증하고 같은 종목 context를 공유한다. 버전이 다른 checkpoint는 오승계하지 않는다. API/token 호출 전 CLI 분기로 빠지며 notifier/policy writer를 호출하지 않는다.
- LP6/consumer: 경제성 flags를 입력 양측 결과에서 재구성한다. 정상 flat0의 참여 순익 개선은 기존 new-symbol/time-extension family가 평가할 수 있으나 EV uplift는 null이고 dual EV 개선과 분리한다. 기존로직 lane의 live 자동 편입 권한은 없다. 이미 동결된 v6 정책 읽기는 기존 검증을 보존하며 새 정책 생성은 v7을 요구한다.

리뷰 보완: serial reference의 identity 메타데이터, manageable carry를 추천으로 오인한 기대값, native publisher fixture의 양측 경제 근거, prospective 빈 baseline에서 이전 arm parameter를 잘못 재사용하던 변수 scope를 수정했다. 수정 후 해당 회귀를 다시 통과했다. 최종 검토 범위의 미해결 구현 finding0; 과거 source/경제성 결손을 구현 PASS로 닫지 않는다.

## 검증

저가주 관련3 suite 422PASS. consumer/attribution/wrapper suite는 최초300PASS·3FAIL 후 fixture/근거 보완으로 실패3개 모두PASS. 후속 affected contract145PASS와 마지막 prospective 검증10PASS(36 deselected)를 확인했다. 반복 실행은 서로 중복되므로 합산하지 않는다. 관련 compile, `git diff --check`, 링크·단일 owner·print-only backlog parser를 수행한다. 상세 log는 `tmp/low-price-economic-comparison-20260918/`에 보존한다.

실제9/18 동결 native 정책 readonly load3개 PASS, hash `5cd93e2f3520ac0a420a10fc022b523036736e044d1ae9b9961df6ba8cdb89cc`, policy write/order0. 광범위 trading suite·API 호출·전체 장후 chain·새 계좌 수집·주문·외부 Project/Calendar sync는 실행하지 않는다.

## 남은 구조적 결손과 closure

| 결손 | owning 입력·다음 조치 | closure |
| --- | --- | --- |
| carry55 | 원 결과의 held/carry/custody 필드; 실제 owner의 lineage 있는 exit/terminal 입력이 없는 과거는 censored 유지 | native 사건·비용·일자 대사 또는 명시 과거 제외; 시간 경과만으로 해결 불가, ETA null |
| 작은 표본/무후보7 | 고정된 후보·원 family/sample guard 보존 | 새 유효 cohort에서 완료 분모 확보; 실패 뒤 후보 교체 금지 |
| 이미 본 holdout | 연구 선택·검증 usage 명시 | 미사용 미래 검증에서 동일 비용/terminal·sample gate 충족 |
| 과거 공동경제 source | 9/17 widget 완성본·현금/보유/예약·same-stage 입력 결손은 전 owning 결과 그대로 | 동등 보존 원천 없으면 joint EV/net null; 개별 EV 합산 금지 |
| 실제 적용·실손익 | selected source·future invocation·actual PID 소비·정책/주문/완료 비용 근거 별도 | 자연 consumption와 rolling/cumulative 실제 비용 차감 성과; owner OPEN 유지 |

## 커밋·푸시·배포 receipt

검증된 source를 immutable managed release로 선택하고 영향받는 기존 service의 다음 실행 source pin을 갱신한다. 실행 중 거래/PID를 재시작하거나 현재 동결 정책을 재발행하지 않는다. 최종 commit·selector·unit 설정·보호 hash receipt는 `tmp/low-price-economic-comparison-20260918/deployment.json`에 기록하며 실제 PID 소비와 별개다.

실제 구현 commit `581b17cb12a72b0782846f2221317f25b4f2ecf5`를 원격 main/review branch에 atomic push했다. 12:27 KST selector는 `/home/ubuntu/KORStockScan-runtime-releases/low-price-distinct-economics-20260918`을 선택했다. 기존 low-price auto-expansion/widget evaluation/machine final-refresh unit의 다음 실행 `ExecStart/WorkingDirectory`만 source pin으로 갱신하고 `daemon-reload` 후 원 환경파일·resource/restart/보안 설정 불변을 확인했다. 서비스 restart0, 거래 PID41757/NRestarts0 및 당시 final-refresh PID195934/NRestarts9는 배포 전후 같았다. 이 final-refresh의 기존 자연 retry 이력은 이번 수리의 재실행이 아니다. 해당 진행 중 PID는 이전 root를 유지한다.

새 release의 readonly 소비에서 기존 동결3개·policy hash 불변과 distinct 결과62개 재구성 PASS를 확인했다. selector/router/source clean·보호 원본/동결 SHA PASS. 이것은 분석 reader 검증이며 새 거래 PID 또는 자연 주문/비용 경제성 증거가 아니다. deployment 후condition 검증에서 없는 optional `EnvironmentFiles` key를 비교하던 일회성 receipt 스크립트 오류를 수정해 검증만 완료했으며 selector/unit mutation을 반복하지 않았다.

[갱신된 장후 기계 판정 JSON](../../data/report/postclose_research_successor_20260917_20260918/distinct_economic_review_20260918/low_price_full_research_result_review_2026-09-17.json)은 실행·분석·결손·달성가능성·소비를 분리한다. 기존3건 자기 비교를 대체한 새로운 결과 generation이며 기존 판정 JSON/원 보고서를 덮어쓰지 않는다. 자연 acceptance는 현재 checklist의 동일 OPEN owner로 남겼다. 추가 재실행은 미확보 과거 입력을 반복하는 것이 아니라 유효 미래 원천/terminal이 새로 확보됐을 때만 필요하다.
