# Main 전 종목·전 시장 등록 후보 복수 정책 운용 구현계획

## 1. 목표와 작업 경계

10/7 사용자 요청 1~3을 반영한다. 삼성 정규장의 복수 분기 운용을 **모든 Main 대상 종목과 지원 시장(PRE/REGULAR/AFTER)**으로 확장한다. 삼성 정제 후보, 네 상시감시 종목별 후보, 일반 비삼성 세분 유형을 등록하고 장후 비교와 실시간 평가에 연결한다.

역할은 다음과 같이 고정한다.

| 역할 | 수행 작업 | 변경 주체 |
| --- | --- | --- |
| 수동연구 | 새로운 유형·특징·조건·확인 방식의 가설 탐색과 재생 | 사용자가 요청한 연구 작업 |
| 후보 등록 | 연구에서 선택한 정의·적용 범위·비교 조합·근거를 버전과 hash로 고정 | 구현·리뷰 작업 |
| 정기 기계 장후 | 등록 후보와 장중 적용된 모든 정책 버전을 같은 누적 원천으로 재평가하고 다음 정책 선택 | 장후 생성기 |
| 정기 보조 장후 | 등록된 보조 문구와 장중 적용 문구의 실제 응답을 비교 | 장후 생성기 |
| 실시간 | 발행된 정책 목록만 평가하고 중복 제거한 Main 진입 후보 생성 | 기존 Main 소비자 |

장후 생성기는 새 특징·임계값·확인 방식·유형을 만들거나 연구 코드의 900/450개 가설 조합을 자동 탐색하지 않는다. 등록 이후 수치나 조건을 바꾸려면 새로운 수동연구 정의/version을 등록한다. 장후가 바꾸는 것은 고정 후보 중 **어느 단독 정책/등록 조합을 다음 적용 주기에 선택하는가**이다.

10/7 후속 사용자 지시로 P1~P7 구현·반복 리뷰·배포·재기동이 승인되었다. 현재 작업은 구현·검증 중이며 완료 여부와 실제 활성 family/PID는 실행 감사의 영수증으로 판단한다. 신규 후보의 기계 승률과 실제 보조 비교 완료를 분리하고, 미준비 scope는 검증된 기존 기계·보조 쌍을 함께 유지한다. 기존 삼성 최초 적용 기록은 원 정의의 이력으로 보존한다.

실행 owner는 [현재 체크리스트](../checklists/2026-10-07-stage2-todo-checklist.md)의 `DirectFamilySourceRepairMainMechanisticEntry` 하나를 사용한다. 별도 중복 OPEN을 만들지 않는다. 기반 계약은 [기존 복수 정책 계획](main-multi-policy-parallel-entry-and-samsung-shallow-pullback-implementation-plan-2026-10-07.md)이며, 아래 확장 규격이 기존 문서의 삼성 전용 catalog/12셀 구현 범위를 보완한다.

## 2. 확인한 현재 제약과 변경 소유

계획 검토 기준 workspace HEAD는 `ca19eb58a7206657471b10c79bbceaec714eedb1`이다. 아래는 코드 구조 확인이며 현재 PID의 신규 정책 소비 증거가 아니다. 검토 중 반영된 `2950f674`의 registered source 보존 수리를 유지한다.

| 현재 제약 | 확인 위치 | 필요한 변경 |
| --- | --- | --- |
| 사용자 등록 패턴은 삼성·SOR 정규장 한 개만 허용 | [branch registry](../../src/engine/scalping/continuous_reversal_branches.py)의 `validate_payload`, `BranchState` | 정의 목록·scope resolver·분기별 상태를 일반화 |
| 삼성 REGULAR만 27개 조합, 나머지는 legacy 13개 단독 | [장후 producer](../../src/engine/scalping/continuous_reversal_branch_postclose.py)의 `catalog`, `select_machine` | 등록 조합 및 당일 실제 적용 버전을 모든 해당 scope에 편입 |
| `cell_key`는 삼성/other×시장×가격대 | [기존 kernel](../../src/engine/scalping/continuous_reversal.py)의 `cell_key` | 네 고정 종목과 일반 비삼성의 모집단·선택 소유권 분리 |
| 한 event의 FIRST/삼성 CONFIRMED를 중심으로 분기 판정 | [v2 consumer](../../src/engine/scalping/continuous_reversal_policy_v2.py)의 `assess` | 복수 확인 상태·동시 확인·scope별 primary 판정 |
| branch code/definition hash가 단일 상수 | 같은 registry와 v2 `validate_family`, `validate_sources` | registry manifest와 사용 정의별 hash 결속 |
| 보조 비교는 기존 cell×phase로 묶이고 date별 최대 24점을 선택 | 장후 producer의 `prepare_daily_inputs`, `auxiliary_report` | 종목/branch/phase별 비교 소유와 전체 eligible 입력의 누락 없는 처리 |
| v2 여부를 개별 호출부에서 비교 | [policy dispatcher](../../src/engine/scalping/continuous_reversal_policy.py), [native loader](../../src/engine/scalping/mechanistic_entry_runtime_policy.py), [AI engine](../../src/engine/ai_engine_openai.py), [Main state handlers](../../src/engine/sniper_state_handlers.py) | v3 dispatch·claim·compose·source 검증·소비 영수증을 함께 연결 |

현재 평가에는 `ANY_MATCH_ONE_INTENT`가 있으므로 정책 목록 구조를 재사용한다. 다만 목록이 있다는 사실만으로 네 고정 종목의 독립 선택이나 비삼성 조합 선택이 구현된 것으로 간주하지 않는다.

### 2.1 현재 프리마켓·통합 애프터마켓 정책은 존재한다

10/7 15:15 KST 재점검에서 native `load_effective(target_date=2026-10-07)`가 읽은 활성 bundle은 `6b615c1b1dc97682b097a4e6781d407e17d523317acb83ee82f1d2affa4b90cf`, family는 `b301a104a2392d19029f97e95052758cc3d69ee5ade1710fccbfde0a27ced2f8`였다. [current pointer](../../data/runtime/mechanistic_entry_policy/current.json)와 그 [불변 generation](../../data/runtime/mechanistic_entry_policy/generations/6b615c1b1dc97682b097a4e6781d407e17d523317acb83ee82f1d2affa4b90cf.json)을 대조했다. 14:42의 PID 918591 [소비 영수증](../../data/runtime/mechanistic_entry_policy/consumed/2026-10-07/918591.json)은 조회 시점 `/proc`의 start ticks·cwd와 일치했다. 이 기록은 해당 시점 증거이며 다음 release 선택이나 이후 장의 체결을 입증하지 않는다.

| 적용 대상 | 프리마켓 PRE | 통합 애프터마켓 AFTER |
| --- | --- | --- |
| 삼성전자 | `DROP_GE_1_0`: 직전 하락≥1.0%의 첫 반전 | `DD5_GE_0_4`: 5분 최대 낙폭≥0.4%의 첫 반전 |
| 비삼성 2만원 미만 | `DD5_0_8_VOL_UP`: DD5≥0.8%·거래량 비율≥1 | `DROP_0_4_REBOUND_LE_0_3`: 직전 하락≥0.4%·저점 대비 반등≤0.3% |
| 비삼성 2만~10만원 미만 | `DD5_0_8_VOL_UP` | `DD5_0_8_REBOUND_LE_0_3`: DD5≥0.8%·저점 대비 반등≤0.3% |
| 비삼성 10만원 이상 | `DD5_GE_1_2`: DD5≥1.2% | `DD5_GE_0_4` |

