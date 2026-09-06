# Market panic breadth 보완·리뷰

기준일: `2026-09-06 KST`

## 1. 판정

- 현재 판정은 **R1~R5 코드 보완 종결 / 자연 적용·경제성 검증 대기**다. 아래 §8이 §6~7의 이전 검토 판정을 대체한다. 2회 activation/3회 release의 발동 가능성은 확인했지만, 자주 발동한다는 사실은 매수 차단이 과도하지 않거나 비용 차감 EV가 개선된다는 증거가 아니다.
- 실전 권한은 `WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_FREEZE_OPEN_BUY_CANCEL_V2`의 위젯·에피소드 신규/추가 BUY 및 exact-owner 미체결 BUY 잔량 취소에만 있다. main bot, 보유, SELL/target, 수량, 가격, provider, broker hard safety에는 권한이 없다.
- 상승·반등 예외는 활성화하지 않았다. 보완 코드의 읽기 전용 재평가에서 30분 executable-BBO 비용 차감 반사실 표본은 `1→4/778`로 복구됐다. widget/KOSDAQ strata는 여전히 비어 있고 개선 후보는 없다. 반등·재진입 평가는 **기존 Machine entry timing에 통합 구현하기로 결정**했으며, 이번에는 결정과 미구현 상태 명시까지 완료했다.

## 2. 확인된 구조 결함

1. exact-date hysteresis policy가 이후 재생성될 수 있는 일별 machine attribution 파일의 전체 hash를 직접 참조했다. 2026-09-04 장중 source가 변경되면서 exact policy가 baseline fallback으로 바뀌었고 notifier가 `intraday_hysteresis_policy_mismatch`를 반복했다.
2. notifier CLI가 위 mismatch와 invalid/missing source 상태에서도 exit 0을 반환했고 intraday wrapper가 `|| true`로 무시했다. state가 멈춰도 wrapper는 DONE과 cooldown을 기록할 수 있었다.
3. live guard는 거래일만 확인하고 마지막 정상 관측의 age를 확인하지 않아, 같은 날짜의 오래된 active latch가 계속 BUY를 막을 수 있었다.
4. threshold floor는 activation/release 자체보다 executable 0B/0D 수집률 때문에 달성 불가능했다. 2026-09-04용 collection target은 장중 12:54에 생성돼 registration receipt가 없었다. 2026-09-07용 manifest는 전일 생성돼 활성 owner 18종목/26 exact-route item 전부를 우선 수집하도록 준비돼 있다.

## 3. 구현 보완

- policy schema를 v2로 올리고, policy에 필요한 `market_weakness_entry_response` section만 source-date와 canonical SHA가 포함된 content-addressed immutable snapshot으로 생성한다. policy loader는 일별 mutable origin이 아니라 이 snapshot만 검증·소비하며 origin path/hash는 provenance로만 확인한다. 기존 v1 또는 snapshot 변조는 2/3 baseline으로 fail closed한다. 전체 3.6MB report 복제 대신 약 212KB section snapshot을 사용한다.
- notifier state write를 atomic replace로 바꾸고 `market_weakness_observer_health_v1` receipt를 같은 state 파일에 남긴다. missing report/observation, invalid policy, intraday policy mismatch, source-quality block은 CLI exit 2다.
- intraday wrapper는 market-weakness state 갱신 실패를 무시하지 않고 FAIL로 종료하며 cooldown/DONE을 기록하지 않는다. Telegram 비활성화는 계속 `--observe-only`로 정상 state를 전진시킨다.
- live guard는 마지막 정상 관측을 최대 300초만 사용한다. health receipt가 실패 상태여도 마지막 정상 latch는 TTL 안에서만 유지되고, TTL 초과·timestamp 결손/미래 skew는 주문취소 권한을 주지 않는다. 이는 hard-safety 해제가 아니라 bounded market-risk veto의 무기한 과잉 차단 방지다.
- threshold report에 eligible yield, 일평균 eligible signal, 50건 floor까지 예상 거래일, 비어 있는 owner/market strata와 `collection_contract_gap`을 추가했다. 수집률이 낮을 때는 floor를 낮추지 않고 exact-route 0B/0D registration/horizon capture 수리를 먼저 요구한다.

