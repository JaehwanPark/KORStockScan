# 주성엔지니어링 하드스톱: 진입 패턴·보조판정·보유·청산 연구 — 2026-10-15

## 1. 결정과 범위

이번 사례의 우선 보완 대상은 **한 호가 반등과 지속 가능한 회복의 구분, 기계가 본 위험 문맥과 보조 입력의 차이, 보유판정 입력 결손, 운영 종료 조건과 장후 재생의 연결**이다. 손실 한 건을 근거로 손절을 넓히거나 기존 약세 차단을 일괄 복원하는 결론은 내리지 않는다.

사용자가 제공한 [14:41:28 KST 모니터링 증거](../../tmp/jusung-exit-monitor-20261015-1438/verification.json)를 기준으로 조사했다. `036930`, Main `record_id=49294`는 수동관리 이관 후 1주 보유 상태이며, 그 시점까지 Main 매도 주문·체결과 실현 순손익 종결은 확인되지 않았다. 미체결 0건은 보유 0주를 뜻하지 않는다. 이후 상태를 새로 계좌 조회하거나 수동 매도를 실행한 작업이 아니다.

이 문서는 연구 결과다. [리뷰 게이트](/home/ubuntu/.codex/skills/korstockscan-review-gate/SKILL.md)에 따라 원천·소비자·당시 실행본을 대조하고 작은 원본 입력 재생을 검증했다. 자동매매 제외 파일, 운영 정책·임계값·보조 프롬프트·provider·주문·프로세스는 변경하지 않았다. 기존 작업 중인 코드와 문서도 보존한다.

## 2. 증거 신원과 전체 흐름

주 증거는 [동결 원천 명세](../../tmp/jusung-pattern-flow-research-20261015/source-read-manifest.json), [검증 결과](../../tmp/jusung-pattern-flow-research-20261015/verification.json), [기계 원본](../../tmp/jusung-pattern-flow-research-20261015/machine-exact.json), [실제 보조 입력](../../tmp/jusung-pattern-flow-research-20261015/ai_decision_payloads.matched.json), [범위 제한 pipeline 원문](../../tmp/jusung-pattern-flow-research-20261015/pipeline-raw-bounded.excerpt.jsonl)이다.

| 단계 | 당시 증거 | 해석 |
|---|---|---|
| 14:06:31.611 기계 신호 | `ENTER_NOW`, `legacy_dd5_0_8_vol_up_v1` 단독 일치, native sequence `6680` | 낙폭·거래량 조건을 만족한 FIRST_UPTICK |
| 14:06:32.567 기계 캡처 | attempt `aims-5f790d73c14eb307d298`, PID `2039852`, start ticks `10014770` | 당시 commit `bb4808c77087231b072efbd3ea12271fbb3889c6`에 결속 |
| 14:06:34.355 보조 응답 | request `analyze_target:036930:1792040793119:cac61080`, `PASS`, confidence `84` | 실제 응답 인용은 `observed_machine_signal` 하나, 반대 근거 없음 |
| 14:06:34.873 제출 전 | `BUY_DEFENSIVE`, `safe_normal_entry_allowed`; 약세 veto는 `risk_context_only` | 기존 약세 판단이 사라진 것이 아니라 보고 문맥으로 남음 |
| 14:06:35 매수 체결 | 주문 `0044238`, 체결 `102164`, 210,000원 × 1주 | 총 계획 5주 중 선행 주문 1주 체결. 이 주문 자체는 1/1 완전체결 |
| 14:06:38.575 잔량 종료 | bundle `036930-probe-82e3caeaf0db`, `residual_revalidation_timeout` | 호가 방향 MIXED 재확인 미완료. 나머지 4주는 미제출; 미체결 취소 4주로 세지 않음 |
| 14:07:20–14:15:33 보유 판정 | 22회 관측 시점의 path 행 63개, 모두 `INSUFFICIENT`, provider 호출 0 | AI HOLD/EXIT 의견이 존재하지 않음 |
| 14:15:49.972 하드스톱 이관 | 현재가 207,500원, 기록 순수익률 -1.42%, 기록 peak -0.23% | preset 하드스톱 → 호가 확인 경로 → 수동 제외 등록 → SELL 제출 전에 반환 |
| 14:28 재기동 이후 / 14:41:28 확인 | PID `2276473`, commit `451b6c1ec84fafa563d95381e95c814ac2b2b18b` | 모니터링 실행본은 진입·하드스톱 실행본과 다름. 수동 제외 유지 |