네 상시감시 비삼성 종목도 현재는 해당 가격대의 other 정책을 사용한다. 위 8셀에는 각각 FIRST 보조 prompt binding도 있다. 현재 PRE/AFTER는 셀마다 단일 branch이며 삼성 REGULAR은 2개다. native `market_bucket`은 `PREMARKET_KRX_LIKE`/`NXT_PREMARKET`/`SOR_PREMARKET` 등을 PRE로, **`INTEGRATED_AFTERMARKET`·`SOR_AFTERMARKET`·`KRX_NXT_AFTERMARKET`** 등을 AFTER로 해석한다. 이 정책 선택 bucket은 실제 주문 venue를 결정하는 값이 아니며 종목·시간·route의 기존 제출 조건은 별도로 검사한다.

PRE/AFTER의 저장된 기계 성과도 전부 null이 아니다. 예를 들어 삼성 PRE는 WIN/확정 2/2, AFTER는 207/686·미확정 276이다. 이는 부모 발행에 사용한 누적 가격 라벨을 유지한 값이며 오늘 프리/애프터 실거래 결과가 아니다. 현재 v2의 일부 cell metric은 초기 부모 값을 보존하므로 새 branch 조합의 최신 성과로 인용하지 않는다.

따라서 **SOR 정규장 한정은 새 S1~G4 연구 근거의 범위**다. 프리·애프터 정책의 부재나 시장 전체 신규 진입 금지를 뜻하지 않는다. 이번 구현은 위 현재 정책의 조건·보조 binding·지원 시장을 보존한 상태에서 복수 목록과 등록 후보 비교를 확장한다.

정확일 `policy_2026-10-07.json`만 직접 읽으면 최초 v1이 보일 수 있다. P1의 incumbent·migration 부모는 반드시 native loader/current activation이 선택한 generation으로 고정한다. selector의 release 경로, 날짜별 준비 파일, 활성 정책, PID 소비를 서로 대체하지 않는다.

15:18:45 KST 최종 재확인에서는 활성 [후속 generation](../../data/runtime/mechanistic_entry_policy/generations/7c500126d082c4ef866ef0b74eb4012141b37902ab52e6463bcb0b7bd6b7b2da.json)이 `7c500126d082c4ef866ef0b74eb4012141b37902ab52e6463bcb0b7bd6b7b2da`, release commit은 `3d946012ba7003c7791393acdba4474dedc64a13`으로 바뀌어 있었다. 이전 활성 generation과 **기계 12셀·보조 12셀의 payload 전부 동일**함을 읽기 비교했다. 따라서 위 시장별 정책 표는 후속 generation에도 같다. 새 bundle의 branch PID 소비 영수증은 이 조회 시점에 미관측이며 과거 PID 영수증을 새 bundle의 소비 증거로 재사용하지 않는다.

## 3. 등록 대상과 연구 근거

근거는 [10/7 종목·유형 연구 결과](../audits/main-symbol-regime-and-slow-pullback-research-review-2026-10-07.md)와 그 문서의 frozen source/result/validation이다. 숫자는 **10/7 14:13:01.380까지의 SOR 정규장 가격 재생**이다. 운영 체결 승률이 아니며 구현 시 같은 원천에서 다시 재현한다. 현재 정책도 같은 source cutoff에서 재계산한다.

아래 ID는 구현 시 registry에 부여할 이름이다. 기존 legacy 13개와 `samsung_up_shallow_next_up_5_v1`을 포함하고 신규 10개를 우선 등록한다.

| ID | 종목/유형 | 고정 조건과 확인 방식 | 연구 WIN/확정, 미확정 |
| --- | --- | --- | --- |
| S1 | 삼성 005930 | 현재 얕은 눌림 + 첫 반전 시 10틱 매수 **수량** 비율 ≥60%; 다음 상승 5초 | 18/18, 0 |
| S2 | 삼성 005930 | 직전 하락≤0.4%, DD5 0.4~0.8%, ret60≥0, 상승 세션·저점 상승, 첫 반전 시 60초 VWAP 대비≥0.1%; 다음 상승 5초 | 15/15, 0 |
| D1 | 두산에너빌리티 034020 | 직전 하락≤0.4%, DD5≥1.2%, ret60≥0; FIRST | 205/205, 57 |
| H1 | HPSP 403870 | 직전 하락≤0.4%, DD5 0.4~0.8%, ret60≥0, 상승 세션·저점 상승; FIRST | 31/31, 32 |
| A1 | 알테오젠 196170 | 직전 하락≤0.4%, DD5≥1.2%, 0≤ret60<0.2%; FIRST | 11/11, 0 |
| J1 | 주성엔지니어링 036930 | 직전 하락≤0.4%, DD5<0.4%, 0≤ret60<0.2%, 상승 세션·저점 상승; FIRST | 29/29, 0 |
| G1 | 일반 비삼성 2~10만원 | 상승 세션·ret60<0·고저 동반 상승·DD5 0.4~0.8%; FIRST | 35/35, 20 |
| G2 | 일반 비삼성 10만원 이상 | 하락 세션·ret60≥0.2%·혼합 고저·0.8%<DD5<1.2%; FIRST | 29/29, 37 |
| G3 | 일반 비삼성 2~10만원 | 중립 세션·ret60≥0.2%·고저 동반 상승·0.8%<DD5<1.2%·volume ratio≥1; FIRST | 17/17, 28 |
| G4 | 일반 비삼성 2만원 미만 | 상승 세션·ret60≥0.2%·고저 동반 하락·0.2%≤DD5<0.4%·spread≤0.1%; FIRST | 12/12, 1 |

현재 삼성 얕은 눌림의 확장 원천 결과는 **32/33**이다. 발행 당시 32/32를 고정 성과처럼 복사하지 않는다. H1·A1·J1의 성공은 오늘에 집중됐고 A1은 하나의 목표 접촉에 집중됐다. 일반 네 유형의 기존 대비 OR 결과는 **29,366/35,816→29,454/35,904**, 추가 WIN 88·미확정 70이며 오늘 추가 매칭은 0이다. 이 한계는 보고 항목이며 추가 최소 표본/날짜/holdout/성공 보존 탈락 조건으로 사용하지 않는다.

HPSP·알테오젠·주성의 5초 후속 확인, 일반 유형의 15초 고점 회복 등 후속 연구 결과는 보관한다. 첫 구현의 등록 목록에는 위 10개만 넣는다. 다른 확인 방식의 도입은 별도의 정의·입력·신호·보조 phase를 검토하여 등록 목록을 명시적으로 갱신한다.

### 3.1 정의를 고정할 때 함께 보존할 값

- `branch_id`, `definition_version`, `definition_sha256`, 연구 artifact/code/source hash, `registered_at`, origin=`manual_research` 또는 `existing_runtime_policy`.
- symbol 포함/제외, market, 실제 route/item 규칙, 가격대, 필수 특징과 단위·경계 연산자, anchor 시점, 확인 방식·기한, 결과 라벨 규격.
- 상태 `registered`/`selected`/`retired_from_selection`. selection에서 퇴역해도 과거 장중 적용 정의와 결과는 보존한다.
- 일반 G1~G4는 `{005930,034020,403870,196170,036930}`을 명시 제외한다. 고정 종목 집합이 바뀌면 scope version과 누적 비교를 새로 만든다.
- 연구용 `tmp` 코드 import를 운영 의존성으로 만들지 않는다. native registry가 정의를 소유하고 정식 발행 시 소비하는 최소 근거·입력은 content-addressed source 저장소에 고정한다.

