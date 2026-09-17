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
| U9 | scoped receipt/publisher/proof/source-delivery implemented | §12–§15 four-arm finite/분모·상충 격리·정책 hash/date/authority·calibration/holdout 증거의 publisher/PREOPEN/runtime 독립 검증과 owner 발급 price-ready 계획→기존 미진입 보고서→Daily exact lineage 전달. executable no-fill/exit/cost quartet 생성·양수 small-net versioned 평가 계약은 잔여 |
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

2026-09-17 08시대 후속. 기존 `entry_split_order_plan`과 Daily materializer/reader만 보완했다. 신규 collector·producer·서비스·장후 단계·Provider/주문 호출 없음. 구현/테스트의 실제 Kiwoom 호출과 배포 시 기존 adapter의 읽기 전용 잔고·미체결 검증은 구분한다. U9 전체 또는 U0–U12 fixed-point 완료가 아니다.

- 최초 결함: 수량 policy의 평가 시점 SHA256와 발행 시점 bytes 대사가 없었고, split policy의 관측 hash 전달이 없어 교체된 파일을 새 hash로 봉인할 수 있었다. 버전·대상일·초기진입 scope·허용 계약도 직접 재검증하지 않았다. 기존 Daily reader가 선택한 split 파일의 SHA256를 전달하고, materializer는 양쪽 파일을 한 번씩 읽은 같은 bytes에서 hash·버전·source date·수량 active date와 기존 수량 authority validator/leg runtime authority를 확인한다. PREOPEN/runtime의 후속 hash 검증은 유지한다. OFF envelope는 기존 형태를 그대로 유지한다.
- 4군 receipt의 NaN/무한대·bool 수치·음수 자본시간·범위 밖 참여율, 무자본인데 비영(非零) 손익인 행을 격리한다. eligible count는 finite 양의 정수만 인정하며, unsigned/잘못된 hash의 count가 유효 source 분모를 오염시키지 못한다. 결측 CF를 0으로 만들지 않는다.
- 같은 exact attempt의 서로 다른 유효 immutable receipt는 양쪽을 격리하고 보존식의 원 분모에 남긴다. 읽기 순서에 따라 유리한 첫 행만 선택하지 않는다. hash가 잘못된 선행 중복행은 후속 유효 attempt를 숨기지 못한다. terminal·cost·executable 계약이 완전한 정상 비노출(0 CF exposure/0 자본/0 fill)은 paired 분모에 남기는 회귀를 검증했다. 실제 체결/실현손익 증거를 합성하지 않는다.
- mechanistic price publisher의 NaN/무한대 EV 통과를 차단했다. 기계 action·compact AI·numeric price 계산·수량 tier/cap·leg 집행·AVG_DOWN/PYRAMID·hard safety는 변경하지 않았다. 새 후보별 사용자 재승인이나 실제 candidate 체결 요구를 추가하지 않았다.
- 기대효과는 잘못된 4군 경제성/파일 교체가 자동 정책으로 승격되는 것을 막고, 정상 무노출이 평가 분모에서 지워지지 않게 하는 계약 수리다. 참여·회전·순이익 증가의 인과 효과는 아직 입증되지 않았다. 기존 quartet을 소비하는 경로의 보완이지 전체 raw population→no-submit/no-fill quartet 생성 연결의 완료가 아니다.
- 잔여 P1: 가격·수량 관련 기존 절대 순 EV 0.10%는 유지되어 있다. 작은 목표 경로에서는 비용 차감 상한보다 높을 수 있으므로 U9/U11의 새 full-population·chronological paired 평가 계약에서 개선해야 한다. 기존 frozen 정책 계약을 임의로 재해석하거나 원천 연결이 미완료인 상태에서 floor만 낮추지 않았다. 전체 price-ready 미진입/no-fill join, 정책별 후행 exit/cost, capacity·holdout 및 기존 선정 consumer의 전수 연결은 OPEN이다.
- 수정→self review→보완→re-review 결과, 이번 receipt/원자 발행 수정 범위의 미해결 finding 0. 기존 Daily·entry split·atomic sizing·allocator·PREOPEN 첫 targeted suite **610 passed** 후 bool 가격 EV도 제외하는 보완/회귀를 추가했다. 최종 작업본 관련5개 suite **611 passed**, 최종 managed release 관련9개 suite **1055 passed**; compile·shell syntax·`git diff --check`·print-only parser 통과, 기존 acceptance owner1개. 전체 U9의 미진입 adapter와 EV floor 결손에는 finding0을 선언하지 않는다.
- 소스 `3133dec9`/`96390701`을 기존 selected `b6cb93b0` 이력에 일반 merge하여 `de8792b7` 릴리스를 main으로 fast-forward push했다. 기존 작업본의 다른 세션 dirty 변경은 포함하지 않았다. 공유 symlink 때문에 추가 병합이 실패하여 **새 비가동 worktree의** mount만 일시 분리/복원한 뒤 병합했다. 기존 가동 release와 원 운영 데이터는 유지했다.
- 코드 자체는 장중 주문 경로 변경이 없지만, 봇/장후 작업을 한 selected release로 pin하는 운영 계약과 사용자 릴리스 기동 지시를 위해 기존 router→`restart.sh`의 graceful 재기동을1회 수행했다. old PID27161 종료 후 new PID37714가 `de8792b7`, `source_dirty=false`로08:08:05 기동했다. strict dated env/PID verify PASS, mismatch/missing0, 미검증 selected family0, singleton1개, Samsung morning handoff `not_required`다. 직접 kill·중복 bot 기동·수동 env/정책/주문 변경 없음.
- 배포 사전08:06:41/사후08:08:25의 기존 strict adapter 읽기 전용 조회에서 KRX/NXT 계약 모두 정상, 삼성전자25주와 매수가269471·미체결0건이 일치한다. custody registry SHA256, 오늘 env와 dated machine policy SHA256도 동일했다. 원 owner를 main에 이관하거나 target를 취소하지 않았다. 자연 WS quote0D 수신08:08:29와 trade0B 수신08:08:36을 확인했으나 서로 다른 symbol의 receipt이므로 same-scope ordered-window acceptance로 확대하지 않는다. REG item budget skip 경고는 U5의 scheduler/budget 잔여로 남긴다.
- 재기동/배포는 새 장후 평가/정책/수익의 완료가 아니다. 오늘 dated 정책/env는 그대로이며, 새 선정은 기존 정기 장후→next-date publisher→PREOPEN/loader 경로가 소유한다. 자연 generation·새 정책 소비·실체결 경제성은 별도 OPEN이다. [배포·가동 검증 receipt](../../data/runtime/runtime_release_validation/u9-contract-closure-20260917-de8792b7.json)를 보존한다.