## 4. 목적·자동화·조건 재확인

| 항목 | 최종 판정 |
| --- | --- |
| 목적 부합성 | 시장 위험 분리·일시 차단 및 평가 계약 보완은 구현. 상승/반등·재진입 경제성 평가는 §8에 따라 기존 timing 통합 구현 대상으로 분리; EV 개선 효과는 미입증 |
| EV 방향 | 손실 억제 자체가 아니라 `skip/delay/control`의 비용 차감 증분 EV와 놓친 상승을 함께 비교하도록 유지 |
| 자동화 연결 | intraday breadth→panic report→notifier health/state→widget/episode guard, postclose attribution→21:15 policy→다음 session exact policy로 연결 |
| activation/release 조건 | 2/3 baseline은 발동 가능. 경제적 적정성은 미검증이며 발동 빈도만으로 과도성 여부를 판정하지 않음 |
| tuning 조건 | 다른 horizon 결손의 연쇄 제외와 오분류 건수 hard veto 제거. 비용 차감 EV·OOS·꼬리손실·10일/50건·공통 market/owner 근거는 유지 |
| 반등 예외 | 비용 차감 exact BBO 근거 부족으로 source-only 유지 |
| 남은 운영 증거 | 2026-09-07 정상 PID의 manifest receipt, health 연속 정상, blocked anchor 30분 성숙, postclose yield/EV 필요 |

## 5. 수용 기준

- PREOPEN/기동 후 `scalp_micro_reversion_registration_receipt_2026-09-07.json`의 requested item census가 manifest와 일치하고 활성 owner exact route마다 0B/0D receipt가 존재한다.
- intraday health의 `ready=true`, `consecutive_failure_count=0`, last healthy observation age가 300초 이내로 유지된다. mismatch/source block이면 wrapper가 FAIL하고 stale latch는 TTL 뒤 주문취소 권한을 잃는다.
- 장후 `threshold_recommendation.attainability`가 실제 eligible yield와 zero-yield strata를 표시한다. `collection_contract_gap`이면 threshold floor나 breadth 기준을 낮추지 않는다.
- 비용 차감 OOS 근거 전에는 상승·반등 예외와 threshold 변경을 live 적용하지 않는다.

## 6. 리뷰 상태

구현 후 producer/consumer, notifier, runtime guard, wrapper, threshold report 계약을 재검토했다. 1차 targeted 157건 PASS 후 immutable inode overwrite race와 health failure-count 정규화를 추가 보완했다. 확장 회귀에서 immutable 파일 변조 테스트 자체의 권한 설정 1건만 수정했고 최종 **605 PASS**다. Ruff, Black, compileall, wrapper `bash -n`, checklist parser와 `git diff --check`도 PASS했다.

2026-09-04 report 재생성 결과는 eligible `1/778=0.128535%`, 50건까지 예상 추가 `245 거래일`, zero-yield strata `market:KOSDAQ`, `owner:widget`, decision `repair_counterfactual_collection_keep_baseline`이다. 2026-09-07 v2 policy는 activation/release `2/3` carry-forward와 section snapshot hash `855a4a...`를 생성했고 loader status=`ready`다. 이후 mutable origin report를 다시 재생성해 origin hash가 `97a2ae...`에서 `383ff2...`로 달라진 상태에서도 policy loader가 같은 immutable snapshot으로 `ready`를 유지해 원 결함의 재발 방지를 확인했다.

위 605 PASS와 당시 finding 0건은 이전 검토 기록이다. §7에서 반례가 확인되어 당시 종결 판정을 철회했고, 후속 구현·최종 재검증은 §8에 기록한다.

## 7. 최종 목적·자동화·달성가능성 재검토

