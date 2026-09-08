# 2026-09-08 현재 due 작업 실행·보완

관찰: `2026-09-08 09:42~09:53 KST`. 대상 거래일은 `2026-09-08`이다. 사용자 요청은 직전 보고의 지금 필요한 점검 실행이며, 장후 전체 재실행이나 실주문 설정 변경이 아니다.

## 판정

현재 범위는 **YELLOW**다. 장전 적용·scout 지시 귀속·census 진단 수리 자연 acceptance·비우선 sim 최소 점검은 닫았다. 메인 제출 drought, micro source loss, 위젯/후속 machine 자연 acceptance는 기존 당일 owner에 남긴다. 전체 장중/장후 완료나 경제성 개선을 선언하지 않는다.

두 결함을 보완했다: 위젯 차단 정책의 비결정적 직렬화, 과거 canary 측정 이후 별도 저장소 수리의 호환 근거 누락. 매매 process 재기동, env/policy/guard 변경, 주문·취소, broker API/Provider 호출, canonical 장후 report 재생성, Project/Calendar sync는 실행하지 않았다. 다른 세션의 pattern-lab/workorder/EV 수정은 보존하고 이번 리뷰에 포함하지 않았다.

## 실행 결과

| Owner | 관찰 및 판정 | 남은 acceptance |
| --- | --- | --- |
| ThresholdEnvAutoApplyPreopen0908 | 당일 07:35 apply와 20 selected family manifest를 현재 PID `461794`에 읽기 전용 대사. `status=pass`, PID missing/mismatch/findings 0, policy fail/unverified selected 0. 수동 env 우회 없음. | 장전 적용 확인 완료. 실제 family별 효과는 RuntimeEnvIntradayObserve0908에서 별도 확인. |
| RisingMissedScoutRuntimePreopen0908 | 아래 stable ID 3개가 main workorder에 각각 1회 `attach_existing_family`로 연결. 모두 `runtime_effect=false`, `allowed_runtime_apply=false`, 당일 selected family에 없음. `source_only_no_runtime_authority`. | 적용 귀속 확인 완료이며 BBO 경제성 floor 충족은 아님. #8/#9 상세검토를 재개하지 않음. |
| ScannerPremarketCensusNaturalAcceptance0908 | 자연 09:15 report의 대상일·hash·`required_in_observed_window`와 due-session 실패 보존을 확인. NXT 장전 12 capture 정상, KRX all due 3 capture 정상; KRX liquid 2 capture 및 NXT overlap 600.37초 gap은 여전히 실패. | 예정 구간 오탐 수리 acceptance 완료. 전체 recall은 `insufficient_evidence_scanner_recall`; 다음 정상 12:00 report에서 별도 판정. |
| RuntimeEnvIntradayObserve0908 | 09:50:04 KRX 보고서 `SUBMIT_DROUGHT_CRITICAL`. exact attempt 54 = terminal 48 + pending 6, submitted 0, 미분류 terminal 0. raw terminal ID/시각도 대사. | 제출/체결/terminal/net 효과는 OPEN. 기존 postclose drought workorder handoff 유지. |
| MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908 | canary는 row-exclusion-only, worker/writer 오류·queue-full·storage stop 0. trade/depth writer 2/2. 09:43:50 유효 enqueue 5739/5246 → 09:49:13 7862/6611로 증가. 09:53 여유 공간 약 10.73GB. | 지속적으로 fresh한 원천이라는 뜻은 아님. timestamp rejected-tail 64개는 전체 205149개 loss를 복원하지 못함. through-close 연속성·exact exclusion/Provider hold는 OPEN. |
| WidgetEpisodeRecommendationApplyAcceptance0908 | 위젯 PID `21846`, collector PID `249964` 정상. 당일 080220 정책 ID와 KRX runtime eligible state 확인; 09:50 signal/order 없음. TYM preflight/live 성공, 09:20:05 `NO_TRADE`, `entry_execution_velocity_too_slow`, 두 leg NO_FILL. | 정상 guard를 완화하지 않음. NHN midday 13:25/13:29, SD afternoon 14:10/14:14 및 자연 signal/custody는 기존 OPEN 항목. |
| SimProbeIntradayCoverage0908 | 현재 PID에서 Swing probe/auto policy와 greenfield OFF. surviving scalp candidate-window/AI-budget ON은 real 권한 아님. 독립 sim worker 미관측, scalp 저장 state active 0; Swing 저장 state 3행은 2026-01-11 표본이며 전부 주문 false/broker forbidden true. | 현행 비우선 최소 점검 완료. historical active 3행을 현재 holding이나 당일 EV로 사용·복원하지 않음. 당일 source-only sim 표본 0에 shortage/ETA를 만들지 않음. |

