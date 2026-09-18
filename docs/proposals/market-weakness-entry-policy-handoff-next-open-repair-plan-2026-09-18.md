# Market weakness 후속 원천·Entry 정책 인계 수리 상세계획 — 2026-09-18

## 1. 목적·현재 판단

기존 기계판정기/보조 AI 정책의 원천→정확 적용일 발행→통합 bundle→PREOPEN→정상 runtime 소비를 복구하고, 실제 다음 개장부터 독립 경제성 표본·기존 후보·실제 적용 버전 성과를 검증한다. EV 개선이나 새 후보 생성을 구현 완료 조건으로 강제하지 않는다. 정상 source와 incumbent carry를 확보한 뒤 기존 경제성 gate가 실제 edge를 판단한다.

사용자 제공 운영조건은 **오늘 휴장·데이터 미적재**다. 오늘 forward partition/새 진입/완료 손익0은 수집 장애·Main 기동 장애의 증거가 아니다. Scheduled collector가 JSON을 쓰고 health가 정상인 것은 기계적 소비 증거이며 실제 거래세션의 자연 호가·진입·경제성 표본 확보로 계산하지 않는다. 과거 수집량/결손을 소급 덮어쓰지 않는다.

현행 `src/utils/market_day.py:get_krx_trading_day_status(2026-09-18)`은 `(True, trading_day)`를 반환한다. 이는 사용자 운영조건과 불일치하며 실제 거래소 휴장 여부를 확정한 증거가 아니다. 실제 다음 개장일은 아직 지정하지 않는다. 공식 거래일/운영중단 조건을 먼저 대사해 불일치의 원인을 기록한다. 본 계획 수립에서 calendar/env/cron을 수정하지 않았다.

확인한 구조적 결함은 휴장과 별도다:

- `data/runtime/mechanistic_entry_policy/policy_2026-09-17.json`은 존재(41,382byte), source9/16·incumbent carry·machine-primary/compact auxiliary·all-continuous adoption 계약을 갖는다.
- `policy_2026-09-18.json`은 부재다. 날짜만 바꾼 복사본을 만들지 않는다.
- 현재 read-only PREOPEN: `runtime_env_handoff_missing`; `integrated_axis_bundle_hash_mismatch`, `integrated_axis_unconfigured`, `integrated_axis_policy_date_mismatch`, `integrated_axis_shared_policy_hash_mismatch`.
- `mechanistic_entry_runtime_policy.publish()`는 대상일07:35 이후 first publication을 거부하며 기존 해당일 generation을 동결한다. 늦은 당일 source 재처리로 인계를 강제하지 않는다.
- 별도 market-weakness 연구의 누적1,323 unique 중 독립CF11, holdout0/KOSDAQ0, 후보 미선정이다. 오늘 휴장으로 이 분모를 증가시키거나 유효율 악화로 판정하지 않는다.
- 현재 구성의 DATA_DIR canonical/alias 비교에서는 bundle hash 차이가 재현되지 않았다. 근거 없는 경로 canonicalization/새 schema 확장을 선행하지 않는다.

증거: `tmp/market-weakness-final-review-20260918/preopen-readonly.json`, `bundle-path-alias-review.json`, [기존 source 수리와 경제성 review](../audit-reports/2026-09-18-market-weakness-source-handoff-repair-and-economics-review.md).

## 2. 다른 세션과 소유 경계

다른 세션이 `scale_in_split_order_plan`을 검증 중이다. 그 세션이 실행 분할·수량/leg·scale-in sizing/price·관련 정책/테스트를 소유한다. 이 계획은 아래 경계를 지킨다.

| 본 작업 소유 | 병행 세션 소유 / 접점 |
|---|---|
| `scalping/ai_action_outcome_calibration.py`의 기존 policy publication 호출 및 source receipt | scale-in policy 재생성·recipe·수량 변경을 하지 않음 |
| `scalping/mechanistic_entry_runtime_policy.py`의 날짜/원천/role/기존 carry 발행 | execution sizing 또는 scale-in threshold를 학습하지 않음 |
| `threshold_cycle_preopen_apply.py`의 Entry action/AI shared policy receipt·bundle 생성/검증 | scale-in axis는 검토 중 source/version/hash를 read-only로 승계; configured 판정 삭제·임의 baseline 대체 금지 |
| 기존 Main collection publisher/observer와 attribution의 evidence 결속 | scale-in order/position leg의 실제 완료를 복제하거나 CF 진입으로 대체하지 않음 |
| 정책 소비·자연 표본·기존 hysteresis 후보/경제성 검증 | 동일 파일에서 병행 diff가 발생하면 해당 hunk와 owner를 대사한 후 최신 remote/selected base에 병합 |