## 13. 가격 평가의 상충·중복 경제성 join과 미제출 진단 전달 보완

2026-09-17 08시대 후속. 기존 Daily producer와 직접 execution-quality consumer, 해당 회귀만 수정했다. 새 collector·모듈·장후 단계·Provider/주문 호출을 만들지 않았다. U9 전체 구현 완료가 아니다.

- 최초 결함은 exact completed fact를 alias별 마지막 행으로 덮어쓰던 index와 한 submit의 여러 outcome/여러 submit의 같은 outcome을 중복 표본으로 세던 grid다. 상충 fact는 모든 별칭에서 격리하고, 동일 내용 복사본은 한 경제성 관측으로 다룬다. candidate/profile 그룹 분리 전에 전 모집단에서 one-submit/one-fact와 one-fact/one-submit을 확인한다. 읽기 순서나 다른 별칭으로 격리를 우회할 수 없다. execution-quality 감사도 같은 fact를 한 번만 계수한다.
- NaN/무한대/bool 손익은 exact index에서 제외한다. 상충/복수/공유 outcome은 명시적인 source-quality 상태로 제출 분모에 보존하며 결측 EV·미체결 기회비용은 null이다. coverage 상한1·음수가 아닌 미join 수·terminal 보존식을 검증했다. 정상 행 전체를 일괄 차단하거나 형식 수리에 추가 실체결·양수 EV를 요구하지 않는다.
- 기존 미진입 CF **진단**에 원 raw event stream을 전달하여 `latency_block`과 이미 구현된 미제출 `entry_execution_sizing_plan` receipt가 제출 전 필터에서 사라지지 않게 했다. top-level identity도 소비하며 candidate/record 등 다른 종류의 ID가 우연히 같다고 연결하지 않는다. 이 join은 identity-lineage 진단일 뿐, price-ready 권한·same-scope executable/cost/exit·chronological paired 경제성을 증명하거나 가격을 발급하지 않는다. `join_semantics`에 이를 명시하고 runtime effect=false를 유지한다.
- 기대효과는 표본 부풀림/상충 손익의 잘못된 자동 승격 방지와 미제출 진단 누락 노출이다. 기존 기계 ENTER·compact AI·가격/수량 계산·leg·scale-in·broker/source/hard safety와 오늘 정책/env는 그대로다. 새 후보의 운용은 기존 정기 장후→publisher→다음 PREOPEN/loader 자동 경로가 소유하며 수동 정책 적용은 하지 않는다.
- 구현→self review→보완→re-review 결과 이번 join/진단 전달 범위 finding0. 동일 fact 복사, 상충 fact의 순서 반전/다른 별칭, 한 submit의 복수 fact, 다른 profile의 공유 fact, finite 손익, top-level 미제출 identity·ID namespace·Daily 직접 전달·execution-quality unique count 회귀 포함. 최종 작업본 관련5개 suite **622 passed**, compile·`git diff --check` 통과. 배포본 검증/현재 PID 소비는 아래 후속 receipt로 별도 기록한다.
- 잔여 P1은 **실제 제출·완료 거래 평균을 price 후보의 주근거로 쓰는 기존 선정 계약**, price-ready 전수 미진입/no-fill의 executable·비용·정책별 exit paired 연결, 조건부 기회비용과 holdout/capacity 비교, 절대 순 EV0.10%다. 이 축을 unbiased paired 계약으로 연결하기 전에 floor만 낮춰 체결 편향 선정을 확대하지 않는다. U9 및 U0–U12 fixed-point·자연 정책 소비·실수익 완료를 선언하지 않는다.
- 검증 코드 `f0c8fc89`를 원격 main 이력에 일반 merge하여 **`33c4ee4b`** 배포본을 만들고 관련9개 suite **1066 passed**·compile/shell/diff 검증 후 main으로 fast-forward push했다. 타 세션 dirty 코드는 포함하지 않았으며 기존 release를 덮어쓰지 않았다. selected release 교체 후 기존 graceful 경로1회로 old PID37714 종료→new **PID56789**,08:26:50 기동·source_dirty=false·strict 당일 env/PID verify PASS/mismatch·missing0/미검증 family0를 확인했다. 삼성 morning handoff는 not_required, singleton1개다.
- 배포 사전08:25:35/사후08:27:03의 읽기 전용 strict KRX/NXT 잔고·미체결 정상화 계약은 모두 complete, 삼성25주/매수가269471·미체결0으로 동일하다. custody registry·오늘 env·dated machine policy hash도 동일하다.08:27:00 main loop,08:27:01 broker sync,08:27:03 WS connect/LOGIN ACK와08:27:09 새 quote0D(005930)/trade0B(007660) 수신을 확인했다. 서로 다른 symbol의 첫 receipt를 ordered same-scope micro acceptance나 새 수익으로 표시하지 않는다. [배포·가동 검증 receipt](../../data/runtime/runtime_release_validation/u9-price-join-20260917-33c4ee4b.json)를 보존하며 오늘 정책 수동 재발행/주문 취소·owner 변경은 없다.