scout 원본 ID:

- `order_rising_missed_classifier_prior_feedback_bridge`: implemented/source-only prior bridge.
- `order_rising_missed_scout_scale_in_qty_evidence_split`: implemented/source-only quantity/evidence split.
- `order_rising_missed_entry_turn_bbo_coverage`: implemented source-quality contract, waiting sample. 당일 raw `rising_missed_entry_turn_pre_anchor_bbo_path` 89개를 09:44경 관측했지만 이를 유효 경제성 pair로 세지 않는다.

## 메인 drought와 source 품질

09:50 보고서의 AI unique 21, budget unique 31, latency-pass unique 4, submitted 0은 서로 다른 raw 모집단이다. 이를 엄격한 21→31→4→0 인과 funnel로 쓰지 않는다. exact attempt ledger의 배타적 terminal 분류를 사용한다.

09:40 root attribution은 latency DANGER 16 event/10 unique, `orderbook_micro_spread_wide`, spread guard와 stale 1건이다. quote refresh 12회 중 11회 적용, latency 회복 2건은 후속 Entry AI authority에서 차단됐다. raw `41223/387690`은 09:30:55 `entry_ai_result_stale_or_untrusted`, 09:31:46 `fresh_ai_wait_observation_only_probe_veto`; `41080/052690`은 09:40:13 `fresh_ai_drop_real_buy_veto`다. 이 근거는 차단 원인 식별이지 모든 차단의 경제적 최적성 보증이 아니다. threshold/spread/stale/AI guard 완화는 하지 않았다.

micro의 최근 rejected 표본은 exchange→recorded receive 약 115~133초, recorded receive→rejection check 약 4~14ms였다. 이는 collector enqueue 이후 worker 병목 근거가 아니지만 socket·수신 처리 이전 지연까지 외부 API 원인으로 확정하지 않는다. 현재 유효 수집은 재개됐고 기존 bounded rejection과 replay hold를 유지한다. 전체 손실의 exact receipt가 없는 상태를 정상 표본이나 0 EV로 바꾸지 않는다.

census primary master missing `0011A0`, cadence/BBO/resolved/right-censor floor는 남아 있다. 09:15 report 이후 수집 cron은 계속 DONE이며 보고서 갱신은 09:15/12:00/15:15/19:45 계약이다. 09:53에 파일이 09:15라는 이유만으로 stale failure를 만들거나 비싼 report를 중복 생성하지 않았다.

## 발견 결함과 review/fix

### 1. Widget blocked-policy hash 비결정성

`policy.py`가 blocked session의 `allowed_entry_states`를 `tuple(frozenset)`로 생성했다. 별도 프로세스 네 번의 동일 loader 입력에서 034020/042660 두 blocked session만 `ENTRY_READY, ENTRY_CAUTION` 또는 역순으로 변했다. runtime receipt의 raw JSON hash가 따라서 비결정적이었다.

