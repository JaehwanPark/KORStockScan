# AI quality 미래 원천·독립 운영 경제성 후속 검토 (2026-09-18)

사용자 승인 범위는 기존 계획 보완, source producer/consumer 수리, 반복 리뷰·검증, 관련 commit/push·immutable successor 선택 및 제한 장후 결과 재생성이다. 봇 재시작·주문·조기 PREOPEN 확정·env/provider/guard/cron 변경은 수행하지 않는다. 실행 owner는 9/18 checklist의 `KiwoomCommonHealthOpportunityCostAcceptance0917` 하나를 재사용한다.

## 기존 완료 판정 정정

원본/v2 라벨 보존과 diagnostic reader 전환은 기존 완료 증거를 재사용한다. ADQ1의 pre-AI 계획 생성, lossless producer census, 초기 BUY→HOLDING 상태 전이, 실측 오차/stress 하한과 원화 provider 비용 결속은 기존 구현·검증 미완료였다. future source 생성 계약을 입증하지 않은 상태를 자연 표본 대기로 분류한 완료 판정은 정정한다.

## 최초 결손과 수리

| 최초 사유 | 자연 9/17 원천 | 수리·보존 및 closure |
|---|---|---|
| 손절 결손11 | compact exact hot payload에 fixed research stop이 없고 실행 plan은 AI_PASS 이후 생성. 원천의 최초 생성 경계 결손 | 기존 5 live analyze_target caller에서 pre-AI source-only owner plan/context를 생성. 당시 stop/cost/TTL/qty/budget를 loaded 운영 owner로 기록. 과거 삭제된 input/stop은 추정 복원하지 않음. |
| 자연 계약 불충족9 | materialized label 기준 timeout8, semantic rejection1. 정확 attempt `analyze_target:394800:1789632325868:cf98178b`, `entry_risk_pass_residual_risk_not_considered` | 모두 실제 부적격. false exclusion으로 바꾸지 않고 보존. timeout을 자연 AI 판단으로 간주하지 않음. |
| 경로 평가 불가1 |27221013:09:09 판단의 canonical context venue=KRX_NXT_INTEGRATED, trace venue=KRX, route_equivalence_proven=false.10m label 없음/partial(1m·30m만 존재) | 과거 window는 누적으로 복구되지 않음. 새 source는 existing native path cutoff/continuous full-depth 검증, gap은 null/blocker. |
| 운영 모델 source gap | 원 report retained execution0, invalid3 plans, original completed-cost outcome 부재, validated scope0 | lossless seed2MiB + execution family partition + producer stage count/identity census; pre-AI population과 actual model calibration 분리; AI 응답 availability 이후만 CF 실행. |
| initial holding 상태 | WATCHING에는 실제 BUY fill owner의 exit_mode/stop가 없음; micro estimator 상태 없는 interpreter는 차단 | 실제 receipt의 기존 필드 설정을 pure helper로 공유. frozen loaded rules/initial micro state/native quote updates 재현. Main의 이미 확보한 시장 국면은 기존 cache/동일 process WS depth cutoff에서 관측. 외부 서비스 미기록 경로는 명시 unsupported. |

큰 trace67,190,422bytes와 payload171,114,354bytes는 전수 raw scan하지 않았다. 작은 frozen projection/materialized labels를 확인하고 정확 semantic rejection은 bounded seek 구간1,938,419bytes로 확인했다. 자연21은 KRX11·통합 애프터마켓10이며 후자는 현행 initial operating model의 SOR 지원 밖이다. 공통 KRX로 합치지 않는다.

## 경제성 문제와 실행 계약

Machine은 현재 ENTER_NOW의 spread/fillability/book-ratio 필터 변경으로 손실·노출을 줄이는 가설을 기존 grid에서 평가한다. 실제 downstream compact 판단을 고정한다. non-entry를 신규 ENTER로 바꾸는 경우 미호출 AI를 가정할 수 없어 별도 진단/unsupported이다. Compact는 실제 machine ENTER_NOW에 한해 현재 등록 prompt의 PASS/VETO 변경을 비교한다. CAUTION recheck 미종결·partial/no-fill cancel/late-fill·ADD·미기록 holding external services는 null/owner/closure로 분리한다.

동일 frozen qty/budget/availability/downstream owner를 사용하며 real SELL을 CF 청산으로 붙이지 않는다. 기존 full holding interpreter와 trade_profit 비용 owner로 순익·EV·tail·capital/reserve·fill 참여율을 계산한다. 겹치는 단일 owner 기회는 allocation 계약 없이 이익을 합산하지 않는다. 모델 holdout은 후보 학습보다 앞서고 후보 holdout은 별도로 미사용이어야 한다. v4는 기존20/20/2dates/coverage1.0/tail/stress/일별 순익 조건을 유지하고, changed decision에 empirical two-arm error envelope + reviewed inference cost를 차감한 paired base/stress 하한을 추가한다. 이는 모델 오차 envelope이며 통계적 신뢰하한·실제 이익이 아니다.