## 14. 수량/leg 4군 chronological 증거와 최종 소비자 검증 보완

2026-09-17 08시대 후속. 가격 전체 CF 연결 전에 확인된 선정 계약 결손부터 닫았다. 기존 evaluator·Daily publisher·PREOPEN audit·runtime loader와 기존 테스트만 수정했으며 새 collector/모듈/producer/장후 단계는 없다.

- 최초 결손은 4군 집계에 독립 최신일 holdout이 없고 `passed=true`만으로 원자 정책이 발급·소비되는 경로다. 새 `quantity_leg_chronological_paired_v2`는 서명된 receipt source date의 이전일 calibration/최신일 holdout을 분리한다. partition/전체 sample·고유 receipt hash 보존식, finite metric·EV/순이익/양수 terminal 빈도·자본효율·p10/ES·fill을 independently 대사한다. malformed/naive/future·source-date 이전 terminal 시각을 정상 경제성 quartet으로 세지 않는다.
- 기존 전체30건/coverage80%와 전체 순 EV0.10%는 유지한다. partition별30건·5/10/20일·0.10%를 복사하지 않으며 양수 순 EV·incumbent 대비 EV/순익 개선·기존 빈도/자본효율/tail 비훼손·fill 하락5%p 이내를 요구한다. 전체0.10%를 넘고 최신 holdout0.09%가 incumbent0.08%보다 개선되는 fixture는 통과한다. 기본 정책 활성화에는 이 challenger gate를 붙이지 않는다.
- Daily는 숫자/partition 증거를 재검증하고 원자 정책에 이를 보존한다. PREOPEN과 runtime도 공동 validator로 재검증하여 artifact hash가 새로 맞아도 위조된 passed/holdout·정책 identity/선택 arm·generation date 불일치를 차단한다. source9/17 신규 발급이 proof를 빼고 legacy로 후퇴할 수 없으며 과거 frozen 정책은 원래 계약을 유지한다. 오늘 env/dated 정책은 수동 재발행하지 않는다.
- 기대효과는 누적 평균이 가린 최신일 성능 악화와 근거 없는 자동 승격 방지다. 기계 ENTER·compact AI·가격·초기 수량 baseline/leg·scale-in·cap·broker/source/hard safety owner는 변경하지 않는다. 기존 정기 장후→Daily 원자 publisher→다음 PREOPEN/loader 경로에서 challenger를 자동 선정/검증하며 별도 사용자 승인을 추가하지 않는다.
- 수정→self review→보완→re-review와 작업본/배포본 각각 관련9개 suite **1079 passed**, compile/shell/diff·print-only parser 검증 통과, 이번 선정 증거 수정 범위의 미해결 finding0. 서명 date 미상·단일일·손실 holdout·가짜 passed·count/hash/metric 위조·NaN·future date·bool count·유효0.09% holdout과 publisher→PREOPEN→runtime 직접 소비 회귀 포함. 전체 미완료 범위에는 finding0을 선언하지 않는다.
- 소스 `9776fab0`를 기존 main 이력에 일반 merge한 **`b8db75d8`**를 검증/fast-forward push하고 새 managed release를 선택했다. 기존 graceful 경로1회로 PID56789 종료→**PID73587**,08:43:47 기동·singleton1·source-clean·strict 당일 env/PID PASS/mismatch·missing0/미검증 family0. 오늘 가격·수량/leg loader는 모두 `disabled_baseline`으로 새 challenger가 아니라 기존 기본 정책을 소비한다. [가동 검증 receipt](../../data/runtime/runtime_release_validation/u9-chronological-closure-20260917-b8db75d8.json)를 보존한다.
- broker 사전08:42:34/사후08:44:06 KRX/NXT 정상화 complete, 삼성25주/매수가269471·미체결0 동일, custody·env·dated machine policy SHA256 동일. main loop/broker sync와 새 WS 연결·LOGIN ACK·005930 첫0B/0D 수신을 확인했다. 단,08:44:02 source-only registration receipt는43 item 중12 complete/31 incomplete·exact-route complete=false다. 첫 데이터 수신을 전 scope ordered micro acceptance로 확대하지 않으며 WS budget/continuity는 기존 U5 잔여에 유지한다.
- 잔여: production 자연 quartet 생성·signed date 전달의 실제 실행 증거, 전체 price-ready 미제출/no-fill CF adapter·stress/capacity 선정과 절대0.10% owning 계약 개선, U0–U6 전수 parity/budget 및 U10/U11. 검색에서 quartet field의 기존 reader들은 확인됐지만 자연 생성자를 입증하지 못했으므로 collector 정상·유한 ETA·U9 전체 완료로 표시하지 않는다. 코드 검증과 자연 정책 소비/미진입 기회비용 개선·실수익은 별도다.