### 3.2 특징·시점 경계

세션 상승은 해당 item/시장/날짜의 첫 유효 **관측 가격** 대비 ≥0.4%, 하락은 ≤-0.4%, 중립은 그 사이다. 공식 시가·지수 추세로 바꾸지 않는다. ret60은 연속 경로에서 t-60초 이하의 마지막 관측 대비 변화다. 최근 `[t-30,t]`와 이전 `[t-60,t-30)`의 고저를 비교한다. RISING은 고점과 저점 모두 엄격 상승, FALLING은 모두 엄격 하락, MIXED는 두 경우 이외의 유효 구조다. 특징 결손은 UNKNOWN이며 MIXED로 넣지 않는다.

DD5 0.4~0.8은 양 끝 포함, 다음 구간은 **0.8 초과~1.2 미만**이다. 가격대는 `<20,000`, `20,000≤p<100,000`, `≥100,000`이다. 10틱 매수 비율은 횟수 비율이 아닌 유효 매수 체결 수량/전체 체결 수량이다. VWAP은 기존 kernel의 유효 수량을 사용한다. 수량·매수/매도 방향 결손을 0으로 채우지 않는다.

유형·필터 값은 첫 반전 시점에 동결한다. 다음 상승 확인형은 그 이후 관측만으로 확인하며, 원 저점 재접촉·불연속·기한 초과 시 소멸한다. 진입 ask와 30분 라벨 시작은 **실제 확인 시점**이다. 확인 시점의 feature와 첫 반전의 filter feature를 별도 필드로 보존하여 뒤의 값으로 앞의 조건을 충족시키지 않는다.

## 4. 전 종목·전 시장 scope와 호환 구조

### 4.1 선택 소유권

새 family schema는 `continuous_reversal_policy_v3`로 계획한다. 기존 v1/v2 정의와 검증기를 덮어쓰지 않고 버전별 읽기를 유지한다. 새 선택 키는 `symbol_group × market × price_band`이며 하위에 실제 `route`별 적용 목록을 둔다.

- `samsung`: PRE/REGULAR/AFTER × ALL = 3개.
- `034020`, `403870`, `196170`, `036930`: 각 PRE/REGULAR/AFTER × 기존 가격대 3개 = 각 9개.
- `other_non_fixed`: PRE/REGULAR/AFTER × 가격대 3개 = 9개.
- 합계 **48개 논리 셀**. 고정 종목도 가격 경계에서 기존 정책을 정확히 이관하기 위해 가격대를 유지한다. 없는 가격대에 표본을 만들어 채우지 않는다. 향후 상시감시 종목 변경은 registry의 scope manifest로 관리한다.

현재 Main이 지원하는 market↔venue/item 계약으로 각 셀의 route 목록을 결정한다. 지원하지 않는 PRE의 KRX 주문 같은 조합을 새로 만들지 않는다. 개별 route 목록은 구현 시작 시 기존 normalized-source/runtime resolver의 실제 지원 집합을 동결한다. branch/portfolio 성과는 **같은 종목군·시장·가격대·route 모집단**에서 비교한다.

셀 선택의 가격은 기존 runtime과 같이 확인 시점 `confirmation_price`를 사용한다. 첫 반전의 유형 필터와 가격대는 별도 anchor 값으로 동결한다. 향후 비삼성 확인형이 가격대 경계를 넘으면 확인 가격 셀에 동일 정의가 선택돼 있는지 확인하고, 없으면 `confirmation_scope_changed`로 남긴다. 원 가격대 정책을 새 가격대에 몰래 적용하거나 사후 가격으로 anchor 유형을 다시 분류하지 않는다. 이번 G1~G4·네 고정 종목 후보는 FIRST라 두 시점이 같다.

고정 종목은 해당 고정 group으로 정확히 하나만 resolve한다. 일반 비삼성 패턴을 고정 종목에 이중 적용하지 않는다. legacy 13개는 고정 group에서도 비교할 수 있어 종목 전용 후보가 없다는 이유로 기본 정책이 사라지지 않는다. 새 전용 후보와 legacy를 함께 운용할 때에도 하나의 명시적 portfolio가 소유한다.

기존 12셀 기반 보고서의 aggregate/projection이 필요하면 `compatibility_projection`으로 발행한다. v3의 여러 group/route winner를 임의 한 개의 old `other` rule로 축약해 런타임에 쓰지 않는다. native writer/loader가 읽는 선택 원본은 하나다.

### 4.2 모든 시장에서의 복수 정책과 현재 후보의 적용 범위

모든 48셀·지원 route에서 길이 1 이상인 동일 portfolio schema를 지원한다. 삼성·REGULAR 분기만을 허용하는 하드코딩과 비삼성 단일 정책 catalog 제한을 제거한다. 상한 2개를 새로 두지 않는다. 같은 정의의 중복 등록은 오류다.

신규 S1~G4의 최초 등록 범위는 근거가 있는 **SOR REGULAR**이다. 전 시장 기능 지원은 이 정규장 조건을 PRE/AFTER 또는 KRX/NXT로 자동 확장한다는 뜻이 아니다. 다른 시장도 기존에 해당 범위를 지원하는 legacy 정책들의 등록 조합과 장중 적용 정책을 비교하며, 수동연구에서 해당 시장을 포함해 등록한 새 후보가 추가되면 같은 엔진에서 소비한다.

SOR 전용 단독 후보가 정규장 SOR에서 선택돼도 KRX/NXT route 목록은 각각의 비교·carry로 채운다. 따라서 기존 `legacy 분기 포함 여부`로 모든 route의 적용 가능성을 대신 검사하던 조건을 **route별 전체 지원 범위 검사**로 교체한다. 의도적으로 후보가 발행되지 않은 scope, 원천 무효, 유효 무신호를 구분한다.

### 4.3 표본 없음·시장 승계

1. 대상 scope의 comparable 누적 결과가 있으면 그 결과로 선택한다.
2. 없으면 같은 symbol group·가격대의 REGULAR 부모 중 대상 route/market에서도 의미가 정의된 정책을 승계한다. REGULAR 전용 S1~G4를 PRE/AFTER에 복사하지 않는다.
3. v2→v3 최초 이관은 활성 정책의 **전체 branch 목록·순서·primary 우선순위·FIRST/CONFIRMED 보조 binding**을 새 group/route에 연결하고 `carry_source`를 남긴다. 삼성 REGULAR의 기존 얕은 눌림도 보존한다. 삼성 전용 branch는 원래 지원 SOR REGULAR에만 배치하고 다른 route는 기존 legacy 평가와 같게 이관한다. 새 group 성과는 재계산하며 과거 `other` 전체 승률을 고정 종목 승률로 복사하지 않는다.
4. 승계 가능한 부모도 없으면 그 scope의 `applicable_parent_missing`을 명시한다. 해당 scope의 이전 유효 정책이 있으면 정상 scope 결과와 함께 하나의 bundle에 결속한다. 이전 유효 정책조차 없어 필수 적용 범위를 채울 수 없으면 incomplete candidate로 보존하고 전체 새 bundle 활성화를 보류한다. 기존 유효 bundle을 계속 사용할 수 있는지는 별도 검증한다. 이를 정상 scope의 원천까지 결손이라는 뜻으로 확장하지 않는다.

