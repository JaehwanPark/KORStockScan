# Main 진입 승률 정책 초기 적용·매일 장후 갱신 구현계획 — 2026-09-24

상태: **구현·검토·9/23 frozen 정책 발행·main release 선택 완료; 9/28 장전 활성화·실제 PID 소비·새 자연일 전체 장후 수용은 OPEN.** [확정한 승률 단독 초기 정책안](../audit-reports/2026-09-24-main-entry-three-market-win-rate-only-initial-policy-v1.md)을 2026-09-28 다음 영업일의 초기 적용 목표로 삼는다. [9/24 구현·배포 영수증](../audit-reports/2026-09-24-main-entry-winrate-implementation-review-deployment.md)은 코드와 frozen 재생의 수용 범위를 기록한다. 실제 매매 PID 소비 증거는 아직 없다.

## 1. 고정할 정책 계약

1. 시장 상황은 `PREMARKET`, `REGULAR`, 통합 `AFTERMARKET` 세 구간만 사용한다. exact venue/session은 정책·원천·주문 영수증의 결속 키다. 초기 행동 변화는 **`KRX|KRX_REGULAR`에만** 적용한다. 다른 REGULAR exact scope, PREMARKET, AFTERMARKET은 현재 정책을 유지한다.
2. `KRX|KRX_REGULAR`에서 기존 기계 판정이 `ENTER_NOW`이고, 같은 판정시각의 검증된 `micro_vwap_available=true`, `minute_candle_window_fresh=true`, 유한한 `curr_vs_micro_vwap_bp >= 68.75`이면 **그 시도만 `BLOCK`**한다. `<68.75`면 기존 판정을 유지한다. 결손·불일치·비유한값은 `VWAP_UNKNOWN`으로 별도 세고 기존 판정과 원래 hard safety를 유지한다. 숫자 0 초기값을 유효 관측으로 취급하지 않는다. 기존 `BLOCK|RECHECK`를 `ENTER_NOW`로 올리는 경로는 없다.
3. 초기 연구의 유일한 순위 지표는 고유 기회 균등 가중 **비용 결속 목표 선도 승률**과 표본수 보정 승률이다. 수익률 크기·EV·paired 수익 차이를 선택 점수/승격 조건으로 쓰지 않는다. 기준 정책의 선택 진입 29시도에서는 `net_target_first|exact_stop_first`와 gross target/adverse 승패가 같지만, 엄격 유효 전체 476행 중 **9행은 다르다**. 정책은 비용 결속 경로의 이진 label만 사용하고 gross와의 차이를 별도 대사한다. 운영 비용·실현 손익은 별도 진단으로 기록하되 승률 점수에 섞지 않는다.
4. 최초 정책 버전 `winrate_initial_v1`의 68.75bp 경계·source manifest·현재 parent machine hash·exact scope·목표일·role/authority를 immutable 초기 정책 영수증에 고정한다. 학습 9/22 선택 11기회 10승, 날짜순 9/23 진단 4기회 3승은 **초기 채택 근거**이며 이후 갱신 허들을 소급 적용하지 않는다. 697개 탐색·4개 날짜순 진단 기회 및 현 기준 정책이 9/23을 이미 소비했다는 한계도 그대로 남긴다.

정책 payload에는 별도 검증 필드 `entry_situation_veto={schema: entry_situation_veto_v1, selection_basis: win_rate_only, market: REGULAR, exact_scope: KRX|KRX_REGULAR, feature: curr_vs_micro_vwap_bp, threshold_bp: 68.75, condition: parent_ENTER_NOW_and_fresh_available, selected_action: BLOCK, unknown_action: parent}`를 포함한다. 현재의 일반 threshold나 AI prompt 필드에 수치를 숨겨 넣지 않는다. evaluator·publisher·loader·runtime이 이 구조와 해시를 동일하게 읽고, 미지원 버전은 fail closed로 승격하지 않는다.

## 2. 구현 순서와 소유자