기계 observation SHA는 `89d4a7fd212b2f70d10b915287a71acfec3fbfae93c91b91cd09738d333969de`, bundle SHA는 `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`이다. machine→request→trace를 신원·hash로 대조했다. wire input SHA `37bfb372…`와 logical replay input SHA `e451dcee…`, trace의 별도 payload hash는 서로 다른 표현이다. 서로 같아야 한다고 가정하지 않고 compact binding으로 확인했다.

표의 confidence 84는 보조 응답 필드이며 검증된 수익 확률 84%를 뜻하지 않는다.

## 3. 기계 진입: 무엇을 회복으로 보았는가

당시 legacy 조건은 `drawdown_5m_pct >= 0.8` AND `volume_ratio_60s >= 1`이다. 실제 값 0.9456%, 1.5708이므로 조건 충족은 코드와 일치한다. [조건 계산](../../src/engine/scalping/continuous_reversal.py)의 통과를 상승 지속이나 고점·저점 상승 전환의 확인으로 확대 해석하면 안 된다.

| 진입 시점 관측 | 값 | 패턴상 의미 |
|---|---:|---|
| 최근 10체결 매수 물량 / 전체 물량 | 287 / 310주 = 92.58% | 강한 매수 체결 비중 |
| 최근 10체결 가격 변화 / native 60초 수익률 | 0% / 0% | 매수 체결 비중에 비해 가격 전진이 없음 |
| 최근 10체결 가격 | 209,500 / 210,000원 두 가격 | 7.301초 구간에서 한 호가 왕복 |
| 첫 반등폭 / 스프레드 | 각각 0.238663% | 반등폭이 호가 간격과 같음 |
| 세션 앵커 대비 / 구조 | -4.3280%, `DOWN`, `MIXED` | 고점 상승·저점 상승 모두 false. 전일 대비 등락률과 다른 값 |
| native 60초 VWAP 대비 | +0.118421% | 매우 짧은 구간의 VWAP 상회 |
| 별도 micro VWAP 대비 | -10.13bp | 기준 창·시계가 다른 지표. 앞 값의 부호 차이를 계산 오류로 단정하지 않음 |
| 기계 저장 완료봉 문맥 | 5봉 -0.3563%, 10봉 -0.8274%, 돌파 미확인 | 국소 반등 위에 남아 있는 하락 문맥. `_AL`/KRX route equivalence는 `not_proven`이므로 별도 원천 검증 필요 |

**연구 가설:** 이번 입력은 “매수 물량이 많으나 가격 전진이 없는 한 호가 반등”에 해당한다. 체결 비중만으로 지속 반등을 판정하는 조건을 보완할 근거다. 매도벽·흡수 주체의 의도나 시장조작을 입증한 자료는 아니다.

제출 경로에는 `spread_1tick_strong_buy_pressure_percent_bps` 예외와 `BUY_DEFENSIVE`가 기록됐다. 따라서 보완 비교는 기계 신호만이 아니라 **한 호가 예외 → 선행 1주 → 잔량 재확인**을 함께 포함해야 한다. 잔량의 사후 MIXED를 매수 전 알고 있던 정보로 옮겨 쓰면 미래 정보 누출이다. 잔량 4주 미제출은 노출을 제한한 사실이며, 5주 전량의 가상 손익을 실적에 붙이지 않는다.

### 3.1 기존 누적 연구 후보와 이번 입력의 실제 대조

[10/15 누적 두 축 연구](main-machine-cumulative-dual-track-research-review-2026-10-15.md)의 주성 REGULAR 고가 후보는 `J:A07+F09`다. 10/14 대표 `A07+F15`와 번호·조건을 구분했다. [기존 연구 발췌](../../tmp/jusung-pattern-flow-research-20261015/existing-research-comparison.json)와 원 연구의 순수 조건 평가기를 사용한 결과는 다음과 같다.

| 기존 후보 조건 | 이번 확인점 결과 |
|---|---|
| F09: spread ≤ 0.1% | 0.238663%이므로 false |
| F15: spread ≤ 0.1% AND buy ≥ 60% | 매수 비중은 통과하나 spread에서 false |
| A07: 저점 재확인 root + 세션 -0.4~+0.4%, 60초 수익률 0~0.2% 미만, VWAP ≥ 0 | 세션 -4.3280%에서 필터 false. root를 새로 재생하거나 이후 확인점까지 배제한 결과는 아님 |