## 15. Owner 발급 price-ready 계획의 기존 미진입 보고서·Daily 전달 보완

2026-09-17 09시대 후속. 기존 `sniper_missed_entry_counterfactual`/Daily compact reader와 기존 회귀 테스트만 보완했다. 새 collector·모듈·서비스·장후 producer·Provider 호출은 없다. U9 전체 경제성 adapter 또는 U0–U12 전체 구현 완료가 아니다.

- 최초 결손: 미진입 보고서는 기존 AI BUY/armed만 인식했고, `entry_execution_sizing_plan`의 원래 가격·수량과 attempt/정책 hash를 projection에서 버렸다. 실제 binder가 이미 발급한 유효한 plan/price SHA256·schema·초기진입 owner·quantity 보존/authority 금지·같은 scope를 검증하여 가격 준비 뒤 미제출 기회를 기존 후행 보고서에 남긴다. BLOCK 종목에 주문가격이나 AI PASS를 발명하지 않는다.
- `scanner_promotion_id × evaluation_attempt_id × stock_code × effective_venue × market_session_bucket × policy_bundle_sha256`으로 Daily 직접 소비를 결속한다. exact identity가 불완전/다른 scope이면 shared record/candidate 별칭으로 우회하지 않는다. 기존 legacy 진단은 원래 분모로 보존한다. 계획 본문은 각16KiB 이하로 제한하고 Daily에는 검증 후 scalar identity만 남긴다.
- 같은 exact attempt의 중복은 최초 anchor를 유지하고 다른 legacy record/중간 scope를 거친 반복도 합친다. 상충하는 유효 계획은 전체 exact identity를 격리한다. 같은 legacy record/초에 발생한 다른 attempt·정책 bundle은 별개다. 새 projection은 `missed_entry_counterfactual_compact_v3`이며 explicit UTC anchor는 KST로 대사한다. 잘못된 date/clock·정책 버전 누락/비문자 identity는 행 단위로 제외한다.
- 실제 producer 호환: `pipeline_event_logger.emit_pipeline_event`는 plan dict를 `str(value)`로, envelope 시각을 `datetime.now().isoformat()`으로 기록한다. 09:13 growing raw의8MiB tail(426행/09:13:10~28)과 host `Asia/Seoul`을 대조하고, 기존 기록기를 실제 실행하는 격리 회귀로 native repr/JSON 문자열→기존 CF/Daily를 검증했다.16KiB 이하의 두 plan field만 `json.loads`/`ast.literal_eval`로 안전하게 해석하며 함수·이름 실행은 금지한다. 정상 producer의 로컬 KST envelope를 무조건 naive-invalid로 차단하지 않는다. 이 진단 시각 해석을 signed quartet terminal/경제성 proof로 전용하지 않으며 기존 §14의 엄격한 경제성 시각 검증은 그대로다. tail의 price-ready0은 해당 짧은 관찰창의 결과이지 당일 전수0/수집 실패/경제성 acceptance가 아니다.
- 원 owner의 계획 가격·수량을 유지하며 기존 virtual sizing을 다시 호출하지 않는다. probe 잔량의 미발급 미래 가격은 null이다. 전체 계획금액과 이미 가격이 있는 leg 금액을 분리하고, `counterfactual_notional_krw`/추정 PnL은 null이다. watch-cycle의 net EV 분모에도 넣지 않는다. `price_ready_source.economic_pair_eligible=false`, `exact_fill_exit_cost_counterfactual_replay_missing`를 직접 전달하여 분봉 MFE/close를 fill·exit·비용 replay 또는 자연 경제성 quartet으로 승격하지 않는다.
- 기대효과는 가격/수량 준비 뒤 사라진 미제출 기회를 기존 보고서와 Daily에서 추적할 수 있게 하는 것이다. 아직 추가 순익/참여율의 수치를 예측하거나 가격·수량 정책 승격 효과로 귀속할 근거는 없다. 기존 장후 자동 실행/다음 PREOPEN publisher·loader 연결은 유지하며 별도 사용자 승인·실체결·추가 표본 floor를 원천 수리의 수용조건에 붙이지 않는다. 기계 action·compact AI·numeric 가격·수량 tier/cap·leg 집행·scale-in·broker/source/hard safety와 오늘 env/dated 정책은 변경하지 않는다.
- 구현→self review→수정→re-review에서 hash 변조/상충·중복 anchor·scope 혼입·미래 잔량·원래 qty 재계산·분봉 경제성 오인·날짜/시계·malformed identity/정책 버전·실제 producer 직렬화 결손을 점검했다. 초기 관련10개 suite1117/추가 malformed 보완1119 통과 뒤 실제 기록기 호환을 추가했다. 최종 작업본·managed release 각각 관련11개 suite **1158 passed**, compile·Black·shell syntax·`git diff --check`·print-only parser(count31/기존 acceptance owner1) 통과. 이번 원천 전달 범위 미해결 finding0이며 전체 잔여 경제성 구현에는 finding0을 선언하지 않는다.
- 배포: 소스 `5caba04f`를 검증한 managed release **`51232b62`**에 통합·main fast-forward push 후 기존 graceful 경로로 **PID111554**,09:22:03 기동·singleton1·source-clean·strict 당일 env/PID PASS/mismatch·missing0/미검증 family0.09:21:32 사전/09:22:23 사후 양시장 broker 계약 complete, 삼성25주/매수가269471·미체결0, custody 상태444개(ambiguous/reserved0) 동일. 오늘 env/dated machine policy SHA256은 각각 `65121195021a3cfdae8829b319fc741332196aad9dba1aea0545a9b40b081f39`/`395a944743719cf4bad6c90540bb6e04d80a30c7d2350fd33f650daf6cfeaac5`로 유지한다.09:22:15 main 시작/09:22:21 loop, WS LOGIN ACK/005930 첫0D 확인; 전체scope ordered0B+0D나 경제성 acceptance로 확대하지 않는다. 오늘 price·qty/leg loader는 `disabled_baseline`으로 기존 기본 정책이며 새 challenger 소비가 아니다.
- 이번 §15 보완 과정에는 첫 `5ecfeffd`/PID94085(09:08), malformed 보완 `1ee69645`/PID99065(09:12), 실제 producer 호환 최종 `51232b62`/PID111554(09:22)의 **graceful3회**가 있었다. 이를1회로 보고하지 않는다. 원 selector/release·mount 원본은 rollback용으로 보존했고 다른 세션의 위젯 dirty 변경은 포함하지 않았다. [최종 배포·가동 receipt](../../data/runtime/runtime_release_validation/u9-price-ready-native-closure-20260917-51232b62.json)를 보존한다. 자연 장후 산출물 소비·새 정책 선정/승격·순익 개선은 별도 OPEN이다.
- 잔여: signed-date 자연 quartet 생성자/직접 전달, same-opportunity executable fill/confirmed no-fill/owner exit/cost/stress/capacity·holdout 및 절대0.10% owning 계약 재설계, 전수 parity/scheduler와 U10/U11. 오늘 대용량 growing raw의 전체 스캔, 조기 report 재생성 및 Provider/API replay는 하지 않는다. 테스트 후속 가격 API는 fixture로 격리하며 배포 broker 점검은 기존 adapter의 읽기 전용 조회로 별도 기록한다.