배포 전에 remote/selected release를 재확인하고 병행 source를 포함한 clean successor를 만든다. 진행 중 worker의 파일/정책을 바꾸지 않는다. 별도 collector/service/timer/DB/engine-root module·범용 새 framework는 만들지 않는다.

## 3. P0 — 거래일·원천일·적용일 계약 확인

1. 휴장(거래소 비영업), 운영중단(거래소 영업이지만 이 시스템 미수집), source missing을 구분한다. 사용자 운영조건을 오늘 성과 판정에 반영하며 일반 요일 판단으로 덮어쓰지 않는다.
2. 공식 휴장 근거와 기존 market-day 계산을 확인한다. 특별휴장/holiday library 실패/운영 calendar 차이를 식별한다. 확인된 결함만 기존 calendar owner에 최소 수리하며 패키지 변경·추정 휴일 추가는 하지 않는다.
3. `source_date=마지막 완료된 유효 거래일`, `effective_date=그 원천 뒤 실제 다음 거래일`, `evaluation_date/as_of`를 분리한다. 저장된 target date를 인위적으로 relabel하지 않는다.
4. 날짜별 source/policy/state/target manifest를 작은 metadata/stat/기존 receipt로 inventory한다. growing JSONL 또는64MiB 초과 입력은 manifest/streaming/bounded tail만 사용한다. 오늘 자료 부재는 expected_non_collection/not_yet_due disposition을 기록한다.

**Closure:** 사용자 운영조건·검증된 trading-day owner·publisher `next_target`·PREOPEN target·collection effective date가 일치한다. 불일치 unresolved이면 다음 적용일 발행/기동으로 진행하지 않고 구체 owner/evidence를 남긴다. 다음 자연 검증의 실제 날짜가 정해졌을 때 기존 stable ID를 그 날짜 checklist로 이전한다.

## 4. P1 — calibration→mechanistic 정책 발행의 직접 결손 수리

Owner는 `src/engine/scalping/ai_action_outcome_calibration.py`의 canonical `--write`→`mechanistic_entry_runtime_policy.publish()`다. 새로운 producer를 추가하지 않는다.

1. 마지막 유효 원천의 schema·artifact_content_sha256·clean baseline·terminal/source-quality·원래 attempt conservation 및 AI partition 계약을 확인한다. 파일이 있다는 이유로 valid source라 하지 않는다. 기계 비진입의 AI 미호출은 N/A다.
2. publication이 호출되지 않았는지, exception/window/lock/invalid source/no initial adoption으로 실패했는지 기존 source/log/receipt를 대사한다. 거대한 calibration/raw를 다시 계산하지 않고 기존 output metadata/receipt를 먼저 사용한다.
3. 기존 유효 source와 기존 승인된 adoption/role이 있을 때 다음 정확 target에 기존 bounded publisher를 실행한다. 후보 없음/AI 표본 부족에서는 incumbent machine/prompt carry가 유지돼야 한다. 모델/threshold/prompt/provider를 새로 선택하는 수리가 아니다.
4. 호출 실패가 source report만 success로 보이는 silent gap이면 기존 publication receipt/요구 flag/후행 readiness를 수정한다. 반복 호출 idempotency·source hash validation·immutable snapshot·발행07:35 경계를 유지한다.
5. 유효 원천이 없으면 publisher blocked source를 명시하고 관련 선행 source owner만 수리한다. 과거 당일 계좌/비용을 현재 값으로 채우거나 수익0으로 대체하지 않는다. `bootstrap`, `replace-initial-role`, `adopt-hierarchy`, `adopt-all-continuous`를 일반 날짜 인계 수리로 자동 사용하지 않는다.

**Closure:** 정확 target의 policy가 기존 source snapshot/file/canonical hash·machine/AI projection·role/all-continuous 계약에 결속되고 `validate/load`가 통과한다. 신규 후보 없이도 incumbent carry가 valid source를 통해 발행된다. 잘못된 source·대상일·late first publication은 실패하며 직전 유효 policy가 보존된다.

## 5. P2 — 정책→통합 bundle→PREOPEN 계약 대사

Owner는 `threshold_cycle_preopen_apply.py:_integrated_entry_axis_bundle`, `_integrated_entry_axis_bundle_errors`, `verify_runtime_env_handoff`다.

