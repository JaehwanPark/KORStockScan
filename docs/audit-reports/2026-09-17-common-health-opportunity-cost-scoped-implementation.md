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
- common machine grid는 §8의 새 전수 평가 계약에서 양수 비용 차감 EV·동일 모집단 대비 개선으로 보완했다. 기존 frozen v1과 hierarchy·price의 절대0.10% gate, 전수 기회/capacity·stress/holdout·four-arm 계약은 여전히 별도 검토/보완 대상이다. 원천 수리에 경제성 floor를 추가하지 않았다.

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
| U7 | scoped common/all-supported hierarchy implemented | §8–§10 전수 원천·현재 incumbent 비교·양수 순 EV/전체 paired 개선·exact-parent 자동 발행. 자연 generation·전체 원장 대사는 잔여 |
| U8 | scoped router implemented / natural pending | §11 CAUTION checkpoint 기회비용·차단으로 피한 손실의 대칭 비교, INSUFFICIENT 원천 복구 분리, 현재 compact partition과 next-date 자동 발행. 자연 generation·전수 전달 acceptance 잔여 |
| U9 | scoped receipt/publisher closure implemented | §12 four-arm finite/분모·상충 receipt 격리·Daily 원자 발행의 정책 hash/date/authority. 전체 price-ready no-submit/no-fill adapter·양수 small-net versioned 평가 계약은 잔여 |
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

확인된 효과는 false freshness 제거, 공백 반복 분모 보존, all-VETO의 valid 기회비용 평가 경로 복구와 §8의 미진입 common 후보 자동 선정 연결이다. 전체 기계 진입 병목 해결·실현 순익 증가는 아직 입증되지 않았다. U7–U11 미완료를 자연 표본 대기로 숨기지 않는다.

## 8. 후속 common 전체 모집단 구현·재리뷰

2026-09-17 06시대 후속 구현이며 위 01시대 부분 H receipt를 오늘 새 PID·정책 소비로 바꾸지 않는다.

- 기존 #82 안에서 paired 원천과 자연 기계 평가 원천을 합친다. AI 미호출·BLOCK도 exact identity, fresh evidence hash, #74 machine-specific receipt, executable outcome·full 비용을 통과하면 평가한다. pending/lineage gap·censored/비용 결손은 제외하며 0원으로 보간하지 않는다.
- 공통 threshold 후보의 control은 당시 AI BUY/WAIT가 아니라 **현재 incumbent의 동일 결정 함수**다. 새 collector·producer·cron·Provider 호출 없음. 변경 가능 좌표는 기존 spread/fillability/ask-to-bid 3개뿐이며 micro·가격·수량·scale-in·AI prompt/model·custody·주문 및 hard safety owner를 변경하지 않는다.
- 같은 trace가 paired/natural 양쪽에 있으면 한 번만 소비한다. exact receipt 충돌은 양쪽을 격리하고 `input_row_disposition_complete` 보존식을 검증한다. caller의 frozen row는 수정하지 않는다.
- 새 `mechanistic_entry_full_population_positive_net_v2` 계약만 순 EV > 0과 동일 전체 모집단 paired delta > 0으로 판정한다. calibration 10건/5종목/5일, holdout 3건/2일, 시간순 분리·완전 terminal·source provenance·catastrophic tail 차단은 유지한다. 기존 frozen v1의 숫자를 조용히 다시 해석하지 않는다.
- 절대 순 EV 0.10%는 gross target 0.30%·비용 0.23%의 고정 경로에서 순 상한 0.07%보다 높아 달성 불가능했다. 새 계약은 **양수 비용 후 작은 수익과 incumbent 대비 개선**을 허용하지만 빈도 증가만으로 손실 후보를 승격하지 않는다. CF 성과는 실제 손익이 아니다.
- 후보에 full incumbent hash·원천 계약 digest·calibration/holdout 증거를 결속한다. 기존 next-date publisher가 guard 통과 후보를 자동 발행한다. 현재 incumbent hash가 다르면 `candidate_parent_changed_revalidation_required`로 carry하며 수동 승인/env를 만들지 않는다.
- publisher가 경제성·표본 floor·시간순 holdout·행 보존식을 재검증한다. 두 번째 v2 generation도 같은 함수로 다시 튜닝 가능하다. central verifier가 v1/v2를 분리하여 소비한다.
- 작업본 후속 targeted 8-suite: **736 passed**. 결함보완 후 공통 후보 → 실제 projection → 실제 publisher 회귀 포함. zero/loss EV, source hash 변조, 잘못된 checks, 표본 floor0, 시간순 위반, 행 보존식 실패, incumbent 변경은 차단된다. 실제 Provider/Kiwoom/주문·운영 replay 호출 없음.
- 이 범위의 code closure는 U0–U12 전체 완료가 아니다. hierarchy, CAUTION/INSUFFICIENT router, price/quantity four-arm, 독립 owner, 모든 direct API 소비자 parity 및 single-flight/scheduler는 미완료다. 다음 PREOPEN/start의 release/PID·자연 정책·경제성은 별도 receipt로 확인한다.