이 확인점은 기존 후보로 제외 가능하다. 그러나 기존 누적 결과는 `914/1,292 → 24/24`, U `2,033 → 7`, 서로 다른 목표 도달 clock `71 → 2`다. 기존 W914개를 모두 제거하고 다른 W24개를 추가한 대안이며, 24승은 10/8에 집중한다. 24개의 독립 실거래 성공이나 이번 손실 회피의 수익성 보장으로 표현하지 않는다.

기존 연구 동결본은 10/15를 native epoch 원천 영수증 결손으로 학습 분모에서 제외했다. 이번 사건의 exact 판정 연결을 확인한 것은 그 전일·당일 원천 자격 결손을 해소한 결과가 아니다. 오늘 사건을 기존 누적 승률의 새 STOP이나 실현 손실로 임의 추가하지 않는다.

기존 승인된 **누적 W/(W+STOP+TIMEOUT) 우선** 비교를 유지한다. 성공 보존율, 최소 표본·일수, 새 holdout·EV를 추가 채택 제한으로 만들지 않는다. 감소한 기회·U·목표 clock은 설명 자료로 공개한다. 이번 단일 사건을 보고 새 종목 전용 영구 제외나 최적 숫자를 정하지 않는다.

## 4. 보조판정: 실제로 전달된 정보와 전달되지 않은 정보

실제 보조 입력은 `continuous_reversal_union_auxiliary_v3`의 compact 표현이다. `buy_pressure_10t`, `buy_pressure_30s`, `return_10t_pct`, VWAP, spread, 낙폭, 거래량, 최근 10체결은 전달됐다. 반면 기계 원본에 있던 **세션 -4.328%, DOWN/MIXED, 고점·저점 상승 여부와 완료봉 구조**는 이 보조 입력에 없다.

근거 ledger는 첫 반등·낙폭·매수 비중·machine signal을 positive로 분류했고 `contradicting_facts=[]`, `risk_fact_bindings={}`였다. 공급자는 PASS의 유일한 supporting fact로 `observed_machine_signal`을 인용했다. 이는 현재 계약을 통과한 **기계 신호의 보조 위험 승인**이지, AI가 완료봉 하락 구조까지 독립 재검증했다는 증거가 아니다. `canonical_context_missing`도 이 compact 입력의 캡처 상태이며, 기계 원본 완료봉 전체가 없었다는 뜻은 아니다.

입력 목표는 비용률 0.0023, 1,800초, 비용 후 +0.4% 선도달 / -3% 손절이었다. 반면 동일 attempt의 `entry_economic_original_stop_receipt`는 `SCALP_PRESET_TP`, hard stop **-1.4%**, grace **0초**, emergency **-2.4%**를 이미 저장했다. 연구 성공 label과 실제 운용 종료 경로가 다른 것이 확정됐다. -3%를 운영 preset에 덮어쓰거나, 연구 label을 이번 건 때문에 소급 교체하지 않는다.

보완은 원 보조 입력·응답·연구 membership·지표를 보존한 채 별도 기계/사후 비교 문맥으로 먼저 수행한다. 향후 보조 입력을 확장한다면 별도 version과 동일 원천의 paired 비교가 필요하다. 기존 PASS를 새 문맥을 본 PASS로 재표기하지 않는다.

## 5. 보유·익절·하드스톱 및 장후 재생

### 5.1 보유 AI 입력 결손 — 확정, 근본 원인은 추가 결속 필요

[원본 path ledger](../../tmp/jusung-pattern-flow-research-20261015/holding-path-votes.jsonl)의 `EXIT_TRAILING_TP` 22개, `EXIT_SOFT_STOP` 22개, `ADD_REBOUND` 19개가 모두 `INSUFFICIENT`, `provider_called=false`다. 사유는 공통 `source_preflight_blocked,holding_flow_evidence_missing`, EXIT에는 `executable_exit_pnl_missing`, ADD에는 `rebound_tape_or_quote_flow_missing`이 추가된다. path 행 63개를 AI 호출 63회로 세지 않는다.