검토일: `2026-09-06 KST`. 현재 코드·기존 산출물·설치된 cron/timer를 읽고, 메모리 격리 반례와 관련 회귀 60건을 실행했다. 이번 재검토는 진단이며 runtime 코드, 정책값, 원천 관측, 생성된 경제성 보고서와 봇 상태는 변경하지 않았다.

### 7.1 확정 결함과 수용 기준

| ID / 우선순위 | 확인 근거와 영향 | 권장 보완 / 수용 기준 |
| --- | --- | --- |
| R1 / P1 과거 관측 버전 회귀 | `market_weakness_threshold_policy.observation_thresholds()`가 observation 내부 policy schema에도 현재 v2만 허용한다. 8/31~9/4 논리 관측 773건 중 기존 정상 v1 관측 688건이 추가로 제외되고, 현재 loader의 일별 eligible은 모두 0이다. 원문을 변경하지 않고 검사 버전만 메모리에서 이전 v1로 대조하면 127/154/154/140/113건이 통과한다. 새 보고서 생성은 누적 근거를 오히려 훼손할 수 있다. | runtime applied policy의 v2 강제와 historical observation의 v1/v2 판독을 분리한다. 원문/identity/hash를 재작성하지 않는다. 정상 688건 복원, 기존 실제 결손 85건 제외, 변조·당일 잘못된 policy 차단을 동시에 검증한다. 시장 관측 복구가 executable BBO 표본 688건 생성을 뜻하지는 않는다. |
| R2 / P1 실패를 정상 health로 오인 | `notify_panic_state_transition`은 `--observe-only`에서 source gate 실패보다 `state_updated_notify_disabled`를 먼저 반환하고, health는 반환 문자열로 ready를 판단한다. 10:02까지 정상 active, 10:12 잘못된 source를 주면 `source_gate=false`인데 `health.ready=true`, CLI exit 0, last healthy=10:12, guard age=0으로 재현된다. TTL 보완에도 오래된 차단이 연장될 수 있다. | source/latch 처리 결과와 Telegram 전달 결과를 분리한다. source 실패는 알림 ON/OFF·duplicate·pending notification과 무관하게 비정상 exit이며 마지막 정상 관측 시각을 전진시키지 않아야 한다. |
| R3 / P1 실전과 장후 EV 재현 불일치 | live guard는 300초 TTL을 적용하지만 `_market_timelines()`/`_state_at()`에는 같은 만료 처리가 없다. 마지막 정상 관측 후 600초 반례에서 live는 `blocked=false, market_weakness_state_stale`, replay는 `active=true, release=None`이다. widget/episode의 허용 분기는 guard provenance를 기록하기 전에 return하므로 stale 허용도 직접 귀속하기 어렵다. | 동일 freshness/도착순서/정책 버전 계약으로 live·replay를 대사한다. 구버전 실제 동작과 신버전 TTL 동작을 구분하고 과거 결과를 조용히 재해석하지 않는다. 정상·실패·TTL 경계·복구·재진입과 허용/차단 receipt를 검증한다. |
| R4 / P2 불필요한 horizon 결합 | 30분 EV를 평가하면서 producer는 1/3/5/10/20/30분 중 하나만 빠져도 전체 CF를 blocked 처리한다. 기존 778행에서 30분 관측은 4건인데 3건은 오직 20분 또는 3/5/10분 결손으로 탈락한다. 제외된 3건의 30분 비용 차감 수익률은 -1.84662818%, -1%, -1%이며 candidate-state matrix는 완전하다. 누락이 방향성까지 바꿀 수 있다. | horizon별 eligibility를 분리한다. 30분 평가에는 공통 entry/수량/비용/exact venue·depth/30분 freshness를 요구하되 다른 horizon 결손은 그 horizon에만 귀속한다. 원천 결손이나 실체결을 합성하지 않는다. 추가 3건은 재검증 후보이지 실전 승인 근거가 아니다. |
| R5 / P2 wrapper 성공 오인 잔존 | `run_panic_sell_defense_intraday.sh`는 producer exit 0 후 report 파일이 없으면 notifier 자체를 건너뛰고 DONE/cooldown을 기록한다. 실패 전파 보완은 notifier가 호출된 경우만 보장한다. | 해당 실행의 필수 report 존재·날짜·시각을 확인하고 missing/stale이면 FAIL 처리한다. 정상 report, 파일 미생성, 이전 산출물 잔존의 실행형 wrapper 반례를 추가한다. |