local 성과 없는 승계는 `local_metrics=null`, parent payload/definition/source hash를 보존한다. 무표본을 0%로 취급하거나 새 성과를 입증했다고 표시하지 않는다.

이관은 두 단계로 검증한다. 먼저 신규 후보를 선택하지 않은 compatibility fixture에서 구 활성 family와 v3의 branch pass/최종 기계 action·primary·보조 요청 bytes가 PRE/REGULAR/AFTER 및 지원 route에서 같아야 한다. 이때 기존 발행 순위를 이관 metadata로 유지하고 새 group 로컬 성과인 것처럼 쓰지 않는다. 그다음 분리된 scope에서 새 누적 비교를 실행해 새 순위·정책을 발행한다. 이관 자체가 정책 변경을 숨기지 않도록 차이를 두 보고서로 나눈다.

## 5. 고정 후보·조합·장중 정책 평가

### 5.1 catalog는 등록 때 고정

`registry manifest`는 패턴 정의와 별도로 비교할 `portfolio_id → branch 목록`을 갖는다. 다음 목록을 최초 등록 시 명시적으로 작성하고 hash로 고정한다.

| 대상 scope | 등록 비교 목록 |
| --- | --- |
| 모든 지원 scope | legacy 13개 단독, 현재 적용 portfolio, 해당 원천일에 실제 적용된 모든 portfolio/version |
| 삼성 SOR REGULAR | 기존 얕은 눌림·S1·S2 각각 단독, 이 세 branch의 명시된 부분집합과 legacy 각 단독의 병행 목록 |
| 네 고정 종목 SOR REGULAR | 해당 D1/H1/A1/J1 단독, 각 legacy와 해당 전용 후보 병행 |
| 일반 SOR REGULAR | 해당 가격대의 G 단독/등록된 G 조합, 각 legacy와 그 조합 병행 |
| 그 외 시장·route | 위 공통 목록과 legacy 복수 조합. 최초에는 legacy의 모든 서로 다른 2개 조합을 등록하며, 이후 복수 목록 추가는 registry 변경으로 고정 |

삼성의 부분집합과 일반 G 조합은 **등록 시 열거·리뷰하는 유한 목록**이다. 생성기는 manifest에 없는 powerset·threshold grid를 매일 만들지 않는다. 동의어·중복 portfolio는 정규화한 정의 hash로 제거한다. 3개 이상 정책도 schema가 허용하며 명시적으로 등록한 목록과 장중 적용 목록을 그대로 평가한다.

장중 실제 적용 목록은 current pointer 한 개로 대체하지 않는다. native activation/PID 소비 영수증에서 source day의 `family/portfolio/definition hash`, 적용 구간, release hash를 가져온다. 등록/선정만 되고 소비되지 않은 정책은 `prepared_not_consumed`로 별도 표기한다. 적용 이력이 결손이면 unknown으로 남기고 현재 정책을 종일 적용됐다고 추정하지 않는다.

실제 적용 정책은 두 모집단으로 보고한다. `applied_window_observed`는 해당 적용 구간의 자연 관측이고, `cumulative_fixed_definition_replay`는 고정한 정의를 전체 동결 원천에 재생한 값이다. 늦게 적용된 후보에 적용 전의 WIN을 자연 운영 성과로 붙이지 않는다. 적용 정책의 정의/code 증빙이 없으면 그 버전은 `historical_definition_missing`으로 남기며 오늘 정의로 소급 대체하지 않는다.

정기 작업은 과거 적용 정의를 자동 변형하거나 과거 퇴역 정책을 재활성화하지 않는다. 정상 후보의 현재 선택 가능 여부는 registry 상태가 소유한다. 과거 버전은 비교 이력으로 계속 평가한다. 장중 소유한 branch가 현재 catalog에서 빠진 경우에도 성과 행을 누락하지 않는다.

### 5.2 모집단·라벨·승률

기존 normalized 연속 가격 전체를 소비한다. ENTER_NOW/BLOCK/RECHECK/AI 호출 여부로 모집단을 제한하지 않는다. 후보 필터는 과거 정보만 쓰고, 결과는 확인 시점 ask에서 30분·비용 0.23%·비용 후 목표 +0.4%·soft -3% 선도달로 계산한다. 10분 이후 기존 가격과 같은 item 완성 분봉 보완을 유지한다. 미래 결과가 feature나 확인 판정에 들어가지 않도록 replay와 label 단계를 분리한다.

`WIN`, `FAIL_STOP`, `FAIL_TIMEOUT`, `UNRESOLVED`를 보존한다. 30분 경로·완성 분봉 coverage가 없는 미도달은 임의 TIMEOUT 실패가 되지 않는다. 양방향 barrier가 같은 분봉에 있어 순서를 알 수 없는 경우도 미확정으로 유지한다. 후보 확인 실패/만료는 미진입 상태이며 승률의 패배로 세지 않는다.

조합의 승률은 **중복 제거한 WIN / (WIN + FAIL_STOP + FAIL_TIMEOUT)**이다. canonical opportunity ID는 `{date,symbol,market,route,item,transport_epoch,confirmation_sequence}`이며 정책 ID/phase를 포함해 같은 틱을 중복 세지 않는다. 분기별 anchor는 lineage로 남긴다. 같은 ID의 ask/라벨 충돌은 source contract 오류로 격리한다. 다른 확인 틱은 별도 가격 기회이며 실제 독립 거래 수로 표시하지 않는다.

canonical ID는 같은 원천 stream의 namespace 안에서만 합친다. 연구 collector와 운영 WS의 epoch/sequence가 서로 다르면 원 생산자의 명시 mapping receipt가 있어야 자연 판정/실행과 연결한다. 가까운 시각·같은 가격만으로 연구 기회를 실제 미진입/주문으로 변환하지 않는다. mapping 미관측은 비교·적용 성과의 관측 한계로 기록하고 source를 새로 수집해야 한다는 결론으로 자동 확장하지 않는다.

같은 scope의 후보·현행을 같은 source universe로 재계산한다. 양쪽 매칭 교집합만 비교하거나 분기 승률 평균으로 조합 승률을 만들지 않는다. 개별 특징 결손은 해당 branch만 unavailable 처리하고, 공통 item/시간/가격 원천 결손은 공유 scope에 적용한다. 결손/UNKNOWN·날짜/종목/목표 접촉 집중도·기존 대비 추가/제외 성공을 함께 기록한다.

### 5.3 선택 순서