- 수정: blocked session의 상태를 `tuple(sorted(SUPPORTED_ENTRY_STATES))`로 고정.
- 회귀: 반대 iteration 순서 두 개를 주입하는 신규 테스트가 수정 전 hash 비교에서 실패하고 수정 후 통과. 서로 다른 `PYTHONHASHSEED=1/2/3/4`의 당일 loader hash는 모두 `ed0d413424c6648f84c82fed0c06cdc9d11907e8f8b1f4f8e7442bfac8d90818`.
- 직접 consumer `engine.py`는 허용 상태의 membership만 사용하며 순위/첫 원소 권한이 없다. blocked=false 전환, 상태 추가, 수량 변경은 없다. 회귀에서 `new_entry_runtime_eligible=false`, 기존 reason, actual order false, broker bypass false를 확인했다.
- 기존 07:58 시작 receipt는 변경하지 않았다. 두 blocked tuple만 기존 역순으로 재구성하면 원래 loaded hash `5369427e8a7a02b344c25e2ae75fe6d9df7c626badbb391c53f3f7226e044d23`와 정확히 같고, 기존 read-only verifier는 `verified_requested_startup_fields`, finding 0으로 검증한다. 새 정렬 hash를 옛 receipt에 넣어 PASS를 조작하지 않는다.
- 이는 **과거 시작 정책 검증**이다. 현재 signal별 소비나 새 코드의 PID 반영은 아니며 `current_policy_consumption_verified=false`를 그대로 둔다. 위젯을 재기동하지 않았고 새 정렬은 다음 정상 코드 로드부터 사용된다.

### 2. Frozen canary storage compatibility 누락

처음 5개 모듈 검증은 `157 passed, 1 failed`였다. 실패는 frozen baseline의 storage hash와 현재 코드 불일치였다. `f9bd4637`에서 offline `maintain_report_artifact_storage`가 두 과거 semantic mismatch를 압축하지 않고 원본 보존하는 수리를 받았고, `2078fbd1`에서 포맷만 변경됐다. callback/observer/guard 변경은 아니다.

- 과거 byte hash: `cc72b533aed4081283ed1cb4d48e50239b13215e3c828bc98139d3bcb7325f9f`.
- 현재 reviewed byte hash: `acbddd3e2e96bef5404142287b7cd15d20d11154de9693bb4f7a918723135816`.
- 위 함수만 제외한 전체 module AST hash는 과거/현재 모두 `9170ec9965725ede3f59c00d30877772cb738c1e50013ad3d55cdf35a8ac06d1`로 동일.
- frozen 측정 JSON과 guard TOML은 변경하지 않았다. 테스트에 이 **정확한 과거→현재 storage pair**와 나머지 AST pin을 별도 호환 근거로 추가했다. 나머지 10개 evidence 파일은 기존 raw hash 일치를 그대로 요구하고, 향후 storage 변경도 현재 byte pin에서 실패한다. 이는 새 latency 측정 또는 guard 조정이 아니다.
- storage 직접 테스트는 현재/과거 날짜, 두 semantic rejection/다른 hash error를 구분하고 원본 보존·compression 없음·tuning approval 없음까지 확인한다. 실제 압축·삭제는 수행하지 않았다.

## Evidence와 검증

| 관찰 파일 | SHA256 |
| --- | --- |
| 09:15 census JSON | `2d0945910e1adbd754a50cbf19dabdfa9477ccfde7f85683d334e710aadc501e` |
| 9/7 scout workorder JSON | `850cddbaaf3a9d32000049ec9a2ed4048dd0d5cdb8639e2441bdfd9fba15bfb9` |
| 09:50:04 BUY Funnel JSON | `af1d1389ae26d35f6bed27957504f83d4918051d936e51266f0984824ef0bde7` |
| 기존 widget startup receipt 파일 bytes | `569116bfa92c60b5935a3ec745099cb34a8f075f88bc816e2f0709e3ccbcb583` |
| 보존한 frozen baseline JSON.txt | `366e94b189383e17158f2267b3c69066b7e16007c036013907461dae2cd16e54` |
| 변경하지 않은 canary guard TOML | `6fb3781d01b89352aeaf828a2aee25474066b9ab2581bbcad2880de71c5124cf` |

관찰 파일은 이후 자연 producer가 갱신할 수 있다. 위 값은 09:53 읽은 generation의 기록이며 immutable source snapshot을 새로 발행한 것이 아니다.

최종 검증: 관련 9개 모듈 `332 passed` (20.02초), 변경 Python 3개 compile·Black·Ruff E9/F63/F7/F82, `git diff --check` PASS. 문서 backlog print-only parser exit 0/32 tasks를 확인했고 닫은 4개 ID는 OPEN 목록에서 제외됐다. 같은 시각 다른 세션이 추가한 PatternLab OPEN 항목은 그대로 보존했다. review gate의 unresolved finding 0은 이번 직렬화/호환 검사 수리 범위에 한하며, 기존 source loss·표본·경제성 blocker가 해소됐다는 뜻이 아니다.