위 항목은 기존 60개 회귀가 모두 통과하는 상태에서 확인했다. 테스트 통과는 연결 계약의 무결성 또는 실전 성과 검증을 대신하지 않는다.

### 7.2 목적과 조건의 설계 재검토

| 검토 항목 | 판정 | 보완 또는 제거 범위 |
| --- | --- | --- |
| 상승/반등 예외와 회복 후 지연 진입 | `relative_strength_and_liquidity_exception.eligible`은 상수 false다. delay arm은 해제 시각만 계산하고 `executable_reentry_price_required`를 출력한다. 재진입 가격·성과 계산이나 해당 예외의 자동 승격 경로가 없어 데이터만 쌓여도 완성되지 않는다. | 기존 owner의 상승/반등·재진입 조건을 실행 가능한 비용 차감 비교로 구현할지 먼저 결정한다. 구현하지 않을 arm은 자동 결과 기대 목록에서 제외하고 명시적 미구현/제외로 닫는다. breadth 수집과 기존 운영 lock 전체를 삭제할 이유는 아니다. |
| 오분류 건수 비증가 hard veto | 전체·각 owner/market에서 EV 양수뿐 아니라 오분류 건수 비증가를 강제한다. 예를 들어 -1% 손실 1건 회피 대신 +0.1% 기회 2건을 놓치면 순기여는 +0.8%p 합계지만 오분류는 1→2로 늘어 탈락할 수 있다. 이 예시는 조건의 논리 반례이며 실제 수익 추정이 아니다. | 오분류 건수는 진단으로 내리고 비용 차감 증분 EV·OOS·꼬리손실·안전성으로 판정하는 설계를 검토한다. 단순 건수 veto 제거를 source-quality/안전 guard 제거와 혼동하지 않는다. |
| 양 시장·양 owner 공통 floor | 현재 원시 응답 778건은 widget/KOSPI 514, widget/KOSDAQ 6, episode/KOSPI 258이다. 유효 CF는 episode/KOSPI 1건뿐이다. 공통 policy 변경은 양 시장·양 owner 각각 10건과 각각 OOS 근거를 모두 요구한다. 빈 집단이 다른 유효 집단까지 묶을 수 있다. | 공통 적용을 유지한다면 그 공통 범위의 근거가 필요하다. 충분한 집단만 변경하고 나머지는 baseline을 유지하려면 producer·policy·collector·runtime·귀속을 함께 scope-versioning해야 하며, 현재 공통 policy의 미관측 시장 floor만 삭제하면 안 된다. |
| 10일/50건·OOS 3일·한 축 ±1 | 단순히 숫자가 높아서 불가능하다고 판단할 근거는 없다. 현재는 source 계약 회귀와 낮은 exact BBO 수집률이 먼저 막는다. | 기본 floor와 기존 hard safety는 유지하고 R1~R4 보완 뒤 실제 yield·표본 분포를 다시 평가한다. 획일적인 floor 완화나 강제 매수는 권고하지 않는다. |

### 7.3 자동화와 실제 개선값의 구분