당시 코드의 `handle_holding_state → _build_holding_ai_decision_context → _holding_context_call_views → _collect_holding_path_votes → build_path_vote_input/path_vote_input_gaps`를 대조했다. quote/tick 사전검사를 통과한 뒤에도 context가 비활성 forensic 문맥이면 `_holding_context_call_views`는 live context로 `None`을 넘긴다. 소비자는 snapshot 부재를 preflight 차단, flow를 빈 값으로 처리한다. 이 경로는 관측된 결손 조합을 설명할 수 있다.

다만 **당시 PID의 context 활성화 플래그와 원 context의 blockers를 확보하지 못했으므로 비활성 분기를 단일 확정 원인으로 쓰지 않는다.** 후속 수리는 원 context 상태/활성화·snapshot 생성·flow 투영을 같은 position/quote 신원으로 대조해야 한다. 결손을 PASS/HOLD로 채우거나 preflight를 제거하는 방식은 부적절하다. 보유 표결은 기존 EXIT의 제한된 지연/허용 역할이며, 단독 SELL 또는 preset hard stop 변경 권한이 없다.

### 5.2 트레일링 — 기록상 미활성, 관측·재생 완전성은 실패

기록된 start는 +0.4%, peak는 -0.23%이고 수집한 전이 257개에 armed/triggered가 없다. 따라서 weak/strong 되돌림폭만 바꿔 이번 건을 설명할 근거가 없다. 30·60·120·180초 후의 각 두 anchor quote에서도 ask 210,000 / bid 209,500으로 동일하다. 이는 **그 표본 시점**의 무진전 증거이며, 3분 내내 동일했다거나 지연 진입으로 손실을 피했다는 증거는 아니다.

다음 원천 결손은 별도 수리 대상이다.

- 진입 약 51초 뒤인 14:07:25.858에 `observation_max_samples=256`, sequence 257, `coverage_exhausted=true`가 기록됐다. 이후 원천을 완전한 전이 재생으로 사용할 수 없다. 이 한도가 live evaluator를 멈췄다는 뜻은 아니다.
- `universal_trailing_quote=source_gap/shared_quote_coverage_unverified`, entry context는 `classification_source_gap`, situation pin은 `BASE/legacy_context_unbound`다. 상황별 정책 소비가 입증되지 않았다.
- 당시 실행본은 14:28 HPSP 고점/원천 보완 이전이다. recorded peak -0.23%를 모든 실제 tick의 최고가가 검증됐다는 의미로 쓰지 않는다. 이번 범위만으로 누락 고점이 없었다고 결론내릴 수 없다.

### 5.3 하드스톱과 수동관리 — 동작 경로 확인

14:15:49의 `scalp_preset_hard_stop_pct`는 207,500원 / 순수익률 -1.42%를 기록했다. 같은 시각 직전 `main_stop_source`의 실행 bid도 207,500원이다. 당시 preset 코드 순서는 **preset 하드스톱 → preset grace/emergency → 호가 확인 guard → manual handoff → 미이관인 경우 SELL dispatch**다. 일반 soft stop/AI 유예보다 먼저 적용된다. 해당 사건은 manual handoff에서 반환했다. source stage 이름을 신규 REST 조회 성공 증거로 쓰지는 않는다.

이관 시점에는 emergency -2.4%에 도달하지 않았다. 이후에는 수동 제외가 보유·fast exit를 차단한다. 수동 이관 후 손실이 커졌다고 emergency가 자동매도를 재개할 것이라 가정해서는 안 된다. 자동매도 부재는 관측된 이관 정책과 일치하며, 이를 SELL 제출 실패로 분류하지 않는다.

모니터링 기준 202,500원 mark의 gross -3.57%, bid 202,000원 기준 gross -3.81%는 미실현 참고치다. 매도 체결·실제 비용·종결이 없으므로 순실현 손익은 null이다. 자동관리 구간과 수동관리 구간의 결과를 분리한다.

### 5.4 장후 stop 재생 — 원본으로 재현된 계약 결함

[당시 불변 실행본의 원본 1행 검증](../../tmp/jusung-pattern-flow-research-20261015/stop-replay-probe.json)에서 `main_stop_replay.replay()`는 `source_gap/cost_model_source_missing`을 반환했다. 원 `cost_model.known_at`은 `2026-10-15T14:06:34.802536+09:00` 문자열인데, 소비자는 유한 숫자 epoch와 `known_at <= at`를 요구한다. 원 행을 수정하지 않고 그대로 재현했다. 이는 실제 비용을 모른다는 사실과 별개인 **producer/consumer 시각 표현 불일치**다.