## 9. KRX regular hierarchy 전수 선정·자동 발행 후속

2026-09-17 07시대 구현. §8 이후 regular hierarchy 결손을 보완했으며 다른 scope·U0–U12 전체 완료로 확대하지 않는다.

- 기존 hierarchy 함수가 §8에서 정규화한 같은 natural+paired 모집단과 source digest/행 보존식을 소비한다. 실제 AI 호출·submit·fill은 CF 학습의 전제조건이 아니다. quality·비용·후행 label 결손은 계속 제외하며 actual PnL을 만들지 않는다.
- incumbent에서 기존 hierarchy·postclose metadata를 제거하던 동작을 새 전수 계약에서는 없앴다. **현재 정책 전체**가 control/parent다. control과 challenger는 동일 past-only group/flow/symbol context를 받는다. source evidence와 incoming row는 변경하지 않는다.
- group 후보·symbol residual·전체 결합 정책을 calibration과 chronological holdout에서 평가한다. 새 계약의 순 EV > 0, 전체 모집단 paired delta > 0, 완전 후행/비용과 catastrophic-tail 차단을 모두 확인한다. 단순 clean/adverse 건수 개선만으로 승격하지 않는다. training에서만 후보를 고르고 holdout 실패 뒤 다른 후보를 재선정하지 않는다.
- group train 5건/3일·holdout 3건/2일, symbol residual 15건/5일과 shrinkage 및 기존 bounded grid·runtime micro confirmation은 보존한다. missing micro·SOURCE_INVALID·broker safety를 threshold로 우회하지 않는다. 기존 v1/frozen 및 다른 scope의 경제성 floor는 조용히 변경하지 않는다.
- 현재 common 후보가 선정됐으면 그 직접 successor를 hierarchy parent로 고정하고, 없으면 현재 complete incumbent을 유지한다. candidate는 `hierarchy_full_population_positive_net_paired_v2`와 full parent hash·원천 digest·각 arm의 paired 증거를 담는다. 소비자는 같은 계약·시간순 분리·표본/terminal·순 EV·delta·tail을 다시 검증한다.
- 기존 자동 publisher는 child의 full parent hash가 현재 적용 예정 정책과 같을 때만 발행한다. common 숫자가 같더라도 micro 등 다른 parent 값이 달라졌으면 carry한다. 수동 승인/env·모델/가격/수량/scale-in/주문 owner 변경 없음.
- 회귀: 순 EV 0.07% 미진입 회복 선정, 0원/손실/현재 정책 대비 무개선 carry, source digest 불일치 거절, paired delta0 거절, 실제 publisher 자동 발행과 exact-parent 변경 carry, 승격된 incumbent 재학습 시 가짜 증분효과 차단.
- natural PID·오늘 정책 변경·수익 개선은 미관측이다. 기존 날짜 정책을 수동으로 다시 발행하거나 전일 원천을 재생성하지 않았다. 신규 collector/서비스/장후 producer 없음. U8–U11 및 공통 소비자·예산 전수 구현은 계속 OPEN이다.
- 작업본 후속 8-suite **742 passed**、compile/diff/print-only parser 통과。오늘 기존 dated policy의 `hierarchy_adopted=true`·`all_continuous_adopted=true`를 읽기 전용 확인했다. 정기 #82 `--write`의 existing `publish(...)`는 이 상태를 승계하므로 매번 별도 승인/수동 adopt가 필요 없다. 테스트도 기존 adopted 상태에서 flag 없는 실제 publisher 호출을 검증한다. 다른 scope 정책은 기존 분리 계약으로 carry한다.

## 10. 등록된 모든 scope의 hierarchy 전수 소비 보완

2026-09-17 07시대 후속. 기존 등록된 9개 scope를 각각의 natural/paired 원천, 비용 계약과 complete incumbent에 결속했다. 새 scope·collector·장후 producer·주문 권한을 생성하지 않는다.