| 연결 | 확인 상태 | 남은 조건 |
| --- | --- | --- |
| 장중 breadth → panic report → notifier → widget/episode guard | 설치 cron 존재. 09:06~15:28의 지정 2분 간격이며 매 10분 경계에 4분 공백이 있다. 두 거래 owner가 guard를 실제 호출하는 코드 경로 확인. | R2/R3/R5 해소와 다음 자연 실행의 정확한 health/decision receipt 필요. 300초 TTL과 4분 수집 공백 사이 여유는 약 60초이므로 작업 지연/실패도 함께 측정해야 한다. |
| 장후 attribution → hysteresis 정책 발행 | 21:15 final-refresh timer는 enabled/active이고 attribution 성공 뒤 hysteresis producer를 실행한다. | R1/R3/R4를 고치지 않으면 정상 실행돼도 비교 근거가 부정확하거나 부족하다. |
| 다음 거래일 정책 소비 | 9/7 v2 snapshot loader는 `ready`, activation/release=2/3. source snapshot 결속 자체는 유효하다. 이는 PREOPEN env 승격이 아니라 다음 거래일 collector의 exact-date policy 직접 소비 경로다. | review는 `current_policy_carry_forward_no_approved_candidate`다. 개선값 적용 완료가 아니라 baseline 유지 준비이며 실제 PID 소비·EV 효과는 미검증이다. |
| exact-route 관측 수집 | 다음-session manifest 생성 경로와 엔진 시작 시 `COMMAND_MICRO_REVERSION_OBSERVATION_SET` publish 연결 존재. | manifest 파일만으로 subscription/0B·0D receipt와 30분 성숙을 증명하지 못한다. 기동 뒤 생성/변경한 manifest가 현재 PID에 자동 재주입된다고 가정하지 않는다. |

9/4 현재 산출물은 `policy_candidate_ready=false`, `selected_policy=null`, 유효 CF `1/778=0.128535%`, 실제 realized comparison 0건이다. `245 추가 거래일`은 5일 평균 0.2건/일을 그대로 연장한 **50건 signal floor만의 산술값**이며, 수집 수리 후 예상치나 전체 승인조건 달성일이 아니다. 양 market/owner·10일·OOS 조건까지 달성한다는 보장도 없다. 전 기간 재생성 전 R1/R3 계약을 복구해야 하므로 이번에는 경제성 보고서를 재생성하지 않았다.

당시 권고: 수집·기존 운영 guard·immutable snapshot은 유지하되, R1/R2 → R3/R5 → R4 순으로 수리하고 목표/평가 범위 설계를 정리한다. 당시 runtime 후속 gate는 OPEN이었으며 후속 사용자 구현 지시에 따른 현재 종결 범위는 아래 §8이다.

## 8. R1~R5 보완·재검증 및 반등·재진입 구현 결정

### 8.1 구현·리뷰 결과

| 범위 | 보완과 재발 방지 확인 |
| --- | --- |
| R1 과거 관측 호환 | historical observation 내부 policy v1/v2 판독을 허용하되 당일 live applied policy는 v2 검증을 유지한다. observation schema-v1 unscoped 자료를 새 권한으로 승격하는 변경이 아니다. 원문·identity/hash 변경 없이 정상 688건을 복구하고 실제 결손 85건은 제외했다. |
| R2 source/health 분리 | Telegram ON/OFF·pending·duplicate 여부와 무관하게 source 실패는 nonzero다. 실제 수용된 동일 ID/시각만 last healthy를 전진시킨다. out-of-order·too-close·강제 알림 재시도는 정상 시각이나 streak를 부풀리지 않는다. |
| R3 live/replay 계약 | `risk/market_weakness_state.py`가 latch 전이와 freshness를 공유한다. 정상·실패 경계·300/301/600초·회복을 대사하고 허용 분기에도 guard receipt를 보존한다. source 실패는 UNKNOWN 경계로 streak를 초기화하되 last healthy를 갱신하지 않는다. legacy 실제 동작과 신버전 TTL 가설을 별도 표시하고 구 candidate matrix는 원관측으로 재계산하거나 제외한다. |
| R4 horizon 독립 판정 | 30분 평가에서 다른 horizon만의 결손은 제외 사유가 아니다. entry/exit exact BBO·수량/depth·5초 freshness·비용·공통 source 계약은 유지한다. 과거 blocked 행도 경제성 필드를 재검증한 경우만 해당 horizon을 복구한다. |
| R5 wrapper 완결성 | producer exit 0만으로 성공 처리하지 않는다. 알림 전에 이번 실행 이후 생성된 exact-date fresh report를 확인하며 missing/stale/wrong-date/source-fail은 FAIL·비정상 health이고 DONE/cooldown을 남기지 않는다. dry-run은 수집·health·알림·cooldown을 변경하지 않는 별도 경로다. |
| EV 목적과 계약 | 전체/owner/market 오분류 건수의 비증가 hard veto를 제거하고 `diagnostic_only`로 전환했다. 양의 비용 차감 증분 EV·OOS·꼬리손실·한 축 ±1·표본/source-quality는 유지한다. 선택 후보에는 새 replay/진단 계약을 hash로 결속하며 구 계약의 선택값은 자동 승인하지 않는다. |