## 16. 기계·AI 상충 attempt의 행 격리와 자동 선정 전달 보완

2026-09-17 장중 후속. U6/U7/U8의 기존 calibration과 next-date machine/compact publisher·기존 테스트만 보완했다. 새 module·collector·서비스·장후 producer 없이 현재 owner·경제성 계약을 유지한다. 전체 U0–U12 완료가 아니다.

- 최초 결함: case table의 상충 count가 하나라도 있으면 정상 종목/venue/session/bundle의 기계 natural 연구와 compact 자동 선정까지 일괄 차단했다. 같은 action/trace의 다른 후행 outcome은 중복으로 덮었고, 다른 trace/action의 상충은 첫 행을 학습에서 확실히 격리하지 않았다.
- 동일 exact6 evaluation key의 decision/evidence/path/cost/AI 본문을 사전 대사하여 상충 위치를 발급한다. 같은 내용의 반복은 한 번만 계수하고 모든 상충 버전은 처음부터 `policy_learning_excluded=true`, `conflicting_exact_attempt`다. 원 diagnostic 행/count는 보존하되 기회비용·순 EV·학습 denominator에 넣지 않는다. arrival 시각만 다른 동일 본문은 새 기회가 아니다.
- common/all-supported hierarchy consumer는 count·위치와 원 natural rows의 실제 상충을 독립 재대사한다. 정상 source/clock/cost/terminal/identity 검증은 유지하며 상충 attempt와 같은 paired 별칭도 격리한다. 위치가 없는 외부 count·누락/변조/중복/invalid manifest는 natural lane fail closed다. 이를 정상0/유한 ETA/임의 PASS로 바꾸지 않는다.
- compact consumer는 현재 prompt/정책 partition의 유효 ENTER screen만 비교하며 profitable VETO와 avoided loss를 기존 대칭 평가로 유지한다. 상충을 제외한 정상20건이 남으면 기존 bounded next-date publisher가 별도 사용자 승인 없이 자동 선정한다.19건이면 기존 표본 gate로 incumbent carry다. publisher는 manifest/count/type·미해결 위치·상충 key의 학습 재유입을 다시 검사한다. 새 실체결 floor·관찰기간·양수 EV 조건을 진단 수리에 붙이지 않았다.
- 기대효과: 정상 미진입/VETO 사례가 관련 없는 상충 때문에 학습에서 사라지는 것을 방지하면서, 상충 이익/손실이 자동 승격 방향을 오염시키지 않도록 한다. 현재 기계 action/compact body·모델·price/qty/leg·scale-in·cap·broker/source/hard safety·당일 dated policy/env는 변경하지 않는다. 신규 후보 선정은 기존 정기 장후→next-date publisher→PREOPEN→loader가 소유하며 오늘 정책을 수동 재발행하지 않는다. 실제 자연 generation/새 정책 소비·비용 후 순익은 별도 OPEN이다.
- 리뷰·검증: 순서 반전, 같은 action/trace의 outcome 상충, 첫 행 격리, 반복 상충 version의 중복 collapse, paired 별칭 우회, malformed manifest, 정상19/20 screen 경계, 실제 flag-free next-date publisher와 machine/provider 비변경 회귀를 검증한다. 최종 test/배포/PID는 검증 뒤 receipt에 기록하며 전체 잔여 구현에는 finding0을 선언하지 않는다.
- 잔여: U0–U6 전수 reader/예산/census, U9 executable no-fill/exit/cost quartet·가격 absolute0.10% owning 계약 개선, U10/U11 전수 handoff 및 자연 경제성 acceptance. 본 보완은 이 결손들을 대신 완료하지 않는다.