1. machine/AI shared receipt가 같은 dated mechanistic policy를 읽는지 확인한다. file bytes SHA, policy `bundle_sha256`, machine/AI projection SHA, 통합 Entry axis SHA, runtime env pin은 각각의 정의대로 검증한다. 서로 다른 hash 종류를 대입하지 않는다.
2. 기존 authoritative/persistent/dated succession overlay 적용 순서 뒤의 **동일 effective env**로 producer/validator가 bundle을 만드는지 비교한다. Path만 바꾸거나 hash만 재핀해서 문제를 숨기지 않는다.
3. 일곱 기존 axis의 configured/missing/source/version/hash/owner를 대사한다. 어떤 axis가 unconfigured인지 구체화한다. 다른 세션의 scale-in receipt 결손은 그 owner에 인계하고 axis를 생략해 PASS하지 않는다.
4. valid policy가 먼저 발행된 후 기존 PREOPEN writer가 bundle/env manifest를 만든다. 새 값 생성이 아니라 검증된 incumbent/approved source의 기존 writer 인계다. 기존 operator pin/expiry/retired guards·hard safety는 유지한다.
5. code를 수정했다면 producer→schema/date/hash→validator→Main resolver를 self-review하고 필요한 regression만 보완한다. selected source와 worker import root를 동일하게 결속한다. 실행 중 오래된 worker는 별도 receipt로 보존한다.

**Closure:** 현재 네 에러가 각각 원천 원인과 함께 닫히고 exact target read-only strict PREOPEN이 PASS한다. Missing policy, tampered SHA, wrong target, bad overlay/owner conflict는 계속 실패한다. 전체 chain의 다른 source failure를 이 단위 PASS로 덮지 않는다.

## 6. P3 — 신호 시점 원천 결속·수량 계약

우선 기존 native blocked/unfilled/live decision을 사용한다. `risk/market_weakness_entry_guard.py:record_market_weakness_blocked_entry`는 original required_quantity·guard observation ID를 기록하므로 신규 채집기를 만들 필요가 없다.

1. 신호/재판정/차단·unfilled를 모두 original signal/opportunity ID로 연결하고 동일 episode/재시도 중복을 제거한다. Actual/sim/probe/CF, owner, venue/session/item/epoch를 분리한다.
2. 기존 collector 대상은 active owner 모든 route와 prospective budget4(상한8), 총200symbol/400item 계약을 유지한다. Configured/registered/dropped/observed disposition을 구분한다.
3. 신호 전에 정해진 original requested quantity/target/cost/route가 있는 경우만 독립 depth 모델로 평가한다. Prospective 연구 신호의 quantity 누락은 source-quality exclusion이다.
4. Prospective source를 평가할 필요가 있고 recipe가 quantity를 이미 고정한다면 **그 기존 source producer**가 선언한 값과 version/hash를 signal payload에 전달한다. 체결 후 수량·미래1주 fill·다른 scale-in leg 수량을 대신 넣지 않는다. 원천에 계약이 없으면 연구 담당 owner와 경제성 정의를 먼저 확인한다.

**Closure:** no-fill/blocked 포함 요청수량 provenance와 route/cost가 source hash에 결속된다. Missing quantity/depth는 null/excluded이고 full/partial capacity를 구분한다. 수량/leg/price/cap을 늘리지 않는다.

## 7. P4 — 실제 다음 개장일의 자연 수집 검증

기존 정상 Main 시작 권한과 strict dated PREOPEN PASS가 있을 때만 기존 운영 시작 경로가 소비한다. 이번 휴장일 검증에서 봇을 시작하거나 주문으로 표본을 만들지 않는다.

- 첫 정상 PID/선택 source/loaded policy→Main collection target publication→WS0B/0D registration→exact KRX/NXT/SOR item·epoch/시간→forward dated partition을 연결한다.
- 등록 receipt의 configured_at은 signal 이전이어야 한다. 0B price와0D depth의 freshness/동일 item·session/venue·순서를 검증하고 H30 경로 완료/대기/누락을 분리한다. Integrated market-data item이 실제 체결 venue를 증명하지 않는다.
- Calendar 영업일 확인 뒤 해당 시장/session에서 실제 signal 발생·H30 성숙 시 한 번 점검한다. 무신호라면 source-ready denominator와 이유를 남긴다. KOSDAQ0을 양시장 충족으로 바꾸지 않는다. 동일 raw 반복 replay·짧은 무한 polling은 하지 않는다.
- Kiwoom request/parser/REG/FID/recovery 수정이 필요하면 해당 변경 전 current official upstream revision/path/time gate를 수행한다. Source 원인 확인 없이 새로운 API/REST fallback 수집기를 추가하지 않는다.

**Closure:** 정상개장 유효 route의 original signal/quantity/cost/depth/H30 경로가 존재하고 수집/중복제거/성숙대기/제외 분모가 보존된다. Collector JSON의 새 collection-clock/health만으로 이 조건을 닫지 않는다.

## 8. P5 — 기존 후보 재검증

동일 frozen opportunity union으로 기존2/3와 이웃2/2·2/4·3/3만 비교한다. 기존 sample/date/owner/시장/cost/chronological holdout/tail·promotion gate를 유지하고 새로운 grid/family/floor를 만들지 않는다.