- 기존 공통 정규화 함수에 명시적 cohort 계약을 추가했다. 각 scope의 raw→valid→후행/비용→평가 분모와 행 disposition을 보존하며 cross-venue/session 원천은 제외한다. KRX common threshold 선정은 KRX regular에만 허용한다.
- 기존 hierarchy 전수 positive-net paired v2를 모든 등록 scope에서 같은 기준으로 검증한다. 작은 양수 순 EV는 허용하지만 0원/손실·무개선·시간순 holdout 실패·source/hash 결손은 승격하지 않는다. independent owner·scale-in·가격/수량·micro·hard safety는 변경하지 않는다.
- scoped 자동 publisher도 full incumbent hash를 비교한다. threshold 숫자가 같아도 다른 parent 값이 달라지면 carry한다. exact scope 후보 발행은 KRX 또는 다른 scope를 변경하지 않는다. 기존 adopted 상태의 flag 없는 publisher 경로를 테스트했다.
- 9개 scope의 양수/0원/손실 및 재학습 무개선 회귀, KRX/NXT 실제 publisher와 parent 변경 carry를 검증한다. 테스트의 CF 순 EV는 자연 수익이 아니다. 오늘 운영 날짜 정책 재발행, Provider/API 호출, 조기 bot 기동은 하지 않는다.
- 부분 H release이며 U0–U6의 전수 소비자/예산/모집단, U8–U11의 router·가격/수량·독립 owner·handoff 구현과 전체 U12 fixed-point는 미완료다. 최신 selected release/검증 건수/기동 receipt는 `data/runtime/runtime_release_validation/`이 소유한다.

## 11. Compact 보조심사 router 경제성·자동 환류 보완

2026-09-17 07시대 후속. 기존 #82/#78/#80/정책 publisher/strict verifier를 보완했다. 신규 collector·서비스·장후 단계·Provider 호출·모델 변경 없음. U0–U12 전체 완료가 아니다.

- 최초 결손은 CAUTION/INSUFFICIENT를 함께 `non_economic_terminal_verdict`로 제외하던 분모다. 새 `compact_auxiliary_router_economic_selection_v3`에서는 exact machine ENTER의 유효 CAUTION을 별도 verdict로 평가한다. 실제 `ai_caution_bounded_recheck`와 `observed_actual_order_submitted=false` 근거가 모두 있어야 하며 unknown/실제 제출·다른 router는 제외한다. PASS/VETO로 의미를 바꾸지 않는다.
- 같은 attempt의 executable target/stop-first와 비용이 완전할 때만 checkpoint의 비용 후 양수 기회·회피한 손실을 계산한다. 이는 재검사를 보류한 **해당 시점의 CF 기회비용**이지 episode 전체의 영구 기회 손실, 새 실현손익 또는 재검사 실패 확정이 아니다. 후속 회복과 실제 수익 귀속은 별도 원천으로 확인해야 한다.
- INSUFFICIENT는 `source_gap_router_verdict`로 분리하여 원천 복구에 전달한다. 전송/semantic 오류·미호출·다른 compact/legacy partition·pending/lineage 결손·비용 결손을 모델 false VETO로 학습하지 않는다. 결측 손익은 null이며 정상 비노출의 0 CF exposure와 구분한다.
- 기존 비용 가중 registered variant selector를 재사용한다. 기회보존 방향은 VETO/CAUTION의 작은 양수 missed CF 합이 dangerous PASS 손실과 차단으로 회피한 손실의 합보다 클 때만 검토한다. 현재 손실 방어가 유리하면 carry하며, material tail의 risk 우선순위는 유지한다. 순 EV 0.10%를 새로 요구하지 않는다. 실제 후보 개선량을 증명한 것으로 표시하지 않는다.
- 유효 economic 20건·관련 분모5·오류3·관련 오류율25%의 기존 bounded feedback 조건은 유지한다. CAUTION도 자신의 유효 모집단에 들어가므로 all-CAUTION 날에 PASS/VETO가 없어 영구적으로 튜닝 불가한 조건을 제거했다. candidate별 사용자 승인·모델/provider 선정·기계/가격/수량/scale-in/주문/hard-safety 변경은 추가하지 않는다.
- 새 v3 detailed verdict count·subtotal·보존식·finite 비용 합·source/partition hash를 publisher와 strict verifier가 다시 검증한다. 과거 frozen v2는 기존 의미로 소비한다. CF authority의 명시적 false를 legacy gate로 우회하지 못하도록 #82/publisher/verifier가 기존 owner 안의 동일 helper를 사용한다. #78은 같은 v3 경제성/선정 receipt를 Provider0으로 전달하고 #80은 새 계약과 optimizer binding을 확인한다.
- 회귀는 작은 순수익 0.07%의 all-CAUTION 자동 successor 발행, 비노출/role 미입증 제외, INSUFFICIENT 분리, 회피 손실이 더 큰 경우 carry, count/schema/partition/NaN/CF authority 변조 차단, central verifier와 optimizer 전달을 포함한다. 검증 건수·최종 release/기동은 기존 `data/runtime/runtime_release_validation/` receipt로 별도 기록한다.
- 오늘 dated policy를 수동으로 다시 발행하지 않는다. 새 동작은 다음 정기 장후 평가→기존 next-date publisher→PREOPEN/loader 경로로 자동 환류하며, 실제 자연 정책 소비·수익성은 OPEN이다. 전수 reader parity·single-flight/scheduler·capacity census·U9/U10/U11 및 전체 fixed-point 구현은 미완료다.