Provider 비용은 기존 operator-reviewed zero-accounting artifact의 모델·유효기간·원 bytes/hash가 유효한 경우만 Δcost0이다. USD nonzero에 임의 FX를 만들지 않는다. 원화 비용 계약이 없으면 null/source gap이다. 미래 policy effective date도 비용 유효기간 안이어야 한다. 운영 arm/model/cost 결손이면 diagnostic proxy 행에 candidate provider API를 사용하지 않는다.

실제 submit의 machine/compact 버전·bundle·attempt·trace·PID receipt를 기존 frozen context/완료 비용 receipt에 전달한다. 기존 actual custody/order journal의 capital join과 post-apply helper를 재사용하여 joint applied version별 episode 중복 제거·rolling/cumulative 완료 순익·EV·tail·노출·model error를 평가한다. Split 정책 적용만으로 machine/compact 소비를 추정하지 않는다. descriptive 실제 성과와 causal 개선은 별개다.

## 검증과 배포 증거

최종 검증·commit/push·immutable 선택·재생성 receipt는 `tmp/ai-quality-source-attainability-20260918/{validation,deployment,regeneration}.json` 및 해당 log로 기록한다. 운영 producer가 만든 plan→실제 저장/projection/census→독립 full holding stop/비용/capital/reserve 계산→public request/response storage→compact source join/paired loss-avoidance 계산을 검증한다. 다른 통제 fixture로 독립 model/후보 holdout 통과 시 활성 policy/Daily/PREOPEN/runtime 소비 및 실패 carry/hash/scope/stale/holdout 차단을 검증한다. 이 증거는 자연 표본/경제 성과가 아니다.

## 완료 범위와 자연 OPEN

구현 검증 완료는 지원된 미래 producer/storage/consumer 및 계산/독립 선택/policy 소비 경로가 실제 작동하는 경우만 선언한다. 현재 9/17 frozen 자연21은 이전 원천 결손/실제 부적격/과거 window gap을 보존하므로 신규 후보0, ΔEV/actual uplift null이며 valid no-edge가 아니다. 다음9/21 정책은 독립 후보 없음이면 incumbent carry로 준비한다. 전체 9/17 native chain DONE, PREOPEN finalization/PID 소비 및 실제 이익을 주장하지 않는다.

자연 OPEN은 지원 기회 관측·actual completed-cost owner journal 축적·scope별 선행 empirical model holdout, 이후 별도 후보 holdout, 정규9/21 PREOPEN/PID·자연 적용·실제 완료 비용 손익이다. SOR/partial/no-fill/uncalled downstream AI/미기록 external-service scope는 자연 기다림으로 바꾸지 않는다. 범위 밖 새 모델/운영 계약은 기존 owner의 구체 blocker와 closure를 유지한다.

공식 Kiwoom 검토: upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`, 조회2026-09-18T18:43:31.104105+09:00. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`의 kt00011, `postman/kiwoom-openapi.postman_collection.json` 확인. `kiwoom_docs`는 해당 tree에 없었다. 기존 bounded source_only capacity owner를 재사용하며 REST request/parser/protocol/FID/order mapping을 수정하거나 broker call을 검증 과정에서 실행하지 않았다.

후속 route 대사: 자연 KRX quote-view11의 `broker_route`는 SOR, 통합 애프터마켓10의 route는 NXT이다. 현행 직접 KRX 승격 cohort/단일 venue operating model을 유지하며 quote venue와 실제 broker route를 합치지 않는다. 미래 producer는 exact broker route를 요구하고 route/quote venue 불일치를 명시 unsupported로 기록한다. Frozen model scope에도 broker route를 포함한다. SOR routing/통합 venue 계약 확대는 기존 operating owner의 별도 source/model closure이며 단순 자연 표본 대기가 아니다. 직접 KRX/NXT 지원 입력의 producer·계산 회귀 통과를 현재 모든 자연 route의 승격 가능성으로 확대하지 않는다.

검증 제외의 근거: origin/main에도 `test_production_string_fields_roundtrip_through_logger_and_report`는 이미 제거된 `_route_arm` fixture를 참조하고 `test_runtime_capture_uses_only_matching_bbo_quantity`는 폐기된 `observe_avg_down_exit_replay_cycle`(항상0)의 관측을 요구한다. 이 둘의 최초 suite 실패는 별도 log에 보존하며 현행 full holding interpreter 테스트 및 새 production writer→paired 계산 회귀로 영향 범위를 검증한다. 퇴역 producer를 테스트 통과용으로 복원하지 않는다. 현행 observer의 실제 enabled/config/PID·자연 source receipt는 다음 정규 기동의 acceptance이고 기본OFF 관측자를 임의로 켜지 않는다.

최종 source-label identity 검토: 운영 CF가 유효하더라도 원 label의 payload/trace venue·session 또는 canonical-context venue/session 충돌은 해제하지 않는다. source projection v3에 이 사유를 보존하고 기존 primary source quality 경계를 승계한다. 자연 path 제외1건은 정확 attempt `analyze_target:272210:1789618146665:381de9ad`의 canonical venue/session mismatch이며, 다른 098460 사례와 혼동하지 않는다.