또한 `role=SCALP_PRESET_TP` source의 `source_stop_values`는 공통 soft -3% / hard -5% / grace 60초를 담고, 실제 별도 preset -1.4% / emergency -2.4% / grace 0초는 담지 않는다. 현재 재생기는 preset soft 후보를 `preset_safety_precedes_soft_policy`로 censor하는 방어가 있어, preset을 잘못 매도한 결과를 확인한 것은 아니다. 그러나 이 공통 원천만으로 **이번 preset crossing과 수동 이관을 정확히 재생할 수 없다.** 별도 preset effective receipt와 실제 분기 우선순위를 연결해야 한다.

비용 모델은 frozen 0.0023의 추정 모델(`actual_broker_cost=false`)이다. 시각 형식을 수리해도 실제 정산 순손익으로 승격되지 않는다. 주문 1/1 완전체결과 전체 bundle 1/5 체결을 각각 보존하고, 원천의 `partial_fill=false`만으로 bundle 전량체결을 추론하지 않는다.

## 6. 보완 연구와 후속 수리의 우선순위

아래는 연구 제안과 결함 인계다. 즉시 운영 적용·예약 또는 추가 주문 권한을 만들지 않는다. 기계 개선은 [누적 정책 반영 계획](../proposals/main-cumulative-research-policy-adoption-plan-2026-10-14.md), 보유 원천/재생 수리는 현재 checklist의 기존 `HoldingProfitExitSourceContractRepair`가 소유한다.

| 순서 | 보완 항목 / 위치 | 비교 및 완료 증거 |
|---|---|---|
| 1 | 보유 context 생산→투영→path 입력 결손, `sniper_state_handlers` / `holding_decision_context` / `ai/holding_exit_vote` | 당시 활성화 상태·원 blockers·position/fill/quote hash 대조. 정상 문맥 전달, 의도적 OFF, source gap을 구분하고 누락을 의견으로 승격하지 않는 반례 검증 |
| 1 | 비용 시각·preset 실효값·manual handoff 연결, `main_stop_policy` / `main_stop_replay` | 원본 문자열/epoch·timezone·잘못된 시각·미래 비용 반례. preset·common·emergency 우선순위와 이관 전후 custody를 원 natural receipt에 맞춰 재생. 경제성 결손은 null 유지 |
| 1 | 256개 전이 한도·shared quote·entry situation 결속, trailing producer/replay | 새 불변 실행본에서 quote 전이·체결 고점·pin을 끝까지 보존하는지 확인. 이번 구간은 source gap 보존. 한도만 무한 증가시키지 않고 기존 compact 저장·분할·checkpoint를 이용 |
| 2 | 기존 F09/F15/A07 후보의 반영 계약 | 동일 확인점에서만 원 branch replacement/독립 A root를 적용. 원 legacy OR 경로가 F를 우회하지 않는지 확인. 현재 누적 결과와 등록·선택·PID 소비를 분리 |
| 2 | 한 호가 왕복 / 매수 압력 대비 가격 무진전 | spread 대비 반등폭, 실제 bid/ask 이동, 동일 가격 매수 이후 가격 유지·고점/저점 변화를 사전 고정 후보로 비교. tick count·기간·route를 명시하고 결손은 UNKNOWN |
| 2 | 세션 하락 중 회복 유형 | `세션 하락·회복 미확인`, `저점 재확인 후 회복`, `중립 구간 반전`, `상승 지속`의 제한된 유형을 기존 인과 feature로 비교. 이번 `DOWN/MIXED`를 일괄 진입 금지로 바꾸지 않음 |
| 3 | 진입 후 무진전·선행 1주 상태 | 30/60/120/180초 기존 quote와 잔량 terminal을 이용해 유지/후보 청산을 비교. 사후 MIXED를 진입 feature에 사용하지 않음. 실행 가능한 bid·비용·custody와 기존 exit 권한이 없는 대안은 CF로만 표시 |
| 3 | 연구 label과 운영 종료의 병렬 보고 | 기존 +0.4/-3/1800 label을 보존하고, 실제 preset stop·trailing·수동 이관을 별도 축으로 표시. `label WIN 뒤 실제 stop` 또는 반대 순서를 대조하며 기존 기계 채택 기준을 몰래 교체하지 않음 |