## 12. 가격·수량/leg 4군 receipt·원자 발행 계약 보완

2026-09-17 08시대 후속. 기존 `entry_split_order_plan`과 Daily materializer/reader만 보완했다. 신규 collector·producer·서비스·장후 단계·Kiwoom/Provider/주문 호출 없음. U9 전체 또는 U0–U12 fixed-point 완료가 아니다.

- 최초 결함: 수량 policy의 평가 시점 SHA256와 발행 시점 bytes 대사가 없었고, split policy의 관측 hash 전달이 없어 교체된 파일을 새 hash로 봉인할 수 있었다. 버전·대상일·초기진입 scope·허용 계약도 직접 재검증하지 않았다. 기존 Daily reader가 선택한 split 파일의 SHA256를 전달하고, materializer는 양쪽 파일을 한 번씩 읽은 같은 bytes에서 hash·버전·source date·수량 active date와 기존 수량 authority validator/leg runtime authority를 확인한다. PREOPEN/runtime의 후속 hash 검증은 유지한다. OFF envelope는 기존 형태를 그대로 유지한다.
- 4군 receipt의 NaN/무한대·bool 수치·음수 자본시간·범위 밖 참여율, 무자본인데 비영(非零) 손익인 행을 격리한다. eligible count는 finite 양의 정수만 인정하며, unsigned/잘못된 hash의 count가 유효 source 분모를 오염시키지 못한다. 결측 CF를 0으로 만들지 않는다.
- 같은 exact attempt의 서로 다른 유효 immutable receipt는 양쪽을 격리하고 보존식의 원 분모에 남긴다. 읽기 순서에 따라 유리한 첫 행만 선택하지 않는다. hash가 잘못된 선행 중복행은 후속 유효 attempt를 숨기지 못한다. terminal·cost·executable 계약이 완전한 정상 비노출(0 CF exposure/0 자본/0 fill)은 paired 분모에 남기는 회귀를 검증했다. 실제 체결/실현손익 증거를 합성하지 않는다.
- mechanistic price publisher의 NaN/무한대 EV 통과를 차단했다. 기계 action·compact AI·numeric price 계산·수량 tier/cap·leg 집행·AVG_DOWN/PYRAMID·hard safety는 변경하지 않았다. 새 후보별 사용자 재승인이나 실제 candidate 체결 요구를 추가하지 않았다.
- 기대효과는 잘못된 4군 경제성/파일 교체가 자동 정책으로 승격되는 것을 막고, 정상 무노출이 평가 분모에서 지워지지 않게 하는 계약 수리다. 참여·회전·순이익 증가의 인과 효과는 아직 입증되지 않았다. 기존 quartet을 소비하는 경로의 보완이지 전체 raw population→no-submit/no-fill quartet 생성 연결의 완료가 아니다.
- 잔여 P1: 가격·수량 관련 기존 절대 순 EV 0.10%는 유지되어 있다. 작은 목표 경로에서는 비용 차감 상한보다 높을 수 있으므로 U9/U11의 새 full-population·chronological paired 평가 계약에서 개선해야 한다. 기존 frozen 정책 계약을 임의로 재해석하거나 원천 연결이 미완료인 상태에서 floor만 낮추지 않았다. 전체 price-ready 미진입/no-fill join, 정책별 후행 exit/cost, capacity·holdout 및 기존 선정 consumer의 전수 연결은 OPEN이다.
- 수정→self review→보완→re-review 결과, 이번 receipt/원자 발행 수정 범위의 미해결 finding 0. 기존 Daily·entry split·atomic sizing·allocator·PREOPEN targeted suite **610 passed**; compile과 `git diff --check` 통과. 문서 parser와 managed release 검증·commit/push/배포 receipt는 별도로 기록한다.
- 현재 PID27161은 `b6cb93b0` 릴리스의 07:55 자동 기동 receipt다. 이번 장후 코드 배포는 그 PID 소비로 표시하지 않는다. 장중 주문 경로 변경이 없어 불필요한 재기동을 만들지 않으며, 오늘 dated 정책/env를 수동 재발행하지 않는다. 새 선정은 기존 정기 장후→next-date publisher→PREOPEN/loader 경로가 소유한다. 자연 generation·새 정책 소비·실체결 경제성은 별도 OPEN이다.

Project/Calendar 동기화는 실행하지 않는다. 사용자 표준 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