- Calibration에서 후보를 고정하고 독립 holdout으로 검증한다. Holdout이 없거나 source-quality-blocked면 부족 상태다. 다른 후보에 같은 holdout을 반복 사용하지 않는다.
- source-valid 기회 전체에서 baseline/challenger의 avoided loss와 missed upside를 대칭 계산한다. filled trade만으로 veto 비용을 추정하지 않는다.
- 후보0이면 source-valid/no-edge, sample/holdout maturation, structural quantity/registration/horizon source gap, intended role-not-applicable를 구분한다. 오늘 휴장으로 sample 부족을 악화된 경제성으로 판정하지 않는다.

**Closure:** 유효 비교·paired 개선·tail/stress·시장/owner coverage가 기존 기준을 통과한 후보만 기존 publisher로 승격한다. 그렇지 않으면 current carry와 구체 disposition을 남긴다. Source가 repaired라는 이유로 양수 ΔEV를 요구하거나 EV를0으로 만들지 않는다.

## 9. P6 — 실제 적용 버전별 rolling/cumulative 성과

Version identity는 적용 target/source_date·policy hash·source/status 및 실제 machine/AI version, owner/venue/session을 결속한다. Hash가 같은 fallback/dated carry도 구간을 분리하되 출처 복구만으로 경제적 treatment가 바뀌었다고 추정하지 않는다.

1. 실제 소비 observation ID→owner decision→original episode/order/fill/exit→COMPLETED+valid profit_rate/정산비용을 연결한다. Native primary key로 episode 중복을 제거하고 reused historical fills를 새 수익으로 합산하지 않는다.
2. 기존 평가 window/원래 version acceptance를 사용한다. Window 정의가 없는 metric은 먼저 정의를 기록하며 임의5/10/20일 공통 floor를 만들지 않는다.
3. 각 버전/owner/venue/session별 completed 표본·순비용 EV·원화 순익·p10/tail·자본노출/점유시간·coverage를 계산한다. Partial/HELD/no-fill/CF는 별도이며 missing은 null이다.
4. Model ΔEV는 같은 기회/수량/원래 guard의 CF 비교다. 실제 이익/정책 인과 uplift와 별개다. Model error는 original signal과 실제 완료가 동일 key·비용·window/exit 정의로 비교 가능할 때만 계산한다. Raw return과 model endpoint 차이를 calibration 오차로 부르지 않는다.

**Closure:** 실제 적용 lineage·episode conservation·valid costs/outcomes가 닫힌 해당 버전에서만 성과를 평가한다. Sample 없음/holiday/guard 미발동에서 economics는 null이고 다음 필요한 성숙 조건을 기록한다. 수익 개선을 입증하기 전 정책 효과/튜닝성과 완료로 보고하지 않는다.

## 10. 검증·실행 비용·완결 기준

| 변경 경계 | 필요한 검증 | 생략 |
|---|---|---|
| 날짜/발행 P0–P1 | `test_mechanistic_entry_runtime_policy.py`의 invalid date/source/hash, late window, idempotent incumbent carry; 해당 calibration writer/publication 연결 test | raw/calibration 전체 재계산·provider 호출 |
| 통합 인계 P2 | `test_threshold_cycle_preopen_apply.py`의 integrated axis/overlay/hash/date·변조 실패, 정적 read-only strict result | 전체 trading suite·live 주문/임의 env pin |
| 수량/수집 P3–P4 | 기존 collection-target/blocked-entry/observer/forward test 및 실제 다음 세션 source receipt | 새 수집 service·performance benchmark·표본 주문 |
| 후보/성과 P5–P6 | 기존 market-response/hysteresis/version-outcome 계약, 같은 frozen cohort·기존 cost/holdout/episode conservation | 새 model/grid/framework·반복 동일 replay |

`implementation→self review→fix→re-review→targeted validation`을 반복하고 defect0인 해당 scope만 commit/push·배포한다. Python compile·wrapper 변경 시 bash syntax·diff check·문서 print-only parser를 수행한다. 코드 closure/배포/자연 수집/후보승격/실제 EV를 별도 보고한다. 조건이 자연 시간/외부 원천에 의존하면 NULL ETA와 owner/artifact/closure test를 제시하며 PASS를 재사용하지 않는다.

Executable owner는 당일 checklist의 `MarketWeaknessSourceHandoffNaturalEconomics0918` 하나다. P0–P6는 같은 owner의 실행 순서이며 별도 병렬 task/전략 owner가 아니다. 다음 실제 개장일이 확정될 때 기존 Acceptance/History를 보존해 하나의 current parsed owner로 이관한다. `scale_in_split_order_plan` 검증 owner는 병행 세션에 유지한다.