| 순서 | 생산자·소비자 | 변경 및 수용 조건 |
| --- | --- | --- |
| A. 실행 권한 정합화 | [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1·§2·§3·§7, [traceability](../report-based-automation-traceability.md) | 사용자 지시의 범위를 **main 기계 진입의 승률 단독 초기/후속 선정**으로 한정해 `primary_ev`/`diagnostic_win_rate`와 live 승격 충돌을 명시적으로 개정한다. 타 진입 가격·holding/exit·sizing·widget/episode·sim 정책의 EV 계약은 유지한다. 초기 채택과 후속 승률 허들의 권한을 별도로 기록하고 9/28 checklist의 실행 owner와 동기화한다. 이 문서는 기준 문서를 지금 수정하거나 live 권한을 합성하지 않는다. |
| B. 판정 전 원천 | [feature producer](../../src/engine/scalping_feature_packet.py), [strategy raw 입력·selector](../../src/engine/scalping/entry_strategy_policy.py), [setup 판정](../../src/engine/scalping/entry_setup_evidence.py) | 기존 `curr_vs_micro_vwap_bp`를 재사용한다. 값·`micro_vwap_available`·`minute_candle_window_fresh`·시각·raw hash를 같은 캡처로 묶고, availability가 거짓인데 0인 행은 `UNKNOWN`이다. 기존 `mechanistic_entry_policy_decision` 안에서 exact-scope·기존 `ENTER_NOW` 한정 veto를 계산해 최종 action/reason/상황/parent 및 정책 hash가 동일한 영수증에 남도록 한다. 별도 늦은 주문 단계 overlay로 붙이지 않는다. 새 Kiwoom 요청이나 FID는 없다. |
| C. 과거·매일 장후 평가 | [main evaluator](../../src/engine/scalping/ai_action_outcome_calibration.py), [strategy rank](../../src/engine/scalping/entry_strategy_policy.py) | clean baseline 이후의 자연 exact attempt·원천 hash·현재 완료봉 구조·이진 terminal label을 보존한다. 비적격/충돌/미완료를 승패 0으로 채우지 않고 전수 `input → accepted → excluded(reason)`을 scope/시장/상황별로 기록한다. 초기 77필드 탐색 결과는 immutable bootstrap 입력으로만 사용하고, 이후 자동 검색은 등록된 `curr_vs_micro_vwap_bp`의 train-only 분위 경계만 탐색한다. 기존 `machine_admission_rank`의 EV tie-break 및 `promotion_pass` 의미를 새 승률 전용 선택 계약과 분리한다. |
| D. 정책 발행·로더 | [publisher/loader](../../src/engine/scalping/mechanistic_entry_runtime_policy.py), [live resolver](../../src/engine/scalping/entry_setup_live_policy.py) | 초기 발행은 후속 성과 `promotion_pass`를 가장하지 않는 **명시적 initial adoption 경로**로 만든다. 9/24에는 parent CAS·immutable generation·source hash·target_date=2026-09-28·exact-scope hash를 가진 **날짜별 대기 정책**만 만든다. 현재 validator는 미래 `strategy_activation.effective_from`을 거부하므로 `current.json`을 미리 미래 세대로 가리키지 않는다. 9/28 장전의 검증된 activation에서 실제 KST activation 시각·parent CAS를 기록하고 pointer를 전환한다. `current.json` 우선 로딩이 날짜별 정책을 가리는 문제와 stale/corrupt 처리를 명시적으로 검증한다. bootstrap/selected release와 실제 PID의 bundle+scope hash를 따로 대사한다. 새로운 진입 권한은 만들지 않고 veto만 추가한다. |
| E. 장후/장전 소비·의미 감시 | [stage dispatcher](../../src/engine/automation/postclose_summary_handoff.py), [runtime summary](../../src/engine/runtime_approval_summary.py), [strict verifier](../../src/engine/verify_threshold_cycle_postclose_chain.py), [semantic detector](../../src/engine/error_detectors/artifact_freshness.py), [PREOPEN wrapper](../../deploy/run_threshold_cycle_preopen.sh) | 기존 `main_machine_policy → legacy_machine_report → summary → strict → controller/finalizer` 소유 경로에서 `selection_basis=win_rate_only`, source/parent/candidate/active hash, 상황별 진입·차단·승리/패배·unknown·제외 분모와 gross/net label 차이, `initial_adopted|successor_selected|incumbent_carried|source_gap`를 정확히 전달한다. 현 `main_machine_policy --activate-now`는 후속 후보 평가·다음 영업일 대기 발행으로 바꾸고 PREOPEN에서 검증된 후보만 활성화한다. 선택 결과를 live 수익 승인으로 읽는 기존 consumer를 고친다. 감시기는 영수증만 정상인 경우에도 0/0 승률, 후보-발행-로더 hash 불일치, scope disposition 불일치, 이전 정책의 무단 덮어쓰기, 현장 action의 68.75bp 위반을 탐지한다. 원천 자체가 없는/미도래 상태는 별도로 표시한다. |

기존 `current.json` 세대가 날짜별 bundle보다 우선하고, 현재 top-level `machine_disposition`과 scope 내부 disposition이 달랐던 사례는 D/E의 회귀 대상으로 둔다. 작업본 변경은 immutable release에 자동 반영되지 않으며, 선택 release/설치 unit/PID를 각각 검증한다. 코드·wrapper 변경과 함께 해당 운영 문서/checklist를 같은 변경 세트로 갱신한다.

## 3. 9/28 초기 적용의 닫힌 경로

1. **9/28 장전 전:** A→E를 구현하고 review→수정→재검토→영향 테스트/compile/wrapper `bash -n`/`git diff --check`를 통과한다. 9/23 frozen 유효 476행을 별도 작업 경로에서 재생하여 기준 대비 REGULAR 29→15 선택 시도와 17→13 목표 선도 시도, PREMARKET/AFTERMARKET 및 다른 exact scope의 행동 불변, `UNKNOWN` fallback, hash 일치를 확인한다. 기존 원본 보고서나 frozen ledger를 덮어쓰지 않는다.
2. **초기 정책 발행:** `source_date=2026-09-23`, `publication_date=2026-09-24`, `target_date=2026-09-28`을 구분한 `winrate_initial_v1` 날짜별 대기 generation을 발행하고 현재 parent hash에 대한 CAS 및 별도의 rollback generation을 남긴다. 기존 `current.json`은 9/24 동안 변경하지 않는다. 9/28 장전 검증을 통과한 후 그 시각의 `effective_from`으로 현재 pointer를 원자적으로 전환한다. 승인되지 않은 자동 `--activate-now` 후보가 초기 정책을 다시 덮지 못하게 발행 순서와 초기 고정 상태를 검사한다.
3. **장전 검증:** 정책 source→published bundle→PREOPEN activation/bootstrap/loader→선택 release의 해시·scope·`effective_from`을 대사한다. 이후 실제 실행 PID가 선택 release와 해당 generation을 읽었는지 직접 영수증으로 확인한다. 이 단계 전에는 `적용 완료`라고 표기하지 않는다. 수리·검증이 장전 시각까지 완료되지 않으면 기존 정책을 유지하고 누락된 정확한 단계와 차단 사유를 남긴다.
4. **정상 사용 후:** 실제 `machine_action`, AI 보조 veto, 주문 계획·제출·체결·terminal을 별도 분모로 관찰한다. 승률 연구 CF, 실제 체결 승률, 실현 손익을 혼용하지 않는다. source/hash 손상 또는 hard safety 위반은 기존 승인된 rollback 절차를 따른다.

## 4. 9/28 이후 매일 장후 후속 정책 갱신 허들

초기 버전은 고정 기준점이다. 매일 장후에는 현재 **마지막으로 검증된 활성 정책**을 parent로 평가한다. 합격 successor가 아직 없으면 그 정책은 `winrate_initial_v1`이다. successor를 한 번 선택한 뒤 다음 날 합격 후보가 없으면 그 마지막 합격 정책을 유지한다. 초기 정책 hash는 복구 기준으로 보존하며, 후보 없음만으로 자동 복귀시키지 않는다. 새로운 날짜별 receipt의 날짜·source hash는 갱신하되 활성 **machine policy payload/hash는 동일하게** 유지한다.

| 허들 | 후속 후보의 별도 기준 |
| --- | --- |
| 원천·분모 | clean baseline 이후, 같은 exact scope/판정 전 캡처/완료봉 구조/신선한 VWAP/고유 attempt·기회/완성된 이진 terminal. 원천·label·정책 hash 결손 또는 충돌은 이유별 제외. 전체 스코프를 막는 범위는 원천 격리가 불가능할 때로 한정. |
| 탐색·독립성 | 등록된 VWAP 단일 경계만 학습 날짜의 고유값 분위 grid에서 생성한다. 후보·parent·분모·코드 hash를 **holdout 날짜 결과가 나오기 전에** 고정하고, 후보/기회/날짜별 holdout 소비 영수증을 남겨 재사용·중복 기회를 막는다. 초기 9/23 진단은 successor의 새 독립 holdout으로 재사용하지 않는다. |
| 최소 표본 | train은 3개 이상 원천일·후보 선택 30개 이상 고유 기회, holdout은 그 이후 2개 이상 원천일·후보 선택 10개 이상 고유 기회. 기준 정책도 두 구간에서 정의된 선택 승률을 가져야 한다. 0건은 0%가 아니라 `insufficient_sample`이다. |
| 승률 통과 | 같은 기회·같은 이진 label에서 후보의 **기회 가중 원시 승률과 표본수 보정 승률이 train·holdout 모두 기준보다 높고**, 표본수 보정 차이가 각 구간 **+5.0%p 이상**이어야 한다. 절대 선택 수를 0에 가깝게 줄여 승률을 부풀리지 않도록 후보의 선택 기회가 기준의 50% 이상이고, 기준의 목표 선도 시도 중 80% 이상을 보존해야 한다. 이들은 승률의 신뢰성·참여 guard이며 수익률 조건이 아니다. |
| 발행·carry | 위 조건과 소유권/안전/정확한 source→candidate→bundle 검증을 모두 통과한 **한 scope의 한 successor**만 다음 거래일 bundle에 CAS 발행한다. 후보 없음·동률·표본 미달·원천 결손·strict 실패에는 이유를 남기고 마지막 검증된 활성 **machine policy payload/hash**를 동일하게 carry한다. 다른 시장과 exact scope는 그대로다. |

이 숫자는 **후속 자동 갱신 전용 고정 구현 상수안**이며 초기 `winrate_initial_v1`의 11/4기회에 소급 적용하지 않는다. `promotion_pass`와 `allowed_runtime_apply`, 장전 loader 통과, 실제 PID 소비는 각각 따로 기록한다. 사용자의 승률 목적을 다른 EV family로 확대하지 않는다.

## 5. 장후 전체 실행·성능 수용

구현·리뷰가 닫힌 뒤 먼저 격리된 frozen 9/23 원천으로 full postclose chain의 변경 영향 stage부터 최종 consumer까지 재생하고, 이후 9/28 **새 자연 원천일**에 기존 장후 wrapper를 전부 실행한다. 활성 15개 stage의 latest receipt, source/prerequisite/code hash, full strict `--require-summary-handoff`, controller DONE, finalizer/cleanup/detector terminal을 확인한다. 새 정책 산출 성공과 전체 chain 완료, 자연 PID 소비, 실제 승률은 각각 별도 결론으로 남긴다.

성능은 단계별 **compute wall/child CPU/peak RSS/swap**, 원천·EOD/resource slot 대기, retry, 후보 수·replay call·cache hit/miss, 원천·분모·정책 결과 hash를 함께 수집한다. 기존 Main replay는 12,127시도×96후보에서 80분 초과·약 3.6GiB RSS+swap 중단 이력이 있으므로 [기존 장시간 작업 최적화 계획](./postclose-long-running-work-quality-preserving-optimization-plan-2026-09-23.md)의 중복 제거/체크포인트/동등성 결과를 기준으로 비교한다. 승률 계산은 한 번 검증한 이진 label·기회 ID·사전 feature를 재사용하고 후보마다 대용량 raw/evidence를 다시 복사하거나 비용 경로를 재계산하지 않는다. 동일 frozen 입력의 행동·분모·label·선택 hash 동등성을 확인한 뒤 compute CPU 또는 compute wall **20% 이상 감소를 목표**로 한다. 목표 미달은 미달로 기록하며 모집단·독립 holdout·원천 검사를 줄이지 않는다. 메모리 압박이나 slot 경합이 재발하면 실제 병목 owner에서 제한된 page/순차 실행을 먼저 검토한다. 성공 stage는 입력·코드·prerequisite hash가 같을 때만 재사용한다.

## 6. 완료 기준과 현 상태

- 초기 적용 완료: 9/28 dated/active generation의 정책·원천·발행 hash, PREOPEN strict/loader, 선택 release, 실제 매매 PID의 exact-scope 소비 영수증이 모두 일치한다. 정책 파일만 존재하거나 9/23 연구 승률이 높다는 사실은 완료가 아니다.
- 일일 갱신 완료: 장후 source/제외/상황/승률 전수 대사, successor 허들 판정, 채택 또는 활성 machine policy hash 유지, 다음 영업일 발행·장전 수용, full strict/controller/finalizer/의미 감시가 각각 닫힌다. 매일 합격 후보가 있어야 완료되는 것은 아니다.
- 성능 완료: 새 원천일 full chain의 stage별 시간·CPU/RSS/swap·대기/재시도와 terminal 영수증을 얻고, 병목이 있으면 결과 동등성 검증을 거쳐 수정·재실행한다. frozen 재생의 속도만으로 자연 실행 성능을 승인하지 않는다.
- **현재:** 추가 검토 코드 release `bd001179`가 main selector에 선택되었다. 9/28 대기 정책 `4d08df81`의 machine hash는 `d94fecaf`이고 9/24 활성 parent `99cb0e3a`의 `current.json`은 유지했다. 9/23 frozen 전체 활성 stage와 strict `--require-summary-handoff`는 PASS했다. 9/28 PREOPEN activation·loader/bootstrap·실제 PID 및 9/28 새 자연 원천의 전체 장후 수용은 checklist의 `[MainEntryWinRateInitialPolicy0928]`와 `[MainEntryWinRateDailyPostclose0928]`가 계속 소유한다.