기존 widget receipt mismatch는 수정 전 byte order를 정확히 재구성한 제한적 시작 정책 검증으로 닫았다. 최신 canonical hash와 옛 receipt가 직접 같다고 주장하지 않는다. 새 코드의 자연 PID receipt, micro의 전수 exclusion 및 장마감 연속성, 전체 scanner recall과 후속 machine 실행은 [당일 체크리스트](../checklists/2026-09-08-stage2-todo-checklist.md)의 기존 OPEN owner를 유지한다.

## 10:03 재리뷰와 남은 작업 실행

사용자 후속 지시에 따라 위 변경과 직접 consumer를 다시 검토했다. 위젯 정책 로더→시작 receipt→검증기→Entry membership/custody, canary frozen pin→offline storage 보존 테스트가 범위다. 다른 세션의 pattern-lab/EV 수정은 포함하지 않았다.

- 회귀 보완: `test_legacy_policy_list_order_is_not_silently_rehashed`를 추가했다. 옛 tuple 순서 receipt에 새 canonical hash를 주면 반드시 mismatch이고 정확한 옛 hash만 성공한다. receipt bytes 불변과 `current_policy_consumption_verified=false`도 확인했다. 운영 코드의 추가 변경은 필요하지 않았다.
- 재검증: 첫 재검토 294 tests PASS 뒤 회귀 추가·재리뷰 후 **295 passed**(25.51초). widget signal auto trade/정책/runtime verification, micro canary/storage 5개 모듈이다. compile·Black·Ruff E9/F63/F7/F82·diff check PASS. 이번 범위 unresolved finding 0이며 전체 시스템 무결함 보증은 아니다.
- 현재 raw 감사 실행: `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-09-08 --print-summary`를 기존 heavy-analysis lock으로 1회 실행했다. write/backfill 없이 41529 events·72 stages, PASS, hard gap/excluded row/unknown token/review warning 모두0, tuning input allowed true. 14:20 점검/20:10 자연 preflight를 대체하지 않는 수동 진단이다. enqueue 전 micro 유실은 분모 밖이므로 이 PASS로 replay hold를 해제하지 않는다.
- Drought handoff 검증: 10:00:04 BUY Funnel(source SHA256 `f4ab11e29cc11090b45a3890fa0623c28fe0609f8d4cc3534fad8e047f257e88`)을 기존 `_buy_funnel_sentinel_followup_orders`에 입력해 native order6개를 메모리상 생성했다. `order_entry_submit_drought_auto_resolution`은 implemented, `order_entry_post_submit_contract_gap_review`, `order_entry_broker_receipt_contract_gap_review`, `order_entry_fill_quality_contract_gap_review`, `order_entry_telegram_post_submit_contract_gap_review`, `order_entry_source_taxonomy_contract_gap_review`는 implemented_but_waiting_sample이다. 모두 runtime/apply false, workorder→EV→runtime summary→postclose verifier 연결을 유지한다. 정식 장후 generation을 발행하거나 무주문을 실체결 증거로 바꾸지 않았다.
- 추가 machine terminal: `sd_biosensor_morning` 09:29:09→09:40:06 Result success/exit0, liquidity touch-depth guard/NO_TRADE, 두 leg NO_FILL/position0. `nhn_morning` 09:39:09→09:51:01 Result success/exit0, scan window closed/NO_TRADE, legs0/position0. 정상 terminal이라 재실행하지 않았다. 이후 신규 midday/afternoon owner와 별개다.
- Micro/위젯 최신 관찰: 10:03:22 canary row-exclusion-only/stop false, enqueue8802/depth7314, worker/writer 오류0. 10:01 위젯080220 당일 정책/KRX eligible은 유지되나 source state/signal/order는 없다. 표본을 만들기 위한 강제 주문·재기동은 하지 않는다.

판정은 계속 YELLOW다. 지금 가능한 재리뷰·진단·handoff 검증은 수행했고 이후 natural source/신호/체결/후속 timer는 기존 OPEN owner와 예정 시각에서 확인한다. 오전 코드 검증으로 장마감·다음 정상 PID·경제성 acceptance를 완료 처리하지 않는다.