반복 리뷰에서 추가로 확인한 강제 알림의 duplicate 재계수, NaN snapshot 예외, 실패 관측 경계의 누락, dry-run의 live health 변경 가능성도 수리했다. 검증 전용 옵션을 다른 알림 종류에 잘못 사용하면 입력 처리·알림 전에 거부한다. exact-owner 미체결 취소는 fresh guard decision을 명시적으로 요구한다. 사람이 읽는 attribution Markdown도 실제 정책값·유효 CF·미구현 반등/재진입 상태를 표시하며 기존 2/3 고정 문구를 제거했다. 기존 lock, 2/3 정책값, provider, 봇 상태, 주문/수량/cap/hard safety는 변경하지 않았다.

### 8.2 기존 데이터 재평가 — 보고서/정책 쓰기 없음

2026-08-31~09-04 원관측과 기존 attribution 입력을 보완 builder에 넣어 **메모리에서만** 재평가했다. 생산 보고서·원관측·9/7 정책을 덮어쓰거나 봇을 재기동하지 않았다.

| 지표 | 재평가 결과와 해석 |
| --- | --- |
| 정상 breadth 관측 | 일별 127/154/154/140/113건, 합계 688건 복구. 기존 실제 결손 85건은 제외 |
| 유효 30분 비용 차감 CF | 1→4/778건, 0.128535→0.514139%. 관측 복구가 실체결 또는 표본 합성을 뜻하지 않음 |
| 실제 realized 비교 | 0건. 30분 CF는 실제 봇 수익률 또는 기존 target/exit 실행 결과가 아님 |
| 선택 후보/현재 정책 | `candidate_ready=false`, `selected_policy=null`. 현재 9/7 immutable 정책 loader `ready`, activation/release=2/3, `current_policy_carry_forward_no_approved_candidate` 그대로 |
| 달성 가능성 | `collection_contract_gap`; widget/KOSDAQ 유효 strata는 비어 있다. 5일 평균 0.8건/일의 단순 외삽은 50건까지 추가 58일이며 승인 완료일이나 수집 수리 후 예측이 아님 |

자동화된 기존 hysteresis 후보 발행→다음 session exact-date 소비 경로는 유지된다. 이번 재평가에서 개선값은 나오지 않았다. 다음 정상 PID의 0B/0D receipt·30분 성숙·health/decision receipt·장후 yield를 확인해야 실제 적용과 개선 후보 생성 가능성을 판단할 수 있다. 공통 policy의 미관측 owner/market floor만 삭제하지 않는다. 부분 적용 정책은 충분한 근거가 생긴 뒤 scope를 producer→policy→collector→runtime→귀속에 일관되게 결속하는 별도 설계가 필요하다.

### 8.3 반등·재진입 평가: 구현 결정, 기존 timing으로 통합

**구현을 권고하고 통합 구현 대상으로 확정한다.** 시장 약세 때의 회피 손실뿐 아니라 이후 상승 기회도 비교해야 EV 목적에 맞다. 그러나 독립 매수 경로나 미구현 arm의 자동 승격을 새로 만들지는 않는다.