## 17. 일반 WATCHING 준비 후 최종 로컬 WS snapshot 재검증

- 대상은 U3/U5 안의 `watching_analyze_target` 준비 중 fresh→stale 전환이다. 288180 exact 평가의 handler start 10:02:01.490에 current/tape1.547초·BBO0.980초였지만 snapshot capture10:02:04.822868에서4.879532/4.312726초로 전환됐다. Provider 미호출·candle build96ms라 전체3.333초를 AI 응답 latency나 분봉 build로 귀속하지 않는다. 355390은 시작부터 tape4.361초였고 최종 호가만0.230초로 회복됐으므로 원래 체결 공백과 구분한다.
- 기존 handler 파일 안의 `_refresh_prepared_entry_inputs`는 history/context 준비 완료 뒤 기존 로컬 WS 취득기를 단회 호출한다. canonical input의 current/BBO/tape age 계약으로 취득하며 기존 `revalidate_entry_candle_snapshot`으로 원시각·route·완성봉/optional source를 보존한다. final submit700ms·가격/수량/leg/scale-in/Provider/정책/guard는 불변이며 추가 REST/Provider 호출·collector·장후 producer는 없다. latest frame에 없는 tape를 과거 REST로 메우지 않는다.
- route/clock/source-age 계약 실패는 이전 allowed preflight를 재사용하지 않고 canonical source preflight를 blocked로 보존한다. refresh reason/max-age/준비 snapshot age/error는 기존 ai ops/tick-source 이벤트 consumer에 `entry_ai_final_*`로 전달한다. 진단 metadata만으로 tick audit 성공을 만들지 않는다.
- review 보완: 최초 회귀에서 telemetry 소비 누락을 수정했다. async immutable prepared-context를 직접 갱신하는 초안은 계약 오류가 확인돼 모두 제외하고 기존 async 구현을 유지했다. async dispatch 직전 갱신·동일 frame 결과 handoff는 잔여다. 일반 WATCHING 기존 build→최종 로컬취득→analyze 순서와 기존 async bridge 불변을 검증한다.
- 검증: 준비5초 후 정상 local frame 회복·tape 누락/오래된 tape·route 변경/역행 clock·bool source limit/malformed preflight·manager 누락/disabled/stale 시 원시각 재검증·telemetry 보존 회귀를 추가했다. 첫 관련3 suite297건, 추가 입력 실패 회귀 뒤 관련6 suite454건 통과. 최종 확장 suite와 배포/PID 확인은 아래 후속 receipt로 별도 기록한다. 이번 범위 수리는 경제성·전체 통합계획 완료가 아니다.
- 10초 체결공백/서로 다른3episode는 trade activity 계약이고, quote/submit 안전 TTL이 아니다. 현재 전수 reader의 activity/required feature 분리가 완료됐다는 주장은 하지 않는다. 공통 health의 `OBSERVATION_UNPROVEN`·원천 continuity/venue gap·U9 경제성 quartet/U10/U11는 기존 OPEN owner에 유지한다.
- 확장7 suite는458 passed/1 failed였다. `test_openai_scalping_analyze_target_returns_feature_audit_fields`의 micro delivery `not_attempted` 대 `computed_not_sent` 기대 불일치는 작업본·수정 전 운영3f9a358a에서 각각 단독 동일 재현됐다. 이번 handler/helper를 호출하지 않는 기존 결함이며 숨기거나 기대값을 바꾸지 않는다. 핵심6 suite454 pass와 확장 나머지 검증을 분리하고 전체 repo finding0은 선언하지 않는다. 후속 owner는 기존 Main AI source-quality acceptance다.