1. 유효 비교가 완료된 등록 portfolio의 raw 원분수를 `Fraction`으로 비교한다. 결과 분모가 0이면 null이고, 0승/양의 분모는 정상 0%다.
2. 가장 높은 누적 승률을 선택한다. 현행도 같은 frozen 원천으로 재평가한다. 현행 대비 누적 승률이 높으면 일부 기존 성공을 잃어도 선택 가능하다.
3. **동률은 기존 계약대로 현행 portfolio 유지**다. 현행이 동률 집합에 없으면 고정된 catalog 순서를 따른다. 조건 수/등록 순서 변동으로 현행을 교체하지 않는다.
4. 현행만 null이고 비교 가능한 후보가 있으면 유효 후보 순위를 적용하면서 `incumbent_not_comparable`을 남긴다. 유효 후보 자체가 없으면 §4.3의 carry를 따른다.
5. 최소 표본·일수·독립 새 날짜·holdout·EV·성공 100%/80% 보존 gate를 다시 추가하지 않는다. source/definition/hash 계약 검증은 유지한다.

복수 정책 지원은 모든 후보의 강제 OR 선택을 뜻하지 않는다. H1을 기존 HPSP와 합친 305/305는 기존 274/274와 동률이므로 위 규칙으로는 자동 추가되지 않을 수 있다. 다중 적용을 지원한다는 목표와 특정 조합을 최초 지정한다는 결정을 구분한다. 최초 신규 조합을 명시 지정하는 후속 지시가 있으면 기존 초기 지정 경로로 처리하고 추가 경제성 입증 gate를 만들지 않는다.

장후는 일별 결과도 출력하지만 일별 최고값을 새 누적 선택 기준으로 사용하지 않는다. 실제 장중 적용 구간의 결과·제출·체결·완료 손익은 별도 표로 보존하고 가격 반사실 승률과 합산하지 않는다.

### 5.4 원천·캐시·증분 평가

현재 producer가 같은 종목·날짜·시장에 대해 정상 행이 가장 많은 route 하나를 선택하는 경로는 v3의 route별 모집단에 사용하지 않는다. 보유한 각 지원 route/item을 독립 재생하고 실시간에서 사용하는 route와 같은 범위끼리 비교한다. SOR/KRX/NXT의 같은 상승을 시장 전체의 독립 거래 수로 더하지 않는다. 여러 route가 같은 종목의 실행 후보를 만들 때는 기존 symbol 단위 미체결/중복 주문 보호를 함께 사용한다.

캐시 키는 registry/portfolio 목록·과거 적용 정의, normalized source/완성 분봉 bytes, source cutoff, feature/confirmation/label code, 비용·horizon, scope/route 선택, parent family, source/publication/effective date를 포함한다. 새 원천일은 증분 추가하고 같은 날짜의 뒤늦은 완성 분봉·정정은 해당 partition 결과만 새 generation으로 재계산한다. 과거 발행 결과를 덮어쓰거나 `UNRESOLVED`가 해소되기 전의 옛 성공률을 재사용하지 않는다.

등록된 모든 후보/조합에는 비교 수와 terminal 상태가 있어야 한다. `valid_empty`, `no_resolved_sample`, `source_gap`, `evaluation_incomplete`, `evaluated_not_selected`, `selected`, `carry`를 구분한다. 일부 후보 재생이 중단됐는데 나머지 중 최고를 전수 비교 winner로 발표하지 않는다. 기계 비교 미완료 scope는 이전 유효 구성을 유지하며 미완료 후보 ID·원인·재개 checkpoint를 기록한다.

## 6. 실시간 복수 평가와 전달

공통 특징 상태는 `{date,symbol,market,route,item,epoch}`마다 한 번 갱신하고 해당 scope의 **선택된** branch만 조건·확인 상태를 평가한다. 모든 등록 후보를 장중에 전수 계산하지 않는다. 기본 가격 흐름과 필요한 rolling 수량/방향/고저를 공유하고 매 틱마다 과거 배열 전체를 재계산하거나 branch별 REST/WS 구독을 추가하지 않는다.

세션 최초 관측 anchor 복원은 현재 삼성 한 종목의 예외 경로에서 모든 해당 symbol/market/route로 확장한다. 재시작·늦은 구독에서 원 anchor를 기존 receipt/동결 접두로 복구할 수 없으면 세션 추세가 필요한 branch만 `required_feature_missing`이다. 현재가를 원 세션 anchor로 새로 지정하여 상승/중립 유형을 바꾸지 않으며, 그 특징이 필요 없는 legacy branch의 정상 평가를 함께 유지한다.

FIRST와 CONFIRMED는 여러 branch에서 동시에 존재할 수 있다. pending/ready/claim key에 definition·family generation·anchor·확인 틱을 결속한다. 확인된 한 branch가 다른 branch의 pending을 덮어쓰거나, 가장 앞의 unmatched confirmed가 유효 FIRST를 영구 가리지 않도록 **한 평가 시점의 applicable signal 묶음**을 판정한다. 선택되지 않은 연구 branch의 ready가 운영 평가 큐를 차지하지 않는다.

같은 confirmation tick의 매칭 branch를 합쳐 `ANY_MATCH_ONE_INTENT`를 만든다. 가장 높은 발행 시 branch raw 승률, 그다음 고정 우선순위로 primary를 정한다. 발행 scope의 branch 성과가 null이면 검증된 부모 순위/고정 순서를 사용하고 다른 종목 승률을 로컬 승률로 가장하지 않는다. 요청에 primary와 전체 matched 목록, group/route, feature as-of, definition hash를 결속한다.

primary가 결정된 뒤 보조 위험판정을 한 번 수행한다. 보조 veto 뒤 다른 branch를 골라 같은 기회에 재호출·재주문하지 않는다. 동일 확인 틱의 중복 provider/intent를 막고 서로 다른 확인 틱에는 기존 중복·cooldown·보유·미체결·주문 수량/자본 규칙을 적용한다. 복수 정책별로 주문 수량을 더하지 않는다.

같은 틱에서 여러 anchor/phase가 매칭되면 branch 정의별 대표 anchor를 가장 이른 유효 anchor, 동일 clock이면 canonical anchor ID 순으로 고정한다. 모든 anchor lineage는 보존하고 대표 anchor·primary 선택 함수를 replay/runtime/보조 입력 생산자가 공유한다. 다른 확인 틱의 신호를 하나의 입력으로 섞지 않는다. 평가 순간 서로 다른 틱의 신호가 동시에 남아 있으면 TTL/현재 경로 검증을 통과한 확인 시각 순으로 소비하고, 더 이상 유효하지 않은 FIRST는 별도 소멸 처리한다.

신호 claim 생성→준비 시작/종료→validation→보조 요청→intent의 같은 attempt clock을 보존한다. 준비 후 FIRST가 교체되거나 5초 TTL이 만료되면 그 신호의 성공 처리 없이 종료한다. 최신 claim을 재평가할 때는 새 attempt/input으로 전환한다. 이미 provider/intent 예약이 있으면 같은 실행으로 중복하지 않는다. 앞선 원천 보존 수리는 회귀로 유지하며 lifecycle 소멸을 API 원천 결손으로 오분류하지 않는다.

최신 호가/계정/보유/주문/quantity/cap/수동 veto/hard safety와 retired owner 제약을 그대로 통과해야 한다. 새 기능 때문에 시장 자체의 거래 제한을 추가하지 않는다. 검증 범위 밖인 개별 branch는 `not_applicable_scope`로 남기고 정상인 다른 branch를 평가한다.

## 7. 보조판정과 장후 연결

기계 승률 선택에 보조 응답을 섞지 않는다. 보조 후보는 현재 등록된 5개 prompt arm과 장중 적용된 문구의 고정 버전이다. 장후에 문구나 모델 파라미터를 자동 생성하지 않는다. AI 역할은 Main 기계 ENTER_NOW 이후 PASS/veto다.