- 구현 owner: 기존 `machine_entry_timing_tuning`의 economic replay/confirmation 평가. 기존 guard 유지(control), 기존 owner의 새 유효 상승·반등 확인, 시장 회복 후 새 owner 신호 확인을 동일 표본의 비용 차감 증분 EV로 비교한다.
- 시장 회복만으로 매수하거나 만료된 옛 신호를 되살리지 않는다. owner별 scan window·signal validity·기존 상승/반등 확인·보유/수량·target/exit·broker/hard-safety 계약을 그대로 적용한다.
- 같은 exact route의 fresh BBO/depth·비용과 owner별 terminal outcome을 확보하고 OOS·놓친 상승·꼬리손실을 함께 비교한다. 단순 30분 markout을 실체결 성과나 target/exit 재현으로 대체하지 않는다.
- 이번에는 **구현 여부 결정과 출력 계약 정정까지** 완료했다. delay/relative-strength arm은 `eligible=false`, `automatic_evaluation_enabled=false`, `implementation_status=integration_required`와 구현 owner를 명시한다. 실제 재진입 가격·성과 평가 로직은 아직 없으며 데이터 대기만으로 완성되지 않는다.
- 다음 구현 항목은 `MarketWeaknessReboundReentryIntegration0907`, 자연 운영 확인은 `MarketWeaknessNaturalEvidence0907`이다. 새 평가 구현과 별개로 live 반등 예외 활성화는 이번 변경에 포함하지 않는다.
- 후속 계획 수립(2026-09-06): [상세 구현안·다음 권장 액션](../proposals/market-weakness-rebound-reentry-evaluation-plan-2026-09-06.md)에 actual-only timing과 별도 source-only section, A0 기존 재개 포함/A1 회복 후 새 신호/A2 약세 중 반등 가설, P0~P6와 검증·유지/종료 기준을 구체화했다. 계획 완료는 `MarketWeaknessReboundReentryPlan0907`, 구현은 여전히 OPEN이며 첫 주 유지 판정은 `MarketWeaknessReboundReentryRetention0911`이다. 아래 745 PASS는 기존 R1~R5 검증이며 신규 평가 로직의 구현/검증 완료를 뜻하지 않는다.

### 8.4 최종 검증

- 최종 통합 회귀 **745 PASS**: breadth collector, notifier, live guard, weakness response, microstructure attribution, panic report, widget·Samsung·저가주 owner, hysteresis policy, wrapper, error-detector completion/coverage 및 machine policy approval의 14개 테스트 모듈이다. 이전 605건·중간 회귀 수치와 합산하지 않는다.
- 변경 Python 18개 파일 Ruff/Black, 변경 runtime/producer compileall, wrapper `bash -n`, `git diff --check`와 문서 parser PASS. **당시** parser에서 OPEN owner는 자연 검증과 반등·재진입 통합 구현 2개였다. 후속 계획 수립으로 첫 주 유지 판정 owner를 추가했으며 현재 owner는 §8.3과 daily checklist를 따른다.
- 구현→코드리뷰→결함 보완→재리뷰→연결 회귀를 반복해 **이번 보완 범위의 미해결 finding 0건**으로 리뷰 게이트를 닫았다. producer→policy validator, TTL 경계, source 실패, 알림/검증 부작용, 허용 guard receipt, 문서 상태 반례를 포함한다.
- 전체 저장소 전수 테스트·실제 브로커 호출·봇 재기동·생산 보고서 재생성은 수행하지 않았다. 자연 PID 적용/0B·0D 수신과 경제성 표본은 아직 미검증이며 별도 OPEN이다. 반등·재진입 경제성 로직은 구현 결정만 완료했고 아직 구현되지 않았다. 이 결론은 실제 수익 개선 또는 live 반등 예외 승인 판정이 아니다.