## 18. 공통 활동 facts의 canonical 소비와 feature-only 미판정 분리

- U2~U4 전수 완료가 아니라 U3의 canonical snapshot→Entry preflight→기존 trace/event→#11/#74 소비 결손을 우선 수리한다. 기존 공통 health를 원래 route receipt에서 consume 시점으로 다시 호출하며 별도의 activity classifier/counter·collector·장후 단계를 만들지 않는다. route projection의 aggregate 시각을 공통 transport 원시각으로 사용하지 않도록 최초 회귀 finding을 수정했다.
- 동일 item/route/venue/0B·0D 시각과 공통 epoch/연속성이 입증된 활동의 old last-sale/tape/skew는 필수 feature 부족과 source 손상을 분리한다. 오래된 tape가 fresh나 현재 매수 체결이 되지는 않으며 final allowed=false/Provider 미호출을 유지한다. feature-only는 machine RECHECK/runtime WAIT·별도 receipt이고 SOURCE_INVALID가 아니다. source/quote/clock 결손과 runtime artifact 미준비가 함께 있으면 feature-only로 정상화하지 않는다. late recheck가 source-only PASS를 전체 preflight PASS로 오인하는 우회도 보완했다.
- 기존 ai ops/tick log와 immutable trace가 활동/feature 사유를 전달한다. #11/#74 감사의 expected→accounted 보존식에 feature-before-assessment 별도 제외 분모를 추가해 정상 미판정이 새 unaccounted source 결손이나 경제성 assessed 표본으로 변환되지 않게 했다. numeric 가격/수량·leg/scale-in·compact body/model·호가/submit/micro·broker/hard safety·당일 정책/env는 변경하지 않는다.
- 최초 관련3 suite239 pass, 경계/consumer 회귀 후9 suite710 pass. 기존 cache 확장에서는787 pass/1 fail이며 holding payload 크기5447>5000은 수정 전 운영3f9a358a에서도 단독 동일 재현했다. 앞선 §17 micro delivery 기존 실패와 함께 숨기지 않고 별도 Main AI source-quality owner에 남긴다. audit/cache targeted265 pass/1 known deselected. 최종 검증/배포 receipt는 후속에 별도로 기록한다.
- 조사 범위: main Entry/holding/price의 canonical snapshot·entry revalidation·enrichment는 같은 공통 owner 경로다. scanner normalization/warm reactivation/scheduler, direct REST/episode/widget client·file projection, micro/exit/web 전달의 U2/U4 전수 migration은 아직 미완료다. quote/bar/micro/REST tape feature TTL은 activity classifier가 아니며 제거하지 않는다. grep 경로 확인을 static/offline/natural coverage 완료나 missing consumer0으로 보고하지 않는다. 기존 acceptance ID를 유지한다.
- 기대효과는 정상 체결 공백과 source 손상을 구분한 진단·미진입 원천 보존이며, tape feature가 부족한 실제 타점의 무조건 ENTER 증가나 순익 개선을 보장하지 않는다. quote-only 판단 가능 owner의 feature 요구 재설계와 전수 공통 소비는 별도 잔여이며 이 단계에서 임의 중립 feature·10초 일괄 TTL·새 정책 승격으로 우회하지 않는다.

## 19. 자연 integrated feed 결손·파일 전달·scanner 복구 오인 보완