보조 비교 키는 `selection scope × primary branch definition × decision phase × input/prompt/schema version`으로 계획한다. 같은 group/phase라는 이유만으로 서로 다른 종목 패턴의 PASS 성과를 합치지 않는다. 분기명이 입력에 수익성 힌트로 들어가거나 연구 WIN/FAIL이 AI 입력에 들어가지 않도록 특징/관측 사실만 직렬화한다. 기존 English ASCII prompt 계약을 유지한다.

기계 장후에서 선택한 portfolio의 실제 primary 경로와 장중 적용 baseline 경로에 대한 **동일 시점 입력**을 구성한다. 각 비교 집합의 모든 등록 arm에서 실제 response ID와 정확한 요청 bytes가 있는 공통 점을 평가한다. 장중 단일 arm 응답은 요청이 완전히 동일할 때 재사용할 수 있으나, 그 한 응답만으로 나머지 arm이 응답했다고 간주하지 않는다. 아직 선택되지 않은 기계 후보도 기계 비교 보고서에는 전부 남기며, 보조 재생 대상 수와 미대상 사유를 별도로 출력한다.

현재 date×cell×phase `[:24]`는 신규 scope/희소 branch를 누락시킬 수 있어 새 producer에서 제거한다. 횟수 quota None을 유지하고, 대상 전체의 `eligible / exact cache hit / needs call / completed comparable / deferred / failed`를 기록한다. 실행 전 실제 대상 수와 예상 호출 수를 산출하고 요청 단위 checkpoint/재개·외부 rate limit·timeout·중복 예약을 유지한다. 실행 시간 종료로 남은 입력은 `evaluation_incomplete`로 남기며 미평가를 무표본/평가 완료로 표시하지 않는다.

비교 키와 실제 요청 key를 분리한다. 같은 event/phase·정확히 같은 input/prompt/schema·provider/model/생성 설정을 쓰는 요청은 여러 portfolio에 속해도 한 번 호출하고 각 비교 소유에 참조한다. branch/scope 이름만 달라 같은 요청을 다시 호출하지 않으며, 설정·bytes가 다르면 재사용하지 않는다. 결과 분모는 각 비교 소유 안에서 opportunity ID로 중복 제거한다. 서로 다른 비교 표가 같은 response를 참조하는 것과 한 표본을 중복 집계하는 것을 구분한다.

24점 제한 제거 뒤에는 기존 전체 `points × arms` 요청 배열을 메모리에 한꺼번에 만들지 않는다. partition별 입력 iterator와 durable 요청 원장, bounded in-flight 실행으로 처리한다. 기계 replay는 출력 feature가 필요한 지점만 재사용하고 보조 호출은 exact-cache 차집합만 실행한다. 호출 수·예상 소요·디스크 임시 사용량을 P4 보고서에 남기며 resource 종료를 임의 표본 상한이나 성과 탈락 기준으로 바꾸지 않는다.

보조 순위는 기존 계약대로 `실제 raw PASS 중 WIN / 실제 raw PASS 전체`이며 validity 보정 점수를 순위에 넣지 않는다. 응답 schema·인용 결함은 따로 기록하고 runtime에서 잘못된 응답을 PASS 주문 허가로 사용하지 않는다. phase/input 계약이 같은 기존 유효 부모는 정확한 binding/hash로 승계할 수 있다. 새 phase/input에 적용 가능한 부모나 실제 응답 근거가 없으면 해당 보조 구성은 미준비다. 기계 연구 성과와 보조 준비 실패를 각각 기록한다.

기계 winner에 필요한 보조 구성이 준비되지 않았으면 `machine_selected_auxiliary_pending`으로 기록한다. winner를 기계 실패로 바꾸지 않고, 해당 scope는 기존의 유효한 기계+보조 쌍을 함께 유지한다. 새 기계에 다른 branch/phase의 보조 응답을 임의 결합하지 않는다. 새 선택을 발행하는 scope에는 해당 candidate 비교 종료와 필요한 보조 binding 준비를 요구한다. 미완료 scope의 검증된 carry를 포함한 family는 발행할 수 있지만 보고서에 전체 비교 완료라고 쓰지 않는다.

## 8. 생산·발행·소비·감시 변경 목록

새 Python 소유는 기존 `src/engine/scalping` 패키지다. registry/공통 feature engine/v3 family 구현 분리가 필요하면 이 안에 두고 `src/engine` root에 모듈을 추가하지 않는다. 테스트는 기존 `src/tests/test_continuous_reversal*.py` 또는 같은 위치의 v3 전용 테스트로 둔다. 위치는 구현 시작 시 주변 모듈을 확인하고 확정한다.

v1/v2 발행 코드 hash를 고정한 kernel/branch/auxiliary 파일은 새 의미로 덮어쓰지 않는다. v3 전용 registry·평가·producer를 같은 역할 패키지에 두고 기존 순수 함수는 정의가 동일한 부분만 호출한다. dispatcher와 native writer/감시 소비자를 확장한다. 구 family를 새 코드에 맞추려고 과거 계약 hash 검사를 느슨하게 하지 않으며, 구 release에서의 읽기/rollback과 새 v3 발행을 각각 검증한다.

| 변경 소유 | 구현 내용 | 검증 산출물 |
| --- | --- | --- |
| registry·공통 kernel/branch | 10개 후보 정의, 명시적 portfolio, scope/특징/확인 상태, 기존 정의 호환 | 정의 manifest·source prefix parity |
| branch postclose·postclose dispatcher | 모든 scope 누적 재생, 등록 후보·당일 적용 버전, 단독/조합 집계, 고정 선택 | candidate/portfolio 비교표·미선정 사유·carry |
| v3 family·native runtime policy | 48셀/route coverage, v1/v2 이관, candidate/activation CAS, 날짜·hash 검증 | migration·stage/activate·rollback 결과 |
| auxiliary contract/phases·producer | branch별 실제 입력·arm 비교·24점 잘림 제거·checkpoint | 요청/응답/기계 부모 binding·비교 수 |
| AI engine·Main state handlers | schema dispatch, 다중 claim 판정, primary·보조·intent 중복 제거 | Main trace·signal→request→intent receipt |
| source diagnostics·decision trace·병목 monitor | group/branch/phase 표시, branch 원천 결손과 lifecycle 소멸 구분 | 정상 다중 분기를 source_gap으로 오인하지 않는 회귀 |
| `monitoring/family_policy_semantics.py`와 기존 family 소비자 | 새 schema·definition/route·과거 생산 코드 증빙·발행 준비 구분 | 의미 검증 및 변조/누락 음성 검사 |
| `automation/postclose_summary_handoff.py` 및 native verifier/controller/PREOPEN | 새 결과 schema·code/source hash·target 일자·최종 소비 연결 | 새 generation strict·finalization·prepared |

`schema == v2`, `B.BRANCH/DEFINITION_SHA256`, `expected_cells()==12`, `phase_policies`, 005930 전용 session anchor 복원, CONFIRMED source 복원 등 영향을 받는 비교문과 직접 소비자를 전수 검색한다. 새 reader를 일부만 적용해 정상 bundle이 구 경로로 떨어지는 silent fallback을 금지한다. 코드 hash manifest에 새 registry/feature/consumer를 포함한다.