유형은 종목명에 붙이는 고정 낙인이 아니라 **판정 당시 관측 가능한 상태**다. 고정/비고정 모든 종목과 PRE/REGULAR/AFTER, exact KRX/NXT/SOR item/route를 census하고, 구조적으로 대상이 아닌 시장과 source gap을 구분한다. 기존 입장 때 situation pin과 보유 중 동적 weak/strong을 구분하며, 미래 경로로 최초 유형을 다시 쓰지 않는다.

누적 비교 모집단에는 체결만이 아니라 기계 ENTER_NOW 전체, 보조 PASS/CAUTION/VETO, 제출/미제출, 선행 1주/잔량, 미보유 후행 경로를 포함한다. Main real fill, 비체결 CF, 수동 이관, U는 별도다. 기존 weak-context veto가 이번에 `risk_context_only`였다는 사실은 확정됐지만, [오전 veto 점검](../../tmp/weak-submit-gate-verification-20261015-1115/verification.json)은 다른 PID·다른 attempt다. 이번 결과만으로 오전 차단의 경제적 정당성이나 veto 복원을 입증하지 않는다.

## 7. 성능 및 원천 보호

이번 대용량 원천 읽기는 명시한 순차/범위 읽기 합계 **246.51 MiB**이며, 소규모 문서·snapshot·추출본 재검증은 별도다. 약 1.79GB pipeline 전체를 재생하지 않고 summary offset과 제한된 시각 창 두 개를 읽었다. 동일 원천 payload는 두 번 읽었으며 manifest에 중복 읽기까지 반영했다. raw 범위 밖의 보유 경로를 완전하다고 주장하지 않는다.

후속 연구도 장중 추가 AI/REST/분봉 재조회·전수 해시·파일 polling을 넣지 않는다. 기존 source capsule·compact quote·fill ledger를 한 번 decode하고 원천/feature/정책 hash별 캐시를 재사용한다. 장후는 모든 scope manifest를 먼저 고정하고 bounded partition/checkpoint로 재개하며, 누락 partition은 완료에서 제외한다. 주문 safety 계산은 관측 writer 대기와 분리한다.

성능 수용은 동일 원천의 baseline/candidate에서 p50/p95/p99/max, CPU/RSS, 읽기 bytes, decode 수, queue 지연·손실, deadline miss, scope coverage를 비교한다. semantic·custody·first-crossing 불일치 0과 원천 보존을 함께 확인한다. 거래 수 감소나 연구 대상을 줄인 결과를 처리 성능 개선으로 부르지 않는다.

## 8. 검증과 미확정 경계

- [로컬 검증기](../../tmp/jusung-pattern-flow-research-20261015/validate_research.py)로 동결 증거 50개 hash, machine/request/wire/logical input 결속, 287/310 매수 비중, 기존 후보 predicate, 보유 63개 결손, trailing 257개 전이·한도 소진, 지연 quote 10개를 검증했다.
- 당시 불변 release의 stop consumer에 원본 1행을 넣어 비용 시각 계약 실패를 재현했다. 원천을 고친 가상 경제성 재생은 수행하지 않았다.
- 문서 링크 64개·기존 owner 1개·권한 경계·공백 검사와 print-only backlog parser를 통과했다. 로컬 검증기 compile도 통과했다. production code 변경이 없어 거래 suite, provider, 장후 전체 재생성, 재기동 및 외부 동기화는 실행하지 않았다.
- 미확정: 보유 context 활성화 결손의 정확한 원인, 전체 tick 경로의 누락 peak 여부, preset 정밀 first crossing, 신규 후보의 누적 성과, 14:41:28 이후 수동 매도/비용/종결. 이 항목은 연구 완료나 코드 결함 발견으로 해소된 것으로 표시하지 않는다.

본 연구의 결론은 **기존 조건상 성립한 짧은 반등을 지속 회복과 구분할 필요가 있고, 보유·장후 원천 결손 때문에 AI 판단과 정책 성과를 온전히 검증할 수 없었다**는 것이다. 하드스톱 판정과 수동관리 이관은 관측된 preset·운영 권한 경로에 부합한다. 새 패턴 후보와 별개로 원천 계약을 먼저 바로잡아야 다음 비교가 설명 가능한 결과가 된다.