- 10:39 bounded pipeline8MiB에서 활동 필드40 event line/최종 갱신14 event line을 확인했다. 고유 attempt/AI 호출 건수가 아니다. 078350의 source10:37:41 표본은 최종 로컬 재취득·fresh quote/canonical preflight와 machine DROP/Provider 미호출이었고, `_AL`의 UNKNOWN 실제 venue 때문에 common activity만 OBSERVATION_UNPROVEN이었다. 운영 귀속을 KRX로 발명하지 않고 공통 관측 범위와 실제 거래소 귀속을 분리했다.
- 공통 owner는 동일 `_AL` item·integrated route·현재 정수 epoch를 증명한다. snapshot의 bounded KRX regular SOR view는 같은 공통 facts를 소비하고 기존 candle/stage/clock/broker 조건을 유지한다. old0B는 quality=stale/required feature 부족 그대로이며 overall allowed=false이다. native UNKNOWN·cross-epoch·원본보다 새 companion print 시각·SOR 밖/NXT overlap은 우회하지 않는다. 동일 공통 관측의 object/file 상태가 불일치하지 않게 last quote/print 원시각 결속도 검증했다.
- U2 부분 전달: 기존 dashboard writer가 bounded route/type에 epoch·0B provider clock·quiet observation 원시각을 전달하고, 공통 helper가 raw/file projection을 같은 함수로 판정한다. micro checkpoint와 Samsung 화면 비교는 consume 시점 facts를 사용한다. file 생성/이전 health로 quote를 fresh화하지 않으며 정상5초 공백을 실제 micro trade backing/refill로 보간하지 않는다. 혼합 epoch는 unproven이다. 별 모듈/collector/장후 작업·wire/parser/FID/REG/auth 변경은 없다.
- scanner의 `_scanner_ws_subscription_recheck_snapshot_and_fields`는 같은 공통 활동을 소비한다. 정상 source에서 trade feature가 오래됐을 때 entry freshness=false/required feature wait를 보존하되 subscription repair는 요구하지 않는다. provenance/epoch/quote 또는 subscribed 결손이면 기존 repair 계약이다. 기존 heavy retry·warm reactivation·수량/가격/기계/compact AI/scale-in·SELL/custody/주문/broker guard는 바꾸지 않는다.
- Official reference gate: 2026-09-17T10:53:42+09:00 조회 완료 확인 upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`; `kiwoom/core/ws_client.py`, `core/auth.py`, `realtime/packets.py`, `kiwoom/specs.py`, `_data/kiwoom_api_spec.json`의0B/0D/ka10004와 `postman/kiwoom-openapi.postman_collection.json`의ka10004를 대사했다. 현행 tree에 `kiwoom_docs`는 없다. LOGIN/PING/REG/REMOVE·real/demo URL·type별 clock/가격/호가/volume·suffix 계약을 확인했으며 미정의 underlying venue는 계속 null/UNKNOWN이다. packaged request example과 SDK의 data 형태 차이는 기존 wire 유지로 격리한다. 프로토콜/주문 권한 승격 근거가 아니다.
- targeted 기존16 suite1101 pass/기존 holding payload1 known deselected; scanner full suite357 pass, 최종17 suite **1458 passed/1 known deselected**, compile/shell/diff/print-only parser32 PASS. scanner fixture의 hot-profile precedence 때문에 환경변수만 변경한3초 테스트가 기존30초로 동작했던2건은 fixture에서 해당 owner TTL을 명시적으로 주입해 검증했다. 운영 TTL/정책을 바꾸거나 기대를 낮추지 않았다. source split/metadata 소비 finding0과 전수 U2~U4 미완료를 구분한다. async 동일 frame handoff·direct REST/독립 gateway 전수 metadata·전체 capacity/economic/정책 생성의 기존 잔여를 완료로 바꾸지 않는다.

- §19 배포: main `c937eecb`/managed **`43126b6f`** release branch push, 물리 release1458/1 known deselected·공유경로555 pass. graceful1회 old210911 종료→**PID241669**, launcher10:55:48.756266·singleton1·source-clean/작업본 source 일치/strict 당일 env/PID PASS/mismatch·missing0.10:54:37~10:56:03 양시장 삼성25주/미체결0·registry/env/dated machine policy hash 보존.10:56:24 snapshot48stock 모두 health 전달, 삼성 `_AL`과010140 native KRX6.80초 공백은 fresh quote/RECENT_TRADE였다.8MiB bounded pipeline의0836503 event line에서 integrated UNKNOWN 유지/canonical binding true/source·feature allowed true를 확인했다. 같은 attempt 후행event를3개 기회로 세지 않는다. 파일 writer의 launch 시각 결손은 아래§20에서 별도로 보완한다.

## 20. WS 파일 worker launch 시각과 frozen-frame 소비 시각 분리

- 자연 snapshot에서0B receive age -4.05ms를 발견했다. packet 미래 시각을 입증한 것이 아니라 callback에서 worker를 예약한 시각을 frozen-frame보다 먼저 `now_ts`로 전달한 결손이다. 기존 lock 아래 두 view를 원자 고정한 뒤 현재 consume 시각을 writer에 전달한다. quote/trade/provider 원시각은 그대로이며 주기 제어의 launch 시각·callback lock/worker·기존 atomic publish는 유지한다. source clock을 현재시각으로 덮어쓰거나 미래 age를0으로 clamp하지 않는다.
- 기존 `test_dashboard_snapshot_freezes_main_and_exact_route_views`에 launch1000.0→source1000.4→worker consume1000.5 회귀를 추가했다. 원 source1000.4·throttle1000.0·frozen copy를 보존한다. 관련4 suite221 pass, 최종18 suite **1634 passed/1 known deselected**·compile/diff/parser32·owner1 PASS. 배포본 검증/기동은 후속 기록한다. 새 Kiwoom wire/parser/FID/REG/요청·후행 작업은 없다. 이 시각 수리 범위의 finding0과 아직 미완료인 전수 migration을 구분한다.

Project/Calendar 동기화는 실행하지 않는다. 사용자 표준 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