normalized source 소비 변경만으로 완료 가능한지 우선 확인한다. Kiwoom parser/FID/REG/REMOVE/복구 흐름 변경이 필요하면 AGENTS의 공식 API reference gate를 해당 변경 전에 수행하고 upstream SHA/path/조회 시각을 기록한다.

## 9. 구현 단계와 완료 조건

아래 P1~P7은 현재 단일 owner의 작업 단계이며 중복 checklist ID가 아니다.

| 순서 | 작업 | 완료 기준 |
| --- | --- | --- |
| P1 | 연구 후보·명시 조합·scope·현재/당일 적용 정의 동결 | native current 기준 신규 10개와 기존/적용 policy census, PRE/AFTER 8개 기존 셀·보조 binding 누락 0 |
| P2 | 공통 feature·복수 상태·v3 resolver 및 이관 | 후보 추가 전 구 family 행동 동등성, 같은 고정 접두의 branch 판단/확인 틱/ask/label parity, 48셀 지원 경로 coverage |
| P3 | 정기 기계 producer 교체 | 등록 전수+실제 적용 버전의 단독/조합 비교, 승률/동률/null/미확정·carry 재현 |
| P4 | 보조 producer·소비자 연결 | scope/branch/phase의 요청 bytes 일치, 실제 arm 비교·재사용·deferred 명세 |
| P5 | Main·native writer·semantic/strict/PREOPEN 통합 | 중복 intent/provider 0, 구 schema 읽기·원자 활성화·rollback 회귀 |
| P6 | 격리 생성 및 리뷰→보완→재리뷰 | in-scope 미해결 코드/계약 결함 0, 아래 targeted 검증 PASS, 실행 성능 보고 |
| P7 | 허용된 적용 시점의 배포·정책 발행·기동·관측 | selected release / prepared / 활성 policy / PID 소비 / 자연 판정을 각각 증명 |

P1에서는 registry 확정에 필요한 source receipt·소규모 비교 결과를 native immutable 저장소로 옮기고 hash를 대조한다. 실제 입력으로 필요한 원천은 현 retention 소유 아래 보호한다. 대용량 결과 전체를 운영 hot path에서 읽거나 임시 연구 파일을 유일한 정의 저장소로 두지 않는다.

P6 격리 재생은 provider/주문 호출 없는 기계 검증부터 수행한다. 미래 시세를 붙였을 때 이미 생성한 feature/signal이 바뀌지 않는 prefix invariant를 확인한다. P4의 실제 provider 비교는 예상 호출 census와 resumable runner로 수행하며 일부 완료를 전체 완료로 축약하지 않는다.

P7 시점에는 최신 workspace/release/부모 bundle을 다시 확인한다. 후보는 별도 파일에 stage하고 현재 parent hash가 맞을 때만 CAS 활성화한다. 기본 장후 흐름은 원천일·발행일·다음 영업일 effective 날짜를 보존한다. 운영 적용 시점 변경을 이 문서 작성만으로 실행하지 않는다. rollback은 정책만 내려 code/registry를 어긋나게 만들지 않고 검증된 release+family+dependency 조합을 복원한다.

문서·checklist·controller 입력이 바뀌면 배포 단계에서 해당 generation의 strict/controller/PREOPEN을 다시 봉인한다. 이번 계획 작성의 print-only parser 결과를 운영 prepared/PID PASS로 대체하지 않는다.

## 10. 필수 검증과 회귀 사례

| 범위 | 필수 사례 |
| --- | --- |
| 등록 정의 | 미등록 정의/hash 변조·중복 branch 거부; 등록 목록 고정 뒤 장후가 새로운 조건을 만들지 않음; 당일 적용 구버전 보존 |
| 범위 | 삼성·네 고정·일반 모집단 상호 배타; 가격 20,000/100,000 경계; PRE/REGULAR/AFTER·지원 route 각각 2개 및 3개 branch 평가 |
| 시장 승계 | SOR 전용 후보를 PRE/AFTER/KRX/NXT에 복사하지 않음; route별 정상 legacy 유지; 로컬 무표본 승률 null |
| 특징 | t-30/t-60 경계, DD .4/.8/1.2·ret .2·session ±.4 경계; 수량/방향 결손·미래 틱·sequence 충돌·불연속 UNKNOWN |
| 시점 | FIRST filter 동결; 실제 CONFIRMED ask/새 30분; 세션 첫 관측 anchor 복원; 장중 재시작에서 현재가를 최초 관측으로 대체하지 않음 |
| 복수 상태 | 여러 anchor/branch가 같은 틱 확인, FIRST+CONFIRMED 동시 일치, 일부 branch 원천 결손, unmatched ready가 다른 신호를 가리지 않음 |
| 전달 | 준비 후 FIRST 교체·5초 TTL·generation 변경, 정확한 claim 재평가/ack, duplicate request/intent·보조 veto 우회 0 |
| 결과/선택 | 같은 confirmation 틱 한 번 집계, 다른 틱 구분, UNRESOLVED 유지, 0%와 null 구분, 평균 승률 오용 금지, 원분수 동률 incumbent 유지 |
| 목적 | 기존 성공 일부를 제거해 raw 승률이 오르는 후보 선택 가능; 단독 각각 우수해도 OR 승률 낮으면 OR 탈락; 같은 승률의 추가 H1은 자동 채택 아님 |
| 평가 전수성 | 장중 가족 A→B→C 적용 후 세 버전 모두 비교; registry에서 제거된 과거 버전도 감사 행 보존; 실제 적용 구간과 누적 CF를 별도 출력 |
| 보조 | 새 group/branch 희소 입력이 24점 잘림으로 사라지지 않음; 실제 5 arm 요청·응답 exact binding; phase 다르면 캐시 오용 0; 미완료 보고·동일 요청 재시도 |
| 발행 | v1/v2 동일 bytes 읽기, v3 전체 직접 소비, report/definition/parent/date tamper, stale CAS, 동시 writer, rollback 및 partial-scope carry |

재리뷰에서 추가한 필수 사례는 dated v1/current v2 불일치 시 활성 부모 선택, 삼성 기존 CONFIRMED 이관, PRE/통합 AFTER의 기존 8셀과 보조 binding 보존, 새 scope의 session anchor 복원 실패 격리, 복수 anchor의 동일 틱 대표 선택, 다른 틱의 input 혼합 금지, 비교 키가 달라도 동일 요청 1회 호출, 대규모 iterator 재개 후 누락·중복 0이다. 이관 단계는 새 ranking으로 기존 행동을 바꾸지 않는지 검사하고, 이후 누적 선택 변화는 별도 기대값으로 검증한다.

고정 연구 원천에서는 §3의 S1/S2/D1/H1/A1/J1/G1~G4 confirmation ID 집합과 결과를 재현한다. 원 등록 삼성 32/33 및 일반 OR +88 WIN/+70 미확정도 차분 대조한다. 숫자 맞추기를 위해 scope/label/feature를 바꾸지 않는다. live source cutoff가 확대된 결과는 과거 고정 결과와 새 결과를 따로 출력한다.

부하는 동일 원천 접두에서 기존 v2 대비 공통 상태 업데이트·선택된 branch 평가의 처리량, queue/claim age, lock 대기, 메모리 최고값을 측정한다. 기존 pending/ready 한도를 단순 확대해 누락을 숨기지 않는다. 초과/만료 사유를 계측하고 실제 지원 선택 목록을 처리할 수 있도록 공유 계산과 큐 소유를 보완한다. 기존 source freshness/5초 claim 예산을 완화하여 성능 시험을 통과시키지 않는다.

Python 변경에는 `.venv` targeted pytest·compile·diff 검증, wrapper 변경에는 `bash -n`과 해당 계약 회귀를 수행한다. 문서 링크/owner/authority와 print-only parser를 확인한다. 자동화 규칙을 구현할 때 운영 문서·체크리스트 변경을 같은 변경 집합에 포함하며 baseline 문서 편집은 해당 사용자 지시 범위에 따른다.

## 11. 이번 계획 리뷰와 잔여 작업

계획 리뷰에서 다음 누락을 반영했다.

1. 삼성 전용 scope 검사만 제거하면 다른 route까지 연구 결과가 확장되는 문제 → 48개 선택 소유와 실제 route별 목록/승계를 명시했다.
2. 등록 정의가 늘어도 비삼성 catalog가 단독에 머무는 문제 → 모든 지원 scope에 복수 조합 manifest와 장중 적용 버전 비교를 넣었다.
3. 새 삼성 정제 정책과 원 눌림을 무조건 OR하면 정제 효과가 사라지는 문제 → 단독·등록 조합을 같은 source에서 각각 비교한다.
4. 고정 종목을 기존 other 통계에 다시 섞거나 기존 pooled 승률을 복사하는 문제 → 모집단 분리와 정확한 이관/null 계약을 명시했다.
5. branch별 별도 주문·보조 veto 재시도·confirmed 우선 큐의 FIRST 누락 → 한 평가 묶음, primary 한 개, 하나의 intent와 동일 기회 중복 방지를 명시했다.
6. current pointer만 평가하여 장중 이전 버전이 사라지는 문제 → activation/PID 구간 census를 포함했다.
7. 보조 date별 24점 제한이 종목/유형 확장을 무력화하는 문제 → eligible 전수 census·exact cache·checkpoint·미완료 표시로 보완했다.
8. 동률 현행 유지가 복수 정책 강제 채택과 충돌할 수 있는 오해 → HPSP 사례로 자동 선택과 최초 지정의 차이를 명시했다.
9. 기존 day별 단일 route 선택·새 group 캐시 오용 → route별 재생과 registry/source/label 전체 cache fingerprint를 추가했다.
10. 적용 가능한 부모가 전혀 없거나 보조 비교가 미완료인데 새 family가 완료로 발행되는 문제 → scope별 기계+보조 carry와 incomplete candidate/activation 금지를 명시했다.
11. 확인 전후 가격대 변경·과거 코드 hash 무효화 → anchor/confirmation 시점 분리와 v3 전용 구현 경계를 보완했다.

이번 문서의 완료는 요청 1~3의 구현 경로·등록 범위·비교 기준·소비자·검증·적용 단계가 정의된 상태다. 코드 구현, 실제 후보 선택, 운영 소비 및 실현 성과는 아직 이 계획의 완료 증거가 아니다. 다음 작업은 P1부터 등록 정의와 공통 재생/실시간 평가 구현을 시작하는 것이다.

## 12. 10/7 추가 계획 리뷰 보완

| 발견한 계획 결함/모호함 | 보완 |
| --- | --- |
| 새 후보의 SOR REGULAR 제한이 PRE/AFTER 정책 부재로 읽힐 수 있음 | §2.1에 현재 활성 8셀·보조 binding·통합 AFTER alias와 근거 generation 명시 |
| 날짜별 파일만 보면 최초 v1을 incumbent으로 잘못 이관 | native load/current/PID 구분과 활성 부모 동결 명시 |
| 최초 이관 문구가 legacy만 언급해 삼성 기존 CONFIRMED를 누락할 위험 | 전체 branch·순서·primary·phase 보조를 보존하는 이관 parity 추가 |
| group/route 분리와 후보 채택이 동시에 일어나 이관 회귀를 감춤 | 구 행동 동등성 검증 후 별도 누적 비교·선택 단계로 분리 |
| 세션 anchor가 삼성만 복원되어 다른 종목의 유형 판정이 잘못될 위험 | 모든 필요한 scope의 원 anchor 복원 및 branch 단위 결손 처리 |
| 여러 anchor/phase/틱의 primary 입력 선택이 미정 | 동일 틱 대표 anchor·primary 공통 함수와 틱 간 입력 분리 규정 |
| branch별 비교 확대로 같은 실제 AI 요청이 반복되고 전수 배열이 과대해질 위험 | comparison/request identity 분리·exact reuse·partition iterator·checkpoint |
| 적용 전 재생 성과를 자연 성과로 오인하거나 collector/live 시계를 근접 연결할 위험 | 적용 구간/누적 고정 재생 분리, 원 stream namespace·mapping 증빙 명시 |

위 재리뷰는 구현 승인 이전의 문서 검토 이력이다. 후속 사용자 지시로 구현·실제 보조 비교·배포·재기동을 수행한다. P1의 활성 generation과 실제 지원 route 목록을 새로 동결하며 신규 분기를 임의 다른 시장으로 확장하지 않는다.

검증은 계획의 로컬 링크·단일 OPEN owner·print-only parser·공백/diff 검사와 현재 native loader의 PRE/AFTER 8셀·보조 binding·시장 alias 읽기 대조로 닫는다. 문서 작업이므로 매매 pytest·정책 재생성·provider 호출은 이번 검증 대상이 아니다.

## 13. 승인된 구현과 운영 인계

- 실행 소유: `DirectFamilySourceRepairMainMechanisticEntry`; [구현·리뷰 감사](../audits/main-registered-multi-policy-v3-implementation-review-2026-10-07.md).
- 코드 소유: 기존 `src/engine/scalping` 안의 v3 registry/runtime/policy/postclose. 기존 해시 고정 v1/v2 kernel·branch·보조 모듈의 bytes를 유지한다. 새 engine-root 모듈은 만들지 않는다.
- 운영 장후: 기존 `continuous_reversal_postclose` dispatcher와 native stage/writer/loader/semantic/strict/PREOPEN을 통해 v3를 소비한다. 기계 단계의 비교 원본을 보조 단계에서 덮어쓰지 않으며 발행 가능한 기계·보조 쌍은 그 비교에 결속한 별도 immutable source다.
- 보조 실행: 요청 횟수 제한 없이 exact request ledger와 bounded in-flight를 사용한다. 기존 stage의 종료 시각 전에 예약된 호출을 drain하고, 미완료·불확실·실패 수와 체크포인트를 기록한다. 부분 비교를 전수 완료로 표시하지 않는다.
- 무표본: 동일 group/band의 적용 가능한 REGULAR 부모, 검증된 이전 scope 순서로 승계한다. 정규장 전용 연구 후보를 PRE/AFTER/KRX/NXT로 복사하지 않는다.
- 재기동: 새 code PID 확인 후 현재 parent에 CAS하여 v3를 적용한다. 원 PREOPEN·EOD·과거 DONE은 보존한다. 소비된 historical checklist의 관측 검증과 신규 기동의 current checklist 검증을 분리해 문서 갱신으로 `strict_checklist_generation_stale`가 재발하지 않는지 확인한다.
